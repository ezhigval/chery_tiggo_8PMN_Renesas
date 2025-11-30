from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal


class IgnitionState(str, Enum):
    """High-level ignition states for the virtual vehicle.

    - OFF: vehicle completely off, both displays dark
    - POWER_READY: power ready (first press from OFF), cluster/QNX starts working
    - ACC_ON: accessory on (second press), Android HU starts, radio, etc.
    - ENGINE_RUNNING: engine starting/running (long press), then returns to ACC_ON
    """

    OFF = "OFF"
    POWER_READY = "POWER_READY"
    ACC_ON = "ACC_ON"
    ENGINE_RUNNING = "ENGINE_RUNNING"


@dataclass
class VehicleState:
    ignition_state: IgnitionState = IgnitionState.OFF
    updated_at: datetime = field(default_factory=datetime.utcnow)
    # Дополнительная логика автомобиля.
    alarm_armed: bool = True
    # Простая модель дверей/капота/багажника: True = открыто.
    doors: dict[str, bool] = field(
        default_factory=lambda: {
            "driver": False,
            "passenger": False,
            "rear_left": False,
            "rear_right": False,
            "trunk": False,
            "hood": False,
        }
    )
    # Флаг «мы сели в машину» – водительская дверь была открыта после снятия с охраны.
    driver_door_opened_since_disarm: bool = False
    # Обнаружен ли «ключ» (proximity) рядом с автомобилем.
    proximity_detected: bool = False
    # Состояние двигателя: работает или нет (независимо от состояния зажигания).
    engine_running: bool = False

    def _set_state(self, new_state: IgnitionState) -> None:
        """Устанавливает новое состояние зажигания.

        ВАЖНО: Это внутренний метод. Используйте StateManager для изменения состояния.
        """
        if new_state is self.ignition_state:
            return
        self.ignition_state = new_state
        self.updated_at = datetime.utcnow()

    # --- Alarm / doors helpers ---

    def _touch(self) -> None:
        self.updated_at = datetime.utcnow()

    def set_alarm(self, armed: bool) -> None:
        """Arm/disarm the vehicle alarm.

        При постановке на охрану все двери считаем закрытыми. При снятии
        проверяем, не открыта ли уже водительская дверь - если да, считаем что сели.
        """

        if self.alarm_armed == armed:
            return
        self.alarm_armed = armed
        if armed:
            # При постановке на охрану закрываем все двери.
            for k in self.doors:
                self.doors[k] = False
            self.driver_door_opened_since_disarm = False
        else:
            # Только что сняли с охраны - если водительская дверь уже открыта,
            # считаем что сели в машину
            if self.doors.get("driver", False):
                self.driver_door_opened_since_disarm = True
            else:
                # Ждём открытия водительской двери
                self.driver_door_opened_since_disarm = False
        self._touch()

    def toggle_alarm(self) -> None:
        self.set_alarm(not self.alarm_armed)

    def set_door(self, name: str, open_: bool) -> None:
        """Open/close a specific door.

        - Пока сигнализация включена, попытку открыть двери игнорируем.
        - Когда после снятия с охраны впервые открывается водительская дверь,
          считаем, что «мы сели в машину».
        - Если дверь уже открыта, а потом снимаем с охраны, тоже считаем что сели.
        """

        if name not in self.doors:
            return
        if self.alarm_armed and open_:
            # Нельзя открыть двери под охраной.
            return
        if self.doors[name] == open_:
            return
        self.doors[name] = open_
        # Если водительская дверь открыта и сигнализация снята - считаем что сели
        if name == "driver" and open_ and not self.alarm_armed:
            self.driver_door_opened_since_disarm = True
        self._touch()

    def set_proximity(self, detected: bool) -> None:
        """Update proximity (key presence) flag."""

        if self.proximity_detected == detected:
            return
        self.proximity_detected = detected
        self._touch()

    def set_engine_running(self, running: bool) -> None:
        """Update engine running state.

        This is independent of ignition_state - engine can be running
        even when ignition is in ACC_ON state.
        """
        if self.engine_running == running:
            return
        self.engine_running = running
        self._touch()

    @property
    def driver_ready(self) -> bool:
        """Разрешаем запуск только если:

        - сигнализация снята;
        - после этого хотя бы раз открывали водительскую дверь;
        - ключ (proximity) обнаружен рядом с автомобилем.
        """

        return (not self.alarm_armed) and self.driver_door_opened_since_disarm and self.proximity_detected


    def to_dict(self) -> dict[str, object]:
        return {
            "ignition_state": self.ignition_state.value,
            "updated_at": self.updated_at.isoformat() + "Z",
            "alarm_armed": self.alarm_armed,
            "doors": dict(self.doors),
            "driver_ready": self.driver_ready,
            "proximity_detected": self.proximity_detected,
            "engine_running": self.engine_running,
        }
