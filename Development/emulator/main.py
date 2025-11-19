#!/usr/bin/env python3
"""
T18FL3 Emulator - Главная точка входа
Запускает GUI в отдельной оболочке с hot reload и детальным логированием
"""

import sys
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
import psutil

# Сохраняем оригинальную рабочую директорию
_original_cwd = os.getcwd()

# КРИТИЧЕСКИ ВАЖНО: Добавляем путь к директории эмулятора в sys.path
# Это позволяет запускать из любой директории (включая launchpad)
try:
    # Пытаемся получить путь из __file__
    _emulator_dir = Path(__file__).resolve().parent
except NameError:
    # Если __file__ не определен (например, при запуске через exec), используем текущую директорию
    _emulator_dir = Path.cwd()
    # Пытаемся найти main.py в текущей директории или родительских
    if not (_emulator_dir / "main.py").exists():
        # Ищем main.py в родительских директориях
        search_path = _emulator_dir
        while search_path != search_path.root:
            if (search_path / "main.py").exists():
                _emulator_dir = search_path
                break
            search_path = search_path.parent

# Добавляем путь к эмулятору в sys.path
if str(_emulator_dir) not in sys.path:
    sys.path.insert(0, str(_emulator_dir))

# Меняем рабочую директорию на директорию эмулятора
os.chdir(_emulator_dir)

