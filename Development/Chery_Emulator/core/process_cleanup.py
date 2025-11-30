"""Utilities for safe process cleanup and port management.

This module provides functions to safely terminate QEMU processes and
clean up ports before starting new emulator instances.
"""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import time
from pathlib import Path
from typing import Optional


def find_qemu_processes(qemu_binary: Optional[str] = None) -> list[tuple[int, str]]:
    """Find all running QEMU processes.

    Returns list of (pid, command_line) tuples.
    """

    processes: list[tuple[int, str]] = []

    try:
        # Use ps to find QEMU processes
        if qemu_binary:
            # Search for specific binary path
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.splitlines():
                if qemu_binary in line and "qemu-system" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            pid = int(parts[1])
                            cmd = " ".join(parts[10:])  # Command starts at index 10
                            processes.append((pid, cmd))
                        except (ValueError, IndexError):
                            continue
        else:
            # Search for any qemu-system-aarch64
            result = subprocess.run(
                ["pgrep", "-fl", "qemu-system"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.splitlines():
                parts = line.split(None, 1)
                if len(parts) >= 2:
                    try:
                        pid = int(parts[0])
                        cmd = parts[1]
                        processes.append((pid, cmd))
                    except (ValueError, IndexError):
                        continue
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        # pgrep/ps not available or failed, try alternative method
        pass

    return processes


def safe_terminate_process(pid: int, timeout: float = 10.0) -> bool:
    """Safely terminate a process: SIGTERM first, then SIGKILL if needed.

    Returns True if process was terminated, False otherwise.
    """

    if not _is_process_running(pid):
        return True

    try:
        # Send SIGTERM for graceful shutdown
        os.kill(pid, signal.SIGTERM)

        # Wait for process to terminate
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not _is_process_running(pid):
                return True
            time.sleep(0.1)

        # If still running, force kill
        if _is_process_running(pid):
            try:
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)
                return not _is_process_running(pid)
            except ProcessLookupError:
                # Process already terminated
                return True
            except PermissionError:
                # No permission to kill (shouldn't happen for our processes)
                return False

    except ProcessLookupError:
        # Process already terminated
        return True
    except PermissionError:
        # No permission to kill
        return False
    except OSError:
        return False

    return False


def _is_process_running(pid: int) -> bool:
    """Check if a process with given PID is still running."""

    try:
        # Send signal 0 to check if process exists
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we don't have permission (unlikely)
        return True
    except OSError:
        return False


def kill_processes_by_port(port: int) -> int:
    """Kill all processes using a specific port.

    Returns number of processes killed.
    """

    killed = 0

    try:
        # Use lsof to find processes using the port
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        for line in result.stdout.strip().splitlines():
            try:
                pid = int(line.strip())
                if safe_terminate_process(pid, timeout=5.0):
                    killed += 1
            except ValueError:
                continue
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        # lsof not available or failed
        pass

    return killed


def cleanup_qemu_processes(
    qemu_binary: Optional[str] = None,
    exclude_pids: Optional[set[int]] = None,
) -> int:
    """Clean up all QEMU processes except those in exclude_pids.

    Returns number of processes terminated.
    """

    exclude_pids = exclude_pids or set()
    processes = find_qemu_processes(qemu_binary)
    killed = 0

    for pid, _ in processes:
        if pid not in exclude_pids:
            if safe_terminate_process(pid, timeout=10.0):
                killed += 1

    return killed


def cleanup_ports(ports: list[int]) -> int:
    """Clean up processes using specified ports.

    Returns total number of processes killed.
    """

    total_killed = 0
    for port in ports:
        killed = kill_processes_by_port(port)
        total_killed += killed

    return total_killed


def wait_for_port_free(port: int, timeout: float = 5.0) -> bool:
    """Wait for a port to become free.

    Returns True if port is free, False if still in use after timeout.
    """

    start_time = time.time()
    while time.time() - start_time < timeout:
        if _is_port_free(port):
            return True
        time.sleep(0.1)

    return _is_port_free(port)


def _is_port_free(port: int) -> bool:
    """Check if a port is free (not in use)."""

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("localhost", port))
            return True
    except OSError:
        return False


def cleanup_all_emulator_resources(
    qemu_binaries: Optional[list[str]] = None,
    ports: Optional[list[int]] = None,
    exclude_pids: Optional[set[int]] = None,
) -> dict[str, int]:
    """Clean up all emulator-related resources.

    Args:
        qemu_binaries: List of QEMU binary paths to search for
        ports: List of ports to free up
        exclude_pids: PIDs to exclude from cleanup

    Returns:
        Dictionary with cleanup statistics:
        {
            "qemu_processes_killed": int,
            "port_processes_killed": int,
        }
    """

    stats: dict[str, int] = {
        "qemu_processes_killed": 0,
        "port_processes_killed": 0,
    }

    # Clean up QEMU processes
    if qemu_binaries:
        for qemu_bin in qemu_binaries:
            killed = cleanup_qemu_processes(qemu_bin, exclude_pids=exclude_pids)
            stats["qemu_processes_killed"] += killed
    else:
        # Clean up all QEMU processes
        killed = cleanup_qemu_processes(exclude_pids=exclude_pids)
        stats["qemu_processes_killed"] += killed

    # Clean up ports
    if ports:
        killed = cleanup_ports(ports)
        stats["port_processes_killed"] += killed

    # Wait a bit for ports to be released
    if ports:
        time.sleep(0.5)

    return stats

