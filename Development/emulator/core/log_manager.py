"""
Log Manager - Централизованная система логирования
Обеспечивает полное логирование всех процессов эмулятора
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from loguru import logger
from threading import Lock
import json


class LogManager:
    """Менеджер логирования для T18FL3 эмулятора"""
    
    def __init__(self, log_dir: Path = Path("logs")):
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)
        self.lock = Lock()
        self.loggers = {}
        self.log_file = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Настройка системы логирования"""
        # Удаляем стандартный handler loguru
        logger.remove()
        
        # Создаем имя файла с временной меткой
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = self.log_dir / f"t18fl3_emulator_{timestamp}.log"
        self.log_file = log_file_path
        
        # Формат логов
        log_format = (
            "[{time:YYYY-MM-DD HH:mm:ss.SSS}] "
            "[{level: <8}] "
            "[{name}:{function}:{line}] "
            "{message}"
        )
        
        # Добавляем handler для файла
        logger.add(
            str(log_file_path),
            format=log_format,
            level="DEBUG",
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            enqueue=True,
            backtrace=True,
            diagnose=True
        )
        
        # Добавляем handler для консоли (только INFO и выше)
        logger.add(
            sys.stderr,
            format=log_format,
            level="INFO",
            colorize=True
        )
        
        # JSON лог для машинной обработки (для GUI таблицы логов)
        json_log_path = self.log_dir / f"t18fl3_emulator_{timestamp}.jsonl"
        self.json_log_file = json_log_path
        
        # Кастомный sink для JSON логов
        def json_sink(message):
            """Кастомный sink для записи JSON логов"""
            try:
                record = message.record
                log_entry = {
                    "timestamp": record["time"].isoformat(),
                    "level": record["level"].name,
                    "source": record.get("extra", {}).get("source", "system"),
                    "module": record.get("extra", {}).get("module", record["name"]),
                    "message": record["message"]
                }
                with open(json_log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            except Exception:
                pass  # Игнорируем ошибки записи
        
        logger.add(
            json_sink,
            level="DEBUG",
            format="{message}"  # Не используется, но требуется
        )
    
    def get_logger(self, name: str):
        """Получить logger для модуля"""
        if name not in self.loggers:
            self.loggers[name] = logger.bind(module=name)
        return self.loggers[name]
    
    def log_qemu_output(self, source: str, output: str, level: str = "INFO"):
        """Логировать вывод QEMU"""
        with self.lock:
            logger.bind(source="qemu", component=source).log(level, output)
    
    def log_can_message(self, can_id: int, data: bytes, direction: str = "TX"):
        """Логировать CAN сообщение"""
        with self.lock:
            logger.bind(
                source="can",
                can_id=hex(can_id),
                direction=direction,
                data_length=len(data)
            ).debug(
                f"CAN {direction}: ID={hex(can_id)}, "
                f"Data={data.hex()}, Length={len(data)}"
            )
    
    def log_process_event(self, event: str, details: dict):
        """Логировать событие процесса"""
        with self.lock:
            logger.bind(source="process", event=event, **details).info(
                f"Process event: {event}"
            )
    
    def log_system_event(self, event: str, details: dict):
        """Логировать системное событие"""
        with self.lock:
            logger.bind(source="system", event=event, **details).info(
                f"System event: {event}"
            )
    
    def log_image_event(self, image_name: str, event: str, details: dict):
        """Логировать событие с образом"""
        with self.lock:
            logger.bind(
                source="image",
                image=image_name,
                event=event,
                **details
            ).info(f"Image {image_name}: {event}")
    
    def get_log_file(self) -> Optional[Path]:
        """Получить путь к текущему файлу логов"""
        return self.log_file
    
    def export_logs(self, start_time: datetime, end_time: datetime, 
                   output_file: Path, level: Optional[str] = None):
        """Экспортировать логи за период"""
        # Реализация экспорта логов из JSON файла
        pass


# Глобальный экземпляр
_log_manager: Optional[LogManager] = None


def get_log_manager() -> LogManager:
    """Получить глобальный экземпляр LogManager"""
    global _log_manager
    if _log_manager is None:
        _log_manager = LogManager()
    return _log_manager


def get_logger(name: str):
    """Получить logger для модуля"""
    return get_log_manager().get_logger(name)

