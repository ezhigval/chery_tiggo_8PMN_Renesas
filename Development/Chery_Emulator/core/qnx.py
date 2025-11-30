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


class QnxPl011Console:
    """TCP client for QNX PL011 (ttyAMA0) console socket.

    Стандартный UART virt-машины на адресе 0x9000000. QNX может использовать
    его по умолчанию для boot логов и консоли.
    """

    def __init__(self, host: str = "localhost", port: int = 1237, timeout: float = 1.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def _open(self) -> socket.socket:
        try:
            sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        except OSError as exc:
            raise QnxConsoleError(f"Failed to connect to QNX PL011 console at {self.host}:{self.port}: {exc}")
        return sock

    def send_line(self, line: str) -> None:
        """Send a single line to QNX PL011 console (adds trailing newline)."""

        try:
            sock = self._open()
        except QnxConsoleError:
            return

        with sock:
            data = (line + "\n").encode("utf-8", errors="replace")
            try:
                sock.sendall(data)
            except OSError:
                return

    def tail(self, max_bytes: int = 4096) -> list[str]:
        """Fetch a small snapshot from the PL011 console socket.

        This is used to quickly inspect QNX boot logs and console output.
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


class QnxVirtioConsole:
    """TCP client for QNX virtio-console socket.

    QNX IFS содержит vdev-virtio-console.so, поэтому консоль QNX скорее всего
    идёт через virtio-console, а не через SCIF. Этот класс подключается к
    сокету, который QEMU создаёт для virtio-console chardev.
    """

    def __init__(self, host: str = "localhost", port: int = 1236, timeout: float = 1.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def _open(self) -> socket.socket:
        try:
            sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        except OSError as exc:
            raise QnxConsoleError(f"Failed to connect to QNX virtio-console at {self.host}:{self.port}: {exc}")
        return sock

    def send_line(self, line: str) -> None:
        """Send a single line to QNX virtio-console (adds trailing newline)."""

        try:
            sock = self._open()
        except QnxConsoleError:
            return

        with sock:
            data = (line + "\n").encode("utf-8", errors="replace")
            try:
                sock.sendall(data)
            except OSError:
                return

    def tail(self, max_bytes: int = 4096) -> list[str]:
        """Fetch a small snapshot from the virtio-console socket.

        This is used to quickly inspect QNX boot logs and console output.
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
    """In-memory CAN bus model for high-level commands.

    Simulates real automotive CAN bus with BCM, ECM, and other module signals
    that QNX cluster expects to receive for proper initialization.
    """

    history: List[CanFrame] = field(default_factory=list)
    headlights_on: bool = False
    doors_unlocked: bool = False
    driver_door_open: bool = False
    engine_running: bool = False
    ignition_on: bool = False
    proximity_detected: bool = False
    alarm_armed: bool = True

    # Bitmask for all doors. Mapping:
    #   bit0: driver
    #   bit1: passenger
    #   bit2: rear_left
    #   bit3: rear_right
    #   bit4: trunk
    #   bit5: hood
    doors_bits: int = 0

    def _record(self, frame: CanFrame) -> None:
        self.history.append(frame)
        if len(self.history) > 256:
            self.history = self.history[-256:]

        # Try to transmit frame through CAN server if available
        try:
            from .can_server import can_server
            if can_server is not None:
                can_server.transmit_frame(frame)
        except (ImportError, AttributeError):
            # CAN server not available, that's OK
            pass

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

    def set_alarm(self, armed: bool) -> List[CanFrame]:
        """Emit frames for alarm arm/disarm.

        This models central locking / security system changes.
        """

        self.alarm_armed = armed
        frame = CanFrame(
            can_id=0x103,  # placeholder CAN ID for alarm state
            data=b"\x01" if armed else b"\x00",
            description="ALARM_ARMED" if armed else "ALARM_DISARMED",
        )
        self._record(frame)
        return [frame]

    def set_door(self, name: str, open_: bool) -> List[CanFrame]:
        """Update internal door bitmask and emit aggregate door-status frame."""

        mapping = {
            "driver": 0,
            "passenger": 1,
            "rear_left": 2,
            "rear_right": 3,
            "trunk": 4,
            "hood": 5,
        }
        if name not in mapping:
            return []

        bit = 1 << mapping[name]
        if open_:
            self.doors_bits |= bit
        else:
            self.doors_bits &= ~bit

        # Keep legacy driver_door_open flag in sync.
        if name == "driver":
            self.driver_door_open = open_

        frame = CanFrame(
            can_id=0x201,  # door status (placeholder; see docs for real ID)
            data=bytes([self.doors_bits & 0xFF]),
            description=f"DOOR_{name.upper()}_{'OPEN' if open_ else 'CLOSED'}",
        )
        self._record(frame)
        return [frame]

    def emit_doors_unlock(self, unlocked: bool) -> List[CanFrame]:
        """Emit CAN frames for door unlock/lock state.

        This simulates BCM (Body Control Module) signals that QNX cluster
        may be waiting for to initialize or show certain UI states.
        """

        self.doors_unlocked = unlocked

        # Placeholder CAN ID - реальные ID нужно взять из документации
        # Обычно это что-то вроде 0x1XX для BCM сообщений
        state_byte = b"\x01" if unlocked else b"\x00"
        frame = CanFrame(
            can_id=0x100,  # placeholder BCM door status
            data=state_byte,
            description="DOORS_UNLOCKED" if unlocked else "DOORS_LOCKED",
        )
        self._record(frame)
        return [frame]

    def emit_engine_status(self, running: bool) -> List[CanFrame]:
        """Emit CAN frames for engine running status.

        This simulates ECM (Engine Control Module) signals that QNX cluster
        definitely needs to show engine-related information and may be
        blocking UI initialization until received.
        """

        self.engine_running = running

        # Placeholder CAN ID - реальные ID нужно взять из документации
        # Обычно это что-то вроде 0x2XX для ECM сообщений
        state_byte = b"\x01" if running else b"\x00"
        frame = CanFrame(
            can_id=0x200,  # placeholder ECM engine status
            data=state_byte,
            description="ENGINE_RUNNING" if running else "ENGINE_OFF",
        )
        self._record(frame)
        return [frame]

    def emit_proximity(self, detected: bool) -> List[CanFrame]:
        """Emit CAN frames for proximity detection (key fob near car).

        When user approaches the car, BCM may send proximity signals.
        This may trigger initial wake-up but displays stay off.
        """

        self.proximity_detected = detected

        frame = CanFrame(
            can_id=0x101,  # placeholder BCM proximity
            data=b"\x01" if detected else b"\x00",
            description="PROXIMITY_DETECTED" if detected else "PROXIMITY_LOST",
        )
        self._record(frame)
        return [frame]

    def emit_driver_door(self, open: bool) -> List[CanFrame]:
        """Emit CAN frames for driver door open/close state.

        This is critical: when driver door opens, displays should wake up
        and show splash screen. This is the key signal for display activation.
        """

        self.driver_door_open = open

        frame = CanFrame(
            can_id=0x102,  # placeholder BCM driver door
            data=b"\x01" if open else b"\x00",
            description="DRIVER_DOOR_OPEN" if open else "DRIVER_DOOR_CLOSED",
        )
        self._record(frame)
        return [frame]

    def emit_ignition(self, on: bool) -> List[CanFrame]:
        """Emit CAN frames for ignition/start-stop button state.

        When start-stop button is pressed, this triggers:
        - System boot sequence
        - Cluster initialization
        - Welcome sound and animation
        - Android launcher startup
        """

        self.ignition_on = on

        frame = CanFrame(
            can_id=0x201,  # placeholder ECM/BCM ignition
            data=b"\x01" if on else b"\x00",
            description="IGNITION_ON" if on else "IGNITION_OFF",
        )
        self._record(frame)
        return [frame]

    def emit_power_ready(self) -> List[CanFrame]:
        """Emit CAN frames for POWER_READY state (first short press).

        POWER_READY: power ready, cluster/QNX starts working.
        """

        frames: List[CanFrame] = []

        # Ignition is on
        frames.extend(self.emit_ignition(True))

        # Power ready signal (BCM)
        frame = CanFrame(
            can_id=0x202,  # placeholder BCM power ready
            data=b"\x01",
            description="POWER_READY",
        )
        self._record(frame)
        frames.append(frame)

        return frames

    def emit_acc_on(self, engine_running: bool = False) -> List[CanFrame]:
        """Emit CAN frames for ACC_ON state (second short press).

        ACC_ON: accessory on, Android HU starts, radio, etc.
        If engine_running=True, engine is running but ignition is in ACC position.
        """

        frames: List[CanFrame] = []

        # Ignition is on
        frames.extend(self.emit_ignition(True))

        # ACC ON signal (BCM)
        frame = CanFrame(
            can_id=0x203,  # placeholder BCM ACC ON
            data=b"\x01",
            description="ACC_ON",
        )
        self._record(frame)
        frames.append(frame)

        # Engine status if running
        if engine_running:
            frames.extend(self.emit_engine_status(True))

        return frames

    def emit_sequence_startup(self) -> List[CanFrame]:
        """Emit complete startup sequence: proximity → doors → ignition → engine.

        This simulates the real car startup sequence:
        1. Proximity detected (key fob near)
        2. Doors unlock
        3. Driver door opens (displays wake up)
        4. Ignition on (start-stop pressed)
        5. Engine starts
        """

        frames: List[CanFrame] = []

        # Sequence with small delays would be better, but for now emit all
        frames.extend(self.emit_proximity(True))
        frames.extend(self.emit_doors_unlock(True))
        frames.extend(self.emit_driver_door(True))
        frames.extend(self.emit_ignition(True))
        frames.extend(self.emit_engine_status(True))

        return frames

    def last_frame(self) -> Optional[CanFrame]:
        return self.history[-1] if self.history else None

    def to_dict(self) -> dict[str, object]:
        return {
            "headlights_on": self.headlights_on,
            "doors_unlocked": self.doors_unlocked,
            "driver_door_open": self.driver_door_open,
            "engine_running": self.engine_running,
            "ignition_on": self.ignition_on,
            "proximity_detected": self.proximity_detected,
            "alarm_armed": self.alarm_armed,
            "doors_bits": self.doors_bits,
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
qnx_pl011_console = QnxPl011Console()
qnx_virtio_console = QnxVirtioConsole()
can_bus = CanBus()

# Import CAN server for integration
try:
    from .can_server import can_server
except ImportError:
    can_server = None  # type: ignore[assignment]


