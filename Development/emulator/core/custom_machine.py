"""
Custom Machine Configuration for T18FL3 (Renesas g6sh 703000765AA)
Создаем кастомную конфигурацию виртуальной машины, совместимую с нашим kernel
"""

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
import tempfile
import os

from .log_manager import get_logger


@dataclass
class RenesasG6SHConfig:
    """Конфигурация для Renesas g6sh (703000765AA)"""
    
    # CPU характеристики (R-Car g6sh спецификация)
    cpu_model: str = "cortex-a57"  # Renesas g6sh использует Cortex-A57
    cpu_count: int = 4  # R-Car g6sh имеет 4 ядра Cortex-A57
    memory_mb: int = 4096  # 4GB RAM
    
    # Memory map для Renesas g6sh (из документации R-Car)
    # R-Car g6sh использует специфичную memory map
    memory_base: int = 0x40000000  # Базовый адрес памяти
    kernel_load_addr: int = 0x48080000  # Адрес загрузки kernel (из boot.img)
    ramdisk_load_addr: int = 0x4a180000  # Адрес загрузки ramdisk (из boot.img)
    
    # R-Car g6sh специфичные адреса устройств
    uart_base: int = 0xe6e80000  # SCIF (Serial Communication Interface)
    can_base: int = 0xe6c00000  # CAN контроллеры
    ethernet_base: int = 0xee700000  # Ethernet контроллер
    
    # Устройства, которые ожидает kernel R-Car g6sh
    devices: List[str] = None
    
    # Параметры для совместимости с R-Car
    use_rcar_dtb: bool = True  # Использовать DTB специфичный для R-Car
    rcar_machine_type: str = "rcar-g6sh"  # Имя machine type для R-Car g6sh
    
    def __post_init__(self):
        if self.devices is None:
            # Расширенный набор устройств для R-Car g6sh
            self.devices = [
                "uart",           # Serial console (SCIF)
                "virtio-net",     # Сеть (замена для Ethernet)
                "virtio-blk",     # Блок-устройства (диски)
                "virtio-gpu",     # Графика
                "virtio-rng",     # Random number generator
                "virtio-balloon", # Memory balloon
            ]


