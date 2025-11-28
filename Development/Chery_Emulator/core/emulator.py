from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Sequence

from datetime import datetime
import os
import shutil
import subprocess
import yaml


class EmulatorStatus(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    ERROR = "ERROR"


@dataclass
class EmulatorConfig:
    """Configuration for QEMU/Android+QNX images.

    Values are loaded from `Development/Chery_Emulator/emulator_config.yaml`.
    Paths are stored as repository-root-relative `Path` objects.
    """

    # QEMU binary / machine configuration
    qemu_binary: Optional[Path] = None
    qemu_machine: str = "virt"
    qemu_dtb: Optional[Path] = None

    android_ota: Optional[Path] = None
    android_boot_img: Optional[Path] = None
    android_system_img: Optional[Path] = None
    android_vendor_img: Optional[Path] = None
    android_product_img: Optional[Path] = None
    android_boot_partition: str = "boot_b"
    android_system_partition: str = "system_b"
    android_vendor_partition: str = "vendor_b"

    qnx_ota: Optional[Path] = None
    qnx_boot_img: Optional[Path] = None
    qnx_system_img: Optional[Path] = None
    qnx_boot_partition: str = "qnx_boot_b"
    qnx_system_partition: str = "qnx_system_b"
    qnx_enable: bool = False

    @classmethod
    def load_default(cls, repo_root: Optional[Path] = None) -> "EmulatorConfig":
        # By default determine repo root as the project root (.. / .. / .. from this file):
        #   <repo_root>/Development/Chery_Emulator/core/emulator.py
        # parents[0] = core, [1] = Chery_Emulator, [2] = Development, [3] = <repo_root>
        repo = repo_root or Path(__file__).resolve().parents[3]
        cfg_path = repo / "Development" / "Chery_Emulator" / "emulator_config.yaml"
        if not cfg_path.exists():
            return cls()

        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}

        android = data.get("android", {}) or {}
        qnx = data.get("qnx", {}) or {}
        qemu_cfg = data.get("qemu", {}) or {}

        android_ota = android.get("ota_zip")
        qnx_ota = qnx.get("ota_zip")

        def _p(rel: Optional[str]) -> Optional[Path]:
            if not rel:
                return None
            p = Path(rel)
            return p if p.is_absolute() else repo / p

        cfg = cls(
            qemu_binary=_p(qemu_cfg.get("binary")),
            qemu_machine=str(qemu_cfg.get("machine", "virt")),
            qemu_dtb=_p(qemu_cfg.get("dtb")),
            android_ota=_p(android_ota),
            android_boot_img=_p(android.get("boot_img")),
            android_system_img=_p(android.get("system_img")),
            android_vendor_img=_p(android.get("vendor_img")),
            android_product_img=_p(android.get("product_img")),
            android_boot_partition=str(android.get("boot_partition", "boot_b")),
            android_system_partition=str(android.get("system_partition", "system_b")),
            android_vendor_partition=str(android.get("vendor_partition", "vendor_b")),
            qnx_ota=_p(qnx_ota),
            qnx_boot_img=_p(qnx.get("qnx_boot_img")),
            qnx_system_img=_p(qnx.get("qnx_system_img")),
            qnx_boot_partition=str(qnx.get("boot_partition", "qnx_boot_b")),
            qnx_system_partition=str(qnx.get("system_partition", "qnx_system_b")),
            qnx_enable=bool(qnx.get("enable", False)),
        )

        # Best-effort auto-discovery if paths are missing or files do not exist.
        def _find_first(name: str) -> Optional[Path]:
            # Prefer firmware directory, then entire repo.
            firmware_dir = repo / "firmware"
            candidates: list[Path] = []
            if firmware_dir.exists():
                candidates += list(firmware_dir.rglob(name))
            if not candidates:
                candidates += list(repo.rglob(name))
            return candidates[0] if candidates else None

        if cfg.android_boot_img is None or not cfg.android_boot_img.exists():
            found = _find_first("boot.img")
            if found is not None:
                cfg.android_boot_img = found
        if cfg.android_system_img is None or not cfg.android_system_img.exists():
            found = _find_first("system.img")
            if found is not None:
                cfg.android_system_img = found
        if cfg.android_vendor_img is None or not cfg.android_vendor_img.exists():
            found = _find_first("vendor.img")
            if found is not None:
                cfg.android_vendor_img = found
        if cfg.android_product_img is None or not cfg.android_product_img.exists():
            found = _find_first("product.img")
            if found is not None:
                cfg.android_product_img = found
        if cfg.qnx_boot_img is None or not cfg.qnx_boot_img.exists():
            found = _find_first("qnx_boot.img")
            if found is not None:
                cfg.qnx_boot_img = found
        if cfg.qnx_system_img is None or not cfg.qnx_system_img.exists():
            found = _find_first("qnx_system.img")
            if found is not None:
                cfg.qnx_system_img = found

        return cfg


