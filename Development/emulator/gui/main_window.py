"""
Main Window - Главное окно эмулятора T18FL3
Содержит два экрана и панель управления
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QPushButton, QLabel, QStatusBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSettings
from PyQt6.QtGui import QFont
from pathlib import Path
import os
import time
import sys

from gui.display1_widget import Display1Widget
from gui.display2_widget import Display2Widget
from gui.log_viewer import LogViewer
from gui.control_panel import ControlPanel
from gui.vehicle_controls import VehicleControls
from gui.developer_interface import DeveloperInterface
from core.qemu_manager import QEMUManager, QEMUState, QEMUConfig
from core.can_simulator import CANSimulator
from core.log_manager import get_logger, get_log_manager
from core.ignition_states import IgnitionState
from core.auto_diagnostics import AutoDiagnostics


class MainWindow(QMainWindow):
    """Главное окно эмулятора T18FL3"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger("main_window")
        self.log_manager = get_log_manager()
        
        # Инициализация
        self.logger.info("MainWindow initialization")
        
        self.qemu_manager: QEMUManager = None
        self.can_simulator: CANSimulator = None
        # Автодиагностика удалена по запросу пользователя
        self.auto_mode = True  # Автоматический режим включен
        self.auto_restart_enabled = False  # Автоматический перезапуск отключен
        
        self.setWindowTitle("T18FL3 Emulator - Chery Tiggo 8 PRO MAX")
        
        # Настройки для сохранения состояния окна
        self.settings = QSettings("Tiggo", "T18FL3Emulator")
        self._restore_window_state()
        
        # На macOS: настраиваем окно как отдельное приложение
        if sys.platform == "darwin":
            try:
                self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
                self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            except:
                pass
        
        self._setup_ui()
        self._setup_timers()
        
        # Автозапуск: включаем эмулятор автоматически при старте
        QTimer.singleShot(2000, self._auto_start)
        self.logger.info("Auto-start scheduled: 2s delay")
    
    def _setup_ui(self):
        """Настроить UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Верхняя часть: два экрана
        screens_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Display 1: Instrument Cluster (12.3")
        self.display1 = Display1Widget()
        self.display1.setMinimumSize(800, 600)
        screens_splitter.addWidget(self.display1)
        
        # Display 2: Multimedia System (12.3")
        self.display2 = Display2Widget()
        self.display2.setMinimumSize(800, 600)
        screens_splitter.addWidget(self.display2)
        
        screens_splitter.setSizes([800, 800])  # Равные размеры
        main_layout.addWidget(screens_splitter, stretch=3)
        
        # Нижняя часть: элементы управления и интерфейс разработчика
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая часть: элементы управления автомобилем
        left_panel = QSplitter(Qt.Orientation.Vertical)
        
        # Панель управления (базовая)
        self.control_panel = ControlPanel()
        self.control_panel.start_clicked.connect(self._on_start)
        self.control_panel.stop_clicked.connect(self._on_stop)
        # reset_clicked убран - кнопка Reset удалена
        left_panel.addWidget(self.control_panel)
        
        # Физические элементы управления
        self.vehicle_controls = VehicleControls()
        # Привязываем внешний контрол зажигания (большая кнопка в ControlPanel)
        # к CAN‑логике и авто‑старту Android.
        self.vehicle_controls.bind_external_ignition(self.control_panel.ignition)
        # Привязываем компактные кнопки руля на панели Control к CAN‑логике
        # VehicleControls.
        self.vehicle_controls.bind_external_steering_buttons(
            self.control_panel.steering_compact.button_clicked
        )
        self.control_panel.ignition.ignition_changed.connect(self._on_ignition_state_changed)
        left_panel.addWidget(self.vehicle_controls)
        
        left_panel.setSizes([200, 400])
        bottom_splitter.addWidget(left_panel)
        
        # Правая часть: интерфейс разработчика и логи
        right_panel = QSplitter(Qt.Orientation.Vertical)
        
        # Интерфейс разработчика
        self.developer_interface = DeveloperInterface()
        right_panel.addWidget(self.developer_interface)
        
        # Просмотр логов (базовый)
        self.log_viewer = LogViewer()
        right_panel.addWidget(self.log_viewer)
        
        right_panel.setSizes([400, 200])
        
        # Настраиваем просмотр логов после создания всех компонентов
        self._setup_log_viewer()
        bottom_splitter.addWidget(right_panel)
        
        bottom_splitter.setSizes([400, 800])
        main_layout.addWidget(bottom_splitter, stretch=1)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def _setup_timers(self):
        """Настроить таймеры для обновления"""
        # Таймер для обновления статуса
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # Каждую секунду
        self.logger.debug("Status timer: 1s interval")
    
    def _setup_qemu(self, config: QEMUConfig):
        """Настроить QEMU менеджер"""
        if self.qemu_manager:
            self.qemu_manager.stop()
        
        self.qemu_manager = QEMUManager(config)
        self.qemu_manager.add_state_callback(self._on_qemu_state_changed)
    
    def _setup_can(self):
        """Настроить CAN симулятор"""
        if self.can_simulator:
            self.can_simulator.stop()
        
        self.can_simulator = CANSimulator()
        self.control_panel.set_can_simulator(self.can_simulator)
    
    def _auto_start(self):
        """Автоматический запуск при старте приложения"""
        if self.auto_mode:
            self.logger.info("Auto-start: enabling emulator")
            # Устанавливаем toggle в ON (кружочек переедет, цвет изменится когда система запустится)
            if self.control_panel:
                self.control_panel._set_toggle_state(True, animate=True)
            # Запускаем систему
            self._start_system()
    
    def _on_start(self):
        """Обработчик включения переключателя - автоматический запуск системы"""
        self.logger.info("Emulator toggle switched ON - starting system automatically")
        self._start_system()
    
    def _start_system(self):
        """Запустить систему (QEMU)"""
        self.logger.info("System start requested")
        
        # Останавливаем только наш T18FL3 QEMU процесс, не трогаем другие эмуляторы!
        if self.qemu_manager and self.qemu_manager.get_state() != QEMUState.STOPPED:
            self.logger.info("Stopping previous QEMU instance")
            self.qemu_manager.stop()  # Останавливает только наш процесс по PID
            import time
            time.sleep(2)
        
        # Создаем конфигурацию QEMU
        self.logger.info("Locating payload directory")
        # Используем абсолютные пути относительно проекта
        # __file__ = development/emulator/gui/main_window.py
        # parent.parent.parent.parent = development/emulator -> development -> Tiggo
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent
        
        # Проверяем, существует ли payload_dir
        payload_dir = project_root / "update_extracted" / "payload"
        if not payload_dir.exists():
            # Пробуем альтернативный путь (если запускаем из другой директории)
            alt_project_root = current_file.parent.parent.parent
            alt_payload_dir = alt_project_root / "update_extracted" / "payload"
            if alt_payload_dir.exists():
                payload_dir = alt_payload_dir
                project_root = alt_project_root
            else:
                # Ищем update_extracted в родительских директориях
                search_path = current_file.parent
                while search_path != search_path.root:
                    test_payload = search_path / "update_extracted" / "payload"
                    if test_payload.exists():
                        payload_dir = test_payload
                        break
                    search_path = search_path.parent
        
        if not payload_dir.exists():
            self.logger.error(f"Payload directory not found: {payload_dir}")
            self.status_bar.showMessage(f"Error: Payload dir not found: {payload_dir}", 10000)
            return
        
        self.logger.info(f"Payload directory: {payload_dir}")
        
        # Режимы запуска:
        #   1) Через GUI чекбоксы (Android/QNX) на панели управления
        #   2) Через переменные окружения (legacy, сохраняем для совместимости):
        #        T18FL3_QEMU_DEBUG=1      - подробные QEMU-логи, без VNC
        #        T18FL3_ANDROID_ONLY=1    - запуск только Android (без QNX-дисков)
        #        T18FL3_QNX_ONLY=1        - запуск только QNX (без Android system/vendor/product)
        debug_mode = os.environ.get("T18FL3_QEMU_DEBUG", "0") in ("1", "true", "True")

        # Значения по умолчанию: обе системы включены (максимально похожий режим)
        android_enabled = True
        qnx_enabled = True

        # Приоритет: GUI > переменные окружения
        try:
            if self.control_panel is not None:
                android_enabled = self.control_panel.android_checkbox.isChecked()
                qnx_enabled = self.control_panel.qnx_checkbox.isChecked()
        except Exception:
            # Fallback на окружение если по какой-то причине чекбоксы недоступны
            android_only_env = os.environ.get("T18FL3_ANDROID_ONLY", "0") in ("1", "true", "True")
            qnx_only_env = os.environ.get("T18FL3_QNX_ONLY", "0") in ("1", "true", "True")
            if android_only_env and not qnx_only_env:
                android_enabled, qnx_enabled = True, False
            elif qnx_only_env and not android_only_env:
                android_enabled, qnx_enabled = False, True
            elif qnx_only_env and android_only_env:
                self.logger.warning("Both ANDROID_ONLY and QNX_ONLY set; prioritizing QNX_ONLY")
                android_enabled, qnx_enabled = False, True
        
        # Проверяем, нужно ли использовать рабочее ядро
        # Переменная окружения T18FL3_USE_WORKING_KERNEL=1 включает режим с рабочим ядром
        use_working_kernel = os.environ.get("T18FL3_USE_WORKING_KERNEL", "0") in ("1", "true", "True")
        working_kernel_path = os.environ.get("T18FL3_WORKING_KERNEL_PATH")
        if working_kernel_path:
            working_kernel_path = Path(working_kernel_path)
        else:
            working_kernel_path = None
        
        # Проверяем, есть ли boot_virt.img (бутерброд) для virt
        # boot_virt.img = ядро из boot_android.img + адаптация для virt
        virt_boot_img = payload_dir / "boot_virt.img"
        boot_img_to_use = virt_boot_img if virt_boot_img.exists() else payload_dir / "boot.img"
        if virt_boot_img.exists():
            self.logger.info(f"✅ Используется boot_virt.img (бутерброд): {virt_boot_img}")
            self.logger.info(f"   Ядро из boot_android.img + оригинальные system/vendor/product.img")
        else:
            self.logger.info(f"⚠️  Используется оригинальный boot.img (может не работать с virt): {boot_img_to_use}")
        
        # Базовая конфигурация со всеми образами
        config = QEMUConfig(
            android_boot_img=boot_img_to_use,
            android_system_img=payload_dir / "system.img",
            android_vendor_img=payload_dir / "vendor.img",
            android_product_img=payload_dir / "product.img",
            android_dtb_img=payload_dir / "dtb.img",
            qnx_boot_img=payload_dir / "qnx_boot.img",
            qnx_system_img=payload_dir / "qnx_system.img",
            enable_qnx=qnx_enabled,
            enable_can=True,
            debug_mode=debug_mode,
            use_working_kernel=use_working_kernel,
            working_kernel_path=working_kernel_path,
        )
        
        if use_working_kernel:
            self.logger.info("🔧 WORKING KERNEL mode enabled - using stable kernel for app testing")

        # Применяем выбранные режимы
        if android_enabled and qnx_enabled:
            self.logger.info("Launch mode: ANDROID + QNX (both systems enabled)")
        elif android_enabled and not qnx_enabled:
            self.logger.info("Launch mode: ANDROID_ONLY (QNX disabled via GUI)")
            config.enable_qnx = False
            config.qnx_boot_img = None
            config.qnx_system_img = None
        elif qnx_enabled and not android_enabled:
            self.logger.info("Launch mode: QNX_ONLY (Android system/vendor/product disabled via GUI)")
            config.android_system_img = None
            config.android_vendor_img = None
            config.android_product_img = None
        else:
            # Если пользователь выключил обе галочки — логируем и не запускаем ничего
            self.logger.warning("Both Android and QNX are disabled in GUI; nothing to start")
            self.status_bar.showMessage("Both Android and QNX are disabled – enable at least one system", 10000)
            return
        
        self._setup_qemu(config)
        self._setup_can()
        
        # Подключаем CAN симулятор к элементам управления (для ручной отправки)
        self.vehicle_controls.set_can_simulator(self.can_simulator)
        self.developer_interface.set_can_simulator(self.can_simulator)
        self.developer_interface.set_qemu_manager(self.qemu_manager)
        
        # Запускаем QEMU
        self.logger.info("Starting QEMU")
        if self.qemu_manager.start():
            self.logger.info("QEMU started successfully")
            self.status_bar.showMessage("System starting...")
            
            # Запускаем VNC на дисплеях с задержкой, чтобы QEMU успел инициализироваться
            from PyQt6.QtCore import QTimer
            def start_vnc_delayed():
                self.logger.info("Starting VNC clients")
                self.display1.start_vnc('localhost', self.qemu_manager.config.display1_vnc)
                self.display2.start_vnc('localhost', self.qemu_manager.config.display1_vnc)
                self.logger.info("VNC clients started")
            QTimer.singleShot(3000, start_vnc_delayed)  # Задержка 3 секунды
        else:
            self.logger.error("QEMU start failed")
            self.status_bar.showMessage("Failed to start system", 5000)
    
    def _on_stop(self):
        """Обработчик выключения переключателя - остановка системы"""
        self.logger.info("Emulator toggle switched OFF - stopping system")
        
        if self.qemu_manager:
            self.qemu_manager.stop()
        
        # CAN симулятор останавливаем только если был запущен
        if self.can_simulator and self.can_simulator.running:
            self.can_simulator.stop()
        
        # Сбрасываем зажигание в OFF (через публичный метод кнопки START/STOP)
        try:
            if self.control_panel and hasattr(self.control_panel, "ignition"):
                self.control_panel.ignition.set_state_off()
        except Exception as e:
            self.logger.debug(f"Error while resetting ignition state: {e}")
        
        self.status_bar.showMessage("System stopped")
    
    def _on_ignition_state_changed(self, state: str):
        """Обработчик изменения состояния зажигания"""
        ignition_state = IgnitionState(state)
        self.logger.info(f"Ignition: {state}")
        
        if ignition_state == IgnitionState.IGN:
            self.logger.info("Ignition ON - checking Android status")
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(5000, self._check_android_status)
        elif ignition_state == IgnitionState.OFF:
            self.logger.info("Ignition OFF")
    
    def _check_android_status(self):
        """Проверить статус Android через ADB (только наш QEMU)"""
        import subprocess
        try:
            # Проверяем только наш T18FL3 QEMU по IP и serialno (ИЗОЛИРОВАННЫЙ ПОРТ)
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=2)
            # Фильтруем только наш T18FL3 QEMU (127.0.0.1:5556 или T18FL3EMU)
            # Используем порт 5556 чтобы не пересекаться с другими эмуляторами
            lines = result.stdout.split('\n')
            our_device = False
            for line in lines:
                if '127.0.0.1:5556' in line and 'device' in line:  # Изолированный порт T18FL3
                    our_device = True
                    break
                elif 'T18FL3EMU' in line and 'device' in line:
                    our_device = True
                    break
            
            if our_device:
                self.logger.info("Android: ADB accessible (T18FL3 QEMU)")
                self.status_bar.showMessage("Android running", 3000)
            else:
                if '127.0.0.1:5556' in result.stdout:
                    self.logger.warning("Android: T18FL3 QEMU found but ADB not ready")
                else:
                    self.logger.debug("Android: ADB not accessible (kernel may not be loaded)")
        except Exception as e:
            self.logger.debug(f"ADB check failed: {e}")
    
    # _on_reset убран - кнопка Reset удалена
    
    def _on_qemu_state_changed(self, state: QEMUState):
        """Обработчик изменения состояния QEMU"""
        self.logger.info(f"QEMU state: {state.value}")
        self.status_bar.showMessage(f"QEMU: {state.value}")
        
        # Обновляем панель управления
        self.control_panel.set_qemu_state(state)
    
    # Автодиагностика удалена по запросу пользователя
    # Методы _auto_diagnostics_cycle и _auto_restart больше не используются
    
    def _update_status(self):
        """Обновить статус"""
        if self.qemu_manager:
            state = self.qemu_manager.get_state()
            if state == QEMUState.RUNNING:
                if self.auto_mode:
                    self.status_bar.showMessage("Running (Auto Mode)")
                else:
                    self.status_bar.showMessage("Running")
            elif state == QEMUState.ERROR:
                self.status_bar.showMessage("Error", 5000)
    
    def _setup_log_viewer(self):
        """Настроить просмотр логов"""
        from core.log_manager import get_log_manager
        log_manager = get_log_manager()
        if log_manager and log_manager.log_file:
            self.log_viewer.set_log_file(log_manager.log_file)
            self.logger.info(f"Log viewer configured: {log_manager.log_file}")
    
    def _restore_window_state(self):
        """Восстановить состояние окна (геометрия и полноэкранный режим)"""
        try:
            # Восстанавливаем геометрию окна
            geometry = self.settings.value("window/geometry")
            if geometry:
                self.restoreGeometry(geometry)
                self.logger.info("  ✅ Геометрия окна восстановлена")
            else:
                # Значения по умолчанию, если нет сохраненных
                self.setGeometry(100, 100, 1920, 1200)
                self.logger.info("  ✅ Использована геометрия по умолчанию")
            
            # Восстанавливаем состояние окна (максимизация, полноэкранный режим)
            window_state = self.settings.value("window/state")
            if window_state:
                self.restoreState(window_state)
                self.logger.info("  ✅ Состояние окна восстановлено")
            
            # Восстанавливаем полноэкранный режим
            is_fullscreen = self.settings.value("window/fullscreen", False, type=bool)
            if is_fullscreen:
                self.showFullScreen()
                self.logger.info("  ✅ Полноэкранный режим восстановлен")
            else:
                self.showNormal()
                self.logger.info("  ✅ Оконный режим восстановлен")
                
        except Exception as e:
            self.logger.warning(f"  ⚠️ Ошибка восстановления состояния окна: {e}")
            # В случае ошибки используем значения по умолчанию
            self.setGeometry(100, 100, 1920, 1200)
            self.showNormal()
    
    def _save_window_state(self):
        """Сохранить состояние окна (геометрия и полноэкранный режим)"""
        try:
            # Сохраняем геометрию окна
            self.settings.setValue("window/geometry", self.saveGeometry())
            
            # Сохраняем состояние окна
            self.settings.setValue("window/state", self.saveState())
            
            # Сохраняем полноэкранный режим
            is_fullscreen = self.isFullScreen()
            self.settings.setValue("window/fullscreen", is_fullscreen)
            
            self.logger.debug(f"  Состояние окна сохранено (fullscreen: {is_fullscreen})")
        except Exception as e:
            self.logger.warning(f"  ⚠️ Ошибка сохранения состояния окна: {e}")
    
    def changeEvent(self, event):
        """Обработчик изменения состояния окна (для отслеживания полноэкранного режима)"""
        if event.type() == event.Type.WindowStateChange:
            # Сохраняем состояние при изменении (например, при переходе в полноэкранный режим)
            self._save_window_state()
        super().changeEvent(event)
    
    def moveEvent(self, event):
        """Обработчик перемещения окна"""
        # Сохраняем геометрию при перемещении
        self._save_window_state()
        super().moveEvent(event)
    
    def resizeEvent(self, event):
        """Обработчик изменения размера окна"""
        # Сохраняем геометрию при изменении размера
        self._save_window_state()
        super().resizeEvent(event)
    
    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        self.logger.info("Closing application")
        
        # Сохраняем состояние окна перед закрытием
        self._save_window_state()
        self.logger.info("  ✅ Состояние окна сохранено")
        
        # Останавливаем QEMU и связанные подсистемы
        self._on_stop()

        # Полностью завершаем приложение, чтобы не оставалось "висящих" процессов в Dock
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app is not None:
                app.quit()
        except Exception as e:
            self.logger.debug(f"Error during app.quit(): {e}")

        event.accept()

