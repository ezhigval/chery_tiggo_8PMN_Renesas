"""QEMU monitor client for querying VM state and debugging.

Подключается к QEMU monitor через TCP socket (HMP protocol) для получения
информации о состоянии виртуальной машины, CPU, памяти и других параметрах.
"""

from __future__ import annotations

import socket
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class QemuMonitor:
    """Client for QEMU Human Monitor Protocol (HMP)."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5558, timeout: float = 1.0) -> None:
        """Initialize QEMU monitor client.

        Args:
            host: Monitor host address.
            port: Monitor TCP port.
            timeout: Socket timeout in seconds.
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self._socket: Optional[socket.socket] = None

    def _connect(self) -> bool:
        """Connect to QEMU monitor socket.

        Returns:
            True if connected, False otherwise.
        """
        if self._socket is not None:
            try:
                # Test if socket is still alive
                self._socket.settimeout(0.1)
                self._socket.recv(1, socket.MSG_PEEK)
                return True
            except (OSError, socket.error):
                # Socket is dead, close it
                try:
                    self._socket.close()
                except Exception:
                    pass
                self._socket = None

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            self._socket = sock
            # Read welcome message (if any)
            try:
                sock.recv(1024)
            except socket.timeout:
                pass
            return True
        except (OSError, socket.error) as e:
            logger.debug(f"Failed to connect to QEMU monitor {self.host}:{self.port}: {e}")
            return False

    def _send_command(self, command: str) -> Optional[str]:
        """Send HMP command and receive response.

        Args:
            command: HMP command (e.g., "info status", "info registers").

        Returns:
            Response string or None if failed.
        """
        if not self._connect():
            return None

        try:
            # Clear any pending data
            self._socket.settimeout(0.1)
            try:
                while True:
                    self._socket.recv(4096, socket.MSG_DONTWAIT)
            except (socket.timeout, OSError):
                pass

            # Send command
            self._socket.sendall((command + "\n").encode("utf-8"))

            # Receive response
            response_parts = []
            self._socket.settimeout(1.0)
            max_iterations = 10
            iteration = 0

            while iteration < max_iterations:
                try:
                    data = self._socket.recv(4096)
                    if not data:
                        break
                    decoded = data.decode("utf-8", errors="ignore")
                    response_parts.append(decoded)

                    # HMP responses typically end with "(qemu) " prompt
                    # Also check for escape sequences (like \r\n, ANSI codes)
                    if "(qemu)" in decoded or "(qemu) " in decoded:
                        break
                    # If we got a complete line with our command echoed back, we're done
                    if command in decoded and len(response_parts) > 1:
                        break
                except socket.timeout:
                    # If we have some data, try to parse it
                    if response_parts:
                        break
                    iteration += 1
                    continue
                iteration += 1

            response = "".join(response_parts)
            # Remove ANSI escape sequences and control characters
            import re
            response = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', response)  # ANSI codes
            response = re.sub(r'\x1b\[K', '', response)  # Clear line
            response = re.sub(r'\[K', '', response)  # Clear line (no ESC)
            response = re.sub(r'\[D', '', response)  # Cursor left

            # Remove prompt and command echo
            response = response.replace("(qemu) ", "")
            response = response.replace("(qemu)", "")
            # Remove echoed command
            for line in response.split("\n"):
                if command in line and "info" not in line.lower():
                    response = response.replace(line, "")

            # Clean up whitespace
            response = "\n".join(line.strip() for line in response.split("\n") if line.strip())
            response = response.strip()

            return response if response else None
        except (OSError, socket.error) as e:
            logger.debug(f"Error sending QEMU monitor command: {e}")
            return None

    def get_status(self) -> dict[str, object]:
        """Get VM status.

        Returns:
            Dictionary with status information.
        """
        result = {
            "connected": False,
            "status": "unknown",
            "running": False,
        }

        response = self._send_command("info status")
        if response:
            result["connected"] = True
            # Parse response (e.g., "VM status: running" or "VM status: paused")
            if "running" in response.lower():
                result["status"] = "running"
                result["running"] = True
            elif "paused" in response.lower():
                result["status"] = "paused"
            elif "inmigrate" in response.lower():
                result["status"] = "inmigrate"
            else:
                result["status"] = response.strip()

        return result

    def get_cpu_info(self) -> dict[str, object]:
        """Get CPU information.

        Returns:
            Dictionary with CPU information.
        """
        result = {
            "connected": False,
            "cpu_count": None,
            "current_cpu": None,
        }

        response = self._send_command("info cpus")
        if response:
            result["connected"] = True
            # Parse response (e.g., "* CPU #0: ...")
            lines = response.split("\n")
            cpu_count = 0
            current_cpu = None
            for line in lines:
                if "* CPU" in line:
                    cpu_count += 1
                    if "*" in line:
                        # Extract CPU number
                        try:
                            parts = line.split("CPU #")
                            if len(parts) > 1:
                                cpu_num = parts[1].split(":")[0].strip()
                                current_cpu = int(cpu_num)
                        except (ValueError, IndexError):
                            pass

            result["cpu_count"] = cpu_count
            result["current_cpu"] = current_cpu

        return result

    def get_memory_info(self) -> dict[str, object]:
        """Get memory information.

        Returns:
            Dictionary with memory information.
        """
        result = {
            "connected": False,
            "total_memory": None,
            "free_memory": None,
        }

        response = self._send_command("info mem")
        if response:
            result["connected"] = True
            # Parse response (memory info format varies)
            # This is a simplified parser
            for line in response.split("\n"):
                if "total" in line.lower() and "memory" in line.lower():
                    # Try to extract memory value
                    try:
                        # Simple heuristic
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part.isdigit():
                                result["total_memory"] = int(part)
                                break
                    except (ValueError, IndexError):
                        pass

        return result

    def close(self) -> None:
        """Close monitor connection."""
        if self._socket is not None:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