@dataclass
class EmulatorRuntime:
    status: EmulatorStatus = EmulatorStatus.STOPPED
    last_error: Optional[str] = None
    last_qemu_command: Optional[str] = None
    pid: Optional[int] = None


class EmulatorManager:
    def __init__(self, repo_root: Optional[Path] = None) -> None:
        # Keep repo_root consistent with EmulatorConfig.load_default()
        self.repo_root = repo_root or Path(__file__).resolve().parents[3]
        self.config = EmulatorConfig.load_default(self.repo_root)
        self.runtime = EmulatorRuntime()
        self._process: Optional[subprocess.Popen[bytes]] = None
        self._adb_process: Optional[subprocess.Popen[bytes]] = None
        self._cfg_path = (
            self.repo_root / "Development" / "Chery_Emulator" / "emulator_config.yaml"
        )
        self._logs_dir = (
            self.repo_root / "Development" / "Chery_Emulator" / "logs"
        )
        self._logs_dir.mkdir(parents=True, exist_ok=True)

    # ----- Internal core log helpers -----

    def _core_log_path(self) -> Path:
        return self._logs_dir / "emulator_core.log"

    def log(self, message: str) -> None:
        """Append a line to the internal emulator core log.

        Non-fatal helper: any I/O errors are silently ignored.
        """

        ts = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        line = f"{ts} {message}\n"
        try:
            with self._core_log_path().open("a", encoding="utf-8") as f:
                f.write(line)
        except OSError:
            return

    def _validate_config(self) -> Optional[str]:
        if self.config.android_boot_img is None or not self.config.android_boot_img.exists():
            return f"Android boot.img not found: {self.config.android_boot_img!r}"
        if self.config.android_system_img is None or not self.config.android_system_img.exists():
            return f"Android system.img not found: {self.config.android_system_img!r}"
        if self.config.android_vendor_img is None or not self.config.android_vendor_img.exists():
            return f"Android vendor.img not found: {self.config.android_vendor_img!r}"
        if self.config.android_product_img is None or not self.config.android_product_img.exists():
            return f"Android product.img not found: {self.config.android_product_img!r}"
        # QNX images are optional for now; we can relax/strengthen this later.
        return None

    def build_qemu_args(self) -> Sequence[str]:
        """Build a QEMU argv list based on current config.

        This does not start QEMU; it only returns the argument list.
        The command is based on the T18FL3_SIMULATION_README.md defaults.
        """

        cfg = self.config

        boot = cfg.android_boot_img
        system = cfg.android_system_img
        vendor = cfg.android_vendor_img
        product = cfg.android_product_img
        qnx_boot = cfg.qnx_boot_img
        qnx_system = cfg.qnx_system_img

        qemu_bin = str(cfg.qemu_binary or "qemu-system-aarch64")

        machine = cfg.qemu_machine or "virt"
        if "," in machine:
            machine_arg = machine
        elif machine == "virt":
            machine_arg = "virt,highmem=on"
        else:
            machine_arg = machine

        # Console log: используем первый UART платы (ttyAMA0 / PL011) и
        # направляем его в файл. Для g6sh это соответствует uart@1c090000.
        logs_dir = self._logs_dir
        logs_dir.mkdir(parents=True, exist_ok=True)
        console_log = logs_dir / "qemu_console.log"

        args: list[str] = [
            qemu_bin,
            "-M",
            machine_arg,
            "-cpu",
            "cortex-a57",
            "-smp",
            "4",
            "-m",
            "4096",
            "-serial",
            f"file:{console_log}",
        ]

        if cfg.qemu_dtb is not None:
            args += ["-dtb", str(cfg.qemu_dtb)]

        if boot is not None:
            args += ["-kernel", str(boot)]

        # Kernel cmdline: use ttyAMA0 as console and enable earlycon on the
        # PL011 at 0x1c090000, matching uart@1c090000 in g6sh-emu.dtb.
        cmdline = (
            "console=ttyAMA0,115200 "
            "earlycon=pl011,0x1c090000 "
            "androidboot.selinux=permissive "
            "androidboot.hardware=g6sh "
            "root=/dev/vda rootfstype=ext4 rw"
        )

        args += ["-append", cmdline]

        if system is not None:
            args += [
                "-drive",
                f"if=none,file={system},format=raw,id=system",
                "-device",
                "virtio-blk-pci,drive=system",
            ]

        if vendor is not None:
            args += [
                "-drive",
                f"if=none,file={vendor},format=raw,id=vendor",
                "-device",
                "virtio-blk-pci,drive=vendor",
            ]

        if product is not None:
            args += [
                "-drive",
                f"if=none,file={product},format=raw,id=product",
                "-device",
                "virtio-blk-pci,drive=product",
            ]

        # Optional: attach QNX images as additional (read‑only) virtual disks.
        # Это не «запускает» QNX само по себе (нужен отдельный загрузчик),
        # но делает образы доступными внутри машины, как в оригинальном плане.
        if cfg.qnx_enable:
            if qnx_system is not None:
                args += [
                    "-drive",
                    f"if=none,file={qnx_system},format=raw,read-only=on,id=qnx_system",
                    "-device",
                    "virtio-blk-pci,drive=qnx_system",
                ]
            if qnx_boot is not None:
                args += [
                    "-drive",
                    f"if=none,file={qnx_boot},format=raw,read-only=on,id=qnx_boot",
                    "-device",
                    "virtio-blk-pci,drive=qnx_boot",
                ]

        args += [
            "-device",
            "virtio-gpu-pci",
            "-netdev",
            # Пробрасываем ADB-порт гостя 5555 на хост-порт 5557, чтобы не
            # конфликтовать с возможными существующими сервисами на 5555.
            "user,id=net0,hostfwd=tcp::5557-:5555",
            "-device",
            "virtio-net-pci,netdev=net0",
            # HU display via VNC on 127.0.0.1:5900 (matches graphics.hu.vnc_*):
            # QEMU интерпретирует ":0" как TCP‑порт 5900.
            "-display",
            "vnc=127.0.0.1:0",
        ]

        return args

    def build_qemu_command(self) -> str:
        return " ".join(self.build_qemu_args())

    def build_qemu_args_with_qnx_uart(
        self,
        qnx_port: int = 1234,
        gps_port: int = 1235,
        bt_port: int = 1236,
    ) -> Sequence[str]:
        """Extended QEMU argv list with QNX UART sockets for the custom g6sh machine.

        This does *not* change the default emulator behaviour and is not yet
        used by the GUI. It provides a single, well-defined extension point
        for the future g6sh/QNX integration described in QEMU_UART_INTEGRATION.md:

        - ttyAMA0 (QNX console) -> chardev `qnx_uart` on localhost:qnx_port
        - ttySC1 (GPS)          -> chardev `gps_uart` on localhost:gps_port
        - ttySC6 (Bluetooth)    -> chardev `bt_uart` on localhost:bt_port

        The corresponding PL011 devices are created inside the custom QEMU
        machine implementation (hw/arm/g6sh.c) by looking up these chardev IDs.
        """

        base_args = list(self.build_qemu_args())
        base_args += [
            "-chardev",
            f"socket,id=qnx_uart,host=localhost,port={qnx_port},server,nowait",
            "-chardev",
            f"socket,id=gps_uart,host=localhost,port={gps_port},server,nowait",
            "-chardev",
            f"socket,id=bt_uart,host=localhost,port={bt_port},server,nowait",
        ]
        return base_args

    def start(self) -> None:
        """Start emulator process.

        Validates configuration, builds QEMU command, spawns a subprocess and
        records PID and command. If QEMU is not available, sets ERROR status
        with a descriptive message.
        """

        if self.runtime.status in {EmulatorStatus.STARTING, EmulatorStatus.RUNNING}:
            return

        self.runtime.status = EmulatorStatus.STARTING
        self.runtime.last_error = None
        self.runtime.last_qemu_command = None
        self.runtime.pid = None

        error = self._validate_config()
        if error is not None:
            self.runtime.status = EmulatorStatus.ERROR
            self.runtime.last_error = error
            self.log(f"CONFIG ERROR: {error}")
            return

        args = list(self.build_qemu_args())
        cmd_str = " ".join(args)
        self.runtime.last_qemu_command = cmd_str

        logs_dir = self._logs_dir
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "qemu_command.txt").write_text(cmd_str + "\n", encoding="utf-8")

        log_path = logs_dir / "qemu_stdout.log"

        try:
            log_file = log_path.open("ab", buffering=0)
        except OSError as exc:
            self.runtime.status = EmulatorStatus.ERROR
            self.runtime.last_error = f"Failed to open log file: {exc}"
            self.log(f"Failed to open QEMU log file: {exc}")
            return

        try:
            self._process = subprocess.Popen(
                args,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )
        except FileNotFoundError:
            self.runtime.status = EmulatorStatus.ERROR
            self.runtime.last_error = "qemu-system-aarch64 not found in PATH"
            self.log("Failed to start emulator: qemu-system-aarch64 not found in PATH")
            self._process = None
            log_file.close()
            return
        except OSError as exc:  # Generic spawn error
            self.runtime.status = EmulatorStatus.ERROR
            self.runtime.last_error = f"Failed to start QEMU: {exc}"
            self.log(f"Failed to start QEMU: {exc}")
            self._process = None
            log_file.close()
            return

        self.runtime.status = EmulatorStatus.RUNNING
        self.runtime.pid = self._process.pid
        self.log(f"Emulator QEMU started with PID {self.runtime.pid}")

        # Best-effort attach adb logger.
        self._start_adb_logger()

    def stop(self) -> None:
        """Stop emulator process (best-effort)."""

        if self.runtime.status not in {EmulatorStatus.RUNNING, EmulatorStatus.STARTING}:
            return

        self.runtime.status = EmulatorStatus.STOPPING
        self.log("Stopping emulator")

        if self._process is not None and self._process.poll() is None:
            try:
                self._process.terminate()
                try:
                    self._process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait(timeout=5)
            except OSError as exc:
                self.runtime.last_error = f"Failed to stop QEMU: {exc}"
                self.log(f"Failed to stop QEMU: {exc}")

        self._process = None
        self.runtime.status = EmulatorStatus.STOPPED
        self.runtime.pid = None
        self.log("Emulator stopped")

        # Stop adb logger as well.
        if self._adb_process is not None and self._adb_process.poll() is None:
            try:
                self._adb_process.terminate()
                try:
                    self._adb_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._adb_process.kill()
                    self._adb_process.wait(timeout=3)
            except OSError as exc:
                self.log(f"Failed to stop adb logcat: {exc}")
        self._adb_process = None

    def _start_adb_logger(self) -> None:
        """Best-effort start of adb logcat mirror into logs/adb_android.log.

        If adb is missing or device not available, we just log the issue and
        continue without failing the emulator.
        """

        if self._adb_process is not None and self._adb_process.poll() is None:
            # Already running.
            return

        adb_bin = shutil.which("adb")
        if adb_bin is None:
            self.log("ADB not found in PATH, skipping adb logcat capture")
            return

        logs_dir = self._logs_dir
        log_path = logs_dir / "adb_android.log"

        # Если ANDROID_ADB_SERIAL не задан, сначала пробуем подключиться к эмулятору.
        serial = os.environ.get("ANDROID_ADB_SERIAL")
        if not serial:
            # Best-effort подключение к эмулятору на порту 5557.
            try:
                subprocess.run(
                    [adb_bin, "connect", "127.0.0.1:5557"],
                    timeout=5,
                    capture_output=True,
                )
            except (subprocess.TimeoutExpired, OSError):
                # Игнорируем ошибки подключения - возможно, устройство ещё не готово.
                pass
            serial = "127.0.0.1:5557"

        args = [adb_bin]
        if serial:
            args += ["-s", serial]
        args += ["logcat", "-v", "brief"]

        try:
            log_file = log_path.open("ab", buffering=0)
        except OSError as exc:
            self.log(f"Failed to open adb log file: {exc}")
            return

        try:
            self._adb_process = subprocess.Popen(
                args,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )
            self.log("Started adb logcat capture")
        except FileNotFoundError:
            self.log("adb binary disappeared while starting logcat")
            self._adb_process = None
            log_file.close()
        except OSError as exc:
            self.log(f"Failed to start adb logcat: {exc}")
            self._adb_process = None
            log_file.close()

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.runtime.status.value,
            "last_error": self.runtime.last_error,
            "last_qemu_command": self.runtime.last_qemu_command,
            "pid": self.runtime.pid,
            "android_ota": str(self.config.android_ota) if self.config.android_ota else None,
            "qnx_ota": str(self.config.qnx_ota) if self.config.qnx_ota else None,
        }

    # ----- Configuration API helpers -----

    def config_for_api(self) -> dict[str, object]:
        """Return config in a form convenient for JSON API."""

        def _rel(p: Optional[Path]) -> Optional[str]:
            if p is None:
                return None
            try:
                return str(p.relative_to(self.repo_root))
            except ValueError:
                return str(p)

        return {
            "android": {
                "boot_img": _rel(self.config.android_boot_img),
                "system_img": _rel(self.config.android_system_img),
                "vendor_img": _rel(self.config.android_vendor_img),
                "product_img": _rel(self.config.android_product_img),
            },
            "qnx": {
                "qnx_boot_img": _rel(self.config.qnx_boot_img),
                "qnx_system_img": _rel(self.config.qnx_system_img),
            },
        }

    def save_config_from_api(self, android: dict[str, Optional[str]] | None) -> None:
        """Update emulator_config.yaml from partial API payload and reload config."""

        # Load existing raw YAML if present.
        raw: dict[str, object] = {}
        if self._cfg_path.exists():
            raw = yaml.safe_load(self._cfg_path.read_text(encoding="utf-8")) or {}

        android_raw = raw.get("android", {}) or {}
        if android is not None:
            for key in ("boot_img", "system_img", "vendor_img", "product_img"):
                if key in android and android[key] is not None:
                    android_raw[key] = android[key]
        raw["android"] = android_raw

        # Persist YAML (keep keys order for readability).
        self._cfg_path.write_text(
            yaml.safe_dump(raw, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

        # Reload config used by the manager.
        self.config = EmulatorConfig.load_default(self.repo_root)


emulator_manager = EmulatorManager()
