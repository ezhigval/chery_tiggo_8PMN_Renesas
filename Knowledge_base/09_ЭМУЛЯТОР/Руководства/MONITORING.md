# Мониторинг Serial Output

## Скрипты мониторинга

### 1. `watch_serial.sh` - Простой мониторинг
```bash
cd /Users/valentinezov/Projects/Tiggo/development/emulator
./watch_serial.sh
```
Показывает новые строки по мере их появления.

### 2. `monitor_serial_live.sh` - Расширенный мониторинг
```bash
cd /Users/valentinezov/Projects/Tiggo/development/emulator
./monitor_serial_live.sh
```
Показывает текущий вывод и новые данные.

### 3. Ручной мониторинг
```bash
cd /Users/valentinezov/Projects/Tiggo/development/emulator
PID=$(ps aux | grep "qemu_custom" | grep -v grep | head -1 | awk '{print $2}')
FILE="/tmp/t18fl3_qemu_serial_raw_${PID}.log"
strings "$FILE" | tail -30
```

## Текущий статус

- ✅ Эмулятор запущен с кастомным QEMU
- ✅ Изоляция настроена (все порты только localhost)
- ✅ Serial output появился (ядро запускается)
- ⚠️ Ядро остановилось на этапе GICv3

## Проблема

Ядро загружается до этапа инициализации GICv3, затем останавливается. Последняя строка:
```
[    0.000000] GICv3: no VLPI support, no direct LPI support
```

## Следующие шаги

1. Проверить конфигурацию GIC в DTB
2. Попробовать упростить конфигурацию
3. Проверить, не ждёт ли ядро инициализации устройств
