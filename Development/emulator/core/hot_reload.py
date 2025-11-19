"""
Hot Reload механизм для перезагрузки модулей без перезапуска приложения
"""

import sys
import importlib
from pathlib import Path
from typing import List, Optional


def reload_module(module_name: str) -> bool:
    """
    Перезагрузить модуль по имени
    
    Args:
        module_name: Имя модуля (например, 'core.qemu_manager')
    
    Returns:
        True если успешно, False если ошибка
    """
    try:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
            return True
        return False
    except Exception as e:
        print(f"Error reloading {module_name}: {e}")
        return False


def reload_package(package_name: str) -> int:
    """
    Перезагрузить весь пакет и все его подмодули
    
    Args:
        package_name: Имя пакета (например, 'core' или 'gui')
    
    Returns:
        Количество перезагруженных модулей
    """
    reloaded = 0
    modules_to_reload = [
        name for name in sys.modules.keys()
        if name.startswith(f"{package_name}.")
    ]
    
    # Сортируем по глубине (сначала подмодули, потом родительские)
    modules_to_reload.sort(key=lambda x: x.count('.'), reverse=True)
    
    for module_name in modules_to_reload:
        if reload_module(module_name):
            reloaded += 1
    
    return reloaded


def clear_python_cache(directory: Optional[Path] = None) -> int:
    """
    Очистить кэш Python (.pyc файлы и __pycache__ директории)
    
    Args:
        directory: Директория для очистки (по умолчанию - директория эмулятора)
    
    Returns:
        Количество удаленных файлов/директорий
    """
    import shutil
    
    if directory is None:
        directory = Path(__file__).parent.parent
    
    removed = 0
    
    # Удаляем __pycache__ директории
    for cache_dir in directory.rglob('__pycache__'):
        try:
            shutil.rmtree(cache_dir)
            removed += 1
        except:
            pass
    
    # Удаляем .pyc файлы
    for pyc_file in directory.rglob('*.pyc'):
        try:
            pyc_file.unlink()
            removed += 1
        except:
            pass
    
    return removed


def reload_all_emulator_modules() -> dict:
    """
    Перезагрузить все модули эмулятора
    
    Returns:
        Словарь с результатами: {'core': count, 'gui': count, 'cache_cleared': count}
    """
    result = {
        'cache_cleared': clear_python_cache(),
        'core': reload_package('core'),
        'gui': reload_package('gui'),
    }
    return result

