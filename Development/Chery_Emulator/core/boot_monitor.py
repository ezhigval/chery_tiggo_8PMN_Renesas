"""Boot monitoring utilities for tracking system boot progress.

Отслеживает процесс загрузки Android и QNX систем, проверяет активность
и определяет, действительно ли системы загружаются или висят.
"""

from __future__ import annotations

import asyncio
import logging
import psutil
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class BootMonitor:
    """Monitors boot progress of emulated systems."""

    def __init__(self, log_dir: Path) -> None:
        """Initialize boot monitor.

        Args:
            log_dir: Directory containing QEMU logs.
        """
        self.log_dir = log_dir
        self._last_android_log_size = 0
        self._last_qnx_log_size = 0
        self._last_check_time = datetime.now()

    def check_android_boot_progress(self) -> dict[str, object]:
        """Check Android boot progress by analyzing logs.

        Returns:
            Dictionary with boot status information.
        """
        console_log = self.log_dir / "qemu_console.log"
        stdout_log = self.log_dir / "qemu_stdout.log"

        result = {
            "log_active": False,
            "has_errors": False,
            "last_activity_seconds_ago": None,
            "log_size_bytes": 0,
            "sample_lines": [],
        }

        # Check console log
        if console_log.exists():
            try:
                current_size = console_log.stat().st_size
                result["log_size_bytes"] = current_size

                if current_size > self._last_android_log_size:
                    result["log_active"] = True
                    self._last_android_log_size = current_size
                    self._last_check_time = datetime.now()

                    # Read last few lines
                    try:
                        with console_log.open("r", encoding="utf-8", errors="ignore") as f:
                            lines = f.readlines()
                            result["sample_lines"] = lines[-10:] if len(lines) > 10 else lines
                            # Check for errors
                            for line in lines[-20:]:
                                if any(keyword in line.lower() for keyword in ["error", "fail", "panic", "oops"]):
                                    result["has_errors"] = True
                                    break
                    except Exception as e:
                        logger.debug(f"Failed to read console log: {e}")

                elif current_size > 0:
                    # Log exists but not growing
                    elapsed = (datetime.now() - self._last_check_time).total_seconds()
                    result["last_activity_seconds_ago"] = elapsed
            except OSError:
                pass

        # Check stdout log for QEMU errors
        if stdout_log.exists():
            try:
                with stdout_log.open("r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    for line in lines[-10:]:
                        if any(keyword in line.lower() for keyword in ["error", "fail", "cannot", "unable"]):
                            result["has_errors"] = True
                            break
            except Exception:
                pass

        return result

    def check_qnx_boot_progress(self) -> dict[str, object]:
        """Check QNX boot progress by analyzing logs and console connections.

        Returns:
            Dictionary with boot status information.
        """
        stdout_log = self.log_dir / "qnx_qemu_stdout.log"
        pl011_socket = Path("/tmp")  # PL011 socket would be on localhost:1237

        result = {
            "log_active": False,
            "has_errors": False,
            "last_activity_seconds_ago": None,
            "log_size_bytes": 0,
            "sample_lines": [],
            "console_available": False,
        }

        # Check stdout log
        if stdout_log.exists():
            try:
                current_size = stdout_log.stat().st_size
                result["log_size_bytes"] = current_size

                if current_size > self._last_qnx_log_size:
                    result["log_active"] = True
                    self._last_qnx_log_size = current_size
                    self._last_check_time = datetime.now()

                    # Read last few lines
                    try:
                        with stdout_log.open("r", encoding="utf-8", errors="ignore") as f:
                            lines = f.readlines()
                            result["sample_lines"] = lines[-10:] if len(lines) > 10 else lines
                            # Check for errors
                            for line in lines[-20:]:
                                if any(keyword in line.lower() for keyword in ["error", "fail", "panic", "unable"]):
                                    result["has_errors"] = True
                                    break
                    except Exception as e:
                        logger.debug(f"Failed to read QNX log: {e}")

                elif current_size > 0:
                    # Log exists but not growing
                    elapsed = (datetime.now() - self._last_check_time).total_seconds()
                    result["last_activity_seconds_ago"] = elapsed
            except OSError:
                pass

        # Check if console socket is available (PL011 on port 1237)
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result["console_available"] = sock.connect_ex(("localhost", 1237)) == 0
            sock.close()
        except Exception:
            pass

        return result

    async def check_adb_status_async(self, host: str = "127.0.0.1", port: int = 5557) -> dict[str, object]:
        """Check Android ADB connection status (async with timeout).

        Returns:
            Dictionary with ADB status information.
        """
        result = {
            "connected": False,
            "device_state": "unknown",
            "boot_completed": False,
        }

        try:
            import shutil
            adb_bin = shutil.which("adb")
            if adb_bin is None:
                return result

            # Check if device is connected (with timeout)
            try:
                proc = await asyncio.wait_for(
                    asyncio.create_subprocess_exec(
                        adb_bin, "devices",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    ),
                    timeout=2.0,
                )
                stdout, _ = await proc.communicate()
                output = stdout.decode("utf-8", errors="ignore")

                if f"{host}:{port}" in output:
                    result["connected"] = True
                    if "device" in output and "offline" not in output:
                        result["device_state"] = "online"

                # Check boot completion (only if connected)
                if result["connected"] and result["device_state"] == "online":
                    try:
                        proc = await asyncio.wait_for(
                            asyncio.create_subprocess_exec(
                                adb_bin, "-s", f"{host}:{port}", "shell", "getprop", "sys.boot_completed",
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE,
                            ),
                            timeout=3.0,
                        )
                        stdout, _ = await proc.communicate()
                        if proc.returncode == 0 and b"1" in stdout:
                            result["boot_completed"] = True
                    except asyncio.TimeoutError:
                        pass
                    except Exception:
                        pass
            except asyncio.TimeoutError:
                pass
        except Exception:
            pass

        return result

    def check_adb_status(self, host: str = "127.0.0.1", port: int = 5557) -> dict[str, object]:
        """Check Android ADB connection status (sync, fast fallback).

        Returns:
            Dictionary with ADB status information.
        """
        result = {
            "connected": False,
            "device_state": "unknown",
            "boot_completed": False,
        }

        try:
            import shutil
            adb_bin = shutil.which("adb")
            if adb_bin is None:
                return result

            # Quick check: try to connect to ADB port
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                if sock.connect_ex((host, port)) == 0:
                    result["connected"] = True
                    result["device_state"] = "online"  # Assume online if port is open
                sock.close()
            except Exception:
                pass

            # If port is open, try quick ADB check (with strict timeout)
            if result["connected"]:
                try:
                    proc = subprocess.run(
                        [adb_bin, "-s", f"{host}:{port}", "shell", "getprop", "sys.boot_completed"],
                        capture_output=True,
                        text=True,
                        timeout=2,
                    )
                    if proc.returncode == 0 and "1" in proc.stdout:
                        result["boot_completed"] = True
                except (subprocess.TimeoutExpired, Exception):
                    pass
        except Exception:
            pass

        return result

    def check_qemu_process(self, pid: Optional[int]) -> dict[str, object]:
        """Check QEMU process status using psutil.

        Returns:
            Dictionary with process information.
        """
        result = {
            "running": False,
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "elapsed_seconds": None,
        }

        if pid is None:
            return result

        try:
            process = psutil.Process(pid)
            with process.oneshot():
                result["running"] = process.is_running()
                if result["running"]:
                    result["cpu_percent"] = process.cpu_percent(interval=0.1)
                    result["memory_percent"] = process.memory_percent()
                    create_time = datetime.fromtimestamp(process.create_time())
                    result["elapsed_seconds"] = (datetime.now() - create_time).total_seconds()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        except Exception:
            pass

        return result

    def check_port_status(self, host: str = "localhost", port: int = 0) -> dict[str, object]:
        """Check if a TCP port is open.

        Returns:
            Dictionary with port status.
        """
        result = {
            "open": False,
            "host": host,
            "port": port,
        }

        if port == 0:
            return result

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            result["open"] = sock.connect_ex((host, port)) == 0
            sock.close()
        except Exception:
            pass

        return result

    def check_qemu_monitor(self, host: str = "127.0.0.1", port: int = 5558) -> dict[str, object]:
        """Check QEMU monitor status.

        Returns:
            Dictionary with monitor status and VM information.
        """
        result = {
            "connected": False,
            "vm_status": "unknown",
            "vm_running": False,
        }

        try:
            from .qemu_monitor import QemuMonitor
            monitor = QemuMonitor(host=host, port=port, timeout=0.5)
            status = monitor.get_status()
            monitor.close()

            result.update(status)
        except Exception as e:
            logger.debug(f"Failed to check QEMU monitor: {e}")

        return result

