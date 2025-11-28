from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from .vnc_client import VncClient


@dataclass
class VncEndpoint:
    host: str
    port: int


@dataclass
class GraphicsConfig:
    hu_vnc: Optional[VncEndpoint]
    cluster_vnc: Optional[VncEndpoint]


def _load_graphics_config(repo_root: Path) -> GraphicsConfig:
    cfg_path = repo_root / "Development" / "Chery_Emulator" / "emulator_config.yaml"
    hu: Optional[VncEndpoint] = None
    cluster: Optional[VncEndpoint] = None

    if cfg_path.exists():
        try:
            data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        except Exception:
            data = {}
        graphics = data.get("graphics", {}) or {}

        def _ep(section: dict | None) -> Optional[VncEndpoint]:
            if not section:
                return None
            host = str(section.get("vnc_host", "127.0.0.1"))
            port_raw = section.get("vnc_port", None)
            try:
                port = int(port_raw)
            except (TypeError, ValueError):
                return None
            return VncEndpoint(host=host, port=port)

        hu = _ep(graphics.get("hu"))
        cluster = _ep(graphics.get("cluster"))

    # Sensible defaults if nothing is configured yet – these match earlier
    # VNC planning docs (5900 / 5901 on localhost).
    if hu is None:
        hu = VncEndpoint(host="127.0.0.1", port=5900)
    if cluster is None:
        cluster = VncEndpoint(host="127.0.0.1", port=5901)

    return GraphicsConfig(hu_vnc=hu, cluster_vnc=cluster)


repo_root_default = Path(__file__).resolve().parents[3]
_graphics_cfg = _load_graphics_config(repo_root_default)

_hu_client = (
    VncClient(_graphics_cfg.hu_vnc.host, _graphics_cfg.hu_vnc.port)  # type: ignore[union-attr]
    if _graphics_cfg.hu_vnc is not None
    else None
)
_cluster_client = (
    VncClient(_graphics_cfg.cluster_vnc.host, _graphics_cfg.cluster_vnc.port)  # type: ignore[union-attr]
    if _graphics_cfg.cluster_vnc is not None
    else None
)


def hu_vnc_frame() -> Optional[bytes]:
    """Return HU frame from VNC (PNG) or None if unavailable."""

    if _hu_client is None:
        return None
    return _hu_client.get_frame_png()


def cluster_vnc_frame() -> Optional[bytes]:
    """Return Cluster frame from VNC (PNG) or None if unavailable."""

    if _cluster_client is None:
        return None
    return _cluster_client.get_frame_png()



