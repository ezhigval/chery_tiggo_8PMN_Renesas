from __future__ import annotations

from pathlib import Path
from typing import Optional
import logging
import platform

import asyncio

from fastapi import FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .state import IgnitionState
from .state_manager import StateManager
from .ignition_controller import IgnitionController
from .config import config
from .boot_monitor import BootMonitor

logger = logging.getLogger(__name__)
from .emulator import emulator_manager
from .api_controls import router as controls_router
from .qnx import qnx_console, qnx_pl011_console, qnx_virtio_console, can_bus
from .qnx_vm import qnx_vm_manager
try:
    from .can_server import can_server
except ImportError:
    can_server = None  # type: ignore[assignment]
from .display_frames import display_manager
from .graphics_vnc import hu_vnc_frame, cluster_vnc_frame


class StateResponse(BaseModel):
    ignition_state: str
    updated_at: str
    emulator_status: str
    emulator_error: str | None = None
    emulator_pid: int | None = None
    alarm_armed: bool
    doors: dict[str, bool]
    driver_ready: bool
    proximity_detected: bool = False
    engine_running: bool = False


class ActionResponse(BaseModel):
    status: str
    ignition_state: str
    emulator_status: str
    emulator_error: str | None = None
    emulator_pid: int | None = None
    environment_status: str = "stopped"  # "running" | "stopped"
    alarm_armed: bool
    doors: dict[str, bool]
    driver_ready: bool
    proximity_detected: bool = False
    engine_running: bool = False


class DoorRequest(BaseModel):
    door: str
    open: bool


class DisplayInfo(BaseModel):
    display: str
    status: str
    note: str


class ConsoleResponse(BaseModel):
    lines: list[str]
    truncated: bool = False


class LogEntry(BaseModel):
    source: str
    level: str
    message: str


class CombinedLogsResponse(BaseModel):
    entries: list[LogEntry]


class QnxConsoleSnapshot(BaseModel):
    lines: list[str]


class CanHeadlightsState(BaseModel):
    state: str


class CanHeadlightsResponse(BaseModel):
    state: str
    history: list[dict[str, object]]


class CanStateResponse(BaseModel):
    state: str
    history: list[dict[str, object]]
    current_state: dict[str, bool]


class QnxVmStateResponse(BaseModel):
    status: str
    last_error: str | None = None
    pid: int | None = None
    last_qemu_command: str | None = None

class EmulatorAndroidConfig(BaseModel):
    boot_img: str | None = None
    system_img: str | None = None
    vendor_img: str | None = None
    product_img: str | None = None


class EmulatorConfigResponse(BaseModel):
    android: EmulatorAndroidConfig


app = FastAPI(title="Chery Emulator Core", version="0.3.0")
app.include_router(controls_router)

# Global instances (will be initialized in startup)
_state_manager: Optional[StateManager] = None
_ignition_controller: Optional[IgnitionController] = None

# Background task for periodic CAN connection checking
_can_check_task: Optional[asyncio.Task] = None


def get_state_manager() -> StateManager:
    """Get state manager instance (dependency injection helper)."""
    if _state_manager is None:
        raise RuntimeError("StateManager not initialized. Call startup_event first.")
    return _state_manager


def get_ignition_controller() -> IgnitionController:
    """Get ignition controller instance (dependency injection helper)."""
    if _ignition_controller is None:
        raise RuntimeError("IgnitionController not initialized. Call startup_event first.")
    return _ignition_controller


async def _periodic_can_check() -> None:
    """Periodically check CAN server connection in background."""
    while True:
        try:
            await asyncio.sleep(2.0)  # Check every 2 seconds
            if can_server is not None and (can_server._listening_socket is not None or can_server._socketcan_socket is not None):
                if not can_server._use_socketcan:
                    can_server.check_connection()
        except asyncio.CancelledError:
            break
        except Exception:
            # Ignore errors in background task
            pass


