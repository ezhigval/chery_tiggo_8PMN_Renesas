"""Ignition controller for managing ignition state transitions.

Отвечает за логику переходов состояний зажигания и запуск эмуляторов.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Callable

from .state import IgnitionState
from .config import config

if TYPE_CHECKING:
    from .state_manager import StateManager
    from .emulator import EmulatorManager
    from .qnx_vm import QnxVmManager

logger = logging.getLogger(__name__)


class IgnitionController:
    """Controls ignition state transitions and emulator startup."""

    def __init__(
        self,
        state_manager: StateManager,
        emulator_manager: EmulatorManager,
        qnx_vm_manager: QnxVmManager,
        emit_can_callback: Callable[[IgnitionState, bool], None] | None = None,
    ) -> None:
        """Initialize ignition controller.

        Args:
            state_manager: State manager instance.
            emulator_manager: Android HU emulator manager.
            qnx_vm_manager: QNX VM manager.
            emit_can_callback: Callback to emit CAN messages for ignition state changes.
                Called with (state, engine_running).
        """
        self._state_manager = state_manager
        self._emulator_manager = emulator_manager
        self._qnx_vm_manager = qnx_vm_manager
        self._emit_can_callback = emit_can_callback

    async def handle_short_press(self) -> None:
        """Handle short press of ignition button.

        Behaviour:
        - OFF         -> POWER_READY  (first press, если driver_ready)
        - POWER_READY -> ACC_ON       (second press)
        - ACC_ON      -> OFF          (third press - глушить машину)
        - ENGINE_RUNNING -> ACC_ON   (если двигатель заведен, возврат в ACC_ON)
        """
        old_state = self._state_manager.state.ignition_state
        new_state = old_state

        if old_state is IgnitionState.OFF:
            # Нельзя «включить машину», пока не сняли с охраны и не открыли дверь.
            if not self._state_manager.state.driver_ready:
                logger.info("Short press ignored: OFF state but driver not ready")
                return
            new_state = IgnitionState.POWER_READY
        elif old_state is IgnitionState.POWER_READY:
            # POWER_READY -> ACC_ON
            new_state = IgnitionState.ACC_ON
        elif old_state is IgnitionState.ACC_ON:
            # ACC_ON -> OFF (глушить машину)
            new_state = IgnitionState.OFF
        elif old_state is IgnitionState.ENGINE_RUNNING:
            # Если двигатель заведен, одно нажатие возвращает в ACC_ON
            # (в реальной машине двигатель продолжает работать, но зажигание в ACC_ON)
            new_state = IgnitionState.ACC_ON

        if old_state != new_state:
            # Если переходим в OFF - выключаем двигатель
            if new_state is IgnitionState.OFF:
                self._state_manager.set_engine_running(False)

            self._state_manager.set_ignition_state(new_state)

            # Emit CAN messages for the new state
            # Используем текущее состояние двигателя для CAN
            current_engine_running = self._state_manager.state.engine_running
            if self._emit_can_callback:
                try:
                    self._emit_can_callback(new_state, engine_running=current_engine_running)
                except Exception as e:
                    logger.error(f"Failed to emit CAN messages: {e}", exc_info=True)
            await self._on_state_changed(old_state, new_state)

    async def handle_long_press(self) -> None:
        """Handle long press of ignition button - sequential state transitions.

        Transitions: OFF → POWER_READY → ACC_ON → ENGINE_RUNNING → ACC_ON
        """
        current_state = self._state_manager.state.ignition_state

        # If already ENGINE_RUNNING, do nothing
        if current_state is IgnitionState.ENGINE_RUNNING:
            logger.info("Already ENGINE_RUNNING, skipping long press")
            return

        # If OFF and driver not ready, do nothing
        if current_state is IgnitionState.OFF and not self._state_manager.state.driver_ready:
            logger.info("OFF state but driver not ready, skipping long press")
            return

        # Sequential transitions
        await self._long_press_sequence()

    async def _long_press_sequence(self) -> None:
        """Execute sequential state transitions for long press."""
        logger.info("Starting long press sequence...")

        current_state = self._state_manager.state.ignition_state

        # Step 1: OFF → POWER_READY
        if current_state is IgnitionState.OFF:
            await self._transition_to(IgnitionState.POWER_READY)
            await asyncio.sleep(config.STATE_TRANSITION_DELAY)
            current_state = IgnitionState.POWER_READY

        # Step 2: POWER_READY → ACC_ON
        if current_state is IgnitionState.POWER_READY:
            await self._transition_to(IgnitionState.ACC_ON)
            await asyncio.sleep(config.STATE_TRANSITION_DELAY)
            current_state = IgnitionState.ACC_ON

        # Step 3: ACC_ON → ENGINE_RUNNING
        if current_state is IgnitionState.ACC_ON:
            # Устанавливаем engine_running = True перед переходом в ENGINE_RUNNING
            self._state_manager.set_engine_running(True)
            await self._transition_to(IgnitionState.ENGINE_RUNNING)
            await asyncio.sleep(config.ENGINE_START_DURATION)
            current_state = IgnitionState.ENGINE_RUNNING

        # Step 4: ENGINE_RUNNING → ACC_ON (after engine start)
        # Двигатель продолжает работать, но зажигание возвращается в ACC_ON
        if current_state is IgnitionState.ENGINE_RUNNING:
            # engine_running остается True - двигатель работает
            await self._transition_to(IgnitionState.ACC_ON, engine_running=True)

        logger.info("Long press sequence completed")

    async def _transition_to(self, new_state: IgnitionState, engine_running: bool = False) -> None:
        """Transition to new state and start emulators if needed.

        Args:
            new_state: Target ignition state.
            engine_running: True if engine is running (for ACC_ON state).
                This parameter is used for CAN messages, but actual engine_running
                state is managed separately via StateManager.
        """
        old_state = self._state_manager.state.ignition_state
        logger.info(f"Transitioning: {old_state.value} → {new_state.value}")

        self._state_manager.set_ignition_state(new_state)
        # Emit CAN messages for the new state
        # Используем переданный engine_running для CAN, но реальное состояние берем из state
        actual_engine_running = self._state_manager.state.engine_running
        if self._emit_can_callback:
            try:
                self._emit_can_callback(new_state, engine_running=actual_engine_running)
            except Exception as e:
                logger.error(f"Failed to emit CAN messages: {e}", exc_info=True)
        await self._start_emulators_if_needed(old_state, new_state, actual_engine_running)

    async def _on_state_changed(self, old_state: IgnitionState, new_state: IgnitionState) -> None:
        """Handle state change - start emulators if needed.

        Args:
            old_state: Previous ignition state.
            new_state: New ignition state.
        """
        await self._start_emulators_if_needed(old_state, new_state, engine_running=False)

    async def _start_emulators_if_needed(
        self,
        old_state: IgnitionState,
        new_state: IgnitionState,
        engine_running: bool = False,
    ) -> None:
        """Start emulators based on ignition state.

        Args:
            old_state: Previous ignition state.
            new_state: New ignition state.
            engine_running: True if engine is running.
        """
        # POWER_READY: Start QNX VM (cluster)
        if new_state is IgnitionState.POWER_READY:
            await self._ensure_qnx_running("POWER_READY")

        # ACC_ON: Start Android HU + QNX VM
        elif new_state is IgnitionState.ACC_ON:
            await self._ensure_emulator_running("ACC_ON", engine_running)
            await self._ensure_qnx_running("ACC_ON")

        # ENGINE_RUNNING: Start everything
        elif new_state is IgnitionState.ENGINE_RUNNING:
            await self._ensure_emulator_running("ENGINE_RUNNING", engine_running=False)
            await self._ensure_qnx_running("ENGINE_RUNNING")

    async def _ensure_emulator_running(self, reason: str, engine_running: bool) -> None:
        """Ensure Android HU emulator is running.

        Args:
            reason: Reason for starting (for logging).
            engine_running: True if engine is running.
        """
        emu_status = self._emulator_manager.runtime.status
        if emu_status in {"RUNNING", "STARTING"}:
            logger.debug(f"Android HU already running (status={emu_status})")
            return

        try:
            logger.info(f"Starting Android HU ({reason})...")
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._emulator_manager.start)
            logger.info(f"Android HU started ({reason})")
        except Exception as e:
            logger.error(f"Failed to start Android HU: {e}", exc_info=True)

    async def _ensure_qnx_running(self, reason: str) -> None:
        """Ensure QNX VM is running.

        Args:
            reason: Reason for starting (for logging).
        """
        qnx_status = self._qnx_vm_manager.runtime.status
        if qnx_status in {"RUNNING", "STARTING"}:
            logger.debug(f"QNX VM already running (status={qnx_status})")
            return

        try:
            logger.info(f"Starting QNX VM ({reason})...")
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._qnx_vm_manager.start)
            logger.info(f"QNX VM started ({reason})")
        except Exception as e:
            logger.error(f"Failed to start QNX VM: {e}", exc_info=True)
