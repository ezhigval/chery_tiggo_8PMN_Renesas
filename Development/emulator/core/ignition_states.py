"""
Состояния зажигания автомобиля
"""

from enum import Enum


class IgnitionState(Enum):
    """Состояния зажигания автомобиля"""
    OFF = "off"           # Выключено
    ACC = "acc"           # Accessory - питание для аксессуаров (радио, USB и т.д.)
    IGN = "ign"           # Ignition - зажигание (запускается Android)
    START = "start"       # Start - запуск двигателя (временное состояние, возвращается в IGN)

