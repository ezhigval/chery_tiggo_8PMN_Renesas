from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Sequence

import subprocess

from .emulator import EmulatorConfig


class QnxVmStatus(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    ERROR = "ERROR"


@dataclass
class QnxVmRuntime:
    status: QnxVmStatus = QnxVmStatus.STOPPED
    last_error: Optional[str] = None
    last_qemu_command: Optional[str] = None
    pid: Optional[int] = None


class QnxVmManager:
    """Separate manager for a QNX‑only QEMU instance.

    This intentionally does not interfere with the main Android+QNX emulator.
    It uses the same EmulatorConfig source (emulator_config.yaml) to locate
    QNX images and the custom g6sh binary, but spawns its own process.
    """

    def __init__(self, repo_root: Optional[Path] = None) -> None:
        self.repo_root = repo_root or Path(__file__).resolve().parents[3]
        self.config = EmulatorConfig.load_default(self.repo_root)
        self.runtime = QnxVmRuntime()
        self._process: Optional[subprocess.Popen[bytes]] = None
        self._hypervisor_ifs: Optional[Path] = self._discover_hypervisor_ifs()

    def _discover_hypervisor_ifs(self) -> Optional[Path]:
        """Best-effort discovery of the QNX hypervisor IFS image.

        For now we primarily look for the known extracted image:
        `Development/Chery_Emulator/qemu_g6sh/hypervisor-ifs-rcar_h3-graphics.bin`.
        """

        default = (
            self.repo_root
            / "Development"
            / "Chery_Emulator"
            / "qemu_g6sh"
            / "hypervisor-ifs-rcar_h3-graphics.bin"
        )
        if default.exists():
            return default

        # Fallback: search the repo for any matching path.
        for path in self.repo_root.rglob("hypervisor-ifs-rcar_h3-graphics.bin"):
            return path
        return None

    def _validate_config(self) -> Optional[str]:
        if self._hypervisor_ifs is None or not self._hypervisor_ifs.exists():
            return "QNX hypervisor IFS image not found (hypervisor-ifs-rcar_h3-graphics.bin)"
        # Rootfs is optional for now; QNX may boot from IFS only.
        return None

    def build_qemu_args(
        self,
        uart_port: int = 1234,
        virtio_console_port: int = 1236,
        enable_debug: bool = True,
    ) -> Sequence[str]:
        """Build QEMU argv for QNX‑only VM.

        This is a minimal baseline:
        - Machine: virt (standard ARM virt board with our QNX tweaks).
        - CPU/RAM: modest defaults.
        - QNX console (ttyAMA0 / PL011 at 0x1c090000) exposed via a TCP socket
          for telnet/nc / QnxConsole access.
        - virtio-console for QNX logs (preferred over SCIF, as QNX IFS includes
          vdev-virtio-console.so).
        - QNX hypervisor IFS passed as -kernel.
        - Optional QNX system image attached as read‑only virtio disk.
        """

        cfg = self.config

        # QNX‑VM всегда запускаем через специализированный SCIF/PL011 форк,
        # чтобы не зависеть от настроек основного эмулятора для Android.
        qemu_bin = str(
            self.repo_root
            / "Development"
            / "Chery_Emulator"
            / "qemu_scif_fork"
            / "qemu-system-aarch64"
        )

        # Для QNX‑VM используем базовую virt‑машину нашего форка. Все нужные
        # устройства (PL011‑консоль, диски) подключаются через параметры и
        # внутреннюю логку virt.c (virt_create_qnx_console_pl011).
        machine_arg = "virt"

        args: list[str] = [
            qemu_bin,
            "-M",
            machine_arg,
            "-cpu",
            "cortex-a57",
            "-smp",
            "2",
            "-m",
            "2048",
        ]

        # На этапе отладки SCIF/консоли мы не привязываем чардев к HSCIF:
        # QEMU просто логирует все MMIO‑доступы к UART‑адресам в qnx_qemu_stdout.log.
        # Когда станет ясно, какой именно UART используется, сюда вернём -chardev.

        # Включаем VNC‑вывод для QNX/cluster дисплея на стандартном порту 5901.
        # Это соответствует graphics.cluster.vnc_* в emulator_config.yaml.
        args += [
            "-display",
            # QEMU interprets ":1" as TCP port 5900 + 1 = 5901.
            "vnc=127.0.0.1:1",
        ]

        # We intentionally do not pass a DTB here; the hypervisor image
        # was validated with the stock "virt" machine and its built‑in DT.

        # Use the extracted hypervisor IFS as the kernel payload. The QNX
        # image itself contains the startup code and embedded system image.
        if self._hypervisor_ifs is not None:
            args += ["-kernel", str(self._hypervisor_ifs)]

        # Attach QNX system image as read‑only disk if present.
        if cfg.qnx_system_img is not None and cfg.qnx_system_img.exists():
            args += [
                "-drive",
                f"if=none,file={cfg.qnx_system_img},format=raw,read-only=on,id=qnxsys",
                "-device",
                "virtio-blk-pci,drive=qnxsys",
            ]

        # virtio-console для QNX: QNX IFS содержит vdev-virtio-console.so, поэтому
        # консоль QNX скорее всего идёт через virtio-console, а не через SCIF.
        args += [
            "-device",
            "virtio-serial-pci,id=qnx_virtio_serial0",
            "-chardev",
            f"socket,id=qnx_virtcon,host=localhost,port={virtio_console_port},server=on,wait=off",
            "-device",
            "virtconsole,chardev=qnx_virtcon,name=qnx-virtcon0",
        ]

        # QEMU debug режим для диагностики: guest_errors, unimp, mmu
        # Это поможет увидеть ошибки инициализации устройств и нереализованные функции.
        if enable_debug:
            args += [
                "-d",
                "guest_errors,unimp,mmu",
            ]

        # We keep networking and GPU minimal for now; they can be added later.

        # Record stdout log path; start() will redirect stdout/stderr there.
        logs_dir = self.repo_root / "Development" / "Chery_Emulator" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        stdout_log = logs_dir / "qnx_qemu_stdout.log"
        self._stdout_log_path = stdout_log

        return args

    def build_qemu_command(self) -> str:
        return " ".join(self.build_qemu_args())

    def start(self) -> None:
        if self.runtime.status in {QnxVmStatus.STARTING, QnxVmStatus.RUNNING}:
            return

        self.runtime.status = QnxVmStatus.STARTING
        self.runtime.last_error = None
        self.runtime.last_qemu_command = None
        self.runtime.pid = None

        error = self._validate_config()
        if error is not None:
            self.runtime.status = QnxVmStatus.ERROR
            self.runtime.last_error = error
            return

        args = list(self.build_qemu_args())
        cmd_str = " ".join(args)
        self.runtime.last_qemu_command = cmd_str

        logs_dir = self.repo_root / "Development" / "Chery_Emulator" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "qnx_qemu_command.txt").write_text(cmd_str + "\n", encoding="utf-8")

        try:
            log_file = self._stdout_log_path.open("ab", buffering=0)  # type: ignore[attr-defined]
        except OSError as exc:
            self.runtime.status = QnxVmStatus.ERROR
            self.runtime.last_error = f"Failed to open QNX log file: {exc}"
            return

        try:
            self._process = subprocess.Popen(
                args,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )
        except FileNotFoundError:
            self.runtime.status = QnxVmStatus.ERROR
            self.runtime.last_error = "qemu-system-aarch64 (QNX VM) not found"
            self._process = None
            log_file.close()
            return
        except OSError as exc:
            self.runtime.status = QnxVmStatus.ERROR
            self.runtime.last_error = f"Failed to start QNX VM: {exc}"
            self._process = None
            log_file.close()
            return

        self.runtime.status = QnxVmStatus.RUNNING
        self.runtime.pid = self._process.pid

    def stop(self) -> None:
        if self.runtime.status not in {QnxVmStatus.RUNNING, QnxVmStatus.STARTING}:
            return

        self.runtime.status = QnxVmStatus.STOPPING

        if self._process is not None and self._process.poll() is None:
            try:
                self._process.terminate()
                try:
                    self._process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait(timeout=5)
            except OSError as exc:
                self.runtime.last_error = f"Failed to stop QNX VM: {exc}"

        self._process = None
        self.runtime.status = QnxVmStatus.STOPPED
        self.runtime.pid = None

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.runtime.status.value,
            "last_error": self.runtime.last_error,
            "last_qemu_command": self.runtime.last_qemu_command,
            "pid": self.runtime.pid,
        }


qnx_vm_manager = QnxVmManager()


