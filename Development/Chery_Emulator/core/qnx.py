from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import socket
from typing import List, Optional


class QnxConsoleError(RuntimeError):
    """Raised when QNX console connection fails."""


class QnxConsole:
    """Lightweight TCP client for QEMU QNX UART sockets.

    This is intentionally simple and synchronous. FastAPI handlers can call it
    from a threadpool if needed. Real-time streaming/WebSocket integration can
    be added later on top.
    """

    def __init__(self, host: str = "localhost", port: int = 1234, timeout: float = 1.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def _open(self) -> socket.socket:
        try:
            sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        except OSError as exc:
            raise QnxConsoleError(f"Failed to connect to QNX console at {self.host}:{self.port}: {exc}")
        return sock

    def send_line(self, line: str) -> None:
        """Send a single line to QNX console (adds trailing newline)."""

        try:
            sock = self._open()
        except QnxConsoleError:
            # For now we silently ignore connection errors at this layer.
            return

        with sock:
            data = (line + "\n").encode("utf-8", errors="replace")
            try:
                sock.sendall(data)
            except OSError:
                # No need to propagate for prototype.
                return

    def tail(self, max_bytes: int = 4096) -> list[str]:
        """Fetch a small snapshot from the console socket.

        This is *not* a full streaming client – it is used to quickly inspect
        the console for debugging in the emulator core.
        """

        try:
            sock = self._open()
        except QnxConsoleError:
            return []

        chunks: list[bytes] = []
        remaining = max_bytes

        with sock:
            sock.settimeout(self.timeout)
            while remaining > 0:
                try:
                    chunk = sock.recv(min(1024, remaining))
                except OSError:
                    break
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)

        if not chunks:
            return []

        text = b"".join(chunks).decode("utf-8", errors="replace")
        return text.splitlines()


@dataclass
class CanFrame:
    """Abstract CAN frame used by the emulator core.

    This models the *logical* frame; actual encoding to raw bytes and mapping
    to specific IDs can be added later from the QNX/Android analyses.
    """

    can_id: int
    data: bytes
    description: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CanBus:
    """In-memory CAN bus model for high-level commands."""

    history: List[CanFrame] = field(default_factory=list)
    headlights_on: bool = False

    def _record(self, frame: CanFrame) -> None:
        self.history.append(frame)
        if len(self.history) > 256:
            self.history = self.history[-256:]

    def emit_headlights(self, on: bool) -> List[CanFrame]:
        """Emit frames that correspond to turning headlights on/off.

        For now this is a placeholder that records abstract frames only.
        Concrete IDs/bytes will be wired from the QNX/CAN analyses.
        """

        self.headlights_on = on

        state_byte = b"\x01" if on else b"\x00"
        frame = CanFrame(
            can_id=0x000,  # placeholder, real ID comes from documentation
            data=state_byte,
            description="HEADLIGHTS_ON" if on else "HEADLIGHTS_OFF",
        )
        self._record(frame)
        return [frame]

    def last_frame(self) -> Optional[CanFrame]:
        return self.history[-1] if self.history else None

    def to_dict(self) -> dict[str, object]:
        return {
            "headlights_on": self.headlights_on,
            "history": [
                {
                    "can_id": f"0x{f.can_id:03X}",
                    "data_hex": f.data.hex(),
                    "description": f.description,
                    "created_at": f.created_at.isoformat() + "Z",
                }
                for f in self.history
            ],
        }


# Global singletons used by the core API.
qnx_console = QnxConsole()
can_bus = CanBus()


