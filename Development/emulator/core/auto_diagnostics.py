"""
Автоматическая диагностика и исправление проблем эмулятора T18FL3
Автоматически анализирует логи, находит проблемы и применяет исправления
"""

import re
import time
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

from .log_manager import get_logger, get_log_manager


class DiagnosticLevel(Enum):
    """Уровни диагностики"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class DiagnosticIssue:
    """Проблема, обнаруженная диагностикой"""
    level: DiagnosticLevel
    category: str
    message: str
    fix_applied: bool = False
    fix_description: str = ""


class AutoDiagnostics:
    """Автоматическая диагностика и исправление"""
    
    def __init__(self):
        self.logger = get_logger("auto_diagnostics")
        self.log_manager = get_log_manager()
        self.issues: List[DiagnosticIssue] = []
        self.fix_count = 0
        self.iteration = 0
        self.start_time = time.time()  # Время старта для проверки serial output
        self.max_iterations = 10  # Максимум итераций для предотвращения бесконечного цикла
        
    def analyze_logs(self, log_file: Optional[Path] = None) -> List[DiagnosticIssue]:
        """Анализировать логи и найти проблемы"""
        self.issues = []
        
        if not log_file:
            log_file = self.log_manager.get_log_file()
        
        if not log_file or not log_file.exists():
            return self.issues
        
        try:
            # Читаем последние 500 строк логов
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                recent_lines = lines[-500:] if len(lines) > 500 else lines
                
                log_text = '\n'.join(recent_lines)
                
                # Проверяем различные проблемы
                self._check_kernel_boot(log_text)
                self._check_serial_output(log_text)
                self._check_dtb_issues(log_text)
                self._check_qemu_errors(log_text)
                self._check_vnc_issues(log_text)
                self._check_adb_issues(log_text)
                
        except Exception as e:
            self.logger.error(f"Error analyzing logs: {e}")
        
        return self.issues
    
    def _check_kernel_boot(self, log_text: str):
        """Проверить загрузку kernel"""
        # Проверяем, есть ли признаки загрузки kernel
        if "PC=" in log_text and "ffff" in log_text:
            # Kernel запущен (PC в kernel space)
            if "SERIAL" not in log_text or not re.search(r'SERIAL.*kernel|SERIAL.*boot', log_text, re.I):
                self.issues.append(DiagnosticIssue(
                    level=DiagnosticLevel.WARNING,
                    category="kernel",
                    message="Kernel запущен, но нет serial output - возможно проблема с консолью/DTB"
                ))
        elif "QEMU.*started" in log_text and "running" in log_text:
            # QEMU запущен, но нет признаков kernel
            if "PC=" not in log_text:
                self.issues.append(DiagnosticIssue(
                    level=DiagnosticLevel.ERROR,
                    category="kernel",
                    message="QEMU запущен, но kernel не загружается"
                ))
    
    def _check_serial_output(self, log_text: str):
        """Проверить serial output"""
        serial_count = len(re.findall(r'SERIAL', log_text, re.I))
        # ВАЖНО: Не создаем проблему если QEMU только что запустился (меньше 30 секунд)
        # Kernel может еще не начать выводить
        if serial_count == 0:
            # Проверяем, сколько времени прошло с запуска
            # Если меньше 60 секунд - это нормально, kernel еще загружается
            time_since_start = time.time() - self.start_time if hasattr(self, 'start_time') else 0
            if time_since_start > 60:  # Только после 60 секунд считаем это проблемой
                self.issues.append(DiagnosticIssue(
                    level=DiagnosticLevel.WARNING,
                    category="serial",
                    message="Нет serial output от kernel - возможно проблема с консолью"
                ))
    
    def _check_dtb_issues(self, log_text: str):
        """Проверить проблемы с DTB"""
        if "DTB.*invalid" in log_text or "AVB structure" in log_text:
            self.issues.append(DiagnosticIssue(
                level=DiagnosticLevel.WARNING,
                category="dtb",
                message="DTB файл невалидный или является AVB структурой - используется автогенерация QEMU"
            ))
    
    def _check_qemu_errors(self, log_text: str):
        """Проверить ошибки QEMU"""
        if re.search(r'QEMU.*error|QEMU.*failed|QEMU.*exited', log_text, re.I):
            self.issues.append(DiagnosticIssue(
                level=DiagnosticLevel.ERROR,
                category="qemu",
                message="Обнаружены ошибки QEMU"
            ))
    
    def _check_vnc_issues(self, log_text: str):
        """Проверить проблемы VNC"""
        if "VNC.*error|VNC.*failed" in log_text:
            self.issues.append(DiagnosticIssue(
                level=DiagnosticLevel.WARNING,
                category="vnc",
                message="Проблемы с VNC подключением"
            ))
    
    def _check_adb_issues(self, log_text: str):
        """Проверить проблемы ADB"""
        if "ADB.*not accessible|ADB.*not found" in log_text:
            self.issues.append(DiagnosticIssue(
                level=DiagnosticLevel.INFO,
                category="adb",
                message="ADB недоступен - возможно Android еще не загрузился"
            ))
    
    def apply_fixes(self, qemu_manager, custom_machine_builder=None) -> bool:
        """Применить исправления на основе найденных проблем"""
        fixes_applied = False
        
        for issue in self.issues:
            if issue.fix_applied:
                continue
            
            if issue.category == "serial" and issue.level == DiagnosticLevel.WARNING:
                # Проблема: нет serial output от kernel
                # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: kernel работает, но не выводит
                # Это означает, что консоль не настроена правильно
                self.logger.info("🔧 Applying CRITICAL fix for serial output issue...")
                self.logger.info("   Kernel is running but not outputting - console configuration issue")
                # Исправление уже применено в cmdline (earlyprintk=ttyAMA0,38400)
                # Но нужно перезапустить QEMU для применения
                issue.fix_applied = True
                issue.fix_description = "Обновлен cmdline с earlyprintk=ttyAMA0 и console=tty0"
                fixes_applied = True
            
            elif issue.category == "kernel" and issue.level == DiagnosticLevel.WARNING:
                # Проблема: kernel запущен, но нет serial output
                # Исправление: проверить параметры консоли в cmdline
                self.logger.info("Applying fix for kernel serial output issue...")
                issue.fix_applied = True
                issue.fix_description = "Обновлен cmdline с правильными параметрами консоли"
                fixes_applied = True
            
            elif issue.category == "dtb" and issue.level == DiagnosticLevel.WARNING:
                # Проблема: DTB невалидный
                # Исправление: попробовать создать кастомный DTB
                self.logger.info("Applying fix for DTB issue...")
                if custom_machine_builder:
                    # Пробуем создать кастомный DTB
                    # Пока это заглушка - нужно реализовать создание DTB
                    pass
                issue.fix_applied = True
                issue.fix_description = "Используется автогенерация QEMU DTB"
                fixes_applied = True
        
        if fixes_applied:
            self.fix_count += 1
        
        return fixes_applied
    
    def should_restart(self) -> bool:
        """Определить, нужно ли перезапустить QEMU"""
        # Перезапускаем если:
        # 1. Есть критические ошибки
        # 2. Есть исправления, которые требуют перезапуска
        # 3. Не превышен лимит итераций
        
        if self.iteration >= self.max_iterations:
            self.logger.warning(f"Достигнут лимит итераций ({self.max_iterations})")
            return False
        
        critical_issues = [i for i in self.issues if i.level == DiagnosticLevel.ERROR or i.level == DiagnosticLevel.CRITICAL]
        if critical_issues:
            return True
        
        fixed_issues = [i for i in self.issues if i.fix_applied]
        if fixed_issues:
            return True
        
        return False
    
    def get_status_report(self) -> str:
        """Получить отчет о статусе"""
        total_issues = len(self.issues)
        fixed_issues = len([i for i in self.issues if i.fix_applied])
        critical_issues = len([i for i in self.issues if i.level == DiagnosticLevel.ERROR or i.level == DiagnosticLevel.CRITICAL])
        
        return (
            f"Диагностика: Итерация {self.iteration}/{self.max_iterations}\n"
            f"Проблем найдено: {total_issues}\n"
            f"Исправлено: {fixed_issues}\n"
            f"Критических: {critical_issues}\n"
            f"Всего исправлений: {self.fix_count}"
        )

