"""
Простой VNC клиент для отображения экрана QEMU
"""

import socket
import struct
import threading
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QImage, QPixmap, QPainter
import select


class SimpleVNCClient(QThread):
    """Простой VNC клиент для получения кадров"""
    frame_ready = pyqtSignal(QImage)
    error_occurred = pyqtSignal(str)
    status_message = pyqtSignal(str)  # Информационные сообщения (не ошибки)
    
    def __init__(self, host='localhost', port=5900, region=None):
        super().__init__()
        self.host = host
        self.port = port
        self.region = region  # (x, y, width, height) для обрезки
        self.running = False
        self.sock = None
        self.width = 0
        self.height = 0
        self.reconnect_delay = 2.0  # Задержка перед переподключением (секунды)
        self.max_reconnect_attempts = 10  # Максимальное количество попыток переподключения
        self.reconnect_count = 0
    
    def run(self):
        """Подключение к VNC и получение кадров"""
        # Ждем, пока QEMU будет готов (задержка перед первым подключением)
        import time
        if self.reconnect_count == 0:
            time.sleep(3)  # Даем QEMU время на инициализацию
        
        while self.running or self.reconnect_count == 0:
            try:
                if self.reconnect_count > 0:
                    self.status_message.emit(f"Переподключение к VNC (попытка {self.reconnect_count}/{self.max_reconnect_attempts})...")
                    time.sleep(self.reconnect_delay)
                else:
                    self.status_message.emit(f"Подключение к VNC {self.host}:{self.port}...")
                
                # Закрываем старое соединение если есть
                if self.sock:
                    try:
                        self.sock.close()
                    except:
                        pass
                    self.sock = None
                
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(10)
                self.sock.connect((self.host, self.port))
                self.status_message.emit("VNC подключен, выполняется handshake...")
                
                # VNC handshake
                version = self.sock.recv(12)
                if not version.startswith(b'RFB'):
                    if self.running and self.reconnect_count < self.max_reconnect_attempts:
                        self.reconnect_count += 1
                        continue
                    self.error_occurred.emit(f"Invalid VNC version: {version}")
                    return
                
                # Отправляем версию клиента
                self.sock.send(b'RFB 003.008\n')
                
                # Получаем тип безопасности
                security_types = self.sock.recv(1)
                num_types = ord(security_types)
                
                if num_types == 0:
                    # Получаем причину отказа
                    reason_len = struct.unpack('>I', self.sock.recv(4))[0]
                    reason = self.sock.recv(reason_len)
                    if self.running and self.reconnect_count < self.max_reconnect_attempts:
                        self.reconnect_count += 1
                        continue
                    self.error_occurred.emit(f"VNC security failed: {reason}")
                    return
                
                types = self.sock.recv(num_types)
                # Выбираем None (тип 1) если доступен
                if b'\x01' in types:
                    self.sock.send(b'\x01')  # None security
                    result = self.sock.recv(4)
                    if result != b'\x00\x00\x00\x00':
                        if self.running and self.reconnect_count < self.max_reconnect_attempts:
                            self.reconnect_count += 1
                            continue
                        self.error_occurred.emit("Security negotiation failed")
                        return
                else:
                    if self.running and self.reconnect_count < self.max_reconnect_attempts:
                        self.reconnect_count += 1
                        continue
                    self.error_occurred.emit("No supported security type")
                    return
                
                # Инициализация
                self.sock.send(b'\x01')  # Shared flag
                
                # Получаем размер экрана
                self.width = struct.unpack('>H', self.sock.recv(2))[0]
                self.height = struct.unpack('>H', self.sock.recv(2))[0]
                self.status_message.emit(f"Размер экрана: {self.width}x{self.height}")
                
                # Получаем pixel format
                pixel_format = self.sock.recv(16)
                
                # Получаем name
                name_length = struct.unpack('>I', self.sock.recv(4))[0]
                name = self.sock.recv(name_length)
                
                # Инициализируем полное изображение
                self.full_frame = None
                
                # Устанавливаем encodings (только Raw)
                self.sock.send(b'\x02')  # SetEncodings
                self.sock.send(struct.pack('>H', 1))  # Количество encodings
                self.sock.send(struct.pack('>i', 0))  # Raw encoding (0)
                
                # Сбрасываем счетчик переподключений при успешном подключении
                self.reconnect_count = 0
                
                # Запрашиваем обновления экрана
                self.running = True
                self._request_framebuffer_update()
                
                while self.running:
                    try:
                        # Используем select для неблокирующего чтения
                        ready, _, _ = select.select([self.sock], [], [], 0.5)
                        if not ready:
                            # Таймаут, запрашиваем обновление
                            self._request_framebuffer_update()
                            continue
                        
                        # Читаем сообщения от сервера
                        msg_type = self.sock.recv(1)
                        if not msg_type:
                            break
                        
                        if msg_type == b'\x00':  # FramebufferUpdate
                            self._handle_framebuffer_update()
                        elif msg_type == b'\x01':  # SetColorMapEntries
                            # Пропускаем
                            num_colors = struct.unpack('>HH', self.sock.recv(4))
                            self.sock.recv(num_colors[1] * 6)  # Пропускаем цвета
                        elif msg_type == b'\x02':  # Bell
                            # Пропускаем (нет данных)
                            pass
                        elif msg_type == b'\x03':  # ServerCutText
                            # Пропускаем
                            text_len = struct.unpack('>I', self.sock.recv(4))[0]
                            self.sock.recv(text_len)
                        else:
                            # Неизвестный тип сообщения
                            self.error_occurred.emit(f"Unknown message type: {msg_type.hex()}")
                            break
                        
                        # Запрашиваем следующее обновление
                        self._request_framebuffer_update()
                        
                    except socket.timeout:
                        # Таймаут, продолжаем
                        self._request_framebuffer_update()
                        continue
                    except (ConnectionResetError, BrokenPipeError, OSError) as e:
                        # Соединение разорвано - пытаемся переподключиться
                        if self.running and self.reconnect_count < self.max_reconnect_attempts:
                            self.reconnect_count += 1
                            self.status_message.emit(f"Соединение разорвано, переподключение... ({self.reconnect_count}/{self.max_reconnect_attempts})")
                            break  # Выходим из внутреннего цикла, переподключаемся
                        else:
                            self.error_occurred.emit(f"Connection lost: {e}")
                            return
                    except Exception as e:
                        # Другие ошибки - пытаемся переподключиться
                        if self.running and self.reconnect_count < self.max_reconnect_attempts:
                            self.reconnect_count += 1
                            self.status_message.emit(f"Ошибка в main loop, переподключение... ({self.reconnect_count}/{self.max_reconnect_attempts})")
                            break  # Выходим из внутреннего цикла, переподключаемся
                        else:
                            self.error_occurred.emit(f"Error in main loop: {e}")
                            return
                
            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                # Ошибка подключения - пытаемся переподключиться
                if self.running and self.reconnect_count < self.max_reconnect_attempts:
                    self.reconnect_count += 1
                    self.status_message.emit(f"Ошибка подключения, переподключение... ({self.reconnect_count}/{self.max_reconnect_attempts})")
                    continue
                else:
                    self.error_occurred.emit(f"VNC connection error: {e}")
                    break
            except Exception as e:
                # Другие ошибки
                if self.running and self.reconnect_count < self.max_reconnect_attempts:
                    self.reconnect_count += 1
                    self.status_message.emit(f"Ошибка, переподключение... ({self.reconnect_count}/{self.max_reconnect_attempts})")
                    continue
                else:
                    self.error_occurred.emit(f"VNC connection error: {e}")
                    break
        
        # Закрываем соединение при выходе
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
    
    def _request_framebuffer_update(self):
        """Запросить обновление framebuffer"""
        if not self.running or not self.sock:
            return
        
        try:
            # Incremental = 0 (полное обновление)
            self.sock.send(b'\x03')  # FramebufferUpdateRequest
            # Формат: incremental(1) + x(2) + y(2) + width(2) + height(2) = 9 байт
            # Если указан region, запрашиваем только нужную область
            if self.region:
                rx, ry, rw, rh = self.region
                # Запрашиваем обновление для указанной области
                self.sock.send(struct.pack('>BHHHH', 0, rx, ry, rw, rh))
            else:
                # Запрашиваем полное обновление
                self.sock.send(struct.pack('>BHHHH', 0, 0, 0, self.width, self.height))
        except Exception as e:
            self.error_occurred.emit(f"Error requesting update: {e}")
    
    def _handle_framebuffer_update(self):
        """Обработать обновление framebuffer"""
        try:
            # Пропускаем padding
            self.sock.recv(1)
            
            # Количество прямоугольников
            num_rects = struct.unpack('>H', self.sock.recv(2))[0]
            
            # Создаем полное изображение если его еще нет
            if not hasattr(self, 'full_frame') or self.full_frame is None:
                self.full_frame = QImage(self.width, self.height, QImage.Format.Format_RGB32)
                self.full_frame.fill(0)  # Черный фон
            
            for _ in range(num_rects):
                # Координаты и размер
                x = struct.unpack('>H', self.sock.recv(2))[0]
                y = struct.unpack('>H', self.sock.recv(2))[0]
                w = struct.unpack('>H', self.sock.recv(2))[0]
                h = struct.unpack('>H', self.sock.recv(2))[0]
                
                # Тип кодирования
                encoding = struct.unpack('>i', self.sock.recv(4))[0]
                
                if encoding == 0:  # Raw
                    # Читаем пиксели (QEMU использует 32-bit, но порядок может быть BGR)
                    expected_size = w * h * 4
                    pixel_data = b''
                    while len(pixel_data) < expected_size:
                        try:
                            chunk = self.sock.recv(min(4096, expected_size - len(pixel_data)))
                            if not chunk:
                                raise ConnectionResetError("Connection closed while reading pixel data")
                            pixel_data += chunk
                        except (ConnectionResetError, BrokenPipeError, OSError):
                            raise  # Пробрасываем дальше для переподключения
                    
                    if len(pixel_data) == expected_size:
                        # Создаем QImage из данных
                        # QEMU может использовать BGR порядок, пробуем RGB32
                        image = QImage(pixel_data, w, h, QImage.Format.Format_RGB32)
                        
                        if image.isNull():
                            # Пробуем другой формат
                            image = QImage(pixel_data, w, h, QImage.Format.Format_ARGB32)
                        
                        if not image.isNull():
                            # Копируем в полное изображение
                            if self.full_frame is None:
                                self.full_frame = QImage(self.width, self.height, QImage.Format.Format_RGB32)
                                self.full_frame.fill(0)
                            
                            painter = QPainter(self.full_frame)
                            painter.drawImage(x, y, image)
                            painter.end()
                            
                            # Если указан region, обрезаем и отправляем только нужную область
                            if self.region:
                                rx, ry, rw, rh = self.region
                                # Проверяем, что обновленная область пересекается с нашим region
                                if x < rx + rw and x + w > rx and y < ry + rh and y + h > ry:
                                    # Берем нужную область из полного изображения
                                    # Ограничиваем координаты границами изображения
                                    crop_x = max(0, rx)
                                    crop_y = max(0, ry)
                                    crop_w = min(rw, self.width - crop_x)
                                    crop_h = min(rh, self.height - crop_y)
                                    
                                    if crop_w > 0 and crop_h > 0:
                                        cropped = self.full_frame.copy(crop_x, crop_y, crop_w, crop_h)
                                        if not cropped.isNull():
                                            self.frame_ready.emit(cropped)
                            else:
                                # Отправляем полное изображение
                                self.frame_ready.emit(self.full_frame)
                else:
                    # Пропускаем другие типы кодирования
                    # Нужно прочитать данные чтобы не сломать протокол
                    if encoding == -239:  # CopyRect
                        src_x = struct.unpack('>H', self.sock.recv(2))[0]
                        src_y = struct.unpack('>H', self.sock.recv(2))[0]
                    elif encoding == -223:  # RRE
                        sub_rects = struct.unpack('>I', self.sock.recv(4))[0]
                        # Пропускаем данные
                        self.sock.recv(w * h * 4 + sub_rects * 4)
                    else:
                        # Неизвестное кодирование, пропускаем
                        pass
                    
        except Exception as e:
            self.error_occurred.emit(f"Error handling framebuffer update: {e}")
            import traceback
            traceback.print_exc()
    
    def stop(self):
        """Остановить клиент"""
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass

