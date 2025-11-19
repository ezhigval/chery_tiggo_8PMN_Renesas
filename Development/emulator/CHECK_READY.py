#!/usr/bin/env python3
"""
Скрипт проверки готовности к запуску
Проверяет наличие всех необходимых компонентов
"""

import sys
from pathlib import Path
import subprocess

def check_images():
    """Проверить наличие образов"""
    print("=" * 60)
    print("Проверка образов...")
    print("=" * 60)
    
    base_path = Path(__file__).parent.parent.parent / "update_extracted" / "payload"
    required_images = {
        "boot.img": "Android boot image",
        "system.img": "Android system (ext2)",
        "vendor.img": "Android vendor (ext2)",
        "product.img": "Android product (ext2)",
        "dtb.img": "Device Tree Blob"
    }
    
    all_ok = True
    for img, desc in required_images.items():
        img_path = base_path / img
        if img_path.exists():
            size = img_path.stat().st_size / (1024**3)  # GB
            print(f"✅ {img:20s} ({desc:30s}) - {size:.2f} GB")
        else:
            print(f"❌ {img:20s} ({desc:30s}) - НЕ НАЙДЕН")
            all_ok = False
    
    return all_ok

def check_qemu():
    """Проверить наличие QEMU"""
    print("\n" + "=" * 60)
    print("Проверка QEMU...")
    print("=" * 60)
    
    qemu_paths = [
        "/opt/homebrew/bin/qemu-system-aarch64",
        "/usr/local/bin/qemu-system-aarch64",
        "/usr/bin/qemu-system-aarch64"
    ]
    
    for path in qemu_paths:
        if Path(path).exists():
            try:
                result = subprocess.run([path, "--version"], 
                                      capture_output=True, text=True, timeout=2)
                version = result.stdout.split('\n')[0] if result.returncode == 0 else "unknown"
                print(f"✅ QEMU найден: {path}")
                print(f"   {version}")
                return True
            except:
                pass
    
    print("❌ QEMU не найден")
    print("   Установите: brew install qemu (macOS)")
    return False

def check_python_packages():
    """Проверить Python пакеты"""
    print("\n" + "=" * 60)
    print("Проверка Python пакетов...")
    print("=" * 60)
    
    required_packages = {
        "PyQt6": "PyQt6",
        "loguru": "loguru",
        "psutil": "psutil"
    }
    
    all_ok = True
    for package, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - не установлен")
            print(f"   Установите: pip install {package}")
            all_ok = False
    
    return all_ok

def main():
    """Главная функция"""
    print("\n" + "=" * 60)
    print("ПРОВЕРКА ГОТОВНОСТИ T18FL3 EMULATOR")
    print("=" * 60 + "\n")
    
    images_ok = check_images()
    qemu_ok = check_qemu()
    packages_ok = check_python_packages()
    
    print("\n" + "=" * 60)
    print("ИТОГ")
    print("=" * 60)
    
    if images_ok and qemu_ok and packages_ok:
        print("✅ ВСЕ ГОТОВО К ЗАПУСКУ!")
        print("\nЗапустите: python main.py")
        return 0
    else:
        print("❌ ТРЕБУЮТСЯ ДОПОЛНИТЕЛЬНЫЕ ДЕЙСТВИЯ")
        if not images_ok:
            print("   - Распакуйте payload.bin если образы отсутствуют")
        if not qemu_ok:
            print("   - Установите QEMU")
        if not packages_ok:
            print("   - Установите Python пакеты: pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())

