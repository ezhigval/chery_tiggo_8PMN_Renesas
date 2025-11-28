# Интеграция UART устройств в QEMU машину g6sh

**Дата:** 2025-11-27
**Цель:** Интегрировать все UART устройства в кастомную машину g6sh для QEMU

---

## 📋 ОБЗОР

Необходимо добавить в машину `g6sh` три UART устройства:
1. **ttyAMA0** - PL011 на `0x1c090000` (QNX Console)
2. **ttySC1** - PL011 на `0xe6550000` (GPS) - заменяем HSCIF на PL011
3. **ttySC6** - PL011 на `0xe6540000` (Bluetooth) - заменяем HSCIF на PL011

---

## 🛠️ РЕАЛИЗАЦИЯ

### Шаг 1: Модификация hw/arm/g6sh.c

Добавить создание UART устройств в функцию `g6sh_init()`:

```c
#include "hw/char/pl011.h"
#include "chardev/char-fe.h"

static void g6sh_init(MachineState *machine)
{
    // ... существующий код ...

    // ttyAMA0 - QNX Console (PL011 на 0x1c090000)
    qemu_chr_fe_init(&qnx_uart_chr, qnx_uart_chardev, &error_fatal);
    pl011_create(0x1c090000, qnx_uart_chr, qdev_get_gpio_in(gic, 65));

    // ttySC1 - GPS (PL011 на 0xe6550000, заменяем HSCIF)
    qemu_chr_fe_init(&gps_uart_chr, gps_uart_chardev, &error_fatal);
    pl011_create(0xe6550000, gps_uart_chr, qdev_get_gpio_in(gic, 155));

    // ttySC6 - Bluetooth (PL011 на 0xe6540000, заменяем HSCIF)
    qemu_chr_fe_init(&bt_uart_chr, bt_uart_chardev, &error_fatal);
    pl011_create(0xe6540000, bt_uart_chr, qdev_get_gpio_in(gic, 154));
}
```

### Шаг 2: Добавить chardev в командную строку QEMU

```bash
qemu-system-aarch64 \
    -M g6sh \
    -cpu cortex-a57 \
    -smp 4 \
    -m 2G \
    \
    # Chardev для UART устройств
    -chardev socket,id=qnx_uart,host=localhost,port=1234,server,nowait \
    -chardev socket,id=gps_uart,host=localhost,port=1235,server,nowait \
    -chardev socket,id=bt_uart,host=localhost,port=1236,server,nowait \
    \
    # Device tree
    -dtb g6sh-emu.dtb \
    \
    # Образы
    -kernel boot.img \
    -append "console=ttyAMA0,115200"
```

### Шаг 3: Полный код для g6sh.c