@app.on_event("startup")
async def startup_event() -> None:
    """Start background tasks on API server startup and initialize managers."""
    global _can_check_task, _state_manager, _ignition_controller

    # Initialize state manager (restores state from disk)
    logger.info("Initializing state manager...")
    _state_manager = StateManager()
    logger.info(f"State restored: ignition={_state_manager.state.ignition_state.value}, alarm={_state_manager.state.alarm_armed}")

    # Initialize ignition controller
    logger.info("Initializing ignition controller...")
    _ignition_controller = IgnitionController(
        state_manager=_state_manager,
        emulator_manager=emulator_manager,
        qnx_vm_manager=qnx_vm_manager,
        emit_can_callback=_emit_ignition_can_messages,
    )

    # Если состояние уже ENGINE_RUNNING или ACC_ON, но engine_running не установлен,
    # устанавливаем engine_running = True для ENGINE_RUNNING
    current_state = _state_manager.state.ignition_state
    if current_state is IgnitionState.ENGINE_RUNNING and not _state_manager.state.engine_running:
        logger.info("State is ENGINE_RUNNING but engine_running is False - setting to True")
        _state_manager.set_engine_running(True)

    # Автоматически запускаем эмуляторы если состояние требует этого
    # Это нужно для случая, когда сервер перезапускается, а состояние уже было установлено
    async def _auto_start_emulators_on_startup() -> None:
        """Auto-start emulators on server startup if state requires it."""
        try:
            current_state = _state_manager.state.ignition_state
            if current_state in (IgnitionState.POWER_READY, IgnitionState.ACC_ON, IgnitionState.ENGINE_RUNNING):
                logger.info(f"Current state is {current_state.value} - checking if emulators need to be started...")
                await _ignition_controller._start_emulators_if_needed(
                    IgnitionState.OFF,  # old_state - считаем что было OFF
                    current_state,      # new_state - текущее состояние
                    _state_manager.state.engine_running
                )
        except Exception as e:
            logger.error(f"Failed to auto-start emulators on startup: {e}", exc_info=True)

    asyncio.create_task(_auto_start_emulators_on_startup())

    # Start CAN check task
    if can_server is not None:
        _can_check_task = asyncio.create_task(_periodic_can_check())


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Stop background tasks on API server shutdown and save vehicle state."""
    global _can_check_task, _state_manager

    # Stop CAN check task
    if _can_check_task is not None:
        _can_check_task.cancel()
        try:
            await _can_check_task
        except asyncio.CancelledError:
            pass

    # Save state
    if _state_manager is not None:
        logger.info("Saving vehicle state to persistence...")
        _state_manager.save()
        logger.info("Vehicle state saved")


BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"
LOGS_DIR = BASE_DIR / "logs"

# Initialize boot monitor
boot_monitor = BootMonitor(LOGS_DIR)

if WEB_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(WEB_DIR), html=True), name="ui")

# Wire up VNC-based frame providers by default; if VNC is not reachable,
# DisplayFrameManager will gracefully fall back to local PNG assets.
display_manager.set_hu_provider(hu_vnc_frame)
display_manager.set_cluster_provider(cluster_vnc_frame)


async def _stream_frames(
    websocket: WebSocket,
    provider: callable,
    fps: float = 15.0,
) -> None:
    """Generic helper to push PNG frames over a WebSocket.

    - `provider` must be a callable returning `bytes | None`.
    - Frames are sent best-effort; if provider returns None, we simply
      wait for the next tick.
    """

    await websocket.accept()
    delay = 1.0 / fps if fps > 0 else 0.1
    loop = asyncio.get_running_loop()
    try:
        while True:
            frame: bytes | None = await loop.run_in_executor(None, provider)
            if frame is not None:
                await websocket.send_bytes(frame)
            await asyncio.sleep(delay)
    except WebSocketDisconnect:
        # Normal client disconnect.
        return
    except Exception:
        # Best-effort: close connection; errors are logged by the server runtime.
        try:
            await websocket.close()
        except Exception:
            pass


def _state_payload() -> dict[str, object]:
    """Build state payload. Optimized for speed - minimal checks."""
    state_manager = get_state_manager()
    v = state_manager.state.to_dict()
    e = emulator_manager.to_dict()

    # Быстрая проверка environment status (CAN server)
    environment_status = "stopped"
    if can_server is not None:
        try:
            # Быстрая проверка без глубокого доступа к атрибутам
            if (hasattr(can_server, '_listening_socket') and can_server._listening_socket is not None) or \
               (hasattr(can_server, '_socketcan_socket') and can_server._socketcan_socket is not None) or \
               (hasattr(can_server, '_connected') and can_server._connected):
                environment_status = "running"
        except Exception:
            # Игнорируем ошибки проверки - не критично
            pass

    return {
        "ignition_state": v["ignition_state"],  # type: ignore[arg-type]
        "updated_at": v["updated_at"],  # type: ignore[arg-type]
        "emulator_status": e["status"],
        "emulator_error": e.get("last_error"),
        "emulator_pid": e.get("pid"),
        "environment_status": environment_status,
        "alarm_armed": v["alarm_armed"],  # type: ignore[arg-type]
        "doors": v["doors"],  # type: ignore[arg-type]
        "driver_ready": v["driver_ready"],  # type: ignore[arg-type]
        "proximity_detected": v.get("proximity_detected", False),  # type: ignore[arg-type]
        "engine_running": v.get("engine_running", False),  # type: ignore[arg-type]
    }


def _state_response(status: str | None = None) -> ActionResponse | StateResponse:
    base = _state_payload()
    if status is None:
        return StateResponse(**base)
    return ActionResponse(status=status, **base)


@app.get("/state", response_model=StateResponse)
async def get_state() -> StateResponse:
    return _state_response()  # type: ignore[return-value]


@app.post("/ignition/press_short", response_model=ActionResponse)
async def ignition_press_short() -> ActionResponse:
    """Handle short press of ignition button."""
    try:
        controller = get_ignition_controller()
        # Run in background to not block the response
        asyncio.create_task(controller.handle_short_press())
        return _state_response(status="ignition_short")  # type: ignore[return-value]
    except Exception as e:
        logger.error(f"Error in ignition_press_short: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ignition/press_long", response_model=ActionResponse)
async def ignition_press_long() -> ActionResponse:
    """Handle long press of ignition button - sequential state transition.

    OFF → POWER_READY → ACC_ON → ENGINE_RUNNING → ACC_ON
    """
    try:
        controller = get_ignition_controller()
        # Run sequence in background to not block the response
        asyncio.create_task(controller.handle_long_press())
        return _state_response(status="ignition_long")  # type: ignore[return-value]
    except Exception as e:
        logger.error(f"Error in ignition_press_long: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))




def _emit_ignition_can_messages(state: IgnitionState, engine_running: bool = False) -> None:
    """Emit CAN messages for ignition state changes."""
    if state is IgnitionState.OFF:
        # OFF: все выключено
        frames = can_bus.emit_ignition(False)
        frames.extend(can_bus.emit_engine_status(False))
        _transmit_can_frames(frames)
    elif state is IgnitionState.POWER_READY:
        # POWER_READY: первое нажатие, зажигание включено, приборка начинает работать
        frames = can_bus.emit_power_ready()
        _transmit_can_frames(frames)
    elif state is IgnitionState.ACC_ON:
        # ACC_ON: второе нажатие, Android HU запускается
        frames = can_bus.emit_acc_on(engine_running=engine_running)
        _transmit_can_frames(frames)
    elif state is IgnitionState.ENGINE_RUNNING:
        # ENGINE_RUNNING: запуск двигателя
        frames = can_bus.emit_ignition(True)
        frames.extend(can_bus.emit_engine_status(True))
        _transmit_can_frames(frames)


def _transmit_can_frames(frames: list) -> None:
    """Transmit CAN frames via CAN server. Non-blocking, errors are logged."""
    if can_server is None:
        return

    # Быстрая проверка статуса без блокировки
    try:
        # Проверяем что CAN server запущен и подключен
        is_connected = (
            (hasattr(can_server, '_socketcan_socket') and can_server._socketcan_socket is not None) or
            (hasattr(can_server, '_client_socket') and can_server._client_socket is not None) or
            (hasattr(can_server, '_connected') and can_server._connected)
        )

        if is_connected:
            for frame in frames:
                try:
                    can_server.transmit_frame(frame)
                except Exception as e:
                    # Логируем только если это не просто "не подключен"
                    if "not connected" not in str(e).lower():
                        logger.error(f"Failed to transmit CAN frame: {e}", exc_info=True)
    except Exception as e:
        # Не критично, просто логируем
        logger.debug(f"CAN transmission check failed: {e}")


@app.post("/vehicle/alarm/toggle", response_model=ActionResponse)
async def vehicle_alarm_toggle() -> ActionResponse:
    """Toggle vehicle alarm state (armed/disarmed)."""
    state_manager = get_state_manager()
    state = state_manager.state

    # Нельзя снять с охраны, если ключ не обнаружен.
    if state.alarm_armed and not state.proximity_detected:
        return _state_response(status="alarm_toggle_ignored_no_proximity")  # type: ignore[return-value]

    state_manager.set_alarm(not state.alarm_armed)
    # Emit CAN frame for new alarm state.
    can_bus.set_alarm(state.alarm_armed)
    return _state_response(status="alarm_toggle")  # type: ignore[return-value]


@app.post("/vehicle/door", response_model=ActionResponse)
async def vehicle_door(req: DoorRequest) -> ActionResponse:
    """Open/close specific door/hood/trunk.

    Door names:
      - driver, passenger, rear_left, rear_right, trunk, hood
    While alarm is armed, attempts to open doors are ignored.
    """
    state_manager = get_state_manager()
    name = req.door.lower()
    state_manager.set_door(name, bool(req.open))
    # Reflect resulting physical state into CAN bus.
    doors = state_manager.state.doors
    if name in doors:
        can_bus.set_door(name, bool(doors[name]))
    return _state_response(status="door_change")  # type: ignore[return-value]


@app.post("/vehicle/proximity/toggle", response_model=ActionResponse)
async def vehicle_proximity_toggle() -> ActionResponse:
    """Toggle virtual key proximity detection and emit CAN frame."""
    state_manager = get_state_manager()
    state = state_manager.state
    new_state = not state.proximity_detected
    state_manager.set_proximity(new_state)
    can_bus.emit_proximity(new_state)
    return _state_response(status="proximity_toggle")  # type: ignore[return-value]


@app.post("/emulator/environment/start", response_model=ActionResponse)
async def emulator_environment_start() -> ActionResponse:
    """Start emulator environment (CAN server, API services) without QEMU.

    This puts the system in 'ready' mode where CAN commands can be sent,
    but QEMU processes (Android HU, QNX VM) are not started yet.
    """
    # Start CAN server for receiving CAN frames
    if can_server is not None:
        can_server.start()
    return _state_response(status="environment_start")  # type: ignore[return-value]


@app.post("/emulator/environment/stop", response_model=ActionResponse)
async def emulator_environment_stop() -> ActionResponse:
    """Stop emulator environment (CAN server, API services).

    This stops CAN server but keeps QEMU processes running if they are active.
    """
    if can_server is not None:
        can_server.stop()
    return _state_response(status="environment_stop")  # type: ignore[return-value]


def _auto_start_environment_if_needed() -> None:
    """Automatically start CAN server if not running."""
    if can_server is not None:
        # Check if CAN server is running
        is_running = False
        if hasattr(can_server, '_listening_socket') and can_server._listening_socket is not None:
            is_running = True
        elif hasattr(can_server, '_socketcan_socket') and can_server._socketcan_socket is not None:
            is_running = True
        elif hasattr(can_server, '_connected') and can_server._connected:
            is_running = True

        if not is_running:
            logger.info("Auto-starting CAN server...")
            can_server.start()


@app.post("/emulator/start", response_model=ActionResponse)
async def emulator_start() -> ActionResponse:
    """Start QEMU processes: Android HU + QNX VM.

    This only starts QEMU processes. Environment (CAN server) should be
    started separately via /emulator/environment/start.

    Before starting, safely stops all existing QEMU processes and cleans up resources.
    """
    import asyncio

    # Auto-start environment if not running
    _auto_start_environment_if_needed()

    # Stop QEMU processes first to ensure clean start (non-blocking)
    try:
        emulator_manager.stop()
        qnx_vm_manager.stop()
    except Exception as e:
        logger.error(f"Error stopping emulators: {e}", exc_info=True)

    # Small delay to ensure ports are released
    await asyncio.sleep(0.5)

    # Start QEMU processes in background to avoid blocking
    def start_emulators() -> None:
        try:
            emulator_manager.start()
            qnx_vm_manager.start()
        except Exception as e:
            logger.error(f"Error starting emulators: {e}", exc_info=True)

    # Run in executor to avoid blocking
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, start_emulators)

    return _state_response(status="emulator_start")  # type: ignore[return-value]


@app.post("/emulator/stop", response_model=ActionResponse)
async def emulator_stop() -> ActionResponse:
    """Stop QEMU processes: Android HU + QNX VM.

    This only stops QEMU processes. Environment (CAN server) remains running
    and can be stopped separately via /emulator/environment/stop.
    """
    # Stop QEMU processes only
    emulator_manager.stop()
    qnx_vm_manager.stop()
    return _state_response(status="emulator_stop")  # type: ignore[return-value]


@app.get("/display/hu", response_model=DisplayInfo)
async def display_hu() -> DisplayInfo:
    state = _state_payload()
    note = "Video streaming not implemented yet; use native QEMU window or future VNC integration."
    return DisplayInfo(display="HU", status=str(state["emulator_status"]), note=note)


@app.get("/display/cluster", response_model=DisplayInfo)
async def display_cluster() -> DisplayInfo:
    state = _state_payload()
    note = "Cluster output will mirror the second QEMU display once streaming is implemented."
    return DisplayInfo(display="CLUSTER", status=str(state["emulator_status"]), note=note)


@app.get("/display/hu/frame")
async def get_hu_frame() -> Response:
    """Return a PNG frame for the HU display.

    Currently this uses extracted Android recovery animation frames as a
    stand‑in for real QEMU video output. The API shape is stable so that
    later we can switch the backing implementation to VNC or a shared
    framebuffer without touching the UI.
    """

    data = display_manager.next_hu_frame()
    if data is None:
        raise HTTPException(status_code=404, detail="HU frame not available")
    return Response(content=data, media_type="image/png")


@app.get("/display/cluster/frame")
async def get_cluster_frame() -> Response:
    """Return a PNG frame for the cluster display."""

    data = display_manager.next_cluster_frame()
    if data is None:
        raise HTTPException(status_code=404, detail="Cluster frame not available")
    return Response(content=data, media_type="image/png")


@app.websocket("/ws/hu")
async def ws_hu_display(websocket: WebSocket) -> None:
    """WebSocket stream of HU display frames (PNG binary messages)."""

    await _stream_frames(websocket, display_manager.next_hu_frame, fps=20.0)


@app.websocket("/ws/cluster")
async def ws_cluster_display(websocket: WebSocket) -> None:
    """WebSocket stream of cluster display frames (PNG binary messages)."""

    await _stream_frames(websocket, display_manager.next_cluster_frame, fps=15.0)


@app.get("/emulator/console", response_model=ConsoleResponse)
async def get_emulator_console() -> ConsoleResponse:
    """Return the tail of QEMU console log (PL011 at 0x1c090000) for HU display."""

    logs_dir = BASE_DIR / "logs"
    log_path = logs_dir / "qemu_console.log"
    max_lines = 160

    if not log_path.exists():
        return ConsoleResponse(lines=[], truncated=False)

    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ConsoleResponse(lines=[], truncated=False)

    all_lines = text.splitlines()
    if len(all_lines) <= max_lines:
        return ConsoleResponse(lines=all_lines, truncated=False)

    tail = all_lines[-max_lines:]
    return ConsoleResponse(lines=tail, truncated=True)


def _tail_file(path: Path, max_lines: int = 160) -> list[str]:
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    all_lines = text.splitlines()
    if len(all_lines) <= max_lines:
        return all_lines
    return all_lines[-max_lines:]


def _classify_level(line: str) -> str:
    lower = line.lower()
    if "fatal" in lower or "traceback" in lower:
        return "FATAL"
    if "error" in lower or " err " in lower:
        return "ERROR"
    if "warn" in lower:
        return "WARN"
    if "debug" in lower or " dbg " in lower:
        return "DEBUG"
    return "INFO"


@app.get("/logs/combined", response_model=CombinedLogsResponse)
async def get_combined_logs() -> CombinedLogsResponse:
    """Aggregate emulator / QEMU / QNX logs for the UI console.

    This is a polling endpoint (not a streaming socket) but it's cheap enough
    for a ~1–2s refresh cadence.
    """

    logs_dir = BASE_DIR / "logs"

    sources: list[tuple[str, list[str]]] = []

    # Core emulator / Android side
    sources.append(("QEMU-CONSOLE", _tail_file(logs_dir / "qemu_console.log")))
    sources.append(("QEMU-STDOUT", _tail_file(logs_dir / "qemu_stdout.log", max_lines=80)))
    sources.append(("QEMU-SERIAL", _tail_file(logs_dir / "qemu_serial.log", max_lines=80)))
    sources.append(("EMU-CORE", _tail_file(logs_dir / "emulator_core.log", max_lines=160)))
    sources.append(("ANDROID-ADB", _tail_file(logs_dir / "adb_android.log", max_lines=120)))

    # QNX VM / second domain
    sources.append(("QNX-QEMU", _tail_file(logs_dir / "qnx_qemu_stdout.log", max_lines=80)))
    # Пробуем все возможные консоли QNX: PL011 (стандартный), virtio-console, и старый UART
    sources.append(("QNX-PL011", qnx_pl011_console.tail(max_bytes=4096)))
    sources.append(("QNX-VIRTCON", qnx_virtio_console.tail(max_bytes=4096)))
    # Старый SCIF/UART endpoint оставляем для обратной совместимости.
    sources.append(("QNX-UART", qnx_console.tail(max_bytes=4096)))

    entries: list[LogEntry] = []
    for source, lines in sources:
        for line in lines:
            if not line:
                continue
            level = _classify_level(line)
            entries.append(LogEntry(source=source, level=level, message=line))

    # Cap total to avoid flooding UI; newest-ish entries last.
    if len(entries) > 400:
        entries = entries[-400:]

    return CombinedLogsResponse(entries=entries)


@app.post("/emulator/console/clear", response_model=ConsoleResponse)
async def clear_emulator_console() -> ConsoleResponse:
    """Best-effort truncation of emulator/QEMU/QNX log files.

    This is wired to the UI "refresh logs" button and is expected to clear
    the visible log console. It does not affect the running emulator, only
    local log files under `Development/Chery_Emulator/logs`.
    """

    logs_dir = BASE_DIR / "logs"
    files = [
        "qemu_console.log",
        "qemu_stdout.log",
        "qemu_serial.log",
        "emulator_core.log",
        "adb_android.log",
        "qnx_qemu_stdout.log",
    ]

    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        for name in files:
            path = logs_dir / name
            try:
                path.write_text("", encoding="utf-8")
            except OSError:
                # Ignore individual file errors; other logs are still cleared.
                continue
    except OSError:
        # On total failure just return current snapshot instead of raising.
        return await get_emulator_console()

    return ConsoleResponse(lines=[], truncated=False)


@app.get("/qnx/console", response_model=QnxConsoleSnapshot)
async def get_qnx_console() -> QnxConsoleSnapshot:
    """Return a lightweight snapshot from the QNX UART console socket.

    This talks directly to the QEMU chardev socket configured for QNX
    (see `build_qemu_args_with_qnx_uart`). If QEMU or the socket is not
    available, it returns an empty list.
    """

    lines = qnx_console.tail(max_bytes=4096)
    return QnxConsoleSnapshot(lines=lines)


@app.get("/qnx/pl011", response_model=QnxConsoleSnapshot)
async def get_qnx_pl011() -> QnxConsoleSnapshot:
    """Return a snapshot from the QNX PL011 (ttyAMA0) console socket.

    Стандартный UART virt-машины на адресе 0x9000000. QNX может использовать
    его по умолчанию для boot логов и консоли (порт 1237).
    """

    lines = qnx_pl011_console.tail(max_bytes=4096)
    return QnxConsoleSnapshot(lines=lines)


@app.get("/qnx/virtconsole", response_model=QnxConsoleSnapshot)
async def get_qnx_virtconsole() -> QnxConsoleSnapshot:
    """Return a snapshot from the QNX virtio-console socket.

    QNX IFS содержит vdev-virtio-console.so, поэтому консоль QNX скорее всего
    идёт через virtio-console, а не через SCIF. Этот endpoint подключается к
    сокету, который QEMU создаёт для virtio-console chardev (порт 1236).
    """

    lines = qnx_virtio_console.tail(max_bytes=4096)
    return QnxConsoleSnapshot(lines=lines)


@app.post("/can/headlights", response_model=CanHeadlightsResponse)
async def post_can_headlights(payload: CanHeadlightsState) -> CanHeadlightsResponse:
    """High-level endpoint to toggle headlights via the virtual CAN bus.

    This does not yet talk to the real QNX/cluster, but it provides the
    end-to-end plumbing from GUI → API → CAN model, so QEMU/QNX wiring
    can be added later without changing the API surface.
    """

    state = payload.state.upper()
    on = state == "ON"
    can_bus.emit_headlights(on=on)
    bus_state = can_bus.to_dict()
    return CanHeadlightsResponse(state="ON" if on else "OFF", history=bus_state["history"])  # type: ignore[arg-type]


@app.post("/can/doors", response_model=CanHeadlightsResponse)
async def post_can_doors(payload: CanHeadlightsState) -> CanHeadlightsResponse:
    """Emit CAN frames for door unlock/lock state.

    QNX cluster may be waiting for BCM door status signals to initialize
    or show certain UI states. This simulates those signals.
    """

    state = payload.state.upper()
    unlocked = state == "UNLOCKED" or state == "OPEN"
    can_bus.emit_doors_unlock(unlocked=unlocked)
    bus_state = can_bus.to_dict()
    return CanHeadlightsResponse(state="UNLOCKED" if unlocked else "LOCKED", history=bus_state["history"])  # type: ignore[arg-type]


@app.post("/can/engine", response_model=CanHeadlightsResponse)
async def post_can_engine(payload: CanHeadlightsState) -> CanHeadlightsResponse:
    """Emit CAN frames for engine running status.

    QNX cluster definitely needs ECM engine status signals to show
    engine-related information and may be blocking UI initialization
    until received. This simulates those signals.
    """

    state = payload.state.upper()
    running = state == "ON" or state == "RUNNING" or state == "START"
    can_bus.emit_engine_status(running=running)
    bus_state = can_bus.to_dict()
    return CanHeadlightsResponse(state="RUNNING" if running else "OFF", history=bus_state["history"])  # type: ignore[arg-type]


@app.post("/can/proximity", response_model=CanStateResponse)
async def post_can_proximity(payload: CanHeadlightsState) -> CanStateResponse:
    """Emit CAN frames for proximity detection (key fob near car).

    When user approaches the car, BCM sends proximity signals.
    Displays may receive signals but stay off until door opens.
    """

    state = payload.state.upper()
    detected = state == "ON" or state == "DETECTED" or state == "NEAR"
    can_bus.emit_proximity(detected=detected)
    bus_state = can_bus.to_dict()
    return CanStateResponse(
        state="DETECTED" if detected else "LOST",
        history=bus_state["history"],  # type: ignore[arg-type]
        current_state={
            "proximity_detected": bus_state["proximity_detected"],  # type: ignore[arg-type]
        },
    )


@app.post("/can/driver_door", response_model=CanStateResponse)
async def post_can_driver_door(payload: CanHeadlightsState) -> CanStateResponse:
    """Emit CAN frames for driver door open/close.

    CRITICAL: When driver door opens, displays should wake up and show splash screen.
    This is the key signal for display activation in real car.
    """

    state = payload.state.upper()
    open = state == "OPEN" or state == "ON"
    can_bus.emit_driver_door(open=open)
    bus_state = can_bus.to_dict()
    return CanStateResponse(
        state="OPEN" if open else "CLOSED",
        history=bus_state["history"],  # type: ignore[arg-type]
        current_state={
            "driver_door_open": bus_state["driver_door_open"],  # type: ignore[arg-type]
        },
    )


@app.post("/can/ignition", response_model=CanStateResponse)
async def post_can_ignition(payload: CanHeadlightsState) -> CanStateResponse:
    """Emit CAN frames for ignition/start-stop button.

    When start-stop button is pressed, this triggers:
    - System boot sequence
    - Cluster initialization
    - Welcome sound and animation
    - Android launcher startup
    """

    state = payload.state.upper()
    on = state == "ON" or state == "START" or state == "PRESSED"
    can_bus.emit_ignition(on=on)
    bus_state = can_bus.to_dict()
    return CanStateResponse(
        state="ON" if on else "OFF",
        history=bus_state["history"],  # type: ignore[arg-type]
        current_state={
            "ignition_on": bus_state["ignition_on"],  # type: ignore[arg-type]
        },
    )


@app.post("/can/sequence/startup", response_model=CanStateResponse)
async def post_can_sequence_startup() -> CanStateResponse:
    """Emit complete startup sequence: proximity → doors → ignition → engine.

    This simulates the real car startup sequence:
    1. Proximity detected (key fob near) - displays may receive signals but stay off
    2. Doors unlock
    3. Driver door opens - displays wake up, show splash screen
    4. Ignition on (start-stop pressed) - system boot, cluster init, welcome animation
    5. Engine starts - Android launcher appears
    """

    can_bus.emit_sequence_startup()
    bus_state = can_bus.to_dict()
    return CanStateResponse(
        state="STARTUP_SEQUENCE_COMPLETE",
        history=bus_state["history"],  # type: ignore[arg-type]
        current_state={
            "proximity_detected": bus_state["proximity_detected"],  # type: ignore[arg-type]
            "doors_unlocked": bus_state["doors_unlocked"],  # type: ignore[arg-type]
            "driver_door_open": bus_state["driver_door_open"],  # type: ignore[arg-type]
            "ignition_on": bus_state["ignition_on"],  # type: ignore[arg-type]
            "engine_running": bus_state["engine_running"],  # type: ignore[arg-type]
        },
    )


@app.get("/can/state", response_model=CanStateResponse)
async def get_can_state() -> CanStateResponse:
    """Get current CAN bus state and history."""

    bus_state = can_bus.to_dict()
    return CanStateResponse(
        state="ACTIVE",
        history=bus_state["history"],  # type: ignore[arg-type]
        current_state={
            "proximity_detected": bus_state["proximity_detected"],  # type: ignore[arg-type]
            "doors_unlocked": bus_state["doors_unlocked"],  # type: ignore[arg-type]
            "driver_door_open": bus_state["driver_door_open"],  # type: ignore[arg-type]
            "ignition_on": bus_state["ignition_on"],  # type: ignore[arg-type]
            "engine_running": bus_state["engine_running"],  # type: ignore[arg-type]
            "headlights_on": bus_state["headlights_on"],  # type: ignore[arg-type]
        },
    )


def _qnx_vm_state_response() -> QnxVmStateResponse:
    data = qnx_vm_manager.to_dict()
    return QnxVmStateResponse(
        status=str(data["status"]),
        last_error=data.get("last_error"),  # type: ignore[arg-type]
        pid=data.get("pid"),  # type: ignore[arg-type]
        last_qemu_command=data.get("last_qemu_command"),  # type: ignore[arg-type]
    )


@app.get("/qnx/state", response_model=QnxVmStateResponse)
async def get_qnx_state() -> QnxVmStateResponse:
    return _qnx_vm_state_response()


@app.post("/qnx/start", response_model=QnxVmStateResponse)
async def qnx_start() -> QnxVmStateResponse:
    qnx_vm_manager.start()
    return _qnx_vm_state_response()


@app.post("/qnx/stop", response_model=QnxVmStateResponse)
async def qnx_stop() -> QnxVmStateResponse:
    qnx_vm_manager.stop()
    return _qnx_vm_state_response()


@app.get("/emulator/environment/state")
async def emulator_environment_state() -> dict[str, object]:
    """Get emulator environment status (CAN server, API services)."""

    can_status = "stopped"
    can_port = None
    can_stats = {}
    can_use_socketcan = False
    can_interface = None

    if can_server is not None:
        # Check connection periodically
        can_server.check_connection()
        is_running = (
            can_server._listening_socket is not None
            or (hasattr(can_server, '_socketcan_socket') and can_server._socketcan_socket is not None)
        )
        if is_running:
            can_status = "running"
            can_port = can_server.config.port
        elif can_server._connected:
            can_status = "connected"
            can_port = can_server.config.port
        can_stats = can_server.get_stats()
        can_use_socketcan = getattr(can_server, '_use_socketcan', False)
        can_interface = can_server.config.can_interface

    return {
        "environment_status": can_status,
        "can_server_port": can_port,
        "can_server_stats": can_stats,
        "can_use_socketcan": can_use_socketcan,
        "can_interface": can_interface,
        "api_server": "running",  # If we can call this endpoint, API is running
    }


@app.post("/can/server/start")
async def can_server_start() -> dict[str, str]:
    """Start CAN server for transmitting frames to QNX."""

    if can_server is not None:
        can_server.start()
        return {"status": "started", "port": str(can_server.config.port)}
    return {"status": "error", "message": "CAN server not available"}


@app.post("/can/server/stop")
async def can_server_stop() -> dict[str, str]:
    """Stop CAN server."""

    if can_server is not None:
        can_server.stop()
        return {"status": "stopped"}
    return {"status": "error", "message": "CAN server not available"}


@app.get("/can/server/status")
async def can_server_status() -> dict[str, object]:
    """Get CAN server status with statistics."""

    if can_server is None:
        return {"status": "not_available"}

    can_server.check_connection()  # Try to accept new connections
    # Check if listening socket exists (server is running)
    is_running = (
        can_server._listening_socket is not None
        or (hasattr(can_server, '_socketcan_socket') and can_server._socketcan_socket is not None)
    ) if hasattr(can_server, '_listening_socket') else can_server._socket is not None

    stats = can_server.get_stats()

    return {
        "status": "running" if is_running else "stopped",
        "port": can_server.config.port,
        "connected": can_server._connected,
        "use_socketcan": getattr(can_server, '_use_socketcan', False),
        "can_interface": can_server.config.can_interface,
        "stats": stats,
    }


@app.get("/health")
async def health_check() -> dict[str, object]:
    """Health check endpoint for monitoring."""

    health: dict[str, object] = {
        "status": "healthy",
        "platform": platform.system(),
        "components": {},
    }

    # Check CAN server
    if can_server is not None:
        can_server.check_connection()
        is_running = (
            can_server._listening_socket is not None
            or (hasattr(can_server, '_socketcan_socket') and can_server._socketcan_socket is not None)
        )
        health["components"]["can_server"] = {
            "status": "running" if is_running else "stopped",
            "connected": can_server._connected,
            "use_socketcan": getattr(can_server, '_use_socketcan', False),
        }
    else:
        health["components"]["can_server"] = {"status": "not_available"}

    # Check emulator
    emu_dict = emulator_manager.to_dict()
    health["components"]["emulator"] = {
        "status": emu_dict.get("status", "unknown"),
        "pid": emu_dict.get("pid"),
    }

    # Check QNX VM
    qnx_dict = qnx_vm_manager.to_dict()
    health["components"]["qnx_vm"] = {
        "status": qnx_dict.get("status", "unknown"),
        "pid": qnx_dict.get("pid"),
    }

    # Overall health
    if any(
        comp.get("status") == "error"
        for comp in health["components"].values()
        if isinstance(comp, dict)
    ):
        health["status"] = "degraded"

    return health


@app.get("/emulator/boot-status")
async def get_boot_status() -> dict[str, object]:
    """Get detailed boot status for both Android and QNX systems.

    Returns boot progress, elapsed time, log activity, and any errors.
    Fast execution with timeouts to prevent hanging.
    """
    try:
        # Run all checks in parallel with timeout
        async def gather_status() -> dict[str, object]:
            # Fast checks (non-blocking)
            android_status = boot_monitor.check_android_boot_progress()
            qnx_status = boot_monitor.check_qnx_boot_progress()

            # Fast ADB check (with timeout)
            adb_status = boot_monitor.check_adb_status()

            # Process checks
            android_process = boot_monitor.check_qemu_process(emulator_manager.runtime.pid)
            qnx_process = boot_monitor.check_qemu_process(qnx_vm_manager.runtime.pid)

            # Port checks
            adb_port = boot_monitor.check_port_status("127.0.0.1", 5557)
            vnc_hu_port = boot_monitor.check_port_status("127.0.0.1", 5900)
            vnc_cluster_port = boot_monitor.check_port_status("127.0.0.1", 5901)
            qnx_pl011_port = boot_monitor.check_port_status("localhost", 1237)

            # QEMU monitor checks
            android_monitor = boot_monitor.check_qemu_monitor("127.0.0.1", 5558)
            qnx_monitor = boot_monitor.check_qemu_monitor("127.0.0.1", 5559)

            # Get boot elapsed times from managers
            android_boot_time = None
            qnx_boot_time = None
            try:
                if hasattr(emulator_manager, 'get_boot_elapsed_time'):
                    android_boot_time = emulator_manager.get_boot_elapsed_time()
                if hasattr(qnx_vm_manager, 'get_boot_elapsed_time'):
                    qnx_boot_time = qnx_vm_manager.get_boot_elapsed_time()
            except Exception:
                pass

            return {
                "android": {
                    "boot_elapsed_seconds": android_boot_time,
                    "log_active": android_status["log_active"],
                    "has_errors": android_status["has_errors"],
                    "last_activity_seconds_ago": android_status["last_activity_seconds_ago"],
                    "log_size_bytes": android_status["log_size_bytes"],
                    "sample_lines": android_status["sample_lines"][-5:],  # Last 5 lines
                    "adb": adb_status,
                    "process": android_process,
                    "ports": {
                        "adb": adb_port,
                        "vnc": vnc_hu_port,
                    },
                    "qemu_monitor": android_monitor,
                },
                "qnx": {
                    "boot_elapsed_seconds": qnx_boot_time,
                    "log_active": qnx_status["log_active"],
                    "has_errors": qnx_status["has_errors"],
                    "last_activity_seconds_ago": qnx_status["last_activity_seconds_ago"],
                    "log_size_bytes": qnx_status["log_size_bytes"],
                    "sample_lines": qnx_status["sample_lines"][-5:],  # Last 5 lines
                    "console_available": qnx_status["console_available"],
                    "process": qnx_process,
                    "ports": {
                        "pl011": qnx_pl011_port,
                        "vnc": vnc_cluster_port,
                    },
                    "qemu_monitor": qnx_monitor,
                },
            }

        # Execute with overall timeout
        return await asyncio.wait_for(gather_status(), timeout=3.0)
    except asyncio.TimeoutError:
        logger.warning("Boot status check timed out")
        return {
            "android": {"error": "timeout"},
            "qnx": {"error": "timeout"},
        }
    except Exception as e:
        logger.error(f"Error getting boot status: {e}", exc_info=True)
        return {
            "android": {"error": str(e)},
            "qnx": {"error": str(e)},
        }


@app.get("/emulator/config", response_model=EmulatorConfigResponse)
async def get_emulator_config() -> EmulatorConfigResponse:
    cfg = emulator_manager.config_for_api()
    android = cfg.get("android", {}) or {}
    return EmulatorConfigResponse(
        android=EmulatorAndroidConfig(
            boot_img=android.get("boot_img"),
            system_img=android.get("system_img"),
            vendor_img=android.get("vendor_img"),
            product_img=android.get("product_img"),
        )
    )


@app.post("/emulator/config", response_model=EmulatorConfigResponse)
async def update_emulator_config(payload: EmulatorConfigResponse) -> EmulatorConfigResponse:
    emulator_manager.save_config_from_api(
        android={
            "boot_img": payload.android.boot_img,
            "system_img": payload.android.system_img,
            "vendor_img": payload.android.vendor_img,
            "product_img": payload.android.product_img,
        }
    )
    return await get_emulator_config()
