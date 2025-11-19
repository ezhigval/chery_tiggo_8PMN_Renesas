# Очистка эмуляторов

## Команды для остановки всех процессов

```bash
# Остановить все QEMU и эмуляторы
pkill -9 -f "qemu-system-aarch64"
pkill -9 -f "python3 main.py"
pkill -9 -f "t18fl3"
pkill -9 -f "watch_serial"
pkill -9 -f "monitor_serial"

# Удалить lock файлы
rm -f /var/folders/fz/2mw_b5ms4tj13vt4wlks6v_r0000gp/T/t18fl3_emulator.lock

# Проверить, что всё остановлено
ps aux | grep -E "(qemu|t18fl3|emulator)" | grep -v grep
```

## Проверка портов

```bash
# Проверить занятые порты
netstat -an | grep -E "(5556|8081|4445|5910)" | grep LISTEN
```

## После очистки

Система готова к чистому запуску. Все процессы остановлены, порты освобождены.

