"""
Конфигурация для использования рабочего ядра вместо оригинального
"""

from pathlib import Path
from typing import Optional

# Путь к рабочему ядру (если есть)
WORKING_KERNEL_PATH: Optional[Path] = None

# Путь к рабочему DTB (если нужен)
WORKING_DTB_PATH: Optional[Path] = None

# Использовать стандартную virt машину вместо кастомной g6sh
USE_VIRT_MACHINE: bool = True

# Параметры загрузки для рабочего ядра
WORKING_KERNEL_LOAD_ADDR: int = 0x40080000  # Стандартный адрес для virt машины
WORKING_RAMDISK_LOAD_ADDR: int = 0x44000000  # Стандартный адрес для virt машины

# Параметры командной строки ядра
WORKING_KERNEL_CMDLINE: str = (
    "console=ttyAMA0,115200 earlyprintk=serial,ttyAMA0,115200 "
    "root=/dev/ram0 rw init=/init androidboot.hardware=qemu "
    "androidboot.selinux=permissive"
)

def get_working_kernel_path() -> Optional[Path]:
    """Получить путь к рабочему ядру"""
    if WORKING_KERNEL_PATH and WORKING_KERNEL_PATH.exists():
        return WORKING_KERNEL_PATH
    
    # Пробуем найти в стандартных местах
    possible_paths = [
        Path(__file__).parent.parent / "kernels" / "android_kernel_arm64",
        Path(__file__).parent.parent.parent.parent / "kernels" / "android_kernel_arm64",
        Path.home() / ".android" / "kernels" / "android_kernel_arm64",
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return None

def get_working_dtb_path() -> Optional[Path]:
    """Получить путь к рабочему DTB"""
    if WORKING_DTB_PATH and WORKING_DTB_PATH.exists():
        return WORKING_DTB_PATH
    
    # Для virt машины DTB генерируется автоматически
    return None





