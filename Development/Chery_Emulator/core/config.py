"""Configuration constants for the emulator."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EmulatorConfig:
    """Configuration constants for the emulator."""

    # Timing constants (in seconds)
    STATE_TRANSITION_DELAY: float = 0.5  # Delay between state transitions
    ENGINE_START_DURATION: float = 3.0    # Engine start sequence duration
    LONG_PRESS_THRESHOLD_MS: int = 1000   # Long press threshold in milliseconds

    # Polling intervals (in milliseconds)
    UI_STATE_POLL_INTERVAL_MS: int = 10000  # UI state polling interval
    UI_CONSOLE_POLL_INTERVAL_MS: int = 5000  # UI console polling interval

    # CAN server
    CAN_CHECK_INTERVAL: float = 2.0  # CAN connection check interval

    # Paths
    DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"
    STATE_FILE: Path = DATA_DIR / "vehicle_state.json"
    LOGS_DIR: Path = Path(__file__).resolve().parent.parent / "logs"

    # Ports
    API_PORT: int = 8000
    CAN_SERVER_PORT: int = 1238
    ADB_PORT: int = 5557
    VNC_HU_PORT: int = 5900
    VNC_CLUSTER_PORT: int = 5901
    QNX_PL011_PORT: int = 1237
    QNX_UART_PORT: int = 1239

    def __post_init__(self) -> None:
        """Ensure directories exist."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)


# Global config instance
config = EmulatorConfig()
