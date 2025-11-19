"""
Developer Interface - Интерфейс разработчика
Для просмотра логов, эмуляции действий и событий
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QTextEdit, QLineEdit, QLabel,
    QGroupBox, QSpinBox, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QTreeWidget, QTreeWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import json
from pathlib import Path
from datetime import datetime

from core.log_manager import get_log_manager, get_logger
from core.can_simulator import CANSimulator
from core.qemu_manager import QEMUManager


class LogAnalyzer(QWidget):
    """Анализатор логов"""
    
    def __init__(self):
        super().__init__()
        self.log_manager = get_log_manager()
        self._setup_ui()
        self._setup_timer()
    
    def _setup_ui(self):
        """Настроить UI"""
        layout = QVBoxLayout()
        
        # Фильтры
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Фильтр:"))
        
        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALL", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"])
        filter_layout.addWidget(self.level_combo)
        
        self.source_combo = QComboBox()
        self.source_combo.addItems(["ALL", "qemu", "can", "process", "system", "image"])
        filter_layout.addWidget(self.source_combo)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск...")
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Таблица логов
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(5)
        self.log_table.setHorizontalHeaderLabels(["Время", "Уровень", "Источник", "Модуль", "Сообщение"])
        self.log_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.log_table.setAlternatingRowColors(True)
        layout.addWidget(self.log_table)
        
        # Статистика
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("Всего: 0 | DEBUG: 0 | INFO: 0 | WARN: 0 | ERROR: 0")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        self.setLayout(layout)
    
    def _setup_timer(self):
        """Настроить таймер для обновления"""
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_logs)
        self.timer.start(500)  # Каждые 500ms
    
    def _update_logs(self):
        """Обновить логи"""
        # Читаем JSON лог файл
        log_file = self.log_manager.get_log_file()
        if not log_file:
            return
        
        # Ищем JSON лог файл
        json_log_file = log_file.parent / log_file.name.replace(".log", ".jsonl")
        if not json_log_file.exists():
            # Если JSON лог не найден, пробуем парсить текстовый лог
            self._update_logs_from_text(log_file)
            return
        
        try:
            with open(json_log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                # Берем последние 1000 строк и разворачиваем, чтобы новые были сверху
                lines = lines[-1000:]
                lines = list(reversed(lines))
                
                self.log_table.setRowCount(len(lines))
                
                # Статистика
                stats = {"DEBUG": 0, "INFO": 0, "WARN": 0, "ERROR": 0, "CRITICAL": 0}
                
                for i, line in enumerate(lines):
                    try:
                        log_entry = json.loads(line.strip())
                        self._add_log_row(i, log_entry)
                        # Подсчитываем статистику
                        level = log_entry.get("level", "INFO")
                        if level in stats:
                            stats[level] += 1
                    except:
                        pass
                
                # Обновляем статистику
                total = len(lines)
                self.stats_label.setText(
                    f"Всего: {total} | DEBUG: {stats['DEBUG']} | INFO: {stats['INFO']} | "
                    f"WARN: {stats['WARN']} | ERROR: {stats['ERROR']}"
                )
        except:
            pass
    
    def _add_log_row(self, row: int, entry: dict):
        """Добавить строку лога"""
        # Время
        time_item = QTableWidgetItem(entry.get("timestamp", "")[:19])
        self.log_table.setItem(row, 0, time_item)
        
        # Уровень
        level = entry.get("level", "INFO")
        level_item = QTableWidgetItem(level)
        level_color = {
            "DEBUG": QColor(128, 128, 128),
            "INFO": QColor(255, 255, 255),
            "WARN": QColor(255, 255, 0),
            "ERROR": QColor(255, 0, 0),
            "CRITICAL": QColor(255, 0, 255)
        }.get(level, QColor(255, 255, 255))
        level_item.setForeground(level_color)
        self.log_table.setItem(row, 1, level_item)
        
        # Источник
        source = entry.get("source", entry.get("extra", {}).get("source", "system"))
        self.log_table.setItem(row, 2, QTableWidgetItem(source))
        
        # Модуль
        module = entry.get("module", entry.get("extra", {}).get("module", ""))
        self.log_table.setItem(row, 3, QTableWidgetItem(module))
        
        # Сообщение
        message = entry.get("message", "")
        self.log_table.setItem(row, 4, QTableWidgetItem(message))
    
    def _update_logs_from_text(self, log_file: Path):
        """Обновить логи из текстового файла (fallback)"""
        import re
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                # Берем последние 1000 строк
                lines = lines[-1000:]
                
                # Парсим формат: [2024-11-16 04:52:00.123] [INFO    ] [module:function:line] message
                pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\] \[(\w+)\s*\] \[([^\]]+)\] (.+)'
                
                parsed_logs = []
                for line in lines:
                    match = re.match(pattern, line.strip())
                    if match:
                        timestamp, level, module_info, message = match.groups()
                        # Парсим module:function:line
                        module_parts = module_info.split(':')
                        module = module_parts[0] if module_parts else ""
                        source = "system"
                        if "qemu" in message.lower():
                            source = "qemu"
                        elif "can" in message.lower():
                            source = "can"
                        
                        parsed_logs.append({
                            "timestamp": timestamp,
                            "level": level,
                            "source": source,
                            "module": module,
                            "message": message
                        })
                
                if parsed_logs:
                    # Разворачиваем, чтобы новые записи были сверху
                    parsed_logs = list(reversed(parsed_logs))

                    self.log_table.setRowCount(len(parsed_logs))
                    
                    # Статистика
                    stats = {"DEBUG": 0, "INFO": 0, "WARN": 0, "ERROR": 0, "CRITICAL": 0}
                    
                    for i, entry in enumerate(parsed_logs):
                        self._add_log_row(i, entry)
                        # Подсчитываем статистику
                        level = entry.get("level", "INFO")
                        if level in stats:
                            stats[level] += 1
                    
                    # Обновляем статистику
                    total = len(parsed_logs)
                    self.stats_label.setText(
                        f"Всего: {total} | DEBUG: {stats['DEBUG']} | INFO: {stats['INFO']} | "
                        f"WARN: {stats['WARN']} | ERROR: {stats['ERROR']}"
                    )
        except Exception as e:
            pass  # Игнорируем ошибки


class CANMessageInjector(QWidget):
    """Инжектор CAN сообщений"""
    
    message_sent = pyqtSignal(int, bytes)
    
    def __init__(self, can_simulator: CANSimulator = None):
        super().__init__()
        self.can_simulator = can_simulator
        self.logger = get_logger("can_injector")
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить UI"""
        layout = QVBoxLayout()
        
        # Быстрые сообщения
        quick_group = QGroupBox("Быстрые сообщения")
        quick_layout = QVBoxLayout()
        
        # Скорость
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Скорость (km/h):"))
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(0, 200)
        speed_layout.addWidget(self.speed_spin)
        speed_btn = QPushButton("Отправить")
        speed_btn.clicked.connect(self._send_speed)
        speed_layout.addWidget(speed_btn)
        quick_layout.addLayout(speed_layout)
        
        # Обороты
        rpm_layout = QHBoxLayout()
        rpm_layout.addWidget(QLabel("RPM:"))
        self.rpm_spin = QSpinBox()
        self.rpm_spin.setRange(0, 8000)
        rpm_layout.addWidget(self.rpm_spin)
        rpm_btn = QPushButton("Отправить")
        rpm_btn.clicked.connect(self._send_rpm)
        rpm_layout.addWidget(rpm_btn)
        quick_layout.addLayout(rpm_layout)
        
        quick_group.setLayout(quick_layout)
        layout.addWidget(quick_group)
        
        # Кастомное сообщение
        custom_group = QGroupBox("Кастомное CAN сообщение")
        custom_layout = QVBoxLayout()
        
        # CAN ID
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("CAN ID (hex):"))
        self.can_id_input = QLineEdit()
        self.can_id_input.setPlaceholderText("0x100")
        id_layout.addWidget(self.can_id_input)
        custom_layout.addLayout(id_layout)
        
        # Данные
        data_layout = QHBoxLayout()
        data_layout.addWidget(QLabel("Data (hex):"))
        self.can_data_input = QLineEdit()
        self.can_data_input.setPlaceholderText("0000")
        data_layout.addWidget(self.can_data_input)
        custom_layout.addLayout(data_layout)
        
        send_btn = QPushButton("Отправить сообщение")
        send_btn.clicked.connect(self._send_custom)
        custom_layout.addWidget(send_btn)
        
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)
        
        # История сообщений
        history_group = QGroupBox("История сообщений")
        history_layout = QVBoxLayout()
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Время", "CAN ID", "Data", "Направление"])
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        history_layout.addWidget(self.history_table)
        
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _send_speed(self):
        """Отправить сообщение о скорости"""
        speed = self.speed_spin.value()
        if self.can_simulator:
            import struct
            data = struct.pack('<H', speed * 10)
            self.can_simulator.send_event_message(0x100, data)
            self._add_to_history(0x100, data, "TX")
            self.logger.info(f"Speed message sent: {speed} km/h")
    
    def _send_rpm(self):
        """Отправить сообщение об оборотах"""
        rpm = self.rpm_spin.value()
        if self.can_simulator:
            import struct
            data = struct.pack('<H', rpm)
            self.can_simulator.send_event_message(0x101, data)
            self._add_to_history(0x101, data, "TX")
            self.logger.info(f"RPM message sent: {rpm}")
    
    def _send_custom(self):
        """Отправить кастомное сообщение"""
        try:
            can_id = int(self.can_id_input.text(), 16)
            data_hex = self.can_data_input.text().replace(" ", "")
            data = bytes.fromhex(data_hex)
            
            if self.can_simulator:
                self.can_simulator.send_event_message(can_id, data)
                self._add_to_history(can_id, data, "TX")
                self.logger.info(f"Custom CAN message sent: ID=0x{can_id:x}, Data={data.hex()}")
        except Exception as e:
            self.logger.error(f"Error sending custom message: {e}")
    
    def _add_to_history(self, can_id: int, data: bytes, direction: str):
        """Добавить в историю"""
        row = self.history_table.rowCount()
        self.history_table.insertRow(row)
        
        # Время
        time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.history_table.setItem(row, 0, QTableWidgetItem(time_str))
        
        # CAN ID
        self.history_table.setItem(row, 1, QTableWidgetItem(f"0x{can_id:x}"))
        
        # Data
        self.history_table.setItem(row, 2, QTableWidgetItem(data.hex().upper()))
        
        # Направление
        self.history_table.setItem(row, 3, QTableWidgetItem(direction))
        
        # Автопрокрутка
        self.history_table.scrollToBottom()
    
    def set_can_simulator(self, simulator: CANSimulator):
        """Установить CAN симулятор"""
        self.can_simulator = simulator


