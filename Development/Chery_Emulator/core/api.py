from __future__ import annotations

from pathlib import Path

import asyncio

from fastapi import FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .state import vehicle_state, IgnitionState
from .emulator import emulator_manager
from .api_controls import router as controls_router
from .qnx import qnx_console, can_bus
from .qnx_vm import qnx_vm_manager
from .display_frames import display_manager
from .graphics_vnc import hu_vnc_frame, cluster_vnc_frame


class StateResponse(BaseModel):
    ignition_state: str
    updated_at: str
    emulator_status: str
    emulator_error: str | None = None
    emulator_pid: int | None = None


class ActionResponse(BaseModel):
    status: str
    ignition_state: str
    emulator_status: str
    emulator_error: str | None = None
    emulator_pid: int | None = None


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


BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"

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


def _auto_start_emulator_if_needed(old_state: IgnitionState, new_state: IgnitionState) -> None:
    """Automatically start emulator when moving out of OFF."""

    if old_state is IgnitionState.OFF and new_state is not IgnitionState.OFF:
        emulator_manager.start()


def _state_payload() -> dict[str, object]:
    v = vehicle_state.to_dict()
    e = emulator_manager.to_dict()
    return {
        "ignition_state": v["ignition_state"],  # type: ignore[arg-type]
        "updated_at": v["updated_at"],  # type: ignore[arg-type]
        "emulator_status": e["status"],
        "emulator_error": e.get("last_error"),
        "emulator_pid": e.get("pid"),
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
    old_state = vehicle_state.ignition_state
    vehicle_state.press_short()
    new_state = vehicle_state.ignition_state
    _auto_start_emulator_if_needed(old_state, new_state)
    return _state_response(status="ignition_short")  # type: ignore[return-value]


@app.post("/ignition/press_long", response_model=ActionResponse)
async def ignition_press_long() -> ActionResponse:
    old_state = vehicle_state.ignition_state
    vehicle_state.press_long()
    new_state = vehicle_state.ignition_state
    _auto_start_emulator_if_needed(old_state, new_state)
    return _state_response(status="ignition_long")  # type: ignore[return-value]


@app.post("/emulator/start", response_model=ActionResponse)
async def emulator_start() -> ActionResponse:
    emulator_manager.start()
    return _state_response(status="emulator_start")  # type: ignore[return-value]


@app.post("/emulator/stop", response_model=ActionResponse)
async def emulator_stop() -> ActionResponse:
    emulator_manager.stop()
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
    """Truncate QEMU console log on disk and return an empty snapshot.

    This is a lightweight helper for the UI "refresh logs" button; it does
    not affect the running emulator, only the accumulated log file.
    """

    logs_dir = BASE_DIR / "logs"
    log_path = logs_dir / "qemu_console.log"

    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_path.write_text("", encoding="utf-8")
    except OSError:
        # If truncation fails, just fall back to current tail snapshot.
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
