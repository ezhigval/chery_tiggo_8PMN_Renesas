"""CAN bus server for transmitting CAN frames to QNX.

This module provides a CAN message server that can transmit CAN frames
to QNX through a virtual CAN interface. Uses Linux socketcan (vcan) interface
to connect to QEMU's can-host-socketcan.
"""

from __future__ import annotations

import platform
import socket
import struct
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .qnx import CanFrame

# Linux socketcan includes
# Socketcan работает только на Linux, не на macOS/Windows
_is_linux = platform.system() == "Linux"

try:
    if _is_linux:
        import ctypes
        import ctypes.util

        # SocketCAN constants
        AF_CAN = 29  # Linux AF_CAN
        PF_CAN = AF_CAN
        SOCK_RAW = 3
        CAN_RAW = 1

        # Linux can_frame structure (for socketcan)
        class LinuxCanFrame(ctypes.Structure):
            _fields_ = [
                ("can_id", ctypes.c_uint32),  # 32 bit CAN_ID + EFF/RTR/ERR flags
                ("can_dlc", ctypes.c_uint8),   # data length code: 0 .. 8
                ("flags", ctypes.c_uint8),      # flags
                ("res0", ctypes.c_uint8),      # reserved
                ("res1", ctypes.c_uint8),      # reserved
                ("data", ctypes.c_uint8 * 8),  # CAN data (0-8 bytes)
            ]

        CAN_MTU = ctypes.sizeof(LinuxCanFrame)  # 16 bytes

        _socketcan_available = True
    else:
        _socketcan_available = False
        LinuxCanFrame = None  # type: ignore[assignment, misc]
        CAN_MTU = 16
except (ImportError, OSError, AttributeError):
    _socketcan_available = False
    LinuxCanFrame = None  # type: ignore[assignment, misc]
    CAN_MTU = 16


@dataclass
class CanServerConfig:
    """Configuration for CAN server."""

    host: str = "localhost"
    port: int = 1238
    can_interface: str = "vcan0"  # Linux socketcan interface (vcan0, can0, etc.)