# Настройка детального логирования ДО импорта модулей
def setup_detailed_logging():
    """Настроить детальное логирование этапов запуска"""
    log_dir = _emulator_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"t18fl3_startup_{timestamp}.log"
    
    # Настраиваем root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] [%(levelname)-8s] [%(name)s:%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger("startup")
    logger.info("=" * 70)
    logger.info("🚀 ЗАПУСК T18FL3 EMULATOR")
    logger.info("=" * 70)
    logger.info(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Рабочая директория: {os.getcwd()}")
    logger.info(f"Директория эмулятора: {_emulator_dir}")
    logger.info(f"Лог файл: {log_file}")
    logger.info("")
    
    return logger, log_file

# Настраиваем логирование ПЕРВЫМ ДЕЛОМ
startup_logger, startup_log_file = setup_detailed_logging()


def ensure_single_instance():
    """
    Грубое, но надёжное ограничение: одновременно может быть запущен только
    один экземпляр T18FL3 Emulator.
    Реализовано через PID‑lock в /tmp.
    """
    import tempfile

    lock_path = Path(tempfile.gettempdir()) / "t18fl3_emulator.lock"

    try:
        if lock_path.exists():
            try:
                existing_pid = int(lock_path.read_text().strip())
            except Exception:
                existing_pid = None

            if existing_pid and psutil.pid_exists(existing_pid):
                startup_logger.error(
                    f"❌ Обнаружен уже запущенный экземпляр T18FL3 Emulator (PID={existing_pid}). "
                    f"Одновременно может работать только один экземпляр."
                )
                sys.exit(1)
            else:
                # Старый lock невалиден – удаляем
                try:
                    lock_path.unlink()
                except Exception:
                    pass

        # Создаём новый lock с текущим PID
        lock_path.write_text(str(os.getpid()), encoding="utf-8")
        startup_logger.info(f"Lock-файл экземпляра: {lock_path} (PID={os.getpid()})")
    except Exception as e:
        startup_logger.warning(f"⚠️ Не удалось установить single-instance lock: {e}")


# Гарантируем, что одновременно запущен только один экземпляр GUI
ensure_single_instance()

# Этап 1: Проверка окружения
startup_logger.info("═══════════════════════════════════════════════════════════════════════════════")
startup_logger.info("ЭТАП 1: ПРОВЕРКА ОКРУЖЕНИЯ")
startup_logger.info("═══════════════════════════════════════════════════════════════════════════════")

try:
    startup_logger.info("Проверка Python версии...")
    startup_logger.info(f"  Python: {sys.version}")
    startup_logger.info(f"  Python путь: {sys.executable}")
    
    startup_logger.info("Проверка PyQt6...")
    try:
        from PyQt6.QtCore import PYQT_VERSION_STR
        startup_logger.info(f"  ✅ PyQt6 найден: {PYQT_VERSION_STR}")
    except ImportError as e:
        startup_logger.error(f"  ❌ PyQt6 не найден: {e}")
        sys.exit(1)
    
    startup_logger.info("✅ ЭТАП 1 ЗАВЕРШЕН: Окружение проверено")
    startup_logger.info("")
except Exception as e:
    startup_logger.error(f"❌ ОШИБКА НА ЭТАПЕ 1: {e}")
    import traceback
    startup_logger.error(traceback.format_exc())
    sys.exit(1)

# Этап 2: Импорт модулей
startup_logger.info("═══════════════════════════════════════════════════════════════════════════════")
startup_logger.info("ЭТАП 2: ИМПОРТ МОДУЛЕЙ")
startup_logger.info("═══════════════════════════════════════════════════════════════════════════════")

try:
    startup_logger.info("Импорт PyQt6 компонентов...")
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    startup_logger.info("  ✅ QApplication импортирован")
    
    startup_logger.info("Импорт модулей эмулятора...")
    from gui.main_window import MainWindow
    startup_logger.info("  ✅ MainWindow импортирован")
    
    from core.log_manager import get_logger, get_log_manager
    startup_logger.info("  ✅ LogManager импортирован")
    
    startup_logger.info("✅ ЭТАП 2 ЗАВЕРШЕН: Модули импортированы")
    startup_logger.info("")
except Exception as e:
    startup_logger.error(f"❌ ОШИБКА НА ЭТАПЕ 2: {e}")
    import traceback
    startup_logger.error(traceback.format_exc())
    sys.exit(1)

# Этап 3: Создание QApplication
startup_logger.info("═══════════════════════════════════════════════════════════════════════════════")
startup_logger.info("ЭТАП 3: СОЗДАНИЕ QAPPLICATION")
startup_logger.info("═══════════════════════════════════════════════════════════════════════════════")

try:
    startup_logger.info("Создание QApplication...")
    # ВАЖНО: Убираем 'Python' из аргументов, чтобы не показывалось в заголовке
    # На macOS это особенно важно для создания отдельного приложения
    app = QApplication(sys.argv)
    
    # Настраиваем приложение как отдельное, не как Python скрипт
    app.setApplicationName("T18FL3 Emulator")
    app.setApplicationDisplayName("T18FL3 Emulator")
    app.setOrganizationName("Tiggo")
    app.setOrganizationDomain("tiggo.local")
    
    # На macOS: скрываем меню Python и делаем приложение независимым
    if sys.platform == "darwin":
        # Устанавливаем bundle identifier для macOS
        try:
            from PyQt6.QtCore import QCoreApplication
            QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        except:
            pass
    
    startup_logger.info("  ✅ QApplication создан")
    startup_logger.info(f"  Аргументы: {sys.argv}")
    startup_logger.info(f"  Application Name: {app.applicationName()}")
    startup_logger.info(f"  Display Name: {app.applicationDisplayName()}")
    startup_logger.info("✅ ЭТАП 3 ЗАВЕРШЕН: QApplication создан")
    startup_logger.info("")
except Exception as e:
    startup_logger.error(f"❌ ОШИБКА НА ЭТАПЕ 3: {e}")
    import traceback
    startup_logger.error(traceback.format_exc())
    sys.exit(1)

# Этап 4: Создание главного окна
startup_logger.info("═══════════════════════════════════════════════════════════════════════════════")
startup_logger.info("ЭТАП 4: СОЗДАНИЕ ГЛАВНОГО ОКНА")
startup_logger.info("═══════════════════════════════════════════════════════════════════════════════")

try:
    startup_logger.info("Создание MainWindow...")
    window = MainWindow()
    startup_logger.info("  ✅ MainWindow создан")
    
    startup_logger.info("Показ окна...")
    window.show()
    startup_logger.info("  ✅ Окно показано")
    
    startup_logger.info("✅ ЭТАП 4 ЗАВЕРШЕН: Главное окно создано и показано")
    startup_logger.info("")
except Exception as e:
    startup_logger.error(f"❌ ОШИБКА НА ЭТАПЕ 4: {e}")
    import traceback
    startup_logger.error(traceback.format_exc())
    sys.exit(1)

# Этап 5: Запуск event loop
startup_logger.info("═══════════════════════════════════════════════════════════════════════════════")
startup_logger.info("ЭТАП 5: ЗАПУСК EVENT LOOP")
startup_logger.info("═══════════════════════════════════════════════════════════════════════════════")
startup_logger.info("")
startup_logger.info("✅ ВСЕ ЭТАПЫ ЗАВЕРШЕНЫ УСПЕШНО!")
startup_logger.info("")
startup_logger.info("🎯 GUI запущен в отдельной оболочке")
startup_logger.info("📝 Логи сохраняются в: " + str(startup_log_file))
startup_logger.info("")
startup_logger.info("💡 Следующие этапы (внутри приложения):")
startup_logger.info("   • Инициализация компонентов GUI")
startup_logger.info("   • Настройка QEMU менеджера")
startup_logger.info("   • Настройка CAN симулятора")
startup_logger.info("   • Автозапуск эмулятора (если включен)")
startup_logger.info("   • Загрузка kernel")
startup_logger.info("   • Запуск Android")
startup_logger.info("   • Подключение ADB")
startup_logger.info("")
startup_logger.info("🔄 Запускаю event loop...")
startup_logger.info("")

try:
    exit_code = app.exec()
    startup_logger.info("")
    startup_logger.info("═══════════════════════════════════════════════════════════════════════════════")
    startup_logger.info("ЗАВЕРШЕНИЕ ПРИЛОЖЕНИЯ")
    startup_logger.info("═══════════════════════════════════════════════════════════════════════════════")
    startup_logger.info(f"Код выхода: {exit_code}")
    sys.exit(exit_code)
except Exception as e:
    startup_logger.error(f"❌ ОШИБКА В EVENT LOOP: {e}")
    import traceback
    startup_logger.error(traceback.format_exc())
    sys.exit(1)
