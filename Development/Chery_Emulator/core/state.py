from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal


class IgnitionState(str, Enum):
    """High-level ignition states for the virtual vehicle.

    - OFF: vehicle completely off, both displays dark
    - ACC: accessory power on, HU is allowed to boot
    - IGN: ignition on (all electronics), engine not running yet
    - ENGINE_RUNNING: engine started, full power
    """

    OFF = "OFF"
    ACC = "ACC"
    IGN = "IGN"
    ENGINE_RUNNING = "ENGINE_RUNNING"


@dataclass
class VehicleState:
    ignition_state: IgnitionState = IgnitionState.OFF
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def _set_state(self, new_state: IgnitionState) -> None:
        if new_state is self.ignition_state:
            return
        self.ignition_state = new_state
        self.updated_at = datetime.utcnow()

    def press_short(self) -> None:
        """Handle a short press of the ignition button.

        Behaviour (v2, single physical button):
        - OFF            -> ACC          (first press: accessories on)
        - ACC            -> IGN          (second press: ignition on)
        - IGN (no engine)-> OFF          (toggle back to full off)
        - ENGINE_RUNNING -> OFF          (engine off, full shutdown for now)
        """

        if self.ignition_state is IgnitionState.OFF:
            self._set_state(IgnitionState.ACC)

        elif self.ignition_state is IgnitionState.ACC:
            self._set_state(IgnitionState.IGN)

        elif self.ignition_state is IgnitionState.IGN:
            self._set_state(IgnitionState.OFF)

        elif self.ignition_state is IgnitionState.ENGINE_RUNNING:
            # Stop engine and shut everything down (later можно добавить задержку ACC).
            self._set_state(IgnitionState.OFF)

    def press_long(self) -> None:
        """Handle a long press of the ignition button.

        Behaviour (v2):
        - OFF  -> ACC (long press acts like short press)
        - ACC  -> IGN (long press acts like short press)
        - IGN  -> ENGINE_RUNNING (start engine, then считаем, что ключ в положении зажигания)
        - ENGINE_RUNNING -> ENGINE_RUNNING (игнорируем, чтобы не дёргать лишний раз)
        """

        if self.ignition_state is IgnitionState.OFF:
            self._set_state(IgnitionState.ACC)

        elif self.ignition_state is IgnitionState.ACC:
            self._set_state(IgnitionState.IGN)

        elif self.ignition_state is IgnitionState.IGN:
            self._set_state(IgnitionState.ENGINE_RUNNING)

        elif self.ignition_state is IgnitionState.ENGINE_RUNNING:
            # Никаких изменений при долгом нажатии в режиме запущенного двигателя.
            pass

    def to_dict(self) -> dict[str, object]:
        return {
            "ignition_state": self.ignition_state.value,
            "updated_at": self.updated_at.isoformat() + "Z",
        }


# Global state instance for the initial prototype.
vehicle_state = VehicleState()
