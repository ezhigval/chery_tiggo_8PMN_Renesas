# Device Tree и UART устройства - Краткая сводка

**Дата:** 2025-11-27

---

## 🎯 ГЛАВНОЕ

### Device Tree структура

**Модель:** `DesaySV G6SH H3N boards based on r8a7795`
**Compatible:** `desaysv,g6sh`, `renesas,r8a7795`
**Консоль:** `console=ttyAMA0` (PL011 через virtio)

### UART устройства

| Устройство | Тип | Адрес | IRQ | Назначение | Статус |
|------------|-----|-------|-----|------------|--------|
| **ttyAMA0** | PL011 | `0x1c090000` | 65 | QNX Console | ✅ Активен |
| **ttySC1** | HSCIF | `0xe6550000` | 155 | GPS | ✅ Активен |
| **ttySC6** | HSCIF | `0xe6540000` | 154 | Bluetooth | ✅ Активен |

---

## 📋 DEVICE TREE ПУТИ

```
/sys/firmware/devicetree/base/
├── soc/
│   ├── serial@e6540000      # ttySC6 (Bluetooth)
│   └── serial@e6550000       # ttySC1 (GPS)
├── vdevs/
│   └── uart@1c090000        # ttyAMA0 (QNX Console)
└── aliases/
    ├── serial1 -> /soc/serial@e6550000
    └── serial6 -> /soc/serial@e6540000
```

---

## 🔧 ИМИТАЦИЯ ДЛЯ ЭМУЛЯТОРА

### Подход: Замена HSCIF на PL011

**Причина:** QEMU не имеет встроенной поддержки Renesas HSCIF

**Решение:** Использовать PL011 для всех UART устройств

### Device Tree для эмулятора

**Файл:** `g6sh-emu.dts`

**Изменения:**
- HSCIF → PL011 для ttySC1 и ttySC6
- Сохранены оригинальные адреса регистров
- Сохранены оригинальные IRQ номера

### Интеграция в QEMU

**Файл:** `QEMU_UART_INTEGRATION.md`

**Шаги:**
1. Добавить создание PL011 устройств в `hw/arm/g6sh.c`
2. Настроить chardev для каждого UART
3. Подключить через socket для отладки

---

## 📝 КОМАНДЫ

### Компиляция device tree

```bash
dtc -I dts -O dtb -o g6sh-emu.dtb g6sh-emu.dts
```

### Запуск QEMU с UART

```bash
qemu-system-aarch64 \
    -M g6sh \
    -chardev socket,id=qnx_uart,host=localhost,port=1234,server,nowait \
    -chardev socket,id=gps_uart,host=localhost,port=1235,server,nowait \
    -chardev socket,id=bt_uart,host=localhost,port=1236,server,nowait \
    -dtb g6sh-emu.dtb
```

### Подключение к UART

```bash
# QNX Console (ttyAMA0)
telnet localhost 1234

# GPS (ttySC1)
telnet localhost 1235

# Bluetooth (ttySC6)
telnet localhost 1236
```

---

## 📚 ДОКУМЕНТАЦИЯ

- **`DEVICE_TREE_UART_ANALYSIS.md`** - Полный анализ device tree и UART устройств
- **`QEMU_UART_INTEGRATION.md`** - План интеграции UART в QEMU
- **`g6sh-emu.dts`** - Device tree для эмулятора

---

## ✅ СТАТУС

- ✅ Device tree проанализирован
- ✅ UART устройства идентифицированы
- ✅ Device tree для эмулятора создан
- ⏳ Интеграция в QEMU (в процессе)