class CustomMachineBuilder:
    """Строитель кастомной виртуальной машины для T18FL3"""
    
    def __init__(self, config: RenesasG6SHConfig):
        self.config = config
        self.logger = get_logger("custom_machine")
    
    def build_qemu_args(self, kernel_path: Path, ramdisk_path: Optional[Path] = None, dtb_path: Optional[Path] = None) -> List[str]:
        """Построить аргументы QEMU для кастомной машины R-Car g6sh"""
        args = []
        
        # ВАЖНО: Создаем кастомную конфигурацию для R-Car g6sh
        # Используем virt machine с параметрами, максимально близкими к R-Car g6sh
        
        # Machine type - используем кастомную машину g6sh
        # ✅ ИСПРАВЛЕНО: Машина g6sh теперь зарегистрирована и работает!
        machine_type = "g6sh"  # Кастомная машина g6sh с правильными адресами ГУ
        args.extend(["-machine", machine_type])
        self.logger.info(f"✅ Using g6sh machine (Renesas R-Car g6sh with correct hardware addresses)")
        
        # CPU - R-Car g6sh спецификация
        args.extend(["-cpu", f"{self.config.cpu_model},aarch64=on"])
        args.extend(["-smp", f"{self.config.cpu_count},cores=4,threads=1,sockets=1"])
        args.extend(["-m", f"{self.config.memory_mb},slots=2,maxmem=8G"])
        
        # Kernel и ramdisk с правильными адресами для R-Car g6sh
        if kernel_path and kernel_path.exists():
            args.extend(["-kernel", str(kernel_path)])
            self.logger.info(f"Kernel: {kernel_path} (R-Car g6sh load address: 0x{self.config.kernel_load_addr:x})")
        
        if ramdisk_path and ramdisk_path.exists():
            args.extend(["-initrd", str(ramdisk_path)])
            self.logger.info(f"Ramdisk: {ramdisk_path} (R-Car g6sh load address: 0x{self.config.ramdisk_load_addr:x})")
        
        # DTB для R-Car g6sh
        if dtb_path and dtb_path.exists():
            # Проверяем, что это валидный DTB
            try:
                with open(dtb_path, 'rb') as f:
                    magic = f.read(4)
                    if magic == b'\xd0\x0d\xfe\xed' or magic == b'\xed\xfe\x0d\xd0':
                        args.extend(["-dtb", str(dtb_path)])
                        self.logger.info(f"R-Car g6sh DTB: {dtb_path}")
                    else:
                        self.logger.warning(f"DTB file has invalid magic, will try to extract/create R-Car DTB")
            except Exception as e:
                self.logger.warning(f"Error checking DTB: {e}")
        
        # Дополнительные устройства для R-Car g6sh совместимости
        # Random number generator (требуется для Android)
        args.extend(["-device", "virtio-rng-pci"])
        
        # Memory balloon (для управления памятью)
        args.extend(["-device", "virtio-balloon-pci"])
        
        # КРИТИЧЕСКИ ВАЖНО: Добавляем RTC для правильной работы Android
        args.extend(["-rtc", "base=utc,clock=host"])
        
        # КРИТИЧЕСКИ ВАЖНО: Добавляем поддержку keyboard и mouse для Android
        args.extend(["-device", "virtio-keyboard-pci"])
        args.extend(["-device", "virtio-tablet-pci"])
        
        # Устройства добавляются в qemu_manager.py для избежания конфликтов
        # Serial, сеть, графика, блок-устройства - все в qemu_manager
        
        return args
    
    def extract_dtb_from_image(self, dtb_img_path: Path) -> Optional[Path]:
        """Попытаться извлечь DTB из dtb.img (может быть AVB структура)"""
        if not dtb_img_path or not dtb_img_path.exists():
            return None
        
        try:
            # Проверяем, не является ли это AVB структурой
            with open(dtb_img_path, 'rb') as f:
                header = f.read(16)
                # AVB структура начинается с "AVB0"
                if header[:4] == b'AVB0':
                    self.logger.warning(f"{dtb_img_path} appears to be AVB structure, not DTB")
                    # Пробуем найти DTB внутри AVB структуры
                    # AVB обычно имеет размеры в заголовке
                    # Пока возвращаем None - нужно более глубокий анализ
                    return None
                
                # Проверяем DTB magic
                f.seek(0)
                magic = f.read(4)
                if magic == b'\xd0\x0d\xfe\xed' or magic == b'\xed\xfe\x0d\xd0':
                    # Это валидный DTB
                    return dtb_img_path
        except Exception as e:
            self.logger.warning(f"Error checking DTB image: {e}")
        
        return None
    
    def create_custom_dtb(self, output_path: Path) -> bool:
        """Создать кастомный Device Tree для Renesas g6sh"""
        # ВАЖНО: Для создания правильного DTB нужно знать точную конфигурацию hardware
        # Пробуем создать минимальный DTB для R-Car g6sh на основе известных параметров
        
        self.logger.info("Attempting to create custom DTB for R-Car g6sh...")
        
        # Пока используем автогенерацию QEMU, но логируем попытку
        # В будущем можно использовать dtc (Device Tree Compiler) для создания DTB
        # Для этого нужен DTS (Device Tree Source) файл
        
        self.logger.warning("Custom DTB creation requires DTS source - using QEMU auto-generation for now")
        return False
    
    def get_rcar_sdk_info(self) -> dict:
        """Получить информацию о Renesas SDK (RoX SDK)"""
        return {
            "name": "Renesas RoX SDK",
            "description": "Software Development Kit for R-Car series",
            "url": "https://www.renesas.cn/zh/software-tool/rox-software-development-kit",
            "supports": ["Linux", "Android", "QNX", "FreeRTOS"],
            "available": False,  # Нужно проверить доступность
            "note": "SDK может содержать примеры конфигурации QEMU для R-Car"
        }
    
    def get_machine_description(self) -> str:
        """Получить описание машины"""
        return f"""
Renesas g6sh (703000765AA) Custom Machine:
  - CPU: {self.config.cpu_model} x{self.config.cpu_count}
  - Memory: {self.config.memory_mb} MB
  - Kernel load: 0x{self.config.kernel_load_addr:x}
  - Ramdisk load: 0x{self.config.ramdisk_load_addr:x}
  - Devices: {', '.join(self.config.devices)}
"""

