"""
Display 1 Widget - Instrument Cluster (12.3")
Левый экран для приборной панели
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap, QImage
from gui.vnc_client import SimpleVNCClient


class Display1Widget(QWidget):
    """Виджет для первого дисплея (Instrument Cluster - Приборная панель)"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Display 1 - Instrument Cluster (Приборная панель)")
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
        title = QLabel("📊 ПРИБОРНАЯ ПАНЕЛЬ (12.3\")")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("background-color: #1a4d2e; color: #4CAF50; padding: 2px; border-radius: 3px; font-weight: bold;")
        layout.addWidget(title)
        
        # Информация о VNC
        vnc_info = QLabel(f"VNC: {self.vnc_host}:{self.vnc_port} | Левая половина экрана")
        vnc_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vnc_info.setStyleSheet("color: #4CAF50; font-size: 9px; padding: 1px;")
        layout.addWidget(vnc_info)
        
        # Область для отображения VNC
        self.display_label = QLabel()
        # Выравниваем содержимое по верхнему краю, по центру по горизонтали,
        # чтобы весь блок экрана "прилипал" вверх.
        self.display_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.display_label.setStyleSheet("""
            background-color: #000000;
            border: 2px solid #4CAF50;
            border-radius: 5px;
        """)
        self.display_label.setText(
            "Ожидание подключения к VNC...\n\n"
            "📊 ПРИБОРНАЯ ПАНЕЛЬ\n"
            "Здесь будет отображаться:\n"
            "• Спидометр\n"
            "• Тахометр\n"
            "• Индикаторы\n"
            "• Температура двигателя\n"
            "• Уровень топлива"
        )
        self.display_label.setStyleSheet(self.display_label.styleSheet() + " color: #4CAF50; padding: 20px; font-size: 12px;")
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
            # Берем левую половину
            width = self.full_image.width()
            height = self.full_image.height()
            cropped = self.full_image.copy(0, 0, width // 2, height)
            self.current_image = cropped
            self._update_display()

    def resizeEvent(self, event):
        """Сохраняем соотношение сторон области отображения как у оригинального дисплея."""
        super().resizeEvent(event)
        if self.display_label:
            # Высота подгоняется под ширину с учётом целевого AR, но не меньше 200px
            new_height = max(200, int(self.display_label.width() / self._target_aspect))
            self.display_label.setFixedHeight(new_height)
    
    def start_vnc(self, host='localhost', port=5900):
        """Начать получение VNC данных"""
        self.vnc_host = host
        self.vnc_port = port
        
        if self.vnc_client:
            self.vnc_client.stop()
            self.vnc_client.wait()
        
        # Запускаем VNC клиент (берем левый экран)
        # Общее разрешение VNC: 3840x720 (два экрана по 1920x720)
        # Левый экран: x=0, y=0, width=1920, height=720
        self.vnc_client = SimpleVNCClient(host, port, region=(0, 0, 1920, 720))
        self.vnc_client.frame_ready.connect(self._on_frame_ready)
        self.vnc_client.error_occurred.connect(self._on_vnc_error)
        self.vnc_client.status_message.connect(self._on_vnc_status)
        self.vnc_client.start()
        
        self.display_label.setText(f"Подключение к VNC: {host}:{port}...\n\nПриборная панель")
    
    def _on_frame_ready(self, image: QImage):
        """Обработчик получения нового кадра"""
        if not image.isNull():
            self.current_image = image
            self.full_image = image  # Сохраняем для возможного использования
    
    def _on_vnc_status(self, message: str):
        """Обработчик статусных сообщений VNC"""
        # Показываем статус, но не как ошибку.
        # Сообщение "Размер экрана: WxH" приходящее из VNC-клиента
        # отражает внутреннее framebuffer‑разрешение (например, 640x480),
        # но внешнее поведение и макет соответствуют оригинальному дисплею 1920x720
        # с соотношением сторон 8:3 (масштабируем под доступную область).
        if not self.current_image:
            if message.startswith("Размер экрана:"):
                self.display_label.setText(
                    "Разрешение дисплея: 1920x720 (AR 8:3)\n"
                    "Изображение масштабируется с сохранением этого соотношения сторон.\n\n"
                    "Приборная панель"
                )
            else:
                self.display_label.setText(f"{message}\n\nПриборная панель")
    
    def _on_vnc_error(self, error: str):
        """Обработчик ошибки VNC"""
        # Не показываем ошибку как критическую - клиент попытается переподключиться
        if "Connection reset" in error or "Connection lost" in error:
            self.display_label.setText(f"⏳ Переподключение к VNC...\n\n{error}\n\nПриборная панель")
        else:
            self.display_label.setText(f"❌ Ошибка VNC: {error}\n\nПроверьте подключение")
    
    def closeEvent(self, event):
        """Обработчик закрытия виджета"""
        if self.vnc_client:
            self.vnc_client.stop()
            self.vnc_client.wait()
        super().closeEvent(event)
