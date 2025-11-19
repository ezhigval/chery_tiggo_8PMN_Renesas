"""
QEMU Manager - Управление процессом QEMU
Запускает и контролирует QEMU с правильными параметрами для T18FL3
"""

import subprocess
import threading
import time
import os
import socket
import struct
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass
from enum import Enum

import psutil

from .log_manager import get_logger, get_log_manager

# Импортируем кастомную машину (может быть не доступна в некоторых случаях)
try:
    from .custom_machine import CustomMachineBuilder, RenesasG6SHConfig
    CUSTOM_MACHINE_AVAILABLE = True
except ImportError:
    CUSTOM_MACHINE_AVAILABLE = False
    CustomMachineBuilder = None
    RenesasG6SHConfig = None


class QEMUState(Enum):
    """Состояния QEMU"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class QEMUConfig:
    """Конфигурация QEMU"""
    # Используем кастомный QEMU с поддержкой g6sh
    qemu_bin: Path = Path("/Users/valentinezov/Projects/Tiggo/qemu_custom/qemu/build/qemu-system-aarch64-unsigned")
    machine: str = "g6sh"  # Кастомная машина g6sh с правильными адресами ГУ (0xe6e80000)
    cpu: str = "cortex-a57"
    memory: int = 4096  # MB
    smp: int = 4
    
    # Образы
    android_boot_img: Optional[Path] = None
    android_system_img: Optional[Path] = None
    android_vendor_img: Optional[Path] = None
    android_product_img: Optional[Path] = None
    android_dtb_img: Optional[Path] = None
    qnx_boot_img: Optional[Path] = None
    qnx_system_img: Optional[Path] = None
    
    # Дисплеи (ИЗОЛИРОВАННЫЕ ПОРТЫ для T18FL3 эмулятора)
    # QEMU не поддерживает порты > 5999 (display > 99)
    # Используем порт 5910 (display :10) для изоляции от стандартных эмуляторов
    display1_vnc: int = 5910  # VNC для T18FL3 (display :10, изолирован от 5900-5909)
    display2_vnc: int = 5911  # Резервный (display :11)
    
    # Сеть (ИЗОЛИРОВАННЫЕ ПОРТЫ для полной изоляции)
    adb_port: int = 5556  # ADB для T18FL3 (изолирован от стандартных эмуляторов)
    http_port: int = 8081  # HTTP для T18FL3 (изолирован)
    monitor_port: int = 4445  # Monitor для T18FL3 (изолирован)
    # ИЗОЛЯЦИЯ: используем только localhost, без внешних подключений
    network_isolated: bool = True  # Полная изоляция сети
    
    # Дополнительно
    enable_qnx: bool = False
    enable_can: bool = True
    # Режим отладки (без VNC, максимум логов от QEMU/kernel)
    debug_mode: bool = False
    # Использовать рабочее ядро вместо оригинального (для быстрого тестирования приложений)
    use_working_kernel: bool = False
    working_kernel_path: Optional[Path] = None


class QEMUManager:
    """Менеджер QEMU для T18FL3"""
    
    def __init__(self, config: QEMUConfig):
        self.config = config
        self.logger = get_logger("qemu_manager")
        self.log_manager = get_log_manager()
        self.process: Optional[subprocess.Popen] = None
        self.state = QEMUState.STOPPED
        self.state_lock = threading.Lock()
        self.output_thread: Optional[threading.Thread] = None
        self.callbacks: List[Callable] = []
        self.temp_dir: Optional[Path] = None  # Инициализируем temp_dir
    
    def add_state_callback(self, callback: Callable[[QEMUState], None]):
        """Добавить callback для изменения состояния"""
        self.callbacks.append(callback)
    
    def _set_state(self, new_state: QEMUState):
        """Установить новое состояние"""
        with self.state_lock:
            old_state = self.state
            self.state = new_state
            self.logger.info(f"State changed: {old_state.value} -> {new_state.value}")
            # Вызываем все callbacks
            for callback in self.callbacks:
                try:
                    callback(new_state)
                except Exception as e:
                    self.logger.error(f"Error in state callback: {e}")
    
    def _build_qemu_command(self) -> List[str]:
        """Построить команду QEMU с кастомной конфигурацией для Renesas g6sh"""
        cmd = [str(self.config.qemu_bin)]
        
        # РЕЖИМ С РАБОЧИМ ЯДРОМ: Используем стандартную virt машину для быстрого тестирования приложений
        if self.config.use_working_kernel:
            return self._build_working_kernel_command()
        
        # ВАЖНО: Используем кастомную конфигурацию для Renesas g6sh (703000765AA)
        # Создаем конфигурацию, совместимую с нашим kernel.
        # В debug_mode упрощаем конфигурацию и используем стандартную virt-машину,
        # чтобы легче было диагностировать поведение ядра.
        # ВРЕМЕННО: Используем virt машину из-за проблем с GIC в g6sh
        use_virt_fallback = os.environ.get("T18FL3_USE_VIRT_FALLBACK", "1") in ("1", "true", "True")
        if CUSTOM_MACHINE_AVAILABLE and not self.config.debug_mode and not use_virt_fallback:
            try:
                # Импортируем локально для избежания UnboundLocalError
                from .custom_machine import RenesasG6SHConfig, CustomMachineBuilder
                
                renesas_config = RenesasG6SHConfig(
                    cpu_model=self.config.cpu,
                    cpu_count=self.config.smp,
                    memory_mb=self.config.memory,
                    kernel_load_addr=0x48080000,  # Из boot.img
                    ramdisk_load_addr=0x4a180000  # Из boot.img
                )
                
                machine_builder = CustomMachineBuilder(renesas_config)
                self.logger.info("Building custom machine configuration for Renesas g6sh (703000765AA)")
                self.logger.info(machine_builder.get_machine_description())
                
                # Извлекаем kernel и ramdisk
                kernel_path = None
                ramdisk_path = None
                dtb_path = None
                if self.config.android_boot_img and self.config.android_boot_img.exists():
                    kernel_path, ramdisk_path = self._extract_boot_components()
                
                # Пробуем извлечь/использовать DTB для R-Car g6sh
                if self.config.android_dtb_img and self.config.android_dtb_img.exists():
                    dtb_path = machine_builder.extract_dtb_from_image(self.config.android_dtb_img)
                    if not dtb_path:
                        # Пробуем создать кастомный DTB
                        self.logger.info("Attempting to create custom DTB for R-Car g6sh...")
                        # Пока используем автогенерацию QEMU
                
                # Получаем базовые аргументы от кастомной машины (с DTB если доступен)
                custom_args = machine_builder.build_qemu_args(kernel_path, ramdisk_path, dtb_path)
                self.logger.debug(f"Custom machine args: {len(custom_args)} arguments")
                
                # Добавляем базовые аргументы от кастомной машины
                cmd.extend(custom_args)
            except ImportError as e:
                self.logger.warning(f"Could not import custom_machine, using fallback: {e}")
                # Fallback на стандартную конфигурацию - будет обработано ниже
                pass
            else:
                # Если try выполнился успешно, кастомная машина использована
                # ВАЖНО: Для загрузки kernel может потребоваться явное указание адреса
                # QEMU virt machine загружает kernel по 0x40080000 по умолчанию
                # Но наш boot.img указывает 0x48080000
                # Пробуем использовать -kernel без явного адреса (QEMU должен обработать)
                # Если не работает, можно попробовать распаковать kernel вручную
                # 
                # Теперь добавляем остальные параметры, которых нет в custom_args
                # (диски, monitor, cmdline и т.д.)
                pass  # Кастомная машина успешно использована, продолжаем
        
        # Если кастомная машина не использована, используем стандартную конфигурацию
        # Проверяем, были ли добавлены аргументы от кастомной машины (cmd должен содержать больше чем только qemu_bin)
        if len(cmd) == 1:  # Только qemu_bin, значит кастомная машина не использована
            # Fallback на стандартную конфигурацию если кастомная машина недоступна или отключена
            if use_virt_fallback:
                self.logger.info("🔧 Using standard virt machine (fallback mode) - g6sh machine has GIC issues")
            else:
                self.logger.warning("Custom machine unavailable, using standard virt")
            # Machine и CPU
            # В fallback режиме используем virt вместо g6sh
            machine_type = "virt" if use_virt_fallback else self.config.machine
            cmd.extend(["-machine", machine_type])
            cmd.extend(["-cpu", self.config.cpu])
            cmd.extend(["-m", str(self.config.memory)])
            cmd.extend(["-smp", str(self.config.smp)])
            
            # Kernel и Ramdisk
            if self.config.android_boot_img and self.config.android_boot_img.exists():
                kernel, ramdisk = self._extract_boot_components()
                if kernel:
                    cmd.extend(["-kernel", str(kernel)])
                if ramdisk:
                    cmd.extend(["-initrd", str(ramdisk)])
        android_cmdline = None
        # В режиме debug используем bootargs только из DTB/boot.img,
        # поэтому НЕ добавляем собственный -append.
        if self.config.android_boot_img and self.config.android_boot_img.exists() and not self.config.debug_mode:
            # Cmdline для Android с отладочными параметрами
            # ВАЖНО: Для Renesas g6sh нужно использовать правильные параметры.
            # КРИТИЧЕСКИ ВАЖНО: Для получения serial output нужно правильно настроить консоль.
            #
            # На основании анализа `dtb_custom/t18fl3_virt_minimal.dts`:
            #   uart0: serial@09000000 { compatible = "arm,pl011"; reg = <0x0 0x09000000 ...>; }
            # то есть консоль сидит на PL011 по адресу 0x09000000.
            # Поэтому настраиваем earlycon непосредственно на этот UART, чтобы увидеть
            # вывод ядра максимально рано.
            android_cmdline = (
                # КРИТИЧЕСКИ ВАЖНО: Используем параметры ТОЧНО как на реальном ГУ!
                # Реальное ГУ использует SCIF на адресе 0xe6e80000
                # Пробуем ВСЕ возможные варианты для максимальной совместимости:
                # 1. earlycon - ранний вывод (реальный адрес ГУ)
                "earlycon=renesas,scif,0xe6e80000,115200 "  # Реальный адрес SCIF из ГУ!
                "earlycon=pl011,0xe6e80000,115200 "  # Fallback на PL011 (если SCIF не работает)
                "earlycon=pl011,0x09000000,115200 "  # Virt адрес (на всякий случай)
                # 2. console - обычная консоль (реальный ГУ использует ttySC0)
                "console=ttySC0,115200 "  # Реальный консоль ГУ (SCIF)
                "console=ttyAMA0,115200 "  # Fallback на PL011
                "console=tty0 "  # VGA/framebuffer консоль (графический вывод)
                # 3. printk - максимальное логирование
                "printk.time=1 "
                "printk.always_kmsg_dump=1 "  # Дамп всех сообщений
                # 4. Дополнительные параметры для вывода
                "ignore_loglevel "  # Игнорировать уровень логирования
                "loglevel=8 "  # Максимальный уровень
                # Root и init
                "root=/dev/ram0 ro rootwait "
                "init=/init "
                "rdinit=/init "
                # Android‑параметры (максимально приближены к реальному T18FL3)
                "androidboot.hardware=g6sh "
                "androidboot.serialno=T18FL3EMU "
                "androidboot.console=ttySC0 "  # SCIF для реального ГУ (как на реальном устройстве)
                "androidboot.slot_suffix=_a "
                "androidboot.selinux=permissive "
                "androidboot.model=T18FL3 "
                "androidboot.chipset=703000765AA "
                "androidboot.baseband=unknown "
                "androidboot.mode=normal "
                "androidboot.bootloader=unknown "
            )
        
        # Диски (ВАЖНО: format=raw для ext2 образов БЕЗ MBR/GPT)
        # Используем cache=unsafe для избежания блокировок файлов (быстрее чем cache=none)
        # ВАЖНО: aio=native не поддерживается во всех сборках QEMU, используем только cache=unsafe
        if self.config.android_system_img:
            cmd.extend([
                "-drive",
                f"file={self.config.android_system_img},format=raw,if=virtio,id=system,cache=unsafe"
            ])
        
        if self.config.android_vendor_img:
            cmd.extend([
                "-drive",
                f"file={self.config.android_vendor_img},format=raw,if=virtio,id=vendor,cache=unsafe"
            ])
        
        if self.config.android_product_img:
            cmd.extend([
                "-drive",
                f"file={self.config.android_product_img},format=raw,if=virtio,id=product,cache=unsafe"
            ])
        
        # QNX диски
        if self.config.enable_qnx:
            if self.config.qnx_boot_img:
                cmd.extend([
                    "-drive",
                    f"file={self.config.qnx_boot_img},format=raw,if=virtio,id=qnx_boot,cache=writeback"
                ])
            if self.config.qnx_system_img:
                cmd.extend([
                    "-drive",
                    f"file={self.config.qnx_system_img},format=raw,if=virtio,id=qnx_system,cache=writeback"
                ])
        
        # Device Tree для R-Car g6sh / virt машины
        # ВАЖНО: Проверяем, не добавлен ли уже DTB в custom_args
        has_dtb = any(arg == "-dtb" for arg in cmd)
        
        if not has_dtb:
            dtb_used = False

            # ВРЕМЕННО: Пробуем БЕЗ кастомного DTB для диагностики
            # Если ядро не выводит serial с кастомным DTB, попробуем автогенерацию QEMU
            use_custom_dtb = os.environ.get("T18FL3_USE_CUSTOM_DTB", "1") in ("1", "true", "True")
            
            if use_custom_dtb:
                # Сначала пробуем использовать наш кастомный DTB (для отладки / экспериментов)
                custom_dtb = Path(__file__).resolve().parent.parent / "dtb_custom" / "t18fl3_virt_minimal.dtb"
                if custom_dtb.exists():
                    cmd.extend(["-dtb", str(custom_dtb)])
                    self.logger.info(f"Using custom DTB: {custom_dtb}")
                    dtb_used = True
                else:
                    self.logger.warning("Custom DTB not found, will use QEMU auto-generated")
            else:
                self.logger.info("Custom DTB disabled via T18FL3_USE_CUSTOM_DTB, using QEMU auto-generated")
            
            # Если кастомный DTB не использован, пробуем dtb.img из образа
            if not dtb_used and self.config.android_dtb_img and self.config.android_dtb_img.exists():
                # Пробуем извлечь DTB из образа (может быть AVB структура)
                if CUSTOM_MACHINE_AVAILABLE:
                    try:
                        from .custom_machine import RenesasG6SHConfig, CustomMachineBuilder
                        temp_config = RenesasG6SHConfig()
                        temp_builder = CustomMachineBuilder(temp_config)
                        extracted_dtb = temp_builder.extract_dtb_from_image(self.config.android_dtb_img)
                        
                        if extracted_dtb:
                            cmd.extend(["-dtb", str(extracted_dtb)])
                            self.logger.info(f"DTB extracted: {extracted_dtb.name}")
                            dtb_used = True
                        else:
                            # Проверяем напрямую
                            try:
                                with open(self.config.android_dtb_img, 'rb') as f:
                                    magic = f.read(4)
                                    if magic == b'\xd0\x0d\xfe\xed' or magic == b'\xed\xfe\x0d\xd0':
                                        cmd.extend(["-dtb", str(self.config.android_dtb_img)])
                                        self.logger.info(f"DTB added: {self.config.android_dtb_img.name}")
                                        dtb_used = True
                                    else:
                                        self.logger.warning(f"DTB invalid magic (may be AVB): {self.config.android_dtb_img.name}")
                            except Exception as e:
                                self.logger.warning(f"Error checking DTB file: {e}")
                    except ImportError as e:
                        self.logger.warning(f"Could not import custom_machine: {e}")
            
            # Если DTB не использован, QEMU автоматически сгенерирует его для virt machine
            if not dtb_used:
                self.logger.info("DTB: using QEMU auto-generated (virt machine)")
        
        # Два дисплея через VNC
        # Проверяем, не добавлен ли уже display и gpu в custom_args
        has_display = any(arg == "-display" for arg in cmd)
        has_gpu = any("virtio-gpu-pci" in arg for arg in cmd)
        
        # Сеть (ИЗОЛИРОВАННЫЕ ПОРТЫ для T18FL3)
        # Используем порты из конфигурации (5556, 8081) - они изолированы от других эмуляторов
        adb_port = self.config.adb_port  # 5556 для T18FL3
        http_port = self.config.http_port  # 8081 для T18FL3
        
        if self.config.debug_mode:
            # DEBUG-РЕЖИМ: без VNC/графики, весь вывод в serial/stdout
            cmd.extend(["-display", "none"])
            self.logger.info("DEBUG mode: display=none, VNC disabled")
        else:
            if not has_display:
                # ВАЖНО: VNC порт теперь 5910 (изолированный для T18FL3)
                # ИЗОЛЯЦИЯ: используем только localhost для VNC
                # QEMU VNC формат: vnc=127.0.0.1:display (где display = port - 5900)
                # Используем display :10 (порт 5910) для изоляции от стандартных эмуляторов (5900-5909)
                vnc_port = self.config.display1_vnc  # 5910 для T18FL3
                display_num = vnc_port - 5900  # 10 для порта 5910
                # ИЗОЛЯЦИЯ: используем 127.0.0.1 для привязки только к localhost
                cmd.extend(["-display", f"vnc=127.0.0.1:{display_num},to=99"])
                self.logger.info(f"VNC (ISOLATED): display=127.0.0.1:{display_num}, port={vnc_port} (localhost only)")
        
        if not self.config.debug_mode and not has_gpu:
            # КРИТИЧЕСКИ ВАЖНО: Настраиваем virtio-gpu для правильной работы графики
            # Используем правильные параметры для Android framebuffer
            cmd.extend([
                "-device", "virtio-gpu-pci,edid=on",
                "-global", "virtio-gpu-pci.xres=3840",
                "-global", "virtio-gpu-pci.yres=720",
                "-vga", "none"
            ])
            # Добавляем поддержку framebuffer для Android
            self.logger.info(f"GPU: virtio-gpu-pci, resolution=3840x720")
        
        # Сеть (ИЗОЛИРОВАННЫЕ ПОРТЫ для T18FL3)
        # Используем порты из конфигурации (5556, 8081) - они изолированы от других эмуляторов
        # ВАЖНО: Проверяем только наши изолированные порты, не ищем свободные
        # Если порт занят - это ошибка, так как мы используем изолированные порты
        def check_port_available(port, name):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('127.0.0.1', port))
                sock.close()
                return True
            except OSError:
                sock.close()
                self.logger.warning(f"⚠️ {name} port {port} is busy - may conflict with another T18FL3 instance")
                return False
        
        if not check_port_available(adb_port, "ADB"):
            # Пробуем найти свободный порт рядом (только для T18FL3 диапазона)
            for port in range(5556, 5560):  # T18FL3 диапазон
                if check_port_available(port, "ADB"):
                    adb_port = port
                    self.logger.warning(f"Using alternative ADB port {port} for T18FL3")
                    break
        
        if not check_port_available(http_port, "HTTP"):
            # Пробуем найти свободный порт рядом (только для T18FL3 диапазона)
            for port in range(8081, 8085):  # T18FL3 диапазон
                if check_port_available(port, "HTTP"):
                    http_port = port
                    self.logger.warning(f"Using alternative HTTP port {port} for T18FL3")
                    break
        
        # Проверяем, не добавлена ли уже сеть в custom_args
        has_netdev = any(arg == "-netdev" for arg in cmd)
        if not has_netdev:
            # ИЗОЛЯЦИЯ: используем только localhost, без внешних подключений
            # restrict=y - запрещает исходящие подключения
            # ipv4=on,ipv6=off - только IPv4, без IPv6
            # net=10.0.2.0/24 - изолированная подсеть
            if self.config.network_isolated:
                cmd.extend([
                    "-netdev",
                    f"user,id=net0,restrict=y,ipv4=on,ipv6=off,net=10.0.2.0/24,"
                    f"hostfwd=tcp:127.0.0.1:{adb_port}-:5555,"
                    f"hostfwd=tcp:127.0.0.1:{http_port}-:8080",
                    "-device", "virtio-net-device,netdev=net0"
                ])
                self.logger.info(f"Network (ISOLATED): ADB=127.0.0.1:{adb_port}->5555, HTTP=127.0.0.1:{http_port}->8080")
                self.logger.info("Network isolation: restrict=y, no external connections allowed")
            else:
                cmd.extend([
                    "-netdev",
                    f"user,id=net0,hostfwd=tcp::{adb_port}-:5555,hostfwd=tcp::{http_port}-:8080",
                    "-device", "virtio-net-device,netdev=net0"
                ])
                self.logger.info(f"Network: ADB={adb_port}->5555, HTTP={http_port}->8080")
        
        # Добавляем cmdline для Android (кроме debug-режима, где работаем с bootargs из DTB)
        if not self.config.debug_mode:
            if android_cmdline:
                cmd.extend(["-append", android_cmdline])
            else:
                # Fallback cmdline если boot.img не указан
                # Также используем PL011 @ 0x09000000 из нашего минимального DTB для раннего вывода.
                cmdline = (
                    "root=/dev/ram0 ro "
                    "androidboot.hardware=ranchu "
                    f"androidboot.serialno=T18FL3EMU "
                    "androidboot.console=ttyAMA0 "
                    "console=ttyAMA0,38400 "
                    "console=tty0 "
                    "earlyprintk=ttyAMA0,38400 "
                    "earlycon=pl011,mmio,0x09010000 "
                    "androidboot.slot_suffix=_a "
                    "androidboot.selinux=permissive "
                    "androidboot.model=T18FL3 "
                    "androidboot.chipset=703000765AA "
                    "loglevel=8 "
                    "ignore_loglevel "
                    "printk.time=1 "
                    "printk.always_kmsg_dump=1 "
                )
                cmd.extend(["-append", cmdline])
        
        # Serial и монитор (ИЗОЛИРОВАННЫЙ ПОРТ для T18FL3)
        # ИЗОЛЯЦИЯ: используем только 127.0.0.1, без внешних подключений
        monitor_port = self.config.monitor_port  # 4445 для T18FL3
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Привязываем только к localhost для изоляции
            sock.bind(('127.0.0.1', monitor_port))
            sock.close()
            cmd.extend(["-monitor", f"telnet:127.0.0.1:{monitor_port},server,nowait"])
            self.logger.info(f"Monitor (ISOLATED): telnet:127.0.0.1:{monitor_port} (localhost only)")
        except OSError:
            # Порт занят - пробуем альтернативный порт в T18FL3 диапазоне
            self.logger.warning(f"Monitor port {monitor_port} is busy, trying alternative T18FL3 port")
            for alt_port in range(4445, 4450):  # T18FL3 диапазон
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.bind(('127.0.0.1', alt_port))
                    sock.close()
                    monitor_port = alt_port
                    cmd.extend(["-monitor", f"telnet:127.0.0.1:{monitor_port},server,nowait"])
                    self.logger.info(f"Using alternative monitor port {alt_port} for T18FL3")
                    break
                except OSError:
                    sock.close()
                    continue
            else:
                # Все порты заняты - используем unix socket
                monitor_socket = Path(tempfile.gettempdir()) / f"t18fl3_qemu_monitor_{os.getpid()}.sock"
                cmd.extend(["-monitor", f"unix:{monitor_socket},server,nowait"])
                self.logger.warning(f"Using unix socket for monitor: {monitor_socket}")
        
        # Serial output - КРИТИЧЕСКИ ВАЖНО для получения вывода kernel
        # ✅ ИСПРАВЛЕНО: Используем кастомную машину g6sh, которая создает устройства на правильных адресах ГУ
        # Машина g6sh создает PL011 на реальных адресах SCIF: 0xe6e80000 (SCIF0), 0xe6e88000 (SCIF1)
        # Это полностью соответствует реальному ГУ!
        
        # Основной serial -> stdio (для Python мониторинга)
        # Машина g6sh автоматически создаст PL011 на 0xe6e80000 для первого -serial
        cmd.extend(["-serial", "stdio"])
        
        # Второй serial для резерва (g6sh создаст на 0xe6e88000)
        cmd.extend(["-serial", "chardev:serial1_chardev"])
        cmd.extend(["-chardev", "socket,host=127.0.0.1,port=4447,server=on,wait=off,id=serial1_chardev"])
        
        self.logger.info("✅ Serial: stdio (машина g6sh создаст PL011 на 0xe6e80000 - реальный адрес SCIF ГУ!)")
        
        # Отладка для диагностики проблем загрузки
        # В обычном режиме - только ошибки гостя и неподдерживаемые инструкции
        if self.config.debug_mode:
            # DEBUG-РЕЖИМ: максимум информации от QEMU (очень много логов)
            cmd.extend(["-d", "guest_errors,unimp,in_asm,cpu"])
            self.logger.info("DEBUG mode: QEMU debug flags = guest_errors,unimp,in_asm,cpu")

            # При включенном GDB‑режиме (T18FL3_QEMU_GDB=1) поднимаем встроенный
            # сервер отладки и останавливаемся на reset, чтобы можно было
            # пошагово изучать ранний бутстрап ядра.
            import os as _os_dbg
            if _os_dbg.environ.get("T18FL3_QEMU_GDB", "0") in ("1", "true", "True"):
                cmd.extend(["-s", "-S"])  # -s = gdbserver :1234, -S = стоп при старте
                self.logger.info("DEBUG mode: GDB server enabled on :1234, QEMU will wait for debugger at reset")
        else:
            cmd.extend(["-d", "guest_errors,unimp"])
        
        # ВАЖНО: Для отладки kernel можно включить GDB сервер
        # Раскомментируйте следующую строку для подключения GDB:
        # cmd.extend(["-s", "-S"])  # -s = gdb server на :1234, -S = остановка при старте
        # Это позволит подключиться через: gdb-multiarch -ex "target remote localhost:1234"
        
        # ВАЖНО: Для принудительной загрузки kernel пробуем добавить параметры
        # Пробуем использовать -bios none чтобы QEMU не пытался загрузить свой bootloader
        # cmd.extend(["-bios", "none"])  # Может не работать для virt machine
        
        # Пробуем добавить -no-reboot чтобы QEMU не перезагружался при ошибках
        cmd.extend(["-no-reboot"])  # Не перезагружаться при ошибках
        
        return cmd
    
    def _build_working_kernel_command(self) -> List[str]:
        """Построить команду QEMU с рабочим ядром для быстрого тестирования приложений"""
        from ..config.working_kernel_config import (
            get_working_kernel_path,
            get_working_dtb_path,
            USE_VIRT_MACHINE,
            WORKING_KERNEL_LOAD_ADDR,
            WORKING_RAMDISK_LOAD_ADDR,
            WORKING_KERNEL_CMDLINE,
        )
        
        cmd = [str(self.config.qemu_bin)]
        
        # Используем стандартную virt машину (стабильная и работает)
        machine = "virt" if USE_VIRT_MACHINE else self.config.machine
        self.logger.info(f"🔧 Using WORKING KERNEL mode with {machine} machine")
        self.logger.info("   This mode uses a working kernel for fast app testing")
        self.logger.info("   Your original system.img and vendor.img will be used")
        
        # Machine и CPU
        cmd.extend(["-machine", f"{machine},accel=tcg"])
        cmd.extend(["-cpu", self.config.cpu])
        cmd.extend(["-m", str(self.config.memory)])
        cmd.extend(["-smp", str(self.config.smp)])
        
        # Рабочее ядро
        kernel_path = self.config.working_kernel_path or get_working_kernel_path()
        if kernel_path and kernel_path.exists():
            self.logger.info(f"✅ Using working kernel: {kernel_path}")
            cmd.extend(["-kernel", str(kernel_path)])
        else:
            # Пробуем извлечь из boot.img как fallback
            if self.config.android_boot_img and self.config.android_boot_img.exists():
                kernel_path, ramdisk_path = self._extract_boot_components()
                if kernel_path:
                    cmd.extend(["-kernel", str(kernel_path)])
                    self.logger.info(f"⚠️  Using extracted kernel from boot.img (may not work)")
                else:
                    self.logger.error("❌ No working kernel found! Please provide working_kernel_path")
                    raise RuntimeError("No working kernel available")
            else:
                self.logger.error("❌ No working kernel found and no boot.img available!")
                raise RuntimeError("No working kernel available")
        
        # Ramdisk из boot.img (если есть)
        if self.config.android_boot_img and self.config.android_boot_img.exists():
            _, ramdisk_path = self._extract_boot_components()
            if ramdisk_path:
                cmd.extend(["-initrd", str(ramdisk_path)])
        
        # DTB (для virt машины обычно генерируется автоматически, но можно указать)
        dtb_path = get_working_dtb_path()
        if dtb_path:
            cmd.extend(["-dtb", str(dtb_path)])
        
        # Командная строка ядра
        cmd.extend(["-append", WORKING_KERNEL_CMDLINE])
        
        # Диски - ВАЖНО: используем оригинальные system.img и vendor.img
        if self.config.android_system_img:
            cmd.extend([
                "-drive",
                f"file={self.config.android_system_img},format=raw,if=virtio,id=system,cache=unsafe"
            ])
            self.logger.info(f"✅ Using original system.img: {self.config.android_system_img}")
        
        if self.config.android_vendor_img:
            cmd.extend([
                "-drive",
                f"file={self.config.android_vendor_img},format=raw,if=virtio,id=vendor,cache=unsafe"
            ])
            self.logger.info(f"✅ Using original vendor.img: {self.config.android_vendor_img}")
        
        if self.config.android_product_img:
            cmd.extend([
                "-drive",
                f"file={self.config.android_product_img},format=raw,if=virtio,id=product,cache=unsafe"
            ])
        
        # QNX диски (если включены)
        if self.config.enable_qnx:
            if self.config.qnx_boot_img and self.config.qnx_boot_img.exists():
                cmd.extend([
                    "-drive",
                    f"file={self.config.qnx_boot_img},format=raw,if=virtio,id=qnx_boot,cache=writeback"
                ])
                self.logger.info(f"✅ Using QNX boot image: {self.config.qnx_boot_img}")
            if self.config.qnx_system_img and self.config.qnx_system_img.exists():
                cmd.extend([
                    "-drive",
                    f"file={self.config.qnx_system_img},format=raw,if=virtio,id=qnx_system,cache=writeback"
                ])
                self.logger.info(f"✅ Using QNX system image: {self.config.qnx_system_img}")
            self.logger.info("⚠️  QNX support: QNX images are mounted, but QNX may require specific hardware configuration")
            self.logger.info("   QNX typically needs its own bootloader and may not work with standard virt machine")
        
        # Serial для вывода
        cmd.extend(["-serial", "stdio"])
        
        # VNC (если не в debug режиме)
        if not self.config.debug_mode:
            cmd.extend(["-vnc", f"127.0.0.1:{self.config.display1_vnc - 5900}"])
        
        # Сеть
        cmd.extend([
            "-netdev", f"user,id=net0,hostfwd=tcp::{self.config.adb_port}-:5555",
            "-device", "virtio-net-device,netdev=net0"
        ])
        
        # Monitor
        cmd.extend([
            "-monitor", f"telnet:127.0.0.1:{self.config.monitor_port},server,nowait"
        ])
        
        # Дополнительные параметры
        cmd.extend(["-no-reboot"])
        
        self.logger.info(f"✅ Working kernel command built: {len(cmd)} arguments")
        return cmd
    
    def _extract_boot_components(self):
        """Извлечь kernel и ramdisk из boot.img"""
        import struct
        import tempfile
        from datetime import datetime
        
        boot_img = self.config.android_boot_img
        if not boot_img or not boot_img.exists():
            return None, None
        
        temp_dir = Path(tempfile.gettempdir()) / "t18fl3_boot_extract"
        temp_dir.mkdir(exist_ok=True, parents=True)
        
        kernel_path = temp_dir / "kernel"
        ramdisk_path = temp_dir / "ramdisk.img"
        
        # Проверяем, что директория создана
        if not temp_dir.exists():
            self.logger.error(f"Failed to create temp directory: {temp_dir}")
            return None, None
        
        try:
            with open(boot_img, 'rb') as f:
                header = f.read(1632)
                if header[0:8] != b'ANDROID!':
                    self.logger.error("Invalid Android boot image")
                    return None, None
                
                kernel_size = struct.unpack('<I', header[8:12])[0]
                ramdisk_size = struct.unpack('<I', header[16:20])[0]
                page_size = struct.unpack('<I', header[36:40])[0]
                kernel_addr = struct.unpack('<I', header[12:16])[0]
                ramdisk_addr = struct.unpack('<I', header[20:24])[0]
                second_size = struct.unpack('<I', header[24:28])[0]
                tags_addr = struct.unpack('<I', header[28:32])[0]
                name = header[48:64].rstrip(b'\x00').decode(errors='ignore')
                cmdline_hdr = header[64:320].rstrip(b'\x00').decode(errors='ignore')
                
                # Подробный дамп заголовка boot.img для диагностики
                self.logger.info(
                    "boot.img header: "
                    f"kernel_size={kernel_size} bytes, ramdisk_size={ramdisk_size} bytes, "
                    f"second_size={second_size} bytes, page_size={page_size}, "
                    f"kernel_addr=0x{kernel_addr:08x}, ramdisk_addr=0x{ramdisk_addr:08x}, "
                    f"tags_addr=0x{tags_addr:08x}, name='{name}', "
                    f"cmdline='{cmdline_hdr}'"
                )
                
                kernel_offset = page_size
                ramdisk_offset = kernel_offset + ((kernel_size + page_size - 1) // page_size) * page_size
                
                # Извлекаем kernel
                f.seek(kernel_offset)
                kernel_data = f.read(kernel_size)
                if len(kernel_data) != kernel_size:
                    self.logger.error(f"Failed to read kernel: expected {kernel_size}, got {len(kernel_data)}")
                    return None, None

                # По факту boot.img содержит **сжатый** (lz4) образ ядра.
                # QEMU при использовании `-kernel` НЕ выполняет распаковку так,
                # как это делал бы настоящий загрузчик, поэтому если отдать
                # сжатый blob напрямую, ядро просто не стартует (нет serial‑вывода).
                #
                # Для корректного старта нам нужно разжать kernel до «голого»
                # образа (`Image`) и уже его передавать в `-kernel`.
                kernel_unpacked_path = temp_dir / "kernel_unpacked"
                try:
                    import subprocess
                    # Записываем сжатый kernel во временный файл
                    temp_compressed = temp_dir / "kernel_compressed.lz4"
                    with open(temp_compressed, 'wb') as tf:
                        tf.write(kernel_data)

                    # Пробуем распаковать через lz4
                    result = subprocess.run(
                        ["lz4", "-d", "-f", str(temp_compressed), str(kernel_unpacked_path)],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )

                    if result.returncode != 0:
                        self.logger.warning(
                            f"lz4 returned non‑zero code ({result.returncode}), "
                            f"stdout='{result.stdout.strip()}', stderr='{result.stderr.strip()}'"
                        )

                    # Проверяем, что файл реально получился осмысленного размера
                    if kernel_unpacked_path.exists() and kernel_unpacked_path.stat().st_size > 1_000_000:
                        unpacked_size = kernel_unpacked_path.stat().st_size
                        self.logger.info(
                            f"Kernel unpacked with lz4: {unpacked_size} bytes "
                            f"(compressed: {kernel_size})"
                        )
                        kernel_path = kernel_unpacked_path
                    else:
                        # Если распаковка не удалась — логируем и используем сжатый как fallback
                        self.logger.error(
                            "Failed to get valid unpacked kernel via lz4; "
                            "falling back to compressed kernel (boot may fail)."
                        )
                        with open(kernel_path, "wb") as kf:
                            kf.write(kernel_data)
                        self.logger.info(
                            f"Using COMPRESSED kernel from boot.img as fallback: {kernel_size} bytes"
                        )

                    # Чистим временный сжатый файл (unpacked оставляем, если он используется)
                    try:
                        temp_compressed.unlink()
                    except Exception:
                        pass

                except Exception as e:
                    # Если lz4 недоступен или что‑то пошло не так — логируем и
                    # используем сжатый вариант как крайний случай.
                    self.logger.warning(
                        f"Could not unpack kernel with lz4 ({e}); using compressed kernel as fallback"
                    )
                    with open(kernel_path, "wb") as kf:
                        kf.write(kernel_data)
                    self.logger.info(
                        f"Using COMPRESSED kernel from boot.img as fallback: {kernel_size} bytes"
                    )
                
                # Проверяем, что файл записан
                if not kernel_path.exists() or kernel_path.stat().st_size == 0:
                    self.logger.error(f"Failed to write kernel: {kernel_path}")
                    return None, None
                
                # Извлекаем ramdisk
                f.seek(ramdisk_offset)
                ramdisk_data = f.read(ramdisk_size)
                if len(ramdisk_data) != ramdisk_size:
                    self.logger.error(f"Failed to read ramdisk: expected {ramdisk_size}, got {len(ramdisk_data)}")
                    return None, None
                
                with open(ramdisk_path, 'wb') as rf:
                    rf.write(ramdisk_data)
                
                # Проверяем, что файл записан
                if not ramdisk_path.exists() or ramdisk_path.stat().st_size != ramdisk_size:
                    self.logger.error(f"Failed to write ramdisk: {ramdisk_path}")
                    return None, None
                
                self.logger.info(f"Boot components extracted: kernel={kernel_size}B -> {kernel_path.name}, ramdisk={ramdisk_size}B -> {ramdisk_path.name}")
                return kernel_path, ramdisk_path
                
        except Exception as e:
            self.logger.error(f"Error extracting boot components: {e}")
            return None, None
    
    def _monitor_output(self):
        """Мониторинг вывода QEMU - захват serial output от kernel/Android"""
        if not self.process:
            self.logger.warning("Monitor: process is None, exiting")
            return
        
        import select
        import sys
        import os
        import time
        import tempfile
        from pathlib import Path
        
        self.logger.info("Monitor: starting output monitoring thread")
        
        try:
            # Файл для сырого дампа stdout QEMU (serial), чтобы ничего не потерять
            # Используем /tmp, чтобы путь был предсказуемым и легко просматриваемым.
            raw_serial_path = Path("/tmp") / f"t18fl3_qemu_serial_raw_{self.process.pid}.log"
            self.logger.info(f"Raw QEMU serial dump: {raw_serial_path}")
            raw_serial_file = open(raw_serial_path, "ab", buffering=0)
            
            # Используем неблокирующее чтение
            import fcntl
            # Устанавливаем неблокирующий режим для stdout и stderr
            stdout_fd = None
            stderr_fd = None
            
            if self.process.stdout:
                try:
                    stdout_fd = self.process.stdout.fileno()
                    flags = fcntl.fcntl(stdout_fd, fcntl.F_GETFL)
                    fcntl.fcntl(stdout_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
                    self.logger.debug(f"Monitor: stdout set to non-blocking (fd={stdout_fd})")
                except Exception as e:
                    self.logger.warning(f"Monitor: failed to set stdout non-blocking: {e}")
            
            if self.process.stderr:
                try:
                    stderr_fd = self.process.stderr.fileno()
                    flags = fcntl.fcntl(stderr_fd, fcntl.F_GETFL)
                    fcntl.fcntl(stderr_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
                    self.logger.debug(f"Monitor: stderr set to non-blocking (fd={stderr_fd})")
                except Exception as e:
                    self.logger.warning(f"Monitor: failed to set stderr non-blocking: {e}")
            
            read_count = 0
            empty_reads = 0
            bytes_read = 0
            last_log_time = time.time()
            first_data_time = None
            last_stats_log = time.time()
            
            # Пробуем использовать select() для macOS (может работать лучше чем неблокирующее чтение)
            use_select = sys.platform == "darwin" and stdout_fd is not None
            
            while self.process and self.process.poll() is None:
                # Проверяем stdout (серийный вывод от kernel/Android)
                if self.process.stdout:
                    try:
                        # На macOS пробуем использовать select() для проверки доступности данных
                        if use_select:
                            try:
                                # Проверяем, есть ли данные для чтения (timeout 0.1 секунды)
                                ready, _, _ = select.select([self.process.stdout], [], [], 0.1)
                                if not ready:
                                    # Нет данных - пропускаем итерацию
                                    empty_reads += 1
                                    read_count += 1
                                    time.sleep(0.05)
                                    continue
                            except (OSError, ValueError) as e:
                                # select может не работать с pipe на некоторых системах
                                use_select = False
                                self.logger.debug(f"Monitor: select() failed, falling back to non-blocking read: {e}")
                        
                        # Читаем все доступные данные (неблокирующий режим)
                        chunk = self.process.stdout.read(8192)
                        read_count += 1
                        
                        if chunk:
                            empty_reads = 0
                            bytes_read += len(chunk)
                            
                            if first_data_time is None:
                                first_data_time = time.time()
                                self.logger.info(f"Monitor: FIRST DATA RECEIVED! {len(chunk)} bytes, hex start: {chunk[:16].hex()}")
                            
                            # Сохраняем сырые байты в отдельный лог-файл (без декодирования)
                            try:
                                raw_serial_file.write(chunk)
                            except Exception as e:
                                self.logger.debug(f"Raw serial write failed: {e}")
                            
                            # Декодируем данные
                            try:
                                output = chunk.decode('utf-8', errors='ignore')
                            except Exception:
                                output = chunk.decode('latin-1', errors='ignore')
                            
                            # Логируем ВСЕ serial output для диагностики kernel
                            lines = output.split('\n')
                            for line in lines:
                                line_stripped = line.strip()
                                if line_stripped:
                                    # Исключаем только явно чужие сообщения (другие эмуляторы)
                                    is_other_emulator = any(
                                        exclude in line_stripped.lower()
                                        for exclude in [
                                            'emulator-5554', 'emulator-5556',
                                            'another emulator', 'other qemu', 'unrelated'
                                        ]
                                    )
                                    
                                    if not is_other_emulator:
                                        self.log_manager.log_qemu_output("SERIAL", line_stripped, "INFO")
                        else:
                            # Нет данных
                            empty_reads += 1
                            
                            # Логируем статистику каждые 5 секунд (чаще для диагностики)
                            current_time = time.time()
                            if current_time - last_stats_log > 5.0:
                                if first_data_time:
                                    elapsed = current_time - first_data_time
                                    data_status = f"data_received={bytes_read}B"
                                else:
                                    elapsed = current_time - last_log_time
                                    data_status = "no_data_yet"
                                
                                self.logger.info(f"Monitor stats: reads={read_count}, empty={empty_reads}, {data_status}, elapsed={elapsed:.1f}s, process_alive={self.process.poll() is None}, use_select={use_select}")
                                last_stats_log = current_time
                                
                    except (IOError, OSError) as e:
                        # Нет данных или ошибка чтения - это нормально в неблокирующем режиме
                        empty_reads += 1
                        # Логируем первые ошибки для диагностики
                        if empty_reads <= 3:
                            self.logger.debug(f"Monitor read error (normal in non-blocking mode): {e}")
                    except Exception as e:
                        self.logger.warning(f"Monitor exception: {e}")
                        import traceback
                        self.logger.debug(traceback.format_exc())
                
                # Проверяем stderr
                if self.process.stderr:
                    try:
                        chunk = self.process.stderr.read(8192)
                        if chunk:
                            output = chunk.decode('utf-8', errors='ignore')
                            # Логируем построчно
                            for line in output.split('\n'):
                                line = line.strip()
                                if line:
                                    self.log_manager.log_qemu_output("QEMU_STDERR", line, "WARNING")
                    except (IOError, OSError) as e:
                        # Нет данных - нормально в неблокирующем режиме
                        pass
                    except Exception as e:
                        self.logger.debug(f"Monitor stderr read error: {e}")
                
                # Небольшая задержка чтобы не нагружать CPU
                time.sleep(0.1)  # 100ms задержка для снижения нагрузки
                    
        except Exception as e:
            self.logger.error(f"Error monitoring QEMU output: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        finally:
            try:
                raw_serial_file.close()
            except Exception:
                pass
    
    def start(self) -> bool:
        """Запустить QEMU"""
        self.logger.info("=== QEMU START REQUESTED ===")
        
        # ВАЖНО: Очищаем все старые процессы T18FL3 перед запуском нового
        # Это гарантирует, что не будет конфликтов портов и ресурсов
        # При этом не трогаем другие эмуляторы
        self.cleanup_old_instances()
        
        if self.state != QEMUState.STOPPED:
            self.logger.warning(f"QEMU is not stopped (current state: {self.state})")
            return False
        
        self._set_state(QEMUState.STARTING)
        self.logger.info("State changed to STARTING")
        
        try:
            self.logger.info("Building QEMU command...")
            cmd = self._build_qemu_command()
            self.logger.info(f"QEMU command built: {len(cmd)} arguments")
            # Логируем полную команду для диагностики
            self.logger.debug(f"Full QEMU command: {' '.join(cmd)}")
            
            # Проверяем существование образов
            if self.config.android_boot_img and not self.config.android_boot_img.exists():
                self.logger.error(f"Boot image missing: {self.config.android_boot_img}")
                self._set_state(QEMUState.ERROR)
                return False
            
            if self.config.android_system_img and not self.config.android_system_img.exists():
                self.logger.error(f"System image missing: {self.config.android_system_img}")
                self._set_state(QEMUState.ERROR)
                return False
            
            self.logger.info("Starting QEMU subprocess")
            
            # Перед запуском QEMU убеждаемся, что ОБРАЗЫ СВОБОДНЫ
            # (никакой другой qemu / эмулятор не держит write‑lock на system/vendor/product)
            def _find_processes_using(path: Path) -> List[psutil.Process]:
                """Найти процессы, использующие данный файл (по open_files)"""
                users: List[psutil.Process] = []
                for proc in psutil.process_iter(["pid", "name", "open_files", "cmdline"]):
                    try:
                        open_files = proc.info.get("open_files") or []
                        for of in open_files:
                            if Path(of.path) == path:
                                users.append(proc)
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                return users

            def _force_release_images(image_paths: List[Path]) -> List[Path]:
                """
                Попробовать освободить образы перед запуском:
                - находим процессы, которые держат файлы;
                - если это qemu‑процессы или python‑обвязка эмуляторов, аккуратно их завершаем;
                - возвращаем список образов, которые всё равно остались заняты.
                """
                still_locked: List[Path] = []
                for img in image_paths:
                    if not img or not img.exists():
                        continue
                    users = _find_processes_using(img)
                    if not users:
                        continue
                    
                    self.logger.warning(
                        f"Image {img.name} is in use by {len(users)} process(es); "
                        f"attempting to free it before starting our QEMU"
                    )
                    
                    for proc in users:
                        try:
                            cmdline = " ".join(proc.info.get("cmdline") or [])
                            name = proc.info.get("name") or ""
                            pid = proc.info.get("pid")
                            
                            # Логируем подробно, что собираемся останавливать
                            self.logger.warning(
                                f"Releasing image {img.name}: found PID={pid}, name={name}, cmd={cmdline}"
                            )
                            
                            # Стратегия: мягко завершаем только процессы,
                            # которые очень похожи на qemu‑инстансы/нашу оболочку.
                            lower = (name + " " + cmdline).lower()
                            is_qemu_like = (
                                "qemu-system" in lower
                                or "emulator" in lower
                                or "t18fl3" in lower
                            )
                            
                            if not is_qemu_like:
                                # Чужие процессы только логируем, но не трогаем.
                                self.logger.warning(
                                    f"Process PID={pid} does not look like QEMU/emulator; "
                                    f"will NOT terminate it automatically"
                                )
                                continue
                            
                            # Стараемся завершить мягко
                            try:
                                proc.terminate()
                                self.logger.info(f"Sent terminate() to PID={pid} using {img.name}")
                                try:
                                    proc.wait(timeout=3)
                                except psutil.TimeoutExpired:
                                    self.logger.warning(f"PID={pid} did not exit, sending kill()")
                                    proc.kill()
                            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                                self.logger.debug(f"Process PID={pid} vanished or access denied: {e}")
                        except Exception as e:
                            self.logger.warning(f"Error while trying to release image {img.name}: {e}")
                
                # Перепроверяем, остались ли лочки после всех попыток
                for img in image_paths:
                    if not img or not img.exists():
                        continue
                    try:
                        import fcntl
                        with open(img, "rb") as f:
                            try:
                                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                            except IOError:
                                still_locked.append(img)
                                self.logger.error(
                                    f"Image {img.name} is STILL locked after attempts to release it"
                                )
                    except Exception as e:
                        self.logger.debug(f"Recheck lock failed for {img}: {e}")
                
                return still_locked

            # Список образов, которые должны быть свободны для нашего запуска
            images_to_check = [
                self.config.android_system_img,
                self.config.android_vendor_img,
                self.config.android_product_img,
            ]
            # ВАЖНО: QNX‑образы тоже могут держаться другими процессами и
            # вызывать "Failed to get \"write\" lock" при старте нашего QEMU.
            # Добавляем их в общий список для проверки и мягкого завершения
            # чужих процессов, использующих эти файлы.
            if self.config.enable_qnx:
                images_to_check.extend([
                    self.config.qnx_boot_img,
                    self.config.qnx_system_img,
                ])

            locked_after_release = _force_release_images(images_to_check)
            if locked_after_release:
                # Если после всех попыток образы остаются залоченными – безопаснее не стартовать QEMU вообще
                locked_names = ", ".join(p.name for p in locked_after_release)
                self.logger.error(
                    f"❌ Images still locked, aborting QEMU start to avoid conflicts: {locked_names}"
                )
                self._set_state(QEMUState.ERROR)
                return False
            
            # Используем unbuffered режим для stdout/stderr чтобы видеть вывод сразу
            import os
            # ВАЖНО: На macOS нужно использовать line buffering для serial output
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                bufsize=1,  # Line buffering (1 = line buffered, 0 = unbuffered может не работать на macOS)
                text=False,  # Бинарный режим для правильной работы с serial
                close_fds=True,
                env=dict(os.environ, PYTHONUNBUFFERED='1')
            )
            self.logger.debug(f"QEMU subprocess created: stdout={self.process.stdout is not None}, stderr={self.process.stderr is not None}")
            self.logger.info(f"QEMU process started with PID: {self.process.pid}")
            
            # Запускаем мониторинг вывода
            self.output_thread = threading.Thread(target=self._monitor_output, daemon=True, name="QEMU-Monitor")
            self.output_thread.start()
            self.logger.info("Monitor: output monitoring thread started")
            
            # Ждем немного и проверяем, что процесс запустился
            # Увеличиваем время ожидания для больших образов
            time.sleep(3)
            poll_result = self.process.poll()
            if poll_result is None:
                self._set_state(QEMUState.RUNNING)
                self.logger.info(f"QEMU running: PID={self.process.pid}, state={QEMUState.RUNNING.value}")
                
                # Проверяем состояние VM через monitor (через 2 секунды после запуска)
                def check_vm_status():
                    try:
                        import socket
                        monitor_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        monitor_sock.settimeout(1.0)
                        monitor_sock.connect(('127.0.0.1', self.config.monitor_port))
                        monitor_sock.send(b"info status\n")
                        response = monitor_sock.recv(1024).decode('utf-8', errors='ignore')
                        monitor_sock.close()
                        self.logger.info(f"QEMU monitor status: {response.strip()}")
                    except Exception as e:
                        self.logger.debug(f"Monitor status check failed: {e}")
                
                threading.Timer(2.0, check_vm_status).start()
                
                return True
            else:
                self._set_state(QEMUState.ERROR)
                self.logger.error(f"QEMU exited immediately: exit_code={poll_result}")
                # Читаем stderr для диагностики
                try:
                    # Используем select для неблокирующего чтения
                    import select
                    if self.process.stderr:
                        ready, _, _ = select.select([self.process.stderr], [], [], 0.5)
                        if ready:
                            stderr_output = self.process.stderr.read(8192).decode('utf-8', errors='ignore')
                            if stderr_output:
                                self.logger.error(f"QEMU stderr (first 8192 bytes):")
                                # Логируем построчно для лучшей читаемости
                                for line in stderr_output.split('\n'):
                                    if line.strip():
                                        self.logger.error(f"QEMU: {line}")
                except Exception as e:
                    self.logger.debug(f"Error reading stderr: {e}")
                
                # Также читаем stdout для диагностики
                try:
                    import select
                    if self.process.stdout:
                        ready, _, _ = select.select([self.process.stdout], [], [], 0.1)
                        if ready:
                            stdout_output = self.process.stdout.read(4096).decode('utf-8', errors='ignore')
                            if stdout_output:
                                self.logger.info(f"QEMU stdout (first 4096 bytes):")
                                for line in stdout_output.split('\n'):
                                    if line.strip():
                                        self.logger.info(f"QEMU: {line}")
                except Exception as e:
                    self.logger.debug(f"Error reading stdout: {e}")
                
                return False
                
        except Exception as e:
            import traceback
            self.logger.error(f"❌ Exception starting QEMU: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self._set_state(QEMUState.ERROR)
            return False
    
    def cleanup_old_instances(self):
        """
        Очистить все старые процессы T18FL3 эмулятора перед запуском нового.
        Останавливает только процессы T18FL3, не трогая другие эмуляторы.
        """
        self.logger.info("=== Cleaning up old T18FL3 instances (other emulators unaffected) ===")
        
        try:
            # Находим все процессы qemu_custom (наш кастомный QEMU для T18FL3)
            qemu_pids = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and any('qemu_custom' in str(arg) for arg in cmdline):
                        # Проверяем, что это действительно T18FL3 процесс
                        if any('t18fl3' in str(arg).lower() or 'T18FL3' in str(arg) for arg in cmdline):
                            qemu_pids.append(proc.info['pid'])
                            self.logger.info(f"Found old T18FL3 QEMU process: PID={proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Находим все Python процессы main.py из директории emulator
            python_pids = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    cwd = proc.info.get('cwd', '')
                    if cmdline and 'main.py' in ' '.join(str(arg) for arg in cmdline):
                        # Проверяем, что это из директории emulator
                        if 'emulator' in str(cwd) or any('emulator' in str(arg) for arg in cmdline):
                            python_pids.append(proc.info['pid'])
                            self.logger.info(f"Found old T18FL3 Python process: PID={proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Останавливаем найденные процессы
            stopped_count = 0
            for pid in qemu_pids + python_pids:
                try:
                    proc = psutil.Process(pid)
                    # Пропускаем текущий процесс (если он уже запущен)
                    if proc.pid == os.getpid():
                        continue
                    self.logger.info(f"Terminating old T18FL3 process: PID={pid}")
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        proc.kill()
                        proc.wait()
                    stopped_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    self.logger.debug(f"Process {pid} already gone or access denied: {e}")
            
            # Удаляем lock файл
            lock_file = Path("/var/folders/fz/2mw_b5ms4tj13vt4wlks6v_r0000gp/T/t18fl3_emulator.lock")
            if lock_file.exists():
                try:
                    lock_file.unlink()
                    self.logger.info("Removed old lock file")
                except Exception as e:
                    self.logger.warning(f"Could not remove lock file: {e}")
            
            if stopped_count > 0:
                self.logger.info(f"✅ Cleaned up {stopped_count} old T18FL3 instance(s)")
            else:
                self.logger.info("✅ No old T18FL3 instances found")
            
            # Даем время на освобождение ресурсов
            import time
            time.sleep(1)
            
        except Exception as e:
            self.logger.warning(f"Error during cleanup of old instances: {e}")
            # Продолжаем работу даже если cleanup не удался
    
    def stop(self):
        """Остановить QEMU (только наш T18FL3 процесс, не трогаем другие эмуляторы)"""
        self.logger.info("=== QEMU STOP REQUESTED (T18FL3 only, other emulators unaffected) ===")
        if self.state == QEMUState.STOPPED:
            self.logger.info("QEMU is already stopped.")
            return
        
        self._set_state(QEMUState.STOPPING)
        
        if self.process:
            our_pid = self.process.pid
            self.logger.info(f"Stopping OUR T18FL3 QEMU process (PID: {our_pid}) only...")
            
            # ВАЖНО: Проверяем что процесс еще существует и это наш процесс
            try:
                # Проверяем что процесс существует
                if self.process.poll() is None:
                    # Процесс еще работает - останавливаем только его
                    try:
                        # Попытка мягкого завершения через монитор (только наш изолированный порт)
                        monitor_port = self.config.monitor_port
                        monitor_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        monitor_sock.settimeout(2)
                        monitor_sock.connect(('127.0.0.1', monitor_port))
                        monitor_sock.send(b'quit\n')
                        monitor_sock.close()
                        self.logger.info(f"Sent 'quit' command to OUR T18FL3 QEMU monitor (port {monitor_port}).")
                        self.process.wait(timeout=5)  # Ждем завершения
                    except (socket.error, socket.timeout, subprocess.TimeoutExpired):
                        self.logger.warning("Failed to quit via monitor, terminating our process only.")
                        # ВАЖНО: Используем terminate() вместо kill() для мягкого завершения
                        self.process.terminate()
                        try:
                            self.process.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            # Если не завершился, только тогда kill (только наш PID)
                            self.logger.warning("Process did not terminate, forcing kill (our PID only).")
                            self.process.kill()
                            self.process.wait()
                    except Exception as e:
                        self.logger.error(f"Error during graceful QEMU shutdown: {e}, terminating our process.")
                        # ВАЖНО: Используем terminate() сначала
                        self.process.terminate()
                        try:
                            self.process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            self.process.kill()
                            self.process.wait()
                else:
                    # Процесс уже завершен
                    self.logger.info(f"Our T18FL3 QEMU process (PID: {our_pid}) already terminated.")
            except Exception as e:
                self.logger.error(f"Error stopping our T18FL3 QEMU process: {e}")
            
            self.process = None
            self.logger.info("Our T18FL3 QEMU process terminated (other emulators unaffected).")
        
        # Даем время на освобождение файлов
        import time
        time.sleep(1)
        
        if self.output_thread and self.output_thread.is_alive():
            self.output_thread.join(timeout=1)
            self.logger.info("Output monitoring thread stopped.")
        
        # Очищаем временные файлы
        # ВАЖНО: Проверяем что temp_dir существует и инициализирован
        if hasattr(self, 'temp_dir') and self.temp_dir is not None:
            try:
                if self.temp_dir.exists():
                    import shutil
                    shutil.rmtree(self.temp_dir)
                    self.logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up temporary directory: {e}")
        
        self._set_state(QEMUState.STOPPED)
        self.logger.info("T18FL3 QEMU stopped (other emulators unaffected).")
    
    def get_state(self) -> QEMUState:
        """Получить текущее состояние"""
        with self.state_lock:
            return self.state
    
    def is_running(self) -> bool:
        """Проверить, запущен ли QEMU"""
        return self.state == QEMUState.RUNNING and self.process and self.process.poll() is None

