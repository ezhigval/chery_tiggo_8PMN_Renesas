from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List


class EngineCommand(str, Enum):
    ACC = "ACC"
    ENGINE_START = "ENGINE_START"
    ENGINE_STOP = "ENGINE_STOP"


class CabinCommand(str, Enum):
    CLIMATE_AUTO = "CLIMATE_AUTO"
    CLIMATE_SYNC = "CLIMATE_SYNC"
    REAR_DEFROST = "REAR_DEFROST"


class SteeringCommand(str, Enum):
    NAV = "NAV"
    MEDIA = "MEDIA"
    VOICE = "VOICE"
    VOL_UP = "VOL_UP"
    VOL_DOWN = "VOL_DOWN"


class InfotainmentCommand(str, Enum):
    OPEN_NAV = "OPEN_NAV"
    OPEN_MEDIA = "OPEN_MEDIA"
    SPLIT_SCREEN = "SPLIT_SCREEN"


@dataclass
class ControlsState:
    last_engine_command: EngineCommand | None = None
    last_cabin_command: CabinCommand | None = None
    last_steering_command: SteeringCommand | None = None
    last_infotainment_command: InfotainmentCommand | None = None
    history: List[str] = field(default_factory=list)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def _record(self, kind: str, value: str) -> None:
        ts = datetime.utcnow().isoformat() + "Z"
        self.history.append(f"{ts} {kind}:{value}")
        # keep history reasonably small
        if len(self.history) > 100:
            self.history = self.history[-100:]
        self.updated_at = datetime.utcnow()

    def apply_engine(self, cmd: EngineCommand) -> None:
        self.last_engine_command = cmd
        self._record("engine", cmd.value)

    def apply_cabin(self, cmd: CabinCommand) -> None:
        self.last_cabin_command = cmd
        self._record("cabin", cmd.value)

    def apply_steering(self, cmd: SteeringCommand) -> None:
        self.last_steering_command = cmd
        self._record("steering", cmd.value)

    def apply_infotainment(self, cmd: InfotainmentCommand) -> None:
        self.last_infotainment_command = cmd
        self._record("infotainment", cmd.value)

    def to_dict(self) -> dict[str, object]:
        return {
            "last_engine_command": self.last_engine_command.value if self.last_engine_command else None,
            "last_cabin_command": self.last_cabin_command.value if self.last_cabin_command else None,
            "last_steering_command": self.last_steering_command.value if self.last_steering_command else None,
            "last_infotainment_command": self.last_infotainment_command.value if self.last_infotainment_command else None,
            "updated_at": self.updated_at.isoformat() + "Z",
            "history": list(self.history),
        }


controls_state = ControlsState()
