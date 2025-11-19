# Мониторинг Serial Output

## Текущий статус

✅ **Serial output появился!**
- Ядро запускается и выводит логи
- earlycon работает: `pl11 at MMIO 0x0000000009000000`
- Machine model: `chery,t18fl3-emulator`
- GICv3 обнаружен

⚠️ **Проблема:**
- Ядро остановилось после инициализации GICv3
- Размер лога не меняется (4269 bytes)
- Последняя строка: `GICv3: no VLPI support, no direct LPI support`

## Команды для мониторинга

### 1. Быстрый просмотр
```bash
cd /Users/valentinezov/Projects/Tiggo/development/emulator
./monitor_serial_live.sh
```

### 2. Периодическая проверка
```bash
cd /Users/valentinezov/Projects/Tiggo/development/emulator
PID=$(ps aux | grep "qemu_custom" | grep -v grep | head -1 | awk '{print $2}')
FILE="/tmp/t18fl3_qemu_serial_raw_${PID}.log"
watch -n 2 "strings $FILE | tail -20"
```

### 3. Проверка через QEMU Monitor
```bash
telnet 127.0.0.1 4445
# Затем в мониторе:
info registers
info cpus
info qtree
```

## Текущий вывод

Ядро загружается до этапа инициализации GICv3, затем останавливается. Возможные причины:
1. Проблема с конфигурацией GIC
2. Ядро ждёт инициализации устройств
3. Проблема с DTB или адресами устройств

## Следующие шаги

1. Проверить состояние через QEMU monitor
2. Проверить конфигурацию GIC в DTB
3. Попробовать упростить конфигурацию для диагностики