class CanServer:
    """CAN message server for transmitting frames to QNX.

    This server listens for CAN frames from the CanBus model and transmits
    them to QNX. Currently uses TCP socket, but can be extended to use
    socketcan or other mechanisms.
    """

    def __init__(self, config: Optional[CanServerConfig] = None, repo_root: Optional[Path] = None) -> None:
        self.config = config or CanServerConfig()
        self._socket: Optional[socket.socket] = None
        self._listening_socket: Optional[socket.socket] = None
        self._socketcan_socket: Optional[socket.socket] = None
        self._connected = False
        self._frames_sent = 0
        self._frames_failed = 0
        self._last_connection_time: Optional[datetime] = None
        self._use_socketcan = False

        # Setup logging
        if repo_root is None:
            repo_root = Path(__file__).resolve().parents[3]
        self._repo_root = repo_root
        self._log_path = repo_root / "Development" / "Chery_Emulator" / "logs" / "can_server.log"
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def _log(self, message: str) -> None:
        """Log a message to the CAN server log file."""
        try:
            ts = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
            with self._log_path.open("a", encoding="utf-8") as f:
                f.write(f"{ts} {message}\n")
        except OSError:
            pass

    def start(self) -> None:
        """Start the CAN server.

        Tries to use Linux socketcan interface first (vcan0), falls back to TCP socket.
        On macOS/Windows, socketcan is not available, so TCP socket is used.
        """

        # Try socketcan first (preferred method, Linux only)
        if _socketcan_available and self.config.can_interface:
            try:
                self._start_socketcan()
                return
            except OSError as exc:
                self._log(f"Failed to start socketcan ({self.config.can_interface}): {exc}")
                self._log("Falling back to TCP socket mode")
        elif not _is_linux and self.config.can_interface:
            self._log(f"Socketcan not available on {platform.system()}")
            self._log("Note: Use Docker container (docker/can-bridge) for socketcan on macOS")
            self._log("Falling back to TCP socket mode (QEMU won't be able to connect)")

        # Fallback to TCP socket mode
        self._start_tcp_socket()

    def _start_socketcan(self) -> None:
        """Start CAN server using Linux socketcan interface."""
        import ctypes

        # Create CAN socket
        sock = socket.socket(PF_CAN, SOCK_RAW, CAN_RAW)

        # Get interface index
        ifr = ctypes.create_string_buffer(self.config.can_interface.encode() + b'\x00' * (16 - len(self.config.can_interface)))
        SIOCGIFINDEX = 0x8933
        ioctl_result = ctypes.CDLL(None).ioctl(sock.fileno(), SIOCGIFINDEX, ctypes.addressof(ifr))
        if ioctl_result < 0:
            raise OSError(f"Interface {self.config.can_interface} not found")

        # Bind to interface
        addr = struct.pack("=HI", AF_CAN, 0)  # AF_CAN, interface index (will be set by kernel)
        sock.bind((AF_CAN, 0))

        self._socketcan_socket = sock
        self._use_socketcan = True
        self._connected = True
        self._log(f"CAN server started using socketcan interface: {self.config.can_interface}")

    def _start_tcp_socket(self) -> None:
        """Start CAN server using TCP socket (fallback mode)."""
        if self._listening_socket is not None:
            self._log("CAN server already started")
            return

        try:
            # Create listening socket for QEMU connections
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((self.config.host, self.config.port))
            self._socket.listen(1)
            self._socket.settimeout(0.1)  # Short timeout for non-blocking accept
            self._listening_socket = self._socket  # Keep reference to listening socket
            self._socket = None  # Will be set when client connects
            self._use_socketcan = False
            self._log(f"CAN server started (TCP mode), listening on {self.config.host}:{self.config.port}")
        except OSError as exc:
            # Port may be in use, that's OK for now
            self._socket = None
            self._listening_socket = None
            self._log(f"Failed to start CAN server: {exc}")
            return

    def stop(self) -> None:
        """Stop the CAN server and close all connections."""

        was_connected = self._connected

        # Close socketcan socket
        if self._socketcan_socket is not None:
            try:
                self._socketcan_socket.close()
            except OSError:
                pass
            self._socketcan_socket = None

        # Close client connection first
        if self._socket is not None:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None

        # Close listening socket
        if self._listening_socket is not None:
            try:
                self._listening_socket.close()
            except OSError:
                pass
            self._listening_socket = None

        self._connected = False
        self._use_socketcan = False
        if was_connected:
            self._log("CAN server stopped, client disconnected")
        else:
            self._log("CAN server stopped")

    def transmit_frame(self, frame: CanFrame) -> bool:
        """Transmit a CAN frame to QNX.

        Returns True if frame was transmitted, False otherwise.
        """

        if self._use_socketcan:
            return self._transmit_socketcan(frame)
        else:
            return self._transmit_tcp(frame)

    def _transmit_socketcan(self, frame: CanFrame) -> bool:
        """Transmit CAN frame using socketcan interface."""
        if not self._connected or self._socketcan_socket is None:
            self._frames_failed += 1
            if self._frames_failed % 10 == 1:
                self._log(f"Failed to transmit CAN frame 0x{frame.can_id:03X}: not connected")
            return False

        try:
            # Format: Linux can_frame structure
            # can_id (uint32), can_dlc (uint8), flags (uint8), res0 (uint8), res1 (uint8), data[8]
            can_id = frame.can_id | 0x80000000  # Extended frame flag (EFF)
            data_len = min(len(frame.data), 8)
            data = frame.data[:8] + b"\x00" * (8 - data_len)

            # Pack Linux can_frame structure (native byte order)
            packet = struct.pack("=IBBBBB8s", can_id, data_len, 0, 0, 0, data)
            self._socketcan_socket.send(packet)
            self._frames_sent += 1
            if self._frames_sent % 50 == 1:
                self._log(f"Transmitted CAN frame 0x{frame.can_id:03X} via socketcan (total: {self._frames_sent})")
            return True
        except OSError as exc:
            self._connected = False
            self._frames_failed += 1
            self._log(f"Failed to transmit CAN frame 0x{frame.can_id:03X}: {exc}")
            return False

    def _transmit_tcp(self, frame: CanFrame) -> bool:
        """Transmit CAN frame using TCP socket (fallback mode)."""
        # Check for new connections before transmitting
        self.check_connection()

        if not self._connected or self._socket is None:
            self._frames_failed += 1
            if self._frames_failed % 10 == 1:  # Log every 10th failure to avoid spam
                self._log(f"Failed to transmit CAN frame 0x{frame.can_id:03X}: not connected")
            return False

        try:
            # CAN frame format: CAN ID (4 bytes) + data length (1 byte) + data (0-8 bytes)
            # Extended format: 29-bit CAN ID
            can_id = frame.can_id | 0x80000000  # Extended frame flag
            data_len = len(frame.data)
            if data_len > 8:
                data_len = 8
                data = frame.data[:8]
            else:
                data = frame.data + b"\x00" * (8 - data_len)

            # Pack: CAN ID (uint32), data length (uint8), data (8 bytes), padding
            packet = struct.pack(">IB8s", can_id, data_len, data)
            self._socket.sendall(packet)
            self._frames_sent += 1
            if self._frames_sent % 50 == 1:  # Log every 50th frame to avoid spam
                self._log(f"Transmitted CAN frame 0x{frame.can_id:03X} via TCP (total: {self._frames_sent})")
            return True
        except OSError as exc:
            self._connected = False
            self._frames_failed += 1
            self._log(f"Failed to transmit CAN frame 0x{frame.can_id:03X}: {exc}")
            return False

    def check_connection(self) -> bool:
        """Check if a client (QEMU/QNX) is connected and accept if pending.

        This should be called periodically (e.g., when transmitting frames)
        to accept new connections from QEMU.
        """

        if self._listening_socket is None:
            self._connected = False
            return False

        # If already connected, verify connection is still alive
        if self._socket is not None and self._connected:
            try:
                # Use getsockopt to check if socket is still valid
                self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                return True
            except OSError:
                # Connection lost, reset
                try:
                    self._socket.close()
                except OSError:
                    pass
                self._socket = None
                self._connected = False
                self._log("CAN client connection lost")

        # Try to accept a new connection (non-blocking)
        try:
            self._listening_socket.settimeout(0.1)  # Short timeout for non-blocking
            client, addr = self._listening_socket.accept()
            # Close old connection if any
            if self._socket is not None:
                try:
                    self._socket.close()
                except OSError:
                    pass
            self._socket = client
            self._connected = True
            self._last_connection_time = datetime.utcnow()
            self._log(f"CAN client connected from {addr[0]}:{addr[1]}")
            return True
        except socket.timeout:
            # No pending connection
            return False
        except OSError as exc:
            # Connection error
            self._connected = False
            self._log(f"Error accepting CAN connection: {exc}")
            return False


    def get_stats(self) -> dict[str, object]:
        """Get CAN server statistics."""
        return {
            "listening": self._listening_socket is not None,
            "connected": self._connected,
            "frames_sent": self._frames_sent,
            "frames_failed": self._frames_failed,
            "last_connection_time": self._last_connection_time.isoformat() + "Z" if self._last_connection_time else None,
        }


# Global CAN server instance
can_server = CanServer()

