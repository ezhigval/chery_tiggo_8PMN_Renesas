from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Callable, List, Optional


class DisplayFrameManager:
    """Lightweight provider of frames for HU and cluster displays.

    For now this uses static PNG frames extracted from the Android boot
    ramdisk (loop000*.png) as a stand‑in for real QEMU video output.
    Later this module can be extended to read from a VNC server or a
    shared framebuffer without changing the public API.
    """

    def __init__(self, repo_root: Optional[Path] = None) -> None:
        # <repo_root>/Development/Chery_Emulator/core/display_frames.py
        # parents[0] = core, [1] = Chery_Emulator, [2] = Development, [3] = <repo_root>
        self._repo_root = repo_root or Path(__file__).resolve().parents[3]
        self._hu_frames: List[Path] = []
        self._cluster_frames: List[Path] = []
        self._hu_index: int = 0
        self._cluster_index: int = 0
        self._lock = Lock()
        self._load_default_frames()

        # Pluggable providers for future QEMU / Remote Desktop integration.
        # By default use local PNG frames discovered above.
        self._hu_provider: Callable[[], Optional[bytes]] = self._default_hu_frame
        self._cluster_provider: Callable[[], Optional[bytes]] = self._default_cluster_frame

    def _load_default_frames(self) -> None:
        """Discover a set of PNG frames under payload/ for both displays.

        HU:
            Uses loop000*.png frames from the Android recovery animation.
        Cluster:
            Uses progress_empty.png as a simple static placeholder.
        """

        images_dir = (
            self._repo_root
            / "Development"
            / "Chery_Emulator"
            / "payload"
            / "boot_extracted"
            / "ramdisk"
            / "res"
            / "images"
        )

        if images_dir.exists():
            loop_frames = sorted(images_dir.glob("loop*.png"))
            if loop_frames:
                self._hu_frames = loop_frames

            cluster_candidate = images_dir / "progress_empty.png"
            if cluster_candidate.exists():
                self._cluster_frames = [cluster_candidate]

        # Fallback: if nothing found, leave lists empty – API will handle it.

    def _next_frame(self, frames: List[Path], index_attr: str) -> Optional[bytes]:
        if not frames:
            return None

        with self._lock:
            idx = getattr(self, index_attr)
            path = frames[idx % len(frames)]
            setattr(self, index_attr, idx + 1)

        try:
            return path.read_bytes()
        except OSError:
            return None

    def _default_hu_frame(self) -> Optional[bytes]:
        """Return PNG bytes for the next HU frame (or None if unavailable)."""

        return self._next_frame(self._hu_frames, "_hu_index")

    def _default_cluster_frame(self) -> Optional[bytes]:
        """Return PNG bytes for the next cluster frame (or None if unavailable)."""

        return self._next_frame(self._cluster_frames, "_cluster_index")

    # --- Public API used by FastAPI layer ---

    def set_hu_provider(self, fn: Optional[Callable[[], Optional[bytes]]]) -> None:
        """Override HU frame provider (e.g. QEMU, VNC).

        Passing None restores the default local PNG sequence.
        """

        if fn is None:
            self._hu_provider = self._default_hu_frame
        else:
            self._hu_provider = fn

    def set_cluster_provider(self, fn: Optional[Callable[[], Optional[bytes]]]) -> None:
        """Override cluster frame provider (e.g. QNX/QEMU, remote desktop)."""

        if fn is None:
            self._cluster_provider = self._default_cluster_frame
        else:
            self._cluster_provider = fn

    def next_hu_frame(self) -> Optional[bytes]:
        """Return PNG bytes for the next HU frame.

        Uses the pluggable provider; if it fails, falls back to local defaults.
        """

        data = self._hu_provider()
        if data is None and self._hu_provider is not self._default_hu_frame:
            # best-effort fallback to local assets
            data = self._default_hu_frame()
        return data

    def next_cluster_frame(self) -> Optional[bytes]:
        """Return PNG bytes for the next cluster frame."""

        data = self._cluster_provider()
        if data is None and self._cluster_provider is not self._default_cluster_frame:
            data = self._default_cluster_frame()
        return data


display_manager = DisplayFrameManager()


