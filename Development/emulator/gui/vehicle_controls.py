"""
Vehicle Controls - Физические элементы управления автомобилем
Кнопки зажигания, магнитолы, руля и т.д.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGroupBox, QLabel, QSlider, QSpinBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon

from core.can_simulator import CANSimulator
from core.log_manager import get_logger
from core.ignition_states import IgnitionState


class IgnitionControl(QGroupBox):
    """Управление зажиганием через большую круглую кнопку с 4 состояниями"""
    
    ignition_changed = pyqtSignal(str)  # Состояние зажигания: "off", "acc", "ign", "start"
    
    def __init__(self):
        super().__init__("Зажигание")
        self.logger = get_logger("ignition_control")
        self.current_state = IgnitionState.OFF
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить UI"""
        layout = QVBoxLayout()

        # Большая круглая кнопка зажигания
        self.ignition_button = QPushButton("START/STOP")
        self.ignition_button.setCheckable(True)
        self.ignition_button.setFixedSize(120, 120)
        self.ignition_button.setStyleSheet("""
            QPushButton {
                background-color: qradialgradient(cx:0.5, cy:0.5, radius:0.7,
                    fx:0.5, fy:0.5,
                    stop:0 #fafafa, stop:0.6 #e0e0e0, stop:1 #9e9e9e);
                color: #212121;
                border-radius: 60px;
                border: 4px solid #616161;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: qradialgradient(cx:0.5, cy:0.5, radius:0.7,
                    fx:0.5, fy:0.5,
                    stop:0 #e0e0e0, stop:0.6 #bdbdbd, stop:1 #757575);
            }
        """)
        self.ignition_button.clicked.connect(self._on_button_clicked)
        layout.addWidget(self.ignition_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Подписи состояний под кнопкой
        labels_layout = QHBoxLayout()
        for text in ["OFF", "ACC", "IGN", "START"]:
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size: 11px;")
            labels_layout.addWidget(lbl)
        layout.addLayout(labels_layout)

        # Статус
        self.status_label = QLabel("Двигатель: ВЫКЛ")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def _on_button_clicked(self):
        """Обработчик нажатия большой кнопки зажигания
        
        Логика близка к реальному автомобилю:
          - если зажигание выключено (OFF) — короткое нажатие включает ACC;
          - из ACC одно нажатие переводит в IGN;
          - если зажигание уже включено (IGN или START) — нажатие отключает
            автомобиль обратно в OFF.
        """
        # Переходы состояний в стиле кнопки START/STOP
        if self.current_state == IgnitionState.OFF:
            new_state = IgnitionState.ACC
        elif self.current_state == IgnitionState.ACC:
            new_state = IgnitionState.IGN
        else:
            # Если зажигание уже включено (IGN или START) — выключаем в OFF
            new_state = IgnitionState.OFF

        self._apply_state(new_state)

        # START остаётся кратковременным состоянием и автоматически
        # устанавливается из CAN‑логики/двигателя при необходимости.

    def _apply_state(self, new_state: IgnitionState):
        """Применить новое состояние и обновить визуал"""
        self.current_state = new_state

        status_map = {
            IgnitionState.OFF: "Двигатель: ВЫКЛ",
            IgnitionState.ACC: "Питание: ACC",
            IgnitionState.IGN: "Зажигание: ВКЛ",
            IgnitionState.START: "Запуск двигателя..."
        }
        self.status_label.setText(status_map[new_state])

        # Цвет обводки/фона в зависимости от состояния
        if new_state == IgnitionState.OFF:
            border = "#616161"
            glow = "#9e9e9e"
        elif new_state == IgnitionState.ACC:
            border = "#ff9800"
            glow = "#ffb74d"
        elif new_state == IgnitionState.IGN:
            border = "#4CAF50"
            glow = "#81C784"
        else:  # START
            border = "#2196F3"
            glow = "#64B5F6"

        self.ignition_button.setStyleSheet(f"""
            QPushButton {{
                background-color: qradialgradient(cx:0.5, cy:0.5, radius:0.7,
                    fx:0.5, fy:0.5,
                    stop:0 #fafafa, stop:0.6 {glow}, stop:1 #757575);
                color: #212121;
                border-radius: 60px;
                border: 4px solid {border};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:pressed {{
                background-color: qradialgradient(cx:0.5, cy:0.5, radius:0.7,
                    fx:0.5, fy:0.5,
                    stop:0 #e0e0e0, stop:0.6 #bdbdbd, stop:1 #616161);
            }}
        """)

        self.logger.info(f"Ignition state changed: {new_state.value}")
        self.ignition_changed.emit(new_state.value)

    def set_state_off(self):
        """Публичный метод для принудительного перевода зажигания в OFF."""
        self._apply_state(IgnitionState.OFF)


class RadioControls(QGroupBox):
    """Управление магнитолой"""
    
    volume_changed = pyqtSignal(int)  # 0-100
    power_changed = pyqtSignal(bool)   # True = включено
    nav_button_clicked = pyqtSignal()
    settings_button_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__("Магнитола")
        self.logger = get_logger("radio_controls")
        self.power_on = False
        self.volume = 50
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить UI"""
        layout = QVBoxLayout()

        # Кнопки управления в один ряд
        top_row = QHBoxLayout()

        self.power_btn = QPushButton("⚫ ВЫКЛ")
        self.power_btn.setCheckable(True)
        self.power_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:checked {
                background-color: #4CAF50;
            }
        """)
        self.power_btn.clicked.connect(self._on_power_toggle)
        top_row.addWidget(self.power_btn)

        self.nav_btn = QPushButton("🗺️ Навигация")
        self.nav_btn.clicked.connect(self._on_nav_clicked)
        self.nav_btn.setEnabled(False)
        top_row.addWidget(self.nav_btn)

        self.settings_btn = QPushButton("⚙️ Настройки")
        self.settings_btn.clicked.connect(self._on_settings_clicked)
        self.settings_btn.setEnabled(False)
        top_row.addWidget(self.settings_btn)

        layout.addLayout(top_row)

        # Громкость – полоска под рядом кнопок
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("🔊 Громкость:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        volume_layout.addWidget(self.volume_slider)
        self.volume_label = QLabel("50")
        self.volume_label.setMinimumWidth(30)
        volume_layout.addWidget(self.volume_label)
        layout.addLayout(volume_layout)
        
        self.setLayout(layout)
    
    def _on_power_toggle(self, checked: bool):
        """Обработчик кнопки питания ГУ - только перезагрузка нативно"""
        # Кнопка питания ГУ только перезагружает его нативно
        # ГУ включается автоматически при появлении зажигания (IGN)
        if checked:
            self.logger.info("Head Unit reboot requested (native reboot)")
            # Эмитируем сигнал перезагрузки
            self.power_changed.emit(True)
            # Возвращаем кнопку в исходное состояние (не остается нажатой)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self.power_btn.setChecked(False))
        else:
            self.logger.debug("Head Unit power button released")
    
    def _on_volume_changed(self, value: int):
        """Обработчик изменения громкости"""
        self.volume = value
        self.volume_label.setText(str(value))
        self.logger.debug(f"Volume changed: {value}")
        self.volume_changed.emit(value)
    
    def _on_nav_clicked(self):
        """Обработчик кнопки навигации"""
        self.logger.info("Navigation button clicked")
        self.nav_button_clicked.emit()
    
    def _on_settings_clicked(self):
        """Обработчик кнопки настроек"""
        self.logger.info("Settings button clicked")
        self.settings_button_clicked.emit()


class SteeringWheelControls(QGroupBox):
    """Кнопки на руле"""
    
    button_clicked = pyqtSignal(str)  # "left", "right", "up", "down", "ok"
    
    def __init__(self):
        super().__init__("Руль")
        self.logger = get_logger("steering_controls")
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить UI"""
        layout = QVBoxLayout()

        # Ряд кнопок поменьше в один ряд: ◄ ▲ OK ▼ ►
        buttons_layout = QHBoxLayout()

        left_btn = QPushButton("◄")
        up_btn = QPushButton("▲")
        ok_btn = QPushButton("OK")
        down_btn = QPushButton("▼")
        right_btn = QPushButton("►")

        for btn, name in [
            (left_btn, "left"),
            (up_btn, "up"),
            (ok_btn, "ok"),
            (down_btn, "down"),
            (right_btn, "right"),
        ]:
            btn.setFixedSize(48, 32)
            if name == "ok":
                btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
            btn.clicked.connect(lambda _, n=name: self._on_button(n))
            buttons_layout.addWidget(btn)

        layout.addLayout(buttons_layout)

        # Стили для всех кнопок
        button_style = """
            QPushButton {
                background-color: #424242;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:pressed {
                background-color: #616161;
            }
        """
        for btn in [up_btn, down_btn, left_btn, right_btn, ok_btn]:
            btn.setStyleSheet(button_style)
        
        self.setLayout(layout)
    
    def _on_button(self, button: str):
        """Обработчик нажатия кнопки"""
        self.logger.info(f"Steering wheel button: {button}")
        self.button_clicked.emit(button)


class VehicleControls(QWidget):
    """Объединенный виджет всех элементов управления"""
    
    def __init__(self, can_simulator: CANSimulator = None):
        super().__init__()
        self.can_simulator = can_simulator
        self.logger = get_logger("vehicle_controls")
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Настроить UI"""
        layout = QVBoxLayout()

        # Зажигание перенесено на основную панель управления (ControlPanel),
        # здесь оставляем только остальные физические элементы.

        # Магнитола
        self.radio = RadioControls()
        layout.addWidget(self.radio)

        # Руль отображается в компактном виде на панели ControlPanel,
        # но CAN-логика остаётся внутри VehicleControls.

        layout.addStretch()
        self.setLayout(layout)
    
    def _connect_signals(self):
        """Подключить сигналы"""
        # Громкость отправляется через CAN
        self.radio.volume_changed.connect(self._on_volume_changed)
    
    def _on_ignition_changed(self, state: str):
        """Обработчик изменения зажигания"""
        from core.ignition_states import IgnitionState
        
        if self.can_simulator:
            ignition_state = IgnitionState(state)
            
            if ignition_state == IgnitionState.OFF:
                self.can_simulator.set_vehicle_state(
                    rpm=0,
                    engine_temp=20
                )
                self.logger.info("Engine stopped (ignition OFF)")
            elif ignition_state == IgnitionState.ACC:
                # ACC - только питание, двигатель не работает
                self.can_simulator.set_vehicle_state(
                    rpm=0,
                    engine_temp=20
                )
                self.logger.info("Accessory mode (ACC)")
            elif ignition_state == IgnitionState.IGN:
                # IGN - зажигание включено, двигатель на холостом ходу
                self.can_simulator.set_vehicle_state(
                    rpm=800,  # Холостой ход
                    engine_temp=90
                )
                self.logger.info("Ignition ON - Android should start")
                # Сигнал для запуска Android будет обработан в main_window
            elif ignition_state == IgnitionState.START:
                # START - запуск двигателя
                self.can_simulator.set_vehicle_state(
                    rpm=1200,  # Повышенные обороты при запуске
                    engine_temp=90
                )
                self.logger.info("Engine starting...")
    
    def _on_volume_changed(self, volume: int):
        """Обработчик изменения громкости"""
        if self.can_simulator:
            # Отправляем CAN сообщение о громкости
            # ID для громкости: 0x300
            import struct
            data = struct.pack('<B', volume)
            self.can_simulator.send_event_message(0x300, data)
            self.logger.debug(f"Volume CAN message sent: {volume}")
    
    def _on_steering_button(self, button: str):
        """Обработчик кнопки руля"""
        if self.can_simulator:
            # Отправляем CAN сообщение о нажатии кнопки
            # ID для кнопок руля: 0x301
            button_map = {
                "left": 0x01,
                "right": 0x02,
                "up": 0x04,
                "down": 0x08,
                "ok": 0x10
            }
            import struct
            data = struct.pack('<B', button_map.get(button, 0))
            self.can_simulator.send_event_message(0x301, data)
            self.logger.info(f"Steering button CAN message sent: {button}")
    
    def set_can_simulator(self, simulator: CANSimulator):
        """Установить CAN симулятор"""
        self.can_simulator = simulator

    def bind_external_steering_buttons(self, button_signal):
        """
        Привязать внешний набор кнопок руля (компактные кнопки на панели Control)
        к CAN‑логике VehicleControls.
        """
        button_signal.connect(self._on_steering_button)

    def bind_external_ignition(self, ignition_control: IgnitionControl):
        """
        Привязать внешний контрол зажигания (например, большую кнопку
        на панели Control) к CAN‑логике VehicleControls.
        """
        ignition_control.ignition_changed.connect(self._on_ignition_changed)

