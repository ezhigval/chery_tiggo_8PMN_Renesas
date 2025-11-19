"""
Log Viewer - Просмотр логов в реальном времени
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QHBoxLayout,
    QPushButton, QComboBox, QLineEdit, QLabel
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor
from pathlib import Path
import json
import re


class LogViewer(QWidget):
    """Виджет для просмотра логов"""
    
    def __init__(self):
        super().__init__()
        self.log_file = None
        self._setup_ui()
        self._setup_timer()
    
    def _setup_ui(self):
        """Настроить UI"""
        layout = QVBoxLayout(self)
        
        # Панель управления
        control_layout = QHBoxLayout()
        
        # Фильтр по уровню
        self.level_filter = QComboBox()
        self.level_filter.addItems(["ALL", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"])
        self.level_filter.currentTextChanged.connect(self._filter_logs)
        control_layout.addWidget(QLabel("Level:"))
        control_layout.addWidget(self.level_filter)
        
        # Поиск
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.textChanged.connect(self._filter_logs)
        control_layout.addWidget(self.search_input)
        
        # Кнопка очистки
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_logs)
        control_layout.addWidget(clear_btn)
        
        # Экспорт
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self._export_logs)
        control_layout.addWidget(export_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Текстовое поле для логов
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFontFamily("Courier")
        self.log_text.setFontPointSize(9)
        layout.addWidget(self.log_text)
        
        # Настройка цветов для уровней
        self._setup_colors()
    
    def _setup_colors(self):
        """Настроить цвета для уровней логов"""
        self.colors = {
            "DEBUG": QColor(128, 128, 128),
            "INFO": QColor(255, 255, 255),
            "WARN": QColor(255, 255, 0),
            "ERROR": QColor(255, 0, 0),
            "CRITICAL": QColor(255, 0, 255),
        }
    
    def _setup_timer(self):
        """Настроить таймер для чтения логов"""
        self.timer = QTimer()
        self.timer.timeout.connect(self._read_logs)
        self.timer.start(100)  # Каждые 100ms
    
    def set_log_file(self, log_file: Path):
        """Установить файл логов для чтения"""
        self.log_file = log_file
        self.log_position = 0
    
    def _read_logs(self):
        """Читать новые логи из файла"""
        if not self.log_file or not self.log_file.exists():
            return
        
        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(self.log_position)
                new_lines = f.readlines()
                self.log_position = f.tell()
                
                if new_lines:
                    self._append_logs(new_lines)
        except Exception as e:
            pass  # Игнорируем ошибки чтения
    
    def _append_logs(self, lines: list):
        """Добавить строки логов"""
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Определяем уровень
            level = "INFO"
            for lvl in ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]:
                if f"[{lvl}" in line:
                    level = lvl
                    break
            
            # Применяем фильтры
            if not self._should_show_line(line, level):
                continue
            
            # Добавляем строку с цветом
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            
            format = QTextCharFormat()
            format.setForeground(self.colors.get(level, QColor(255, 255, 255)))
            cursor.setCharFormat(format)
            cursor.insertText(line + "\n")
            
            # Автопрокрутка
            self.log_text.ensureCursorVisible()
    
    def _should_show_line(self, line: str, level: str) -> bool:
        """Проверить, должна ли строка отображаться"""
        # Фильтр по уровню
        selected_level = self.level_filter.currentText()
        if selected_level != "ALL" and level != selected_level:
            return False
        
        # Фильтр по поиску
        search_text = self.search_input.text()
        if search_text and search_text.lower() not in line.lower():
            return False
        
        return True
    
    def _filter_logs(self):
        """Перефильтровать логи"""
        # TODO: Реализовать перефильтрацию существующих логов
        pass
    
    def _clear_logs(self):
        """Очистить логи"""
        self.log_text.clear()
    
    def _export_logs(self):
        """Экспортировать логи"""
        # TODO: Реализовать экспорт
        pass

