"""State persistence for vehicle state.

Сохраняет состояние в файл и восстанавливает при запуске.
Все изменения состояния должны происходить через этот модуль.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .state import IgnitionState, VehicleState

logger = logging.getLogger(__name__)

# Путь к файлу сохранения состояния
STATE_FILE = Path(__file__).resolve().parent.parent / "data" / "vehicle_state.json"


def ensure_data_dir() -> None:
    """Создает директорию для данных если её нет."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


def save_state(state: VehicleState) -> None:
    """Сохраняет состояние в файл."""
    try:
        ensure_data_dir()
        data = {
            "ignition_state": state.ignition_state.value,
            "alarm_armed": state.alarm_armed,
            "doors": state.doors,
            "driver_door_opened_since_disarm": state.driver_door_opened_since_disarm,
            "proximity_detected": state.proximity_detected,
            "engine_running": state.engine_running,
        }
        with STATE_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.debug(f"State saved to {STATE_FILE}")
    except Exception as e:
        logger.error(f"Failed to save state: {e}", exc_info=True)


def load_state() -> dict[str, Any] | None:
    """Загружает состояние из файла."""
    try:
        if not STATE_FILE.exists():
            logger.debug(f"State file not found: {STATE_FILE}, using defaults")
            return None

        with STATE_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"State loaded from {STATE_FILE}")
        return data
    except Exception as e:
        logger.error(f"Failed to load state: {e}", exc_info=True)
        return None


def restore_state(state: VehicleState) -> None:
    """Восстанавливает состояние из файла."""
    data = load_state()
    if data is None:
        logger.info("No saved state found, using defaults")
        return

    try:
        # Восстанавливаем состояние зажигания
        if "ignition_state" in data:
            try:
                state.ignition_state = IgnitionState(data["ignition_state"])
            except ValueError:
                logger.warning(f"Invalid ignition_state: {data['ignition_state']}, using OFF")
                state.ignition_state = IgnitionState.OFF

        # Восстанавливаем остальные поля
        if "alarm_armed" in data:
            state.alarm_armed = bool(data["alarm_armed"])

        if "doors" in data and isinstance(data["doors"], dict):
            for key, value in data["doors"].items():
                if key in state.doors:
                    state.doors[key] = bool(value)

        if "driver_door_opened_since_disarm" in data:
            state.driver_door_opened_since_disarm = bool(data["driver_door_opened_since_disarm"])

        if "proximity_detected" in data:
            state.proximity_detected = bool(data["proximity_detected"])

        if "engine_running" in data:
            state.engine_running = bool(data["engine_running"])

        logger.info(f"State restored: ignition={state.ignition_state.value}, alarm={state.alarm_armed}, engine_running={state.engine_running}")
    except Exception as e:
        logger.error(f"Failed to restore state: {e}", exc_info=True)

