"""CAN bridge service for macOS.

This module provides a bridge between TCP socket and Linux socketcan.
It can run in a Docker container on macOS to provide socketcan functionality.

Usage:
    # Run in Docker container with socketcan support
    python3 -m core.can_bridge
"""

from __future__ import annotations

import socket
import struct
import threading
from pathlib import Path
from typing import Optional

# Try to import socketcan (only works on Linux)
try:
    import ctypes

    AF_CAN = 29
    PF_CAN = AF_CAN
    SOCK_RAW = 3
    CAN_RAW = 1

    class LinuxCanFrame(ctypes.Structure):
        _fields_ = [
            ("can_id", ctypes.c_uint32),
            ("can_dlc", ctypes.c_uint8),
            ("flags", ctypes.c_uint8),
            ("res0", ctypes.c_uint8),
            ("res1", ctypes.c_uint8),
            ("data", ctypes.c_uint8 * 8),
        ]

    CAN_MTU = ctypes.sizeof(LinuxCanFrame)
    _socketcan_available = True
except (ImportError, OSError, AttributeError):
    _socketcan_available = False
    LinuxCanFrame = None  # type: ignore[assignment, misc]
    CAN_MTU = 16


class CanBridge:
    """Bridge between TCP socket and socketcan interface.

    Listens on TCP port and forwards CAN frames to socketcan interface.
    """

    def __init__(
        self,
        tcp_host: str = "localhost",
        tcp_port: int = 1238,
        can_interface: str = "vcan0",
    ) -> None:
        self.tcp_host = tcp_host
        self.tcp_port = tcp_port
        self.can_interface = can_interface
        self._tcp_socket: Optional[socket.socket] = None
        self._can_socket: Optional[socket.socket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the bridge service."""
        if not _socketcan_available:
            raise RuntimeError("Socketcan not available (Linux required)")

        # Create CAN socket
        self._can_socket = socket.socket(PF_CAN, SOCK_RAW, CAN_RAW)

        # Get interface index
        import ctypes
        ifr = ctypes.create_string_buffer(
            self.can_interface.encode() + b'\x00' * (16 - len(self.can_interface))
        )
        SIOCGIFINDEX = 0x8933
        ioctl_result = ctypes.CDLL(None).ioctl(
            self._can_socket.fileno(), SIOCGIFINDEX, ctypes.addressof(ifr)
        )
        if ioctl_result < 0:
            raise OSError(f"Interface {self.can_interface} not found")

        # Bind to CAN interface
        self._can_socket.bind((AF_CAN, 0))

        # Create TCP listening socket
        self._tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._tcp_socket.bind((self.tcp_host, self.tcp_port))
        self._tcp_socket.listen(1)

        self._running = True
        self._thread = threading.Thread(target=self._bridge_loop, daemon=True)
        self._thread.start()

        print(f"CAN bridge started: TCP {self.tcp_host}:{self.tcp_port} -> {self.can_interface}")

    def _bridge_loop(self) -> None:
        """Main bridge loop: forward TCP -> socketcan."""
        while self._running:
            try:
                # Accept TCP connection
                client, _ = self._tcp_socket.accept()
                print(f"TCP client connected")

                # Forward frames
                while self._running:
                    # Read from TCP (our format: >IB8s)
                    data = client.recv(13)  # 4 + 1 + 8 bytes
                    if not data:
                        break

                    if len(data) < 13:
                        continue

                    # Parse our format
                    can_id, data_len, data_bytes = struct.unpack(">IB8s", data)

                    # Convert to Linux can_frame format
                    can_frame = struct.pack("=IBBBBB8s", can_id, data_len, 0, 0, 0, data_bytes)

                    # Send to socketcan
                    if self._can_socket:
                        self._can_socket.send(can_frame)

            except OSError:
                if self._running:
                    break

    def stop(self) -> None:
        """Stop the bridge service."""
        self._running = False
        if self._tcp_socket:
            try:
                self._tcp_socket.close()
            except OSError:
                pass
        if self._can_socket:
            try:
                self._can_socket.close()
            except OSError:
                pass


if __name__ == "__main__":
    import os

    tcp_host = os.getenv("TCP_HOST", "0.0.0.0")
    tcp_port = int(os.getenv("TCP_PORT", "1238"))
    can_interface = os.getenv("CAN_INTERFACE", "vcan0")

    bridge = CanBridge(tcp_host=tcp_host, tcp_port=tcp_port, can_interface=can_interface)
    try:
        bridge.start()
        import time
        print("CAN bridge running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping CAN bridge...")
        bridge.stop()

