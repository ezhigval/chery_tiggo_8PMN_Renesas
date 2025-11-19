"""
Control Panel - Панель управления эмулятором
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QSpinBox, QGroupBox, QCheckBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QFont

from core.qemu_manager import QEMUState
from core.can_simulator import CANSimulator
from gui.vehicle_controls import IgnitionControl
from gui.steering_buttons_compact import SteeringButtonsCompact


class ControlPanel(QWidget):
    """Панель управления эмулятором"""
    
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    # reset_clicked убран - кнопка Reset удалена
    
    def __init__(self):
        super().__init__()
        self.can_simulator: CANSimulator = None
        self.qemu_state = QEMUState.STOPPED
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить UI"""
        layout = QHBoxLayout(self)
        
        # Группа: Управление
        control_group = QGroupBox("Control")
        control_layout = QVBoxLayout()
        
        # Ползунок-переключатель Start/Stop с анимированным кружочком
        toggle_layout = QHBoxLayout()
        toggle_layout.addWidget(QLabel("Эмулятор:"))
        
        # Создаем кастомный виджет для toggle switch
        self.toggle_widget = QWidget()
        self.toggle_widget.setFixedSize(80, 40)
        self.toggle_widget.setStyleSheet("""
            QWidget {
                background-color: #f44336;
                border-radius: 20px;
                border: 2px solid #d32f2f;
            }
        """)
        
        # Кружочек внутри
        self.toggle_circle = QWidget(self.toggle_widget)
        self.toggle_circle.setFixedSize(32, 32)
        self.toggle_circle.move(4, 4)  # Слева (OFF)
        self.toggle_circle.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 16px;
                border: 2px solid #ccc;
            }
        """)
        
        # Анимация для кружочка
        self.toggle_animation = QPropertyAnimation(self.toggle_circle, b"pos")
        self.toggle_animation.setDuration(200)  # 200ms анимация
        self.toggle_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Делаем виджет кликабельным
        self.toggle_widget.mousePressEvent = self._on_toggle_clicked
        
        toggle_layout.addWidget(self.toggle_widget)
        
        # Текст состояния справа от переключателя
        self.toggle_label = QLabel("OFF")
        self.toggle_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 14px;
                font-weight: bold;
                padding: 0 10px;
            }
        """)
        toggle_layout.addWidget(self.toggle_label)
        toggle_layout.addStretch()
        
        # Внутреннее состояние (для отслеживания)
        self._toggle_state = False  # False = OFF, True = ON
        
        control_layout.addLayout(toggle_layout)

        # Чекбоксы режимов запуска систем
        modes_group = QGroupBox("Системы")
        modes_layout = QVBoxLayout()

        # По умолчанию запускаем обе системы (Android + QNX)
        self.android_checkbox = QCheckBox("Android")
        self.android_checkbox.setChecked(True)
        self.android_checkbox.setToolTip("Запускать Android subsystem (system/vendor/product.img)")
        modes_layout.addWidget(self.android_checkbox)

        self.qnx_checkbox = QCheckBox("QNX")
        self.qnx_checkbox.setChecked(False)  # По умолчанию выключен - фокус на Android
        self.qnx_checkbox.setToolTip("Запускать QNX subsystem (qnx_boot.img/qnx_system.img)")
        modes_layout.addWidget(self.qnx_checkbox)

        modes_group.setLayout(modes_layout)
        control_layout.addWidget(modes_group)
        
        # Кнопка Refresh для перезагрузки модулей
        self.refresh_btn = QPushButton("🔄 Перезагрузить модули")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.refresh_btn.setToolTip("Очищает кэш Python и перезагружает модули без перезапуска GUI")
        self.refresh_btn.clicked.connect(self._on_refresh)
        control_layout.addWidget(self.refresh_btn)
        
        # Кнопка Reset убрана по запросу пользователя
        
        control_group.setLayout(control_layout)

        # Размещаем плитку Control, большую кнопку зажигания и компактные кнопки руля в один ряд
        layout.addWidget(control_group)

        self.ignition = IgnitionControl()
        layout.addWidget(self.ignition)

        self.steering_compact = SteeringButtonsCompact()
        layout.addWidget(self.steering_compact)

        layout.addStretch()
    
    def _on_toggle_clicked(self, event):
        """Обработчик клика по toggle switch"""
        # Переключаем состояние
        new_state = not self._toggle_state
        self._set_toggle_state(new_state, animate=True)
        
        # Отправляем сигнал (кружочек уже переехал, цвет изменится когда система реально запустится/остановится)
        if new_state:
            self.start_clicked.emit()
        else:
            self.stop_clicked.emit()
    
    def _set_toggle_state(self, state: bool, animate: bool = True):
        """Установить состояние toggle switch (кружочек переезжает сразу)"""
        self._toggle_state = state
        
        if animate:
            # Анимируем перемещение кружочка
            if state:
                # ON - кружочек справа
                self.toggle_animation.setStartValue(QPoint(4, 4))
                self.toggle_animation.setEndValue(QPoint(44, 4))
            else:
                # OFF - кружочек слева
                self.toggle_animation.setStartValue(QPoint(44, 4))
                self.toggle_animation.setEndValue(QPoint(4, 4))
            self.toggle_animation.start()
        else:
            # Без анимации (для программного изменения)
            if state:
                self.toggle_circle.move(44, 4)
            else:
                self.toggle_circle.move(4, 4)
        
        # Обновляем текст справа от переключателя
        self.toggle_label.setText("ON" if state else "OFF")
    
    def _update_toggle_color(self, state: QEMUState):
        """Обновить цвет toggle switch в зависимости от реального состояния системы"""
        # Проверяем, что toggle_widget существует (может быть не инициализирован при первом вызове)
        if not hasattr(self, 'toggle_widget') or self.toggle_widget is None:
            return
        
        # Цвет меняется только когда система реально запустилась/остановилась
        if state == QEMUState.RUNNING:
            # Система запущена - зеленый
            self.toggle_widget.setStyleSheet("""
                QWidget {
                    background-color: #4CAF50;
                    border-radius: 20px;
                    border: 2px solid #388e3c;
                }
            """)
        elif state == QEMUState.STOPPED:
            # Система остановлена - красный
            self.toggle_widget.setStyleSheet("""
                QWidget {
                    background-color: #f44336;
                    border-radius: 20px;
                    border: 2px solid #d32f2f;
                }
            """)
        elif state == QEMUState.STARTING:
            # Система запускается - синий
            self.toggle_widget.setStyleSheet("""
                QWidget {
                    background-color: #2196F3;
                    border-radius: 20px;
                    border: 2px solid #1976d2;
                }
            """)
        elif state == QEMUState.ERROR:
            # Ошибка - оранжевый
            self.toggle_widget.setStyleSheet("""
                QWidget {
                    background-color: #ff9800;
                    border-radius: 20px;
                    border: 2px solid #f57c00;
                }
            """)
    
    def _on_refresh(self):
        """Обработчик кнопки Refresh - перезагрузка модулей"""
        import importlib
        import sys
        from pathlib import Path
        import shutil
        import traceback
        
        try:
            self.refresh_btn.setEnabled(False)
            self.refresh_btn.setText("🔄 Перезагрузка...")
            
            # Принудительно обновляем UI
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
            
            # Очищаем кэш
            cache_cleared = 0
            # __file__ = gui/control_panel.py, parent.parent = development/emulator
            emulator_dir = Path(__file__).resolve().parent.parent
            
            if not emulator_dir.exists():
                raise Exception(f"Директория эмулятора не найдена: {emulator_dir}")
            
            # Очищаем логи
            logs_cleared = 0
            logs_dir = emulator_dir / "logs"
            if logs_dir.exists():
                # Удаляем все .log и .jsonl файлы
                for log_file in logs_dir.glob("*.log"):
                    try:
                        log_file.unlink()
                        logs_cleared += 1
                    except Exception as ex:
                        print(f"Ошибка удаления {log_file}: {ex}")
                
                for jsonl_file in logs_dir.glob("*.jsonl"):
                    try:
                        jsonl_file.unlink()
                        logs_cleared += 1
                    except Exception as ex:
                        print(f"Ошибка удаления {jsonl_file}: {ex}")
            
            for cache_dir in emulator_dir.rglob('__pycache__'):
                try:
                    if cache_dir.exists():
                        shutil.rmtree(cache_dir)
                        cache_cleared += 1
                except Exception as ex:
                    print(f"Ошибка удаления {cache_dir}: {ex}")
            
            for pyc_file in emulator_dir.rglob('*.pyc'):
                try:
                    if pyc_file.exists():
                        pyc_file.unlink()
                        cache_cleared += 1
                except Exception as ex:
                    print(f"Ошибка удаления {pyc_file}: {ex}")
            
            # Перезагружаем модули
            reloaded_core = 0
            reloaded_gui = 0
            
            # Сортируем модули по зависимостям (сначала core, потом gui)
            modules_to_reload = []
            for module_name in list(sys.modules.keys()):
                if module_name.startswith('core.') or module_name.startswith('gui.'):
                    modules_to_reload.append(module_name)
            
            # Сортируем: сначала core, потом gui
            modules_to_reload.sort(key=lambda x: (0 if x.startswith('core.') else 1, x))
            
            for module_name in modules_to_reload:
                try:
                    if module_name in sys.modules:
                        importlib.reload(sys.modules[module_name])
                        if module_name.startswith('core.'):
                            reloaded_core += 1
                        elif module_name.startswith('gui.'):
                            reloaded_gui += 1
                except Exception as ex:
                    print(f"Ошибка перезагрузки {module_name}: {ex}")
            
            result = {
                "cache_cleared": cache_cleared,
                "logs_cleared": logs_cleared,
                "core": reloaded_core,
                "gui": reloaded_gui
            }
            
            self.refresh_btn.setText("🔄 Перезагрузить модули")
            self.refresh_btn.setEnabled(True)
            
            # Показываем сообщение
            msg = QMessageBox(self)
            msg.setWindowTitle("Hot Reload")
            msg.setText(
                f"✅ Модули перезагружены!\n\n"
                f"Очищено кэша: {result['cache_cleared']}\n"
                f"Очищено логов: {result['logs_cleared']}\n"
                f"Перезагружено core: {result['core']}\n"
                f"Перезагружено gui: {result['gui']}"
            )
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
            
        except Exception as e:
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            print(f"Ошибка в _on_refresh: {error_msg}")
            
            self.refresh_btn.setText("🔄 Перезагрузить модули")
            self.refresh_btn.setEnabled(True)
            
            msg = QMessageBox(self)
            msg.setWindowTitle("Ошибка Hot Reload")
            msg.setText(f"❌ Ошибка при перезагрузке модулей:\n{str(e)}")
            msg.setDetailedText(traceback.format_exc())
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.exec()
    
    def set_can_simulator(self, simulator: CANSimulator):
        """Установить CAN симулятор"""
        self.can_simulator = simulator
    
    def set_qemu_state(self, state: QEMUState):
        """Установить состояние QEMU (обновляет цвет, но не двигает кружочек)"""
        self.qemu_state = state
        
        # Проверяем, что toggle_widget инициализирован
        if not hasattr(self, 'toggle_widget') or self.toggle_widget is None:
            return
        
        # Обновляем цвет в зависимости от реального состояния системы
        self._update_toggle_color(state)
        
        # Обновляем текст справа от переключателя
        if state == QEMUState.RUNNING:
            self.toggle_label.setText("ON")
            # Система запущена - кружочек должен быть справа (ON)
            if not self._toggle_state:
                self._set_toggle_state(True, animate=False)
        elif state == QEMUState.STOPPED:
            self.toggle_label.setText("OFF")
            # Система остановлена - кружочек должен быть слева (OFF)
            if self._toggle_state:
                self._set_toggle_state(False, animate=False)
        elif state == QEMUState.STARTING:
            self.toggle_label.setText("STARTING")
        elif state == QEMUState.ERROR:
            self.toggle_label.setText("ERROR")
    
    def _on_speed_changed(self, value: int):
        """Обработчик изменения скорости"""
        if self.can_simulator:
            self.can_simulator.set_vehicle_state(speed=float(value))
    
    def _on_rpm_changed(self, value: int):
        """Обработчик изменения оборотов"""
        if self.can_simulator:
            self.can_simulator.set_vehicle_state(rpm=value)
    
    def _on_temp_changed(self, value: int):
        """Обработчик изменения температуры"""
        if self.can_simulator:
            self.can_simulator.set_vehicle_state(engine_temp=value)
