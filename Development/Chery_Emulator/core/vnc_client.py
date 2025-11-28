from __future__ import annotations

import socket
import struct
from dataclasses import dataclass
from threading import Lock
from typing import Optional

from PIL import Image


@dataclass
class VncPixelFormat:
    bits_per_pixel: int
    depth: int
    big_endian: int
    true_color: int
    red_max: int
    green_max: int
    blue_max: int
    red_shift: int
    green_shift: int
    blue_shift: int


class VncClient:
    """Minimal RFB 3.8/VNC client for grabbing full-frame snapshots.

    - Supports only security type "None".
    - Requests encoding RAW only.
    - Assumes 32bpp true-color, little-endian, BGRX layout.
    - Intended for local QEMU instances on 127.0.0.1.
    """

    def __init__(self, host: str, port: int, timeout: float = 1.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: Optional[socket.socket] = None
        self._lock = Lock()
        self._width: int = 0
        self._height: int = 0
        self._pixfmt: Optional[VncPixelFormat] = None
        self._handshaken = False

    # ----- Public API -----

    def get_frame_png(self) -> Optional[bytes]:
        """Return latest framebuffer as PNG bytes (or None on failure).

        Thread-safe and tolerant to transient connection errors. On any
        protocol error it will close the socket and fall back to a fresh
        connection on the next call.
        """

        with self._lock:
            try:
                if not self._ensure_handshake():
                    return None
                raw = self._request_full_frame_raw()
                if raw is None or self._width <= 0 or self._height <= 0:
                    return None
                return self._encode_png(raw, self._width, self._height)
            except Exception:
                self._close()
                return None

    # ----- Internal helpers -----

    def _close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
        self._sock = None
        self._handshaken = False

    def _ensure_socket(self) -> bool:
        if self._sock is not None:
            return True
        try:
            sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
            sock.settimeout(self.timeout)
        except OSError:
            return False
        self._sock = sock
        self._handshaken = False
        return True

    def _recv_exact(self, n: int) -> Optional[bytes]:
        assert self._sock is not None
        data = b""
        while len(data) < n:
            try:
                chunk = self._sock.recv(n - len(data))
            except OSError:
                return None
            if not chunk:
                return None
            data += chunk
        return data

    def _send_all(self, data: bytes) -> bool:
        assert self._sock is not None
        try:
            self._sock.sendall(data)
            return True
        except OSError:
            return False

    def _ensure_handshake(self) -> bool:
        if self._handshaken and self._sock is not None:
            return True
        if not self._ensure_socket():
            return False
        assert self._sock is not None

        # 1. Protocol version
        ver = self._recv_exact(12)
        if ver is None or not ver.startswith(b"RFB "):
            self._close()
            return False

        # Echo back 3.8 (or whatever server suggested).
        try:
            self._send_all(b"RFB 003.008\n")
        except Exception:
            self._close()
            return False

        # 2. Security types
        sec_types_raw = self._recv_exact(1)
        if sec_types_raw is None:
            self._close()
            return False
        n_types = sec_types_raw[0]
        if n_types == 0:
            # Server will send a reason string; ignore for now.
            self._close()
            return False

        sec_types = self._recv_exact(n_types)
        if sec_types is None:
            self._close()
            return False

        if 1 in sec_types:
            # Choose "None".
            if not self._send_all(b"\x01"):
                self._close()
                return False
        else:
            # No supported security type.
            self._close()
            return False

        # 3. SecurityResult (4 bytes, 0 == OK)
        sec_result = self._recv_exact(4)
        if sec_result is None or struct.unpack("!I", sec_result)[0] != 0:
            self._close()
            return False

        # 4. ClientInit (shared flag = 1)
        if not self._send_all(b"\x01"):
            self._close()
            return False

        # 5. ServerInit
        init_hdr = self._recv_exact(24)
        if init_hdr is None:
            self._close()
            return False

        self._width, self._height = struct.unpack("!HH", init_hdr[:4])
        (
            bpp,
            depth,
            big_endian,
            true_color,
            red_max,
            green_max,
            blue_max,
            red_shift,
            green_shift,
            blue_shift,
        ) = struct.unpack("!BBBBHHHBBBxxx", init_hdr[4:20])

        self._pixfmt = VncPixelFormat(
            bits_per_pixel=bpp,
            depth=depth,
            big_endian=big_endian,
            true_color=true_color,
            red_max=red_max,
            green_max=green_max,
            blue_max=blue_max,
            red_shift=red_shift,
            green_shift=green_shift,
            blue_shift=blue_shift,
        )

        # Skip name string.
        name_len_bytes = init_hdr[20:24]
        name_len = struct.unpack("!I", name_len_bytes)[0]
        if name_len:
            if self._recv_exact(name_len) is None:
                self._close()
                return False

        # 6. SetPixelFormat: request 32bpp, true-color, little-endian, BGRX.
        # bits_per_pixel=32, depth=24, big_endian=0, true_color=1,
        # red_max=255, green_max=255, blue_max=255, shifts 16/8/0.
        spf = struct.pack(
            "!BBBBHHHBBBxxx",
            32,
            24,
            0,
            1,
            255,
            255,
            255,
            16,
            8,
            0,
        )
        msg_set_pf = b"\x00" + b"\x00\x00\x00" + spf
        if not self._send_all(msg_set_pf):
            self._close()
            return False

        # 7. SetEncodings: RAW only (0).
        msg_set_enc = struct.pack("!BBHii", 2, 0, 1, 0, 0)
        if not self._send_all(msg_set_enc):
            self._close()
            return False

        self._handshaken = True
        return True

    def _request_full_frame_raw(self) -> Optional[bytes]:
        if self._sock is None or not self._handshaken:
            return None
        if self._width <= 0 or self._height <= 0:
            return None

        # FramebufferUpdateRequest (type=3, incremental=0, full rect).
        msg = struct.pack("!BBHHHH", 3, 0, 0, 0, self._width, self._height)
        if not self._send_all(msg):
            return None

        # Expect FramebufferUpdate (type=0).
        hdr = self._recv_exact(4)
        if hdr is None or hdr[0] != 0:
            return None
        _msg_type, _pad, n_rects = struct.unpack("!BBH", hdr)
        if n_rects == 0:
            return None

        # For now, take the first rectangle and assume it covers the full screen.
        rect_hdr = self._recv_exact(12)
        if rect_hdr is None:
            return None
        x, y, w, h, enc = struct.unpack("!HHHHI", rect_hdr)
        if enc != 0:  # RAW encoding only
            return None

        bytes_per_pixel = 4  # we requested 32bpp
        expected = w * h * bytes_per_pixel
        data = self._recv_exact(expected)
        if data is None or len(data) != expected:
            return None

        # Consume any remaining rectangles in the update to stay in sync.
        for _ in range(n_rects - 1):
            rh = self._recv_exact(12)
            if rh is None:
                return None
            _rx, _ry, rw, rh2, enc2 = struct.unpack("!HHHHI", rh)
            if enc2 != 0:
                return None
            extra = self._recv_exact(rw * rh2 * bytes_per_pixel)
            if extra is None:
                return None

        # If rectangle smaller than full screen, we could composite, but for
        # now assume QEMU sends full-frame updates.
        if w != self._width or h != self._height:
            # Simple guard; avoid misinterpreting sizes.
            return None

        return data

    def _encode_png(self, raw_bgrx: bytes, width: int, height: int) -> Optional[bytes]:
        """Convert raw BGRX bytes to PNG using Pillow."""

        try:
            # RFB uses B,G,R,X (little-endian) with shifts 16/8/0, so Pillow's
            # "BGRX" raw decoder is appropriate.
            img = Image.frombytes("RGB", (width, height), raw_bgrx, "raw", "BGRX")
            from io import BytesIO

            buf = BytesIO()
            img.save(buf, format="PNG", optimize=True)
            return buf.getvalue()
        except Exception:
            return None



