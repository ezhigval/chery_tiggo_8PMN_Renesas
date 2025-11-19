from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QGroupBox, QVBoxLayout
from PyQt6.QtCore import pyqtSignal, Qt


class SteeringButtonsCompact(QGroupBox):
    """
    Компактный блок кнопок руля:
      ◄  ▲  OK  ▼  ►
    Используется справа от кнопки START/STOP на панели Control.
    """

    button_clicked = pyqtSignal(str)  # "left", "right", "up", "down", "ok"

    def __init__(self):
        super().__init__("Руль")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        buttons = [
            ("◄", "left"),
            ("▲", "up"),
            ("OK", "ok"),
            ("▼", "down"),
            ("►", "right"),
        ]

        for text, name in buttons:
            btn = QPushButton(text)
            btn.setFixedSize(40, 26)
            if name == "ok":
                btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
            btn.clicked.connect(lambda _, n=name: self.button_clicked.emit(n))
            row.addWidget(btn)

        layout.addLayout(row)
        self.setLayout(layout)


