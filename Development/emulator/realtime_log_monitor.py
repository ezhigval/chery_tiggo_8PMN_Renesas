#!/usr/bin/env python3
"""
Real-time Log Monitor для T18FL3 Emulator
Перехватывает все логи в режиме реального времени и диагностирует проблемы запуска
"""

import sys
import os
import time
import subprocess
import threading
import socket
import select
import psutil
from pathlib import Path
from datetime import datetime
from collections import deque
from typing import Optional, List, Dict
import json

# Цвета для терминала
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'

class RealTimeLogMonitor:
    """Монитор логов в реальном времени"""
    
    def __init__(self):
        self.running = True
        self.qemu_process: Optional[psutil.Process] = None
        self.qemu_pid: Optional[int] = None
        self.serial_output = deque(maxlen=1000)  # Последние 1000 строк
        self.qemu_stderr = deque(maxlen=500)
        self.stats = {
            'serial_lines': 0,
            'qemu_errors': 0,
            'start_time': time.time(),
            'last_serial_time': None,
            'last_adb_check': None,
            'adb_connected': False,
            'vnc_ports': {'5910': False, '5911': False}
        }
        self.lock = threading.Lock()
        
    def find_qemu_process(self) -> Optional[int]:
        """Найти процесс QEMU для T18FL3"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if not cmdline:
                    continue
                
                # Ищем qemu-system-aarch64 с нашими параметрами
                if 'qemu-system-aarch64' in ' '.join(cmdline):
                    # Проверяем что это наш процесс (T18FL3)
                    cmdline_str = ' '.join(cmdline)
                    if 'T18FL3' in cmdline_str or 't18fl3' in cmdline_str or 'display=:10' in cmdline_str or 'port=5910' in cmdline_str:
                        return proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def check_port(self, port: int) -> bool:
        """Проверить открыт ли порт"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result == 0
        except:
            return False
    
    def check_adb(self) -> bool:
        """Проверить доступность ADB"""
        try:
            result = subprocess.run(
                ['adb', 'devices'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                # Проверяем есть ли наше устройство
                output = result.stdout
                if 'T18FL3' in output or '5556' in output or '5555' in output:
                    # Ищем device в статусе
                    lines = output.split('\n')
                    for line in lines:
                        if 'device' in line and ('5556' in line or '5555' in line):
                            return True
            return False
        except:
            return False
    
    def monitor_qemu_output(self):
        """Мониторинг вывода QEMU (serial output)"""
        if not self.qemu_process:
            return
        
        try:
            # Получаем stdout и stderr процесса
            # ВАЖНО: QEMU использует -serial stdio, поэтому serial output идет в stdout
            stdout_fd = None
            stderr_fd = None
            
            # Пытаемся получить файловые дескрипторы
            try:
                # Для psutil нужно использовать другой подход
                # Читаем через /proc или используем другой метод
                pass
            except:
                pass
            
            # Альтернативный метод: читаем через lsof и tail
            # Или используем strace/dtrace для перехвата
            # Но проще всего - читать напрямую из процесса если возможно
            
            # Пока используем метод проверки через psutil
            while self.running and self.qemu_process.is_running():
                try:
                    # Проверяем что процесс еще работает
                    if self.qemu_process.status() == psutil.STATUS_ZOMBIE:
                        break
                    
                    # Читаем информацию о процессе
                    time.sleep(0.1)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
        except Exception as e:
            self.print_error(f"Ошибка мониторинга QEMU: {e}")
    
    def monitor_system_logs(self):
        """Мониторинг системных логов"""
        log_dir = Path(__file__).parent / "logs"
        if not log_dir.exists():
            return
        
        # Находим последний лог файл
        log_files = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not log_files:
            return
        
        latest_log = log_files[0]
        
        # Используем tail -f для мониторинга
        try:
            process = subprocess.Popen(
                ['tail', '-f', '-n', '0', str(latest_log)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            while self.running:
                try:
                    line = process.stdout.readline()
                    if line:
                        line = line.strip()
                        if line:
                            # Фильтруем только важные сообщения
                            if any(keyword in line.lower() for keyword in [
                                'serial', 'qemu', 'kernel', 'android', 'adb', 
                                'vnc', 'error', 'warning', 'boot', 'init'
                            ]):
                                self.print_log_line("SYSTEM", line)
                except:
                    break
        except Exception as e:
            self.print_error(f"Ошибка мониторинга системных логов: {e}")
    
    def monitor_qemu_direct(self):
        """Прямой мониторинг QEMU через его stdout/stderr"""
        # Находим процесс QEMU
        pid = self.find_qemu_process()
        if not pid:
            return
        
        self.qemu_pid = pid
        self.qemu_process = psutil.Process(pid)
        
        # На macOS используем lsof для получения файловых дескрипторов
        # Затем читаем через /dev/fd или используем dtrace/strace
        
        # Метод: Используем lsof для получения stdout/stderr процесса
        try:
            # Получаем файловые дескрипторы через lsof
            result = subprocess.run(
                ['lsof', '-p', str(pid), '-a', '-d', '0,1,2'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                # Парсим вывод lsof
                for line in result.stdout.split('\n')[1:]:  # Пропускаем заголовок
                    if not line.strip():
                        continue
                    parts = line.split()
                    if len(parts) >= 4:
                        fd = parts[3]
                        file_path = parts[-1] if len(parts) > 4 else ''
                        
                        # stdout (fd=1) или stderr (fd=2)
                        if fd in ['1', '2']:
                            # Если это pipe, пытаемся читать через другой метод
                            if 'pipe' in file_path.lower() or 'PIPE' in file_path:
                                # Это pipe - используем альтернативный метод
                                pass
        
        except Exception as e:
            self.print_error(f"Ошибка получения FD: {e}")
        
        # Альтернативный метод: читаем логи напрямую из JSONL файлов
        # и мониторим QEMU monitor
        self.monitor_qemu_via_monitor()
        
        # Также мониторим логи в реальном времени
        self.monitor_log_files_realtime()
    
    def monitor_qemu_via_monitor(self):
        """Мониторинг через QEMU monitor (telnet)"""
        monitor_port = 4445  # Порт из конфигурации
        
        while self.running:
            try:
                if not self.check_port(monitor_port):
                    time.sleep(1)
                    continue
                
                # Подключаемся к monitor
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect(('127.0.0.1', monitor_port))
                
                # Отправляем команды для получения информации
                commands = [
                    b"info status\n",
                    b"info registers\n",
                    b"info network\n",
                ]
                
                for cmd in commands:
                    try:
                        sock.send(cmd)
                        response = sock.recv(4096).decode('utf-8', errors='ignore')
                        if response:
                            self.print_log_line("QEMU_MONITOR", response.strip())
                    except:
                        pass
                
                sock.close()
                time.sleep(5)  # Проверяем каждые 5 секунд
                
            except (socket.error, ConnectionRefusedError):
                time.sleep(1)
            except Exception as e:
                self.print_error(f"Ошибка monitor: {e}")
                time.sleep(2)
    
    def print_header(self):
        """Вывести заголовок"""
        os.system('clear' if os.name != 'nt' else 'cls')
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}T18FL3 EMULATOR - REAL-TIME LOG MONITOR{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
        print()
    
    def print_status(self):
        """Вывести статус системы"""
        uptime = time.time() - self.stats['start_time']
        
        # Статус QEMU
        qemu_status = f"{Colors.RED}НЕ НАЙДЕН{Colors.RESET}"
        if self.qemu_process and self.qemu_process.is_running():
            qemu_status = f"{Colors.GREEN}РАБОТАЕТ{Colors.RESET} (PID: {self.qemu_pid})"
            try:
                cpu_percent = self.qemu_process.cpu_percent(interval=0.1)
                mem_info = self.qemu_process.memory_info()
                mem_mb = mem_info.rss / 1024 / 1024
                qemu_status += f" | CPU: {cpu_percent:.1f}% | MEM: {mem_mb:.0f}MB"
            except:
                pass
        
        # Статус портов
        vnc1_status = f"{Colors.GREEN}ОТКРЫТ{Colors.RESET}" if self.check_port(5910) else f"{Colors.RED}ЗАКРЫТ{Colors.RESET}"
        vnc2_status = f"{Colors.GREEN}ОТКРЫТ{Colors.RESET}" if self.check_port(5911) else f"{Colors.RED}ЗАКРЫТ{Colors.RESET}"
        adb_port_status = f"{Colors.GREEN}ОТКРЫТ{Colors.RESET}" if self.check_port(5556) else f"{Colors.RED}ЗАКРЫТ{Colors.RESET}"
        
        # Статус ADB
        adb_status = f"{Colors.GREEN}ПОДКЛЮЧЕН{Colors.RESET}" if self.stats['adb_connected'] else f"{Colors.RED}НЕ ПОДКЛЮЧЕН{Colors.RESET}"
        
        print(f"{Colors.BOLD}СТАТУС СИСТЕМЫ:{Colors.RESET}")
        print(f"  QEMU:        {qemu_status}")
        print(f"  VNC Display1: {vnc1_status} (порт 5910)")
        print(f"  VNC Display2: {vnc2_status} (порт 5911)")
        print(f"  ADB порт:     {adb_port_status} (порт 5556)")
        print(f"  ADB устройство: {adb_status}")
        print(f"  Serial строк: {self.stats['serial_lines']}")
        print(f"  Время работы: {uptime:.0f}с")
        if self.stats['last_serial_time']:
            time_since_serial = time.time() - self.stats['last_serial_time']
            print(f"  Последний serial: {time_since_serial:.1f}с назад")
        print()
        print(f"{Colors.BOLD}{'='*80}{Colors.RESET}")
        print()
    
    def print_log_line(self, source: str, line: str):
        """Вывести строку лога"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Цвета по источнику
        color_map = {
            'SERIAL': Colors.GREEN,
            'QEMU': Colors.YELLOW,
            'QEMU_MONITOR': Colors.CYAN,
            'SYSTEM': Colors.BLUE,
            'ERROR': Colors.RED,
        }
        
        color = color_map.get(source, Colors.RESET)
        source_tag = f"{color}[{source:15s}]{Colors.RESET}"
        
        print(f"{Colors.GRAY}{timestamp}{Colors.RESET} {source_tag} {line}")
        
        # Сохраняем в очередь
        if source == 'SERIAL':
            with self.lock:
                self.serial_output.append((timestamp, line))
                self.stats['serial_lines'] += 1
                self.stats['last_serial_time'] = time.time()
    
    def print_error(self, message: str):
        """Вывести ошибку"""
        self.print_log_line("ERROR", message)
        with self.lock:
            self.stats['qemu_errors'] += 1
    
    def run_diagnostics(self):
        """Запустить диагностику"""
        self.print_header()
        
        print(f"{Colors.BOLD}🔍 ДИАГНОСТИКА СИСТЕМЫ{Colors.RESET}")
        print()
        
        # Проверка QEMU процесса
        print("1. Поиск процесса QEMU...")
        pid = self.find_qemu_process()
        if pid:
            print(f"   {Colors.GREEN}✅ QEMU найден: PID {pid}{Colors.RESET}")
            self.qemu_pid = pid
            self.qemu_process = psutil.Process(pid)
        else:
            print(f"   {Colors.RED}❌ QEMU процесс не найден{Colors.RESET}")
            print(f"   {Colors.YELLOW}   Убедитесь что эмулятор запущен{Colors.RESET}")
            return
        
        # Проверка портов
        print()
        print("2. Проверка портов...")
        ports_to_check = {
            5910: "VNC Display 1",
            5911: "VNC Display 2", 
            5556: "ADB",
            4445: "QEMU Monitor"
        }
        
        for port, name in ports_to_check.items():
            if self.check_port(port):
                print(f"   {Colors.GREEN}✅ {name} (порт {port}): ОТКРЫТ{Colors.RESET}")
            else:
                print(f"   {Colors.RED}❌ {name} (порт {port}): ЗАКРЫТ{Colors.RESET}")
        
        # Проверка ADB
        print()
        print("3. Проверка ADB...")
        if self.check_adb():
            print(f"   {Colors.GREEN}✅ ADB устройство обнаружено{Colors.RESET}")
            self.stats['adb_connected'] = True
        else:
            print(f"   {Colors.RED}❌ ADB устройство не обнаружено{Colors.RESET}")
            print(f"   {Colors.YELLOW}   Запуск: adb devices{Colors.RESET}")
            try:
                result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=2)
                print(f"   {Colors.GRAY}   Вывод: {result.stdout.strip()}{Colors.RESET}")
            except:
                pass
        
        # Проверка образов
        print()
        print("4. Проверка образов...")
        base_path = Path(__file__).parent.parent.parent / "update_extracted" / "payload"
        required_images = ["boot.img", "system.img", "vendor.img", "product.img"]
        
        for img_name in required_images:
            img_path = base_path / img_name
            if img_path.exists():
                size_gb = img_path.stat().st_size / (1024**3)
                print(f"   {Colors.GREEN}✅ {img_name}: {size_gb:.2f} GB{Colors.RESET}")
            else:
                print(f"   {Colors.RED}❌ {img_name}: НЕ НАЙДЕН{Colors.RESET}")
        
        print()
        print(f"{Colors.BOLD}{'='*80}{Colors.RESET}")
        print()
        print(f"{Colors.BOLD}📊 МОНИТОРИНГ В РЕАЛЬНОМ ВРЕМЕНИ{Colors.RESET}")
        print(f"{Colors.GRAY}Нажмите Ctrl+C для выхода{Colors.RESET}")
        print()
    
    def monitor_loop(self):
        """Главный цикл мониторинга"""
        # Запускаем потоки мониторинга
        threads = []
        
        # Поток проверки статуса
        def status_checker():
            while self.running:
                try:
                    # Обновляем статус ADB
                    self.stats['adb_connected'] = self.check_adb()
                    self.stats['vnc_ports']['5910'] = self.check_port(5910)
                    self.stats['vnc_ports']['5911'] = self.check_port(5911)
                    
                    # Перерисовываем статус каждые 2 секунды
                    time.sleep(2)
                except:
                    time.sleep(1)
        
        status_thread = threading.Thread(target=status_checker, daemon=True)
        status_thread.start()
        threads.append(status_thread)
        
        # Поток мониторинга системных логов
        log_thread = threading.Thread(target=self.monitor_system_logs, daemon=True)
        log_thread.start()
        threads.append(log_thread)
        
        # Поток мониторинга QEMU
        if self.qemu_process:
            qemu_thread = threading.Thread(target=self.monitor_qemu_direct, daemon=True)
            qemu_thread.start()
            threads.append(qemu_thread)
        
        # Поток мониторинга лог файлов в реальном времени
        log_realtime_thread = threading.Thread(target=self.monitor_log_files_realtime, daemon=True)
        log_realtime_thread.start()
        threads.append(log_realtime_thread)
        
        # Главный цикл
        last_status_update = 0
        while self.running:
            try:
                # Обновляем статус каждые 2 секунды
                current_time = time.time()
                if current_time - last_status_update >= 2:
                    self.print_status()
                    last_status_update = current_time
                
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                print()
                print(f"{Colors.YELLOW}Остановка мониторинга...{Colors.RESET}")
                self.running = False
                break
            except Exception as e:
                self.print_error(f"Ошибка в главном цикле: {e}")
                time.sleep(1)
    
    def monitor_log_files_realtime(self):
        """Мониторинг лог файлов в реальном времени"""
        log_dir = Path(__file__).parent / "logs"
        if not log_dir.exists():
            return
        
        last_positions = {}
        
        while self.running:
            try:
                # Ищем все лог файлы
                jsonl_files = sorted(log_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
                log_files = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
                
                # Читаем новые строки из JSONL
                for jsonl_file in jsonl_files[:2]:  # Только последние 2 файла
                    file_path = str(jsonl_file)
                    last_pos = last_positions.get(file_path, 0)
                    
                    try:
                        with open(jsonl_file, 'r', encoding='utf-8') as f:
                            f.seek(last_pos)
                            new_lines = f.readlines()
                            last_positions[file_path] = f.tell()
                            
                            for line in new_lines:
                                try:
                                    entry = json.loads(line.strip())
                                    source = entry.get('source', 'system')
                                    component = entry.get('module', '')
                                    message = entry.get('message', '')
                                    level = entry.get('level', 'INFO')
                                    
                                    # Определяем тип сообщения
                                    if 'qemu' in source.lower() or 'qemu' in component.lower():
                                        if 'serial' in message.lower() or 'SERIAL' in component.upper():
                                            source_tag = 'SERIAL'
                                        else:
                                            source_tag = 'QEMU'
                                    else:
                                        source_tag = 'SYSTEM'
                                    
                                    # Показываем все важные сообщения
                                    if any(keyword in message.lower() for keyword in [
                                        'serial', 'kernel', 'android', 'boot', 'init', 
                                        'error', 'warning', 'adb', 'vnc', 'monitor',
                                        'first data', 'data received'
                                    ]) or level in ['ERROR', 'WARNING']:
                                        self.print_log_line(source_tag, message)
                                        
                                        # Обновляем статистику
                                        if source_tag == 'SERIAL':
                                            with self.lock:
                                                self.stats['serial_lines'] += 1
                                                self.stats['last_serial_time'] = time.time()
                                except:
                                    pass
                    except:
                        pass
                
                # Также читаем обычные log файлы для поиска serial output
                for log_file in log_files[:1]:  # Только последний
                    file_path = str(log_file)
                    last_pos = last_positions.get(file_path, 0)
                    
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            f.seek(last_pos)
                            new_lines = f.readlines()
                            last_positions[file_path] = f.tell()
                            
                            for line in new_lines:
                                line = line.strip()
                                if not line:
                                    continue
                                
                                # Ищем serial output в логах
                                if any(keyword in line.lower() for keyword in [
                                    'serial', 'kernel', 'android', 'boot', 'init',
                                    '[qemu]', 'monitor:', 'first data'
                                ]):
                                    # Определяем тип
                                    if 'serial' in line.lower() or 'SERIAL' in line:
                                        source_tag = 'SERIAL'
                                    elif 'qemu' in line.lower():
                                        source_tag = 'QEMU'
                                    else:
                                        source_tag = 'SYSTEM'
                                    
                                    # Извлекаем сообщение (после timestamp и уровня)
                                    parts = line.split(']', 3)
                                    if len(parts) >= 4:
                                        message = parts[-1].strip()
                                    else:
                                        message = line
                                    
                                    self.print_log_line(source_tag, message)
                                    
                                    if source_tag == 'SERIAL':
                                        with self.lock:
                                            self.stats['serial_lines'] += 1
                                            self.stats['last_serial_time'] = time.time()
                    except:
                        pass
                
                time.sleep(0.5)  # Проверяем каждые 0.5 секунды
                
            except Exception as e:
                self.print_error(f"Ошибка чтения логов: {e}")
                time.sleep(1)
    
    def read_latest_logs(self):
        """Читать последние логи из файлов (legacy метод, теперь используется monitor_log_files_realtime)"""
        pass

def main():
    """Главная функция"""
    monitor = RealTimeLogMonitor()
    
    try:
        # Запускаем диагностику
        monitor.run_diagnostics()
        
        # Запускаем мониторинг
        monitor.monitor_loop()
        
    except KeyboardInterrupt:
        print()
        print(f"{Colors.YELLOW}Мониторинг остановлен{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Критическая ошибка: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