```c
static void g6sh_init(MachineState *machine)
{
    ARMCPU *cpu;
    MemoryRegion *sysmem = get_system_memory();
    MemoryRegion *ram = g_new0(MemoryRegion, 1);
    int n;

    /* Initialize CPUs */
    for (n = 0; n < smp_cpus; n++) {
        cpu = ARM_CPU(object_new(TYPE_ARM_CPU));
        object_property_set_int(OBJECT(cpu), "psci-conduit", QEMU_PSCI_CONDUIT_SMC,
                                &error_abort);
        if (n == 0) {
            object_property_set_bool(OBJECT(cpu), "realized", true, &error_abort);
        } else {
            object_property_set_bool(OBJECT(cpu), "realized", true, &error_abort);
        }
    }

    /* RAM */
    memory_region_init_ram(ram, NULL, "g6sh.ram", 2 * GiB, &error_fatal);
    memory_region_add_subregion(sysmem, 0x40000000, ram);

    /* GIC */
    gic = qdev_create(NULL, "arm_gicv3");
    qdev_prop_set_uint32(gic, "num-cpu", smp_cpus);
    qdev_prop_set_uint32(gic, "num-irq", 256);
    qdev_init_nofail(gic);
    sysbus_mmio_map(SYS_BUS_DEVICE(gic), 0, 0xf0000000);
    sysbus_mmio_map(SYS_BUS_DEVICE(gic), 1, 0xf00010000);

    /* UART устройства */
    Chardev *qnx_uart_chardev = qemu_chr_find("qnx_uart");
    Chardev *gps_uart_chardev = qemu_chr_find("gps_uart");
    Chardev *bt_uart_chardev = qemu_chr_find("bt_uart");

    if (qnx_uart_chardev) {
        qemu_chr_fe_init(&qnx_uart_chr, qnx_uart_chardev, &error_fatal);
        pl011_create(0x1c090000, qnx_uart_chr, qdev_get_gpio_in(gic, 65));
    }

    if (gps_uart_chardev) {
        qemu_chr_fe_init(&gps_uart_chr, gps_uart_chardev, &error_fatal);
        pl011_create(0xe6550000, gps_uart_chr, qdev_get_gpio_in(gic, 155));
    }

    if (bt_uart_chardev) {
        qemu_chr_fe_init(&bt_uart_chr, bt_uart_chardev, &error_fatal);
        pl011_create(0xe6540000, bt_uart_chr, qdev_get_gpio_in(gic, 154));
    }
}
```

---

## 🔧 ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ

Создать функцию для создания PL011 устройств:

```c
static void pl011_create(hwaddr base, CharBackend *chr, qemu_irq irq)
{
    DeviceState *dev;
    SysBusDevice *s;

    dev = qdev_create(NULL, "pl011");
    qdev_prop_set_chr(dev, "chardev", chr);
    qdev_init_nofail(dev);

    s = SYS_BUS_DEVICE(dev);
    sysbus_mmio_map(s, 0, base);
    sysbus_connect_irq(s, 0, irq);
}
```

---

## 📝 КОМАНДЫ ДЛЯ ТЕСТИРОВАНИЯ

### 1. Компиляция device tree

```bash
dtc -I dts -O dtb -o g6sh-emu.dtb g6sh-emu.dts
```

### 2. Запуск QEMU

```bash
qemu-system-aarch64 \
    -M g6sh \
    -cpu cortex-a57 \
    -smp 4 \
    -m 2G \
    -chardev socket,id=qnx_uart,host=localhost,port=1234,server,nowait \
    -chardev socket,id=gps_uart,host=localhost,port=1235,server,nowait \
    -chardev socket,id=bt_uart,host=localhost,port=1236,server,nowait \
    -dtb g6sh-emu.dtb \
    -kernel boot.img \
    -append "console=ttyAMA0,115200"
```

### 3. Подключение к UART через telnet

```bash
# QNX Console (ttyAMA0)
telnet localhost 1234

# GPS (ttySC1)
telnet localhost 1235

# Bluetooth (ttySC6)
telnet localhost 1236
```

---

## 🎯 ПРЕИМУЩЕСТВА ПОДХОДА

1. **Простота:** Используем встроенный PL011 вместо кастомного HSCIF
2. **Совместимость:** PL011 хорошо поддерживается в QEMU
3. **Отладка:** Легко подключиться через telnet/socket
4. **Гибкость:** Можно заменить на реальные устройства позже

---

## ⚠️ ОГРАНИЧЕНИЯ

1. **Не точная эмуляция HSCIF:** Используем PL011 вместо HSCIF
2. **Может потребоваться адаптация драйверов:** Если драйверы ожидают HSCIF
3. **Прерывания:** Нужно проверить правильность IRQ номеров

---

## 📚 СЛЕДУЮЩИЕ ШАГИ

1. ✅ Создать device tree для эмулятора
2. ⏳ Интегрировать UART в машину g6sh
3. ⏳ Протестировать подключение
4. ⏳ Проверить работу драйверов в Android
5. ⏳ При необходимости создать кастомный HSCIF эмулятор

