"""
Display 2 Widget - Multimedia System (12.3")
Правый экран для головного устройства (ГУ)
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap, QImage
from gui.vnc_client import SimpleVNCClient


class Display2Widget(QWidget):
    """Виджет для второго дисплея (Multimedia System - Головное устройство)"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Display 2 - Multimedia System (Головное устройство)")
        self.vnc_host = 'localhost'
        self.vnc_port = 5910  # Изолированный порт для T18FL3 (display :10)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.vnc_client = None
        self.current_image = None
        self.full_image = None  # Полное изображение от VNC
        self._setup_ui()
        self._target_aspect = 1920 / 720  # Соотношение сторон оригинального дисплея (8:3)
    
    def _setup_ui(self):
        """Настроить UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Заголовок
        title = QLabel("🖥️ ГОЛОВНОЕ УСТРОЙСТВО (12.3\")")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("background-color: #0d47a1; color: #2196F3; padding: 2px; border-radius: 3px; font-weight: bold;")
        layout.addWidget(title)
        
        # Информация о VNC
        vnc_info = QLabel(f"VNC: {self.vnc_host}:{self.vnc_port} | Правая половина экрана")
        vnc_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vnc_info.setStyleSheet("color: #2196F3; font-size: 9px; padding: 1px;")
        layout.addWidget(vnc_info)
        
        # Область для отображения VNC
        self.display_label = QLabel()
        # Выравниваем картинку по верхнему краю, чтобы оба экрана были ровно по верху.
        self.display_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.display_label.setStyleSheet("""
            background-color: #000000;
            border: 2px solid #2196F3;
            border-radius: 5px;
        """)
        self.display_label.setText(
            "Ожидание подключения к VNC...\n\n"
            "🖥️ ГОЛОВНОЕ УСТРОЙСТВО\n"
            "Здесь будет отображаться:\n"
            "• Android интерфейс\n"
            "• Навигация\n"
            "• Медиаплеер\n"
            "• Настройки\n"
            "• Приложения"
        )
        self.display_label.setStyleSheet(self.display_label.styleSheet() + " color: #2196F3; padding: 20px; font-size: 12px;")
        layout.addWidget(self.display_label, stretch=1)
        
        # Запускаем обновление
        self.update_timer.start(100)  # Обновление каждые 100ms
    
    def _update_display(self):
        """Обновить отображение"""
        if self.current_image and not self.current_image.isNull():
            pixmap = QPixmap.fromImage(self.current_image)
            scaled_pixmap = pixmap.scaled(
                self.display_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.display_label.setPixmap(scaled_pixmap)
            self.display_label.setText("")  # Убираем текст
        elif self.full_image and not self.full_image.isNull():
            # Берем правую половину
            width = self.full_image.width()
            height = self.full_image.height()
            cropped = self.full_image.copy(width // 2, 0, width // 2, height)
            self.current_image = cropped
            self._update_display()

    def resizeEvent(self, event):
        """Сохраняем соотношение сторон области отображения как у оригинального дисплея."""
        super().resizeEvent(event)
        if self.display_label:
            new_height = max(200, int(self.display_label.width() / self._target_aspect))
            self.display_label.setFixedHeight(new_height)
    
    def start_vnc(self, host='localhost', port=5900):
        """Начать получение VNC данных"""
        self.vnc_host = host
        self.vnc_port = port
        
        if self.vnc_client:
            self.vnc_client.stop()
            self.vnc_client.wait()
        
        # Запускаем VNC клиент (берем правый экран)
        # Общее разрешение VNC: 3840x720 (два экрана по 1920x720)
        # Правый экран: x=1920, y=0, width=1920, height=720
        self.vnc_client = SimpleVNCClient(host, port, region=(1920, 0, 1920, 720))
        self.vnc_client.frame_ready.connect(self._on_frame_ready)
        self.vnc_client.error_occurred.connect(self._on_vnc_error)
        self.vnc_client.status_message.connect(self._on_vnc_status)
        self.vnc_client.start()
        
        self.display_label.setText(f"Подключение к VNC: {host}:{port}...\n\nГоловное устройство")
    
    def _on_frame_ready(self, image: QImage):
        """Обработчик получения нового кадра"""
        if not image.isNull():
            self.current_image = image
            self.full_image = image  # Сохраняем для возможного использования
    
    def _on_vnc_status(self, message: str):
        """Обработчик статусных сообщений VNC"""
        # Показываем статус, но не как ошибку.
        # Для сообщения "Размер экрана: WxH" вместо внутреннего framebuffer‑размера
        # показываем целевое разрешение 1920x720 с соотношением сторон 8:3,
        # которое масштабируется под рамку виджета (как у реального дисплея).
        if not self.current_image:
            if message.startswith("Размер экрана:"):
                self.display_label.setText(
                    "Разрешение дисплея: 1920x720 (AR 8:3)\n"
                    "Изображение масштабируется с сохранением этого соотношения сторон.\n\n"
                    "Головное устройство"
                )
            else:
                self.display_label.setText(f"{message}\n\nГоловное устройство")
    
    def _on_vnc_error(self, error: str):
        """Обработчик ошибки VNC"""
        # Не показываем ошибку как критическую - клиент попытается переподключиться
        if "Connection reset" in error or "Connection lost" in error:
            self.display_label.setText(f"⏳ Переподключение к VNC...\n\n{error}\n\nГоловное устройство")
        else:
            self.display_label.setText(f"❌ Ошибка VNC: {error}\n\nПроверьте подключение")
    
    def closeEvent(self, event):
        """Обработчик закрытия виджета"""
        if self.vnc_client:
            self.vnc_client.stop()
            self.vnc_client.wait()
        super().closeEvent(event)
