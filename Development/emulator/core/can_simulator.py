"""
CAN Bus Simulator - Симуляция CAN-шины для имитации автомобиля
Генерирует CAN сообщения для эмуляции различных систем автомобиля
"""

import threading
import time
import socket
import struct
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json

from .log_manager import get_logger, get_log_manager


class CANMessageType(Enum):
    """Типы CAN сообщений"""
    PERIODIC = "periodic"  # Периодические (скорость, обороты и т.д.)
    EVENT = "event"        # Событийные (нажатие кнопки и т.д.)
    STATUS = "status"      # Статусные (температура, давление и т.д.)


@dataclass
class CANMessage:
    """CAN сообщение"""
    can_id: int
    data: bytes
    period: float = 0.0  # Период для периодических сообщений (секунды)
    message_type: CANMessageType = CANMessageType.PERIODIC
    description: str = ""


class CANSimulator:
    """Симулятор CAN-шины для T18FL3"""
    
    def __init__(self, interface: str = "vcan0"):
        self.interface = interface
        self.logger = get_logger("can_simulator")
        self.log_manager = get_log_manager()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # Сообщения
        self.periodic_messages: List[CANMessage] = []
        self.event_messages: List[CANMessage] = []
        
        # Socket для отправки CAN сообщений
        self.socket: Optional[socket.socket] = None
        
        # Состояние автомобиля (для генерации сообщений)
        self.vehicle_state = {
            "speed": 0.0,           # км/ч
            "rpm": 0,              # об/мин
            "engine_temp": 90,     # °C
            "fuel_level": 50,      # %
            "gear": 0,             # передача
            "brake_pedal": False,  # педаль тормоза
            "accelerator": 0,      # % нажатия
            "steering_angle": 0,   # градусы
            "parking_brake": True, # ручной тормоз
            "doors_locked": True,  # двери заблокированы
            "climate_temp": 22,    # °C
            "climate_fan": 2,      # уровень вентиляции
        }
        
        # Загружаем стандартные CAN сообщения
        self._load_can_messages()
    
    def _load_can_messages(self):
        """Загрузить стандартные CAN сообщения из конфигурации"""
        config_file = Path(__file__).parent.parent / "config" / "can_messages.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self._parse_can_config(config)
            except Exception as e:
                self.logger.error(f"Error loading CAN config: {e}")
        else:
            # Создаем стандартные сообщения
            self._create_default_messages()
    
    def _parse_can_config(self, config: Dict):
        """Парсить конфигурацию CAN сообщений"""
        for msg_config in config.get("messages", []):
            can_id = int(msg_config["id"], 16) if isinstance(msg_config["id"], str) else msg_config["id"]
            data = bytes.fromhex(msg_config["data"]) if isinstance(msg_config["data"], str) else msg_config["data"]
            
            msg = CANMessage(
                can_id=can_id,
                data=data,
                period=msg_config.get("period", 0.1),
                message_type=CANMessageType(msg_config.get("type", "periodic")),
                description=msg_config.get("description", "")
            )
            
            if msg.message_type == CANMessageType.PERIODIC:
                self.periodic_messages.append(msg)
            else:
                self.event_messages.append(msg)
    
    def _create_default_messages(self):
        """Создать стандартные CAN сообщения"""
        # Скорость автомобиля (ID: 0x100)
        self.periodic_messages.append(CANMessage(
            can_id=0x100,
            data=struct.pack('<H', 0),  # скорость в км/ч * 10
            period=0.1,
            description="Vehicle speed"
        ))
        
        # Обороты двигателя (ID: 0x101)
        self.periodic_messages.append(CANMessage(
            can_id=0x101,
            data=struct.pack('<H', 0),  # обороты
            period=0.1,
            description="Engine RPM"
        ))
        
        # Температура двигателя (ID: 0x102)
        self.periodic_messages.append(CANMessage(
            can_id=0x102,
            data=struct.pack('<B', 90),  # температура
            period=1.0,
            description="Engine temperature"
        ))
        
        # Уровень топлива (ID: 0x103)
        self.periodic_messages.append(CANMessage(
            can_id=0x103,
            data=struct.pack('<B', 50),  # процент
            period=2.0,
            description="Fuel level"
        ))
        
        # Климат-контроль (ID: 0x200)
        self.periodic_messages.append(CANMessage(
            can_id=0x200,
            data=struct.pack('<BB', 22, 2),  # температура, вентиляция
            period=1.0,
            description="Climate control"
        ))
        
        # Громкость магнитолы (ID: 0x300)
        self.periodic_messages.append(CANMessage(
            can_id=0x300,
            data=struct.pack('<B', 50),  # громкость 0-100
            period=0.5,
            description="Radio volume"
        ))
        
        # Кнопки руля (ID: 0x301)
        self.periodic_messages.append(CANMessage(
            can_id=0x301,
            data=struct.pack('<B', 0),  # кнопка (left/right/up/down/ok)
            period=0.0,  # только по событию
            message_type=CANMessageType.EVENT,
            description="Steering wheel buttons"
        ))
        
        # Статус дверей (ID: 0x201)
        self.periodic_messages.append(CANMessage(
            can_id=0x201,
            data=struct.pack('<B', 0x0F),  # биты для каждой двери
            period=0.5,
            description="Door status"
        ))
    
    def _setup_socket(self) -> bool:
        """Настроить socket для CAN"""
        try:
            # Пытаемся использовать реальный CAN интерфейс (Linux)
            self.socket = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
            self.socket.bind((self.interface,))
            self.logger.info(f"CAN socket bound to {self.interface}")
            return True
        except (OSError, AttributeError):
            # Если нет реального CAN (macOS/Windows), используем эмуляцию через UDP
            self.logger.warning(f"Real CAN not available, using UDP emulation")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # В эмуляции мы будем логировать сообщения, но не отправлять реально
            return True
    
    def _send_can_message(self, message: CANMessage):
        """Отправить CAN сообщение"""
        if not self.socket:
            return
        
        try:
            # Формируем CAN frame
            # Linux: struct can_frame { uint32_t can_id; uint8_t can_dlc; uint8_t data[8]; }
            can_id = message.can_id | 0x80000000  # Extended frame
            can_dlc = len(message.data)
            frame = struct.pack('<IB', can_id, can_dlc) + message.data.ljust(8, b'\x00')
            
            if hasattr(self.socket, 'send'):
                try:
                    self.socket.send(frame)
                except:
                    # В эмуляции просто логируем
                    pass
            
            # Логируем сообщение только если это ручное (не периодическое)
            # Периодические сообщения не логируем, чтобы не засорять логи
            if message.message_type != CANMessageType.PERIODIC:
                self.log_manager.log_can_message(message.can_id, message.data, "TX")
            
        except Exception as e:
            self.logger.error(f"Error sending CAN message: {e}")
    
    def _update_vehicle_state_messages(self):
        """Обновить CAN сообщения на основе состояния автомобиля"""
        # Скорость
        speed_msg = next((m for m in self.periodic_messages if m.can_id == 0x100), None)
        if speed_msg:
            speed_msg.data = struct.pack('<H', int(self.vehicle_state["speed"] * 10))
        
        # Обороты
        rpm_msg = next((m for m in self.periodic_messages if m.can_id == 0x101), None)
        if rpm_msg:
            rpm_msg.data = struct.pack('<H', self.vehicle_state["rpm"])
        
        # Температура двигателя
        temp_msg = next((m for m in self.periodic_messages if m.can_id == 0x102), None)
        if temp_msg:
            temp_msg.data = struct.pack('<B', self.vehicle_state["engine_temp"])
        
        # Уровень топлива
        fuel_msg = next((m for m in self.periodic_messages if m.can_id == 0x103), None)
        if fuel_msg:
            fuel_msg.data = struct.pack('<B', self.vehicle_state["fuel_level"])
        
        # Климат-контроль
        climate_msg = next((m for m in self.periodic_messages if m.can_id == 0x200), None)
        if climate_msg:
            climate_msg.data = struct.pack('<BB', 
                self.vehicle_state["climate_temp"],
                self.vehicle_state["climate_fan"]
            )
    
    def _run_periodic_messages(self):
        """Запустить периодическую отправку сообщений"""
        last_send_times = {msg.can_id: 0.0 for msg in self.periodic_messages}
        
        while self.running:
            current_time = time.time()
            
            for message in self.periodic_messages:
                if current_time - last_send_times[message.can_id] >= message.period:
                    self._update_vehicle_state_messages()
                    self._send_can_message(message)
                    last_send_times[message.can_id] = current_time
            
            time.sleep(0.01)  # Небольшая задержка для CPU
    
    def start(self):
        """Запустить CAN симулятор"""
        if self.running:
            return
        
        if not self._setup_socket():
            self.logger.error("Failed to setup CAN socket")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_periodic_messages, daemon=True)
        self.thread.start()
        self.logger.info("CAN simulator started")
    
    def stop(self):
        """Остановить CAN симулятор"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        if self.socket:
            self.socket.close()
        self.logger.info("CAN simulator stopped")
    
    def set_vehicle_state(self, **kwargs):
        """Установить состояние автомобиля"""
        with self.lock:
            self.vehicle_state.update(kwargs)
            self.logger.debug(f"Vehicle state updated: {kwargs}")
    
    def get_vehicle_state(self) -> Dict:
        """Получить текущее состояние автомобиля"""
        with self.lock:
            return self.vehicle_state.copy()
    
    def send_event_message(self, can_id: int, data: bytes):
        """Отправить событийное CAN сообщение (ручное управление)"""
        # Убеждаемся, что socket настроен (но не запускаем периодическую отправку)
        if not self.socket:
            self._setup_socket()
        
        message = CANMessage(
            can_id=can_id,
            data=data,
            message_type=CANMessageType.EVENT,
            description="User event"
        )
        self._send_can_message(message)

