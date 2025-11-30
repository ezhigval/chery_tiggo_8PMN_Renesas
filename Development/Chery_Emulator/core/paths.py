"""Centralized path management for the emulator.

All path calculations should use functions from this module to ensure consistency.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def get_repo_root(repo_root: Optional[Path] = None) -> Path:
    """Get repository root directory.

    Args:
        repo_root: Optional explicit repo root. If None, calculates from __file__.

    Returns:
        Path to repository root (Tiggo/).

    Path calculation:
        <repo_root>/Development/Chery_Emulator/core/paths.py
        parents[0] = core
        parents[1] = Chery_Emulator
        parents[2] = Development
        parents[3] = <repo_root>
    """
    if repo_root is not None:
        return repo_root
    # This file is in core/, so parents[3] gets us to repo root
    return Path(__file__).resolve().parents[3]


def get_emulator_dir(repo_root: Optional[Path] = None) -> Path:
    """Get Chery_Emulator directory.

    Args:
        repo_root: Optional explicit repo root.

    Returns:
        Path to Development/Chery_Emulator/.
    """
    repo = get_repo_root(repo_root)
    return repo / "Development" / "Chery_Emulator"


def get_data_dir(repo_root: Optional[Path] = None) -> Path:
    """Get data directory.

    Args:
        repo_root: Optional explicit repo root.

    Returns:
        Path to Development/Chery_Emulator/data/.
    """
    emulator_dir = get_emulator_dir(repo_root)
    return emulator_dir / "data"


def get_logs_dir(repo_root: Optional[Path] = None) -> Path:
    """Get logs directory.

    Args:
        repo_root: Optional explicit repo root.

    Returns:
        Path to Development/Chery_Emulator/logs/.
    """
    emulator_dir = get_emulator_dir(repo_root)
    return emulator_dir / "logs"


def get_config_path(repo_root: Optional[Path] = None) -> Path:
    """Get emulator_config.yaml path.

    Args:
        repo_root: Optional explicit repo root.

    Returns:
        Path to Development/Chery_Emulator/emulator_config.yaml.
    """
    emulator_dir = get_emulator_dir(repo_root)
    return emulator_dir / "emulator_config.yaml"


def get_web_dir(repo_root: Optional[Path] = None) -> Path:
    """Get web directory.

    Args:
        repo_root: Optional explicit repo root.

    Returns:
        Path to Development/Chery_Emulator/web/.
    """
    emulator_dir = get_emulator_dir(repo_root)
    return emulator_dir / "web"