class SystemEvents(QWidget):
    """Эмулятор системных событий и управление модулями"""
    
    def __init__(self, qemu_manager: QEMUManager = None):
        super().__init__()
        self.qemu_manager = qemu_manager
        self.logger = get_logger("system_events")
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить UI"""
        layout = QVBoxLayout()
        
        # События загрузки
        boot_group = QGroupBox("События загрузки")
        boot_layout = QVBoxLayout()
        
        reboot_btn = QPushButton("Перезагрузка")
        reboot_btn.clicked.connect(self._on_reboot)
        boot_layout.addWidget(reboot_btn)
        
        shutdown_btn = QPushButton("Выключение")
        shutdown_btn.clicked.connect(self._on_shutdown)
        boot_layout.addWidget(shutdown_btn)
        
        boot_group.setLayout(boot_layout)
        layout.addWidget(boot_group)
        
        # Системные события
        events_group = QGroupBox("Системные события")
        events_layout = QVBoxLayout()
        
        low_memory_btn = QPushButton("Эмуляция нехватки памяти")
        low_memory_btn.clicked.connect(self._on_low_memory)
        events_layout.addWidget(low_memory_btn)
        
        high_cpu_btn = QPushButton("Эмуляция высокой нагрузки CPU")
        high_cpu_btn.clicked.connect(self._on_high_cpu)
        events_layout.addWidget(high_cpu_btn)
        
        events_group.setLayout(events_layout)
        layout.addWidget(events_group)
        
        # Hot Reload модулей
        reload_group = QGroupBox("🔄 Hot Reload модулей")
        reload_layout = QVBoxLayout()
        
        reload_btn = QPushButton("Перезагрузить модули (очистить кэш)")
        reload_btn.clicked.connect(self._on_reload_modules)
        reload_btn.setToolTip("Очищает кэш Python и перезагружает модули без перезапуска GUI")
        reload_layout.addWidget(reload_btn)
        
        reload_group.setLayout(reload_layout)
        layout.addWidget(reload_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _on_reboot(self):
        """Обработчик перезагрузки"""
        self.logger.info("Reboot event triggered")
        # TODO: Отправить команду перезагрузки в QEMU
    
    def _on_shutdown(self):
        """Обработчик выключения"""
        self.logger.info("Shutdown event triggered")
        # TODO: Отправить команду выключения в QEMU
    
    def _on_low_memory(self):
        """Обработчик нехватки памяти"""
        self.logger.warn("Low memory event triggered")
        # TODO: Эмуляция нехватки памяти
    
    def _on_high_cpu(self):
        """Обработчик высокой нагрузки CPU"""
        self.logger.warn("High CPU event triggered")
        # TODO: Эмуляция высокой нагрузки
    
    def _on_reload_modules(self):
        """Обработчик перезагрузки модулей"""
        try:
            from core.hot_reload import reload_all_emulator_modules
            
            self.logger.info("🔄 Hot reload модулей...")
            result = reload_all_emulator_modules()
            
            self.logger.info(
                f"✅ Модули перезагружены: "
                f"кэш очищен ({result['cache_cleared']} элементов), "
                f"core ({result['core']} модулей), "
                f"gui ({result['gui']} модулей)"
            )
            
            # Показываем сообщение пользователю
            msg = QMessageBox(self)
            msg.setWindowTitle("Hot Reload")
            msg.setText(
                f"✅ Модули перезагружены!\n\n"
                f"Очищено кэша: {result['cache_cleared']}\n"
                f"Перезагружено core: {result['core']}\n"
                f"Перезагружено gui: {result['gui']}"
            )
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
            
        except Exception as e:
            self.logger.error(f"Ошибка при перезагрузке модулей: {e}")
            msg = QMessageBox(self)
            msg.setWindowTitle("Ошибка Hot Reload")
            msg.setText(f"❌ Ошибка при перезагрузке модулей:\n{str(e)}")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.exec()


class DeveloperInterface(QWidget):
    """Интерфейс разработчика"""
    
    def __init__(self, can_simulator: CANSimulator = None, qemu_manager: QEMUManager = None):
        super().__init__()
        self._setup_ui(can_simulator, qemu_manager)
    
    def _setup_ui(self, can_simulator: CANSimulator, qemu_manager: QEMUManager):
        """Настроить UI"""
        layout = QVBoxLayout()
        
        # Вкладки
        tabs = QTabWidget()
        
        # Анализатор логов
        self.log_analyzer = LogAnalyzer()
        tabs.addTab(self.log_analyzer, "📊 Анализ логов")
        
        # Инжектор CAN сообщений
        self.can_injector = CANMessageInjector(can_simulator)
        tabs.addTab(self.can_injector, "🔌 CAN Injector")
        
        # Системные события
        self.system_events = SystemEvents(qemu_manager)
        tabs.addTab(self.system_events, "⚡ Системные события")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
    
    def set_can_simulator(self, simulator: CANSimulator):
        """Установить CAN симулятор"""
        self.can_injector.set_can_simulator(simulator)
    
    def set_qemu_manager(self, manager: QEMUManager):
        """Установить QEMU менеджер"""
        self.system_events.qemu_manager = manager

