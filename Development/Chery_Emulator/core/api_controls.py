from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from .controls import (
    CabinCommand,
    ControlsState,
    EngineCommand,
    InfotainmentCommand,
    SteeringCommand,
    controls_state,
)


class ControlsStateResponse(BaseModel):
    last_engine_command: str | None
    last_cabin_command: str | None
    last_steering_command: str | None
    last_infotainment_command: str | None
    updated_at: str
    history: list[str]


class CommandRequest(BaseModel):
    command: str


router = APIRouter(prefix="/controls", tags=["controls"])


@router.get("/state", response_model=ControlsStateResponse)
async def get_controls_state() -> ControlsStateResponse:
    data = controls_state.to_dict()
    return ControlsStateResponse(**data)  # type: ignore[arg-type]


@router.post("/vehicle", response_model=ControlsStateResponse)
async def post_vehicle_command(req: CommandRequest) -> ControlsStateResponse:
    try:
        cmd = EngineCommand(req.command)
    except ValueError:
        # ignore unknown command, just return current state
        return await get_controls_state()
    controls_state.apply_engine(cmd)
    return await get_controls_state()


@router.post("/cabin", response_model=ControlsStateResponse)
async def post_cabin_command(req: CommandRequest) -> ControlsStateResponse:
    try:
        cmd = CabinCommand(req.command)
    except ValueError:
        return await get_controls_state()
    controls_state.apply_cabin(cmd)
    return await get_controls_state()


@router.post("/steering", response_model=ControlsStateResponse)
async def post_steering_command(req: CommandRequest) -> ControlsStateResponse:
    try:
        cmd = SteeringCommand(req.command)
    except ValueError:
        return await get_controls_state()
    controls_state.apply_steering(cmd)
    return await get_controls_state()


@router.post("/infotainment", response_model=ControlsStateResponse)
async def post_infotainment_command(req: CommandRequest) -> ControlsStateResponse:
    try:
        cmd = InfotainmentCommand(req.command)
    except ValueError:
        return await get_controls_state()
    controls_state.apply_infotainment(cmd)
    return await get_controls_state()
