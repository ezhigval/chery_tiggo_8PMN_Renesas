"""State manager with observer pattern for persistence.

Централизованное управление состоянием с автоматическим сохранением.
"""

from __future__ import annotations

import logging
from typing import Callable, Protocol

from .state import IgnitionState, VehicleState
from .state_persistence import save_state, restore_state

logger = logging.getLogger(__name__)


class StateObserver(Protocol):
    """Protocol for state change observers."""

    def on_state_changed(self, old_state: IgnitionState, new_state: IgnitionState) -> None:
        """Called when ignition state changes."""
        ...


class StateManager:
    """Manages vehicle state with automatic persistence.

    Uses observer pattern to notify listeners about state changes.
    Automatically saves state to disk on every change.
    """

    def __init__(self, initial_state: VehicleState | None = None) -> None:
        """Initialize state manager.

        Args:
            initial_state: Initial vehicle state. If None, creates new state.
        """
        self._state = initial_state or VehicleState()
        self._observers: list[StateObserver] = []
        self._persistence_enabled = True

        # Restore state from disk
        try:
            restore_state(self._state)
            logger.info(f"State restored: ignition={self._state.ignition_state.value}")
        except Exception as e:
            logger.error(f"Failed to restore state: {e}", exc_info=True)

    @property
    def state(self) -> VehicleState:
        """Get current vehicle state."""
        return self._state

    def add_observer(self, observer: StateObserver) -> None:
        """Add state change observer."""
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: StateObserver) -> None:
        """Remove state change observer."""
        if observer in self._observers:
            self._observers.remove(observer)

    def set_ignition_state(self, new_state: IgnitionState) -> None:
        """Set ignition state and notify observers.

        Args:
            new_state: New ignition state.
        """
        old_state = self._state.ignition_state
        if old_state == new_state:
            return

        self._state._set_state(new_state)
        self._notify_observers(old_state, new_state)
        self._save_state()

    def set_alarm(self, armed: bool) -> None:
        """Set alarm state.

        Args:
            armed: True to arm, False to disarm.
        """
        self._state.set_alarm(armed)
        self._save_state()

    def set_door(self, name: str, open_: bool) -> None:
        """Set door state.

        Args:
            name: Door name.
            open_: True if open, False if closed.
        """
        self._state.set_door(name, open_)
        self._save_state()

    def set_proximity(self, detected: bool) -> None:
        """Set proximity detection state.

        Args:
            detected: True if key detected, False otherwise.
        """
        self._state.set_proximity(detected)
        self._save_state()

    def set_engine_running(self, running: bool) -> None:
        """Set engine running state.

        Args:
            running: True if engine is running, False otherwise.
        """
        self._state.set_engine_running(running)
        self._save_state()


    def _notify_observers(self, old_state: IgnitionState, new_state: IgnitionState) -> None:
        """Notify all observers about state change."""
        for observer in self._observers:
            try:
                observer.on_state_changed(old_state, new_state)
            except Exception as e:
                logger.error(f"Observer {observer} failed: {e}", exc_info=True)

    def _save_state(self) -> None:
        """Save state to disk."""
        if not self._persistence_enabled:
            return

        try:
            save_state(self._state)
        except Exception as e:
            logger.error(f"Failed to save state: {e}", exc_info=True)
            # Don't raise - persistence failure shouldn't break the app

    def save(self) -> None:
        """Manually save state to disk."""
        self._save_state()

    def disable_persistence(self) -> None:
        """Temporarily disable automatic persistence."""
        self._persistence_enabled = False

    def enable_persistence(self) -> None:
        """Re-enable automatic persistence."""
        self._persistence_enabled = True
