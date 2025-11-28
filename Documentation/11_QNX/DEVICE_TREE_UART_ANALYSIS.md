# Device Tree и UART устройства - G6SH/T18FL3

**Дата:** 2025-11-27
**Цель:** Понимание структуры device tree и способов имитации UART устройств для эмулятора

---

## 📊 DEVICE TREE СТРУКТУРА

### Базовая информация

**Модель устройства:**
```
DesaySV G6SH H3N boards based on r8a7795
```

**Compatible:**
```
desaysv,g6sh
renesas,r8a7795
```

**Bootargs:**
```
console=ttyAMA0 androidboot.selinux=permissive androidboot.hardware=g6sh
init=/init loop.max_part=7 androidboot.revision=1.1 androidboot.board_id=0x0779611
init_time=1577808000 androidboot.serialno=00002260 skip_initramfs
androidboot.slot_suffix_bootloader=_b androidboot.slot_suffix_qnx=_b
androidboot.slot_suffix=_b androidboot.veritymode=eio rootwait ro
root=/dev/vda25 rootfstype=ext4 lpj=33333 quiet cma=64M clk_ignore_unused
blkdevparts=vdb:4194304(bootloader_a);vdc:4194304(bootloader_b)
```

**Консоль:** `console=ttyAMA0` (PL011 UART через virtio)

---

## 🔌 UART УСТРОЙСТВА

### 1. ttyAMA0 - PL011 UART (QNX Console)

**Device Tree Path:**
```
/vdevs/uart@1c090000
```

**Compatible:**
```
arm,pl011
arm,primecell
```

**Регистры (reg):**
```
0x1c090000 (base address)
0x00100000 (size)
```

**Interrupts:**
```
0x41000000 (IRQ)
0x04000000 (flags)
```

**TTY Driver:**
```
ttyAMA               /dev/ttyAMA   204 64-77 serial
```

**Device Path:**
```
/dev/ttyAMA0 -> ../../devices/platform/vdevs/1c090000.uart/tty/ttyAMA0
```

**Назначение:** Консоль QNX, используется для отладки и связи с QNX/MCU

**Статус:** ✅ Активен, используется как системная консоль

---

### 2. ttySC1 - HSCIF UART (GPS)

**Device Tree Path:**
```
/soc/serial@e6550000
```

**Compatible:**
```
renesas,hscif-r8a7795
renesas,rcar-gen3-hscif
renesas,hscif
```

**Регистры (reg):**
```
0xe6550000 (base address)
0x60000000 (size)
```

**Interrupts:**
```
0x9b000000 (IRQ)
0x04000000 (flags)
```

**Clock Names:**
```
brg_int
scif_clk
```

**TTY Driver:**
```
sci                  /dev/ttySC    204 8-17 serial
```

**Device Path:**
```
/dev/ttySC1 -> ../../devices/platform/soc/e6550000.serial/tty/ttySC1
```

**Alias:**
```
serial1 -> /soc/serial@e6550000
```

**Назначение:** GPS модуль

**Статус:** ✅ Активен

---

### 3. ttySC6 - HSCIF UART (Bluetooth)

**Device Tree Path:**
```
/soc/serial@e6540000
```

**Compatible:**
```
renesas,hscif-r8a7795
renesas,rcar-gen3-hscif
renesas,hscif
```

**Регистры (reg):**
```
0xe6540000 (base address)
0x60000000 (size)
```

**Interrupts:**
```
0x9a000000 (IRQ)
0x04000000 (flags)
```

**Clock Names:**
```
brg_int
scif_clk
```

**TTY Driver:**
```
sci                  /dev/ttySC    204 8-17 serial
```

**Device Path:**
```
/dev/ttySC6 -> ../../devices/platform/soc/e6540000.serial/tty/ttySC6
```

**Alias:**
```
serial6 -> /soc/serial@e6540000
```

**Features:**
```
uart-has-rtscts (RTS/CTS flow control)
```

**Назначение:** Bluetooth модуль

**Статус:** ✅ Активен

---

## 🗺️ DEVICE TREE СТРУКТУРА

### Основные узлы

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

### Свойства узлов

**serial@e6540000 (ttySC6):**
- `compatible`: `renesas,hscif-r8a7795`, `renesas,rcar-gen3-hscif`, `renesas,hscif`
- `reg`: `0xe6540000`, `0x60000000`
- `interrupts`: `0x9a000000`, `0x04000000`
- `clock-names`: `brg_int`, `scif_clk`
- `uart-has-rtscts`: присутствует
- `status`: `okay` (активен)

**serial@e6550000 (ttySC1):**
- `compatible`: `renesas,hscif-r8a7795`, `renesas,rcar-gen3-hscif`, `renesas,hscif`
- `reg`: `0xe6550000`, `0x60000000`
- `interrupts`: `0x9b000000`, `0x04000000`
- `clock-names`: `brg_int`, `scif_clk`
- `status`: `okay` (активен)

**uart@1c090000 (ttyAMA0):**
- `compatible`: `arm,pl011`, `arm,primecell`
- `reg`: `0x1c090000`, `0x00100000`
- `interrupts`: `0x41000000`, `0x04000000`
- `status`: `okay` (активен)

---

## 🎯 ИМИТАЦИЯ UART УСТРОЙСТВ В QEMU

### Подход 1: Использование встроенных QEMU UART

#### ttyAMA0 (PL011)

**QEMU уже поддерживает PL011:**
```bash
-chardev socket,id=pl011,host=localhost,port=1234,server,nowait \
-device pl011,chardev=pl011,id=uart0
```

**Device Tree для эмулятора:**
```dts
uart@1c090000 {
    compatible = "arm,pl011", "arm,primecell";
    reg = <0x1c090000 0x1000>;
    interrupts = <0x41 0x4>;
    clocks = <&uartclk>;
    clock-names = "uartclk";
    status = "okay";
};
```

#### ttySC1 и ttySC6 (HSCIF)

**Проблема:** QEMU не имеет встроенной поддержки Renesas HSCIF

**Решение 1: Использовать PL011 для всех**
- Заменить HSCIF на PL011 в device tree
- Изменить адреса регистров
- Адаптировать драйверы (или использовать generic serial)

**Решение 2: Создать кастомный HSCIF эмулятор**
- Реализовать `hw/char/renesas_hscif.c` в QEMU
- Эмулировать регистры HSCIF
- Поддержать прерывания и DMA

**Решение 3: Использовать generic serial**
- Использовать `serial` устройство QEMU
- Адаптировать device tree для generic serial
- Модифицировать драйверы в ядре

---

### Подход 2: Создание кастомных UART устройств

#### Структура для QEMU

**1. Создать hw/char/renesas_hscif.c:**

```c
#include "qemu/osdep.h"
#include "hw/char/renesas_hscif.h"
#include "hw/irq.h"
#include "hw/qdev-properties.h"
#include "migration/vmstate.h"
#include "chardev/char-fe.h"
#include "qemu/log.h"
#include "qemu/module.h"

#define HSCIF_REG_SIZE 0x1000

typedef struct RenesasHSCIFState {
    SysBusDevice parent_obj;
    MemoryRegion iomem;
    qemu_irq irq;
    CharBackend chr;

    uint32_t regs[HSCIF_REG_SIZE / 4];
    uint32_t base_addr;
} RenesasHSCIFState;

static void renesas_hscif_write(void *opaque, hwaddr addr,
                                uint64_t val, unsigned size)
{
    RenesasHSCIFState *s = opaque;

    // Эмуляция регистров HSCIF
    // SMR, BRR, SCR, TDR, SSR, SCMR, SEMR, etc.

    switch (addr) {
    case 0x00: // SMR - Serial Mode Register
        s->regs[addr / 4] = val;
        break;
    case 0x04: // BRR - Bit Rate Register
        s->regs[addr / 4] = val;
        break;
    // ... другие регистры
    default:
        qemu_log_mask(LOG_UNIMP, "HSCIF: Unimplemented write @ 0x%lx\n", addr);
        break;
    }
}

static uint64_t renesas_hscif_read(void *opaque, hwaddr addr,
                                   unsigned size)
{
    RenesasHSCIFState *s = opaque;

    switch (addr) {
    case 0x00: // SMR
        return s->regs[addr / 4];
    // ... другие регистры
    default:
        qemu_log_mask(LOG_UNIMP, "HSCIF: Unimplemented read @ 0x%lx\n", addr);
        return 0;
    }
}

static const MemoryRegionOps renesas_hscif_ops = {
    .read = renesas_hscif_read,
    .write = renesas_hscif_write,
    .endianness = DEVICE_NATIVE_ENDIAN,
    .valid = {
        .min_access_size = 4,
        .max_access_size = 4,
    },
};

static void renesas_hscif_realize(DeviceState *dev, Error **errp)
{
    RenesasHSCIFState *s = RENESAS_HSCIF(dev);
    SysBusDevice *sbd = SYS_BUS_DEVICE(dev);

    memory_region_init_io(&s->iomem, OBJECT(s), &renesas_hscif_ops,
                          s, "renesas-hscif", HSCIF_REG_SIZE);
    sysbus_init_mmio(sbd, &s->iomem);
    sysbus_init_irq(sbd, &s->irq);
}

static void renesas_hscif_class_init(ObjectClass *klass, void *data)
{
    DeviceClass *dc = DEVICE_CLASS(klass);

    dc->realize = renesas_hscif_realize;
}

static const TypeInfo renesas_hscif_info = {
    .name = TYPE_RENESAS_HSCIF,
    .parent = TYPE_SYS_BUS_DEVICE,
    .instance_size = sizeof(RenesasHSCIFState),
    .class_init = renesas_hscif_class_init,
};

static void renesas_hscif_register_types(void)
{
    type_register_static(&renesas_hscif_info);
}

type_init(renesas_hscif_register_types);
```

**2. Добавить в hw/char/meson.build:**
```meson
softmmu_ss.add(when: 'CONFIG_RENESAS_HSCIF', if_true: files('renesas_hscif.c'))
```

**3. Добавить в default-configs/devices/aarch64-softmmu.mak:**
```make
CONFIG_RENESAS_HSCIF=y
```

---

### Подход 3: Device Tree для эмулятора

#### Полный DTS для всех UART

```dts
/dts-v1/;

/ {
    compatible = "desaysv,g6sh-emu", "renesas,r8a7795";
    model = "DesaySV G6SH Emulator";

    chosen {
        bootargs = "console=ttyAMA0,115200 androidboot.selinux=permissive";
        stdout-path = "serial0:115200n8";
    };

    aliases {
        serial0 = &uart0;  // ttyAMA0
        serial1 = &uart1;  // ttySC1
        serial6 = &uart6;  // ttySC6
    };

    soc {
        #address-cells = <2>;
        #size-cells = <2>;
        compatible = "simple-bus";
        ranges;

        // ttySC6 (Bluetooth) - используем PL011 вместо HSCIF
        uart6: serial@e6540000 {
            compatible = "arm,pl011", "arm,primecell";
            reg = <0x0 0xe6540000 0x0 0x1000>;
            interrupts = <GIC_SPI 154 IRQ_TYPE_LEVEL_HIGH>;
            clocks = <&uartclk>;
            clock-names = "uartclk";
            status = "okay";
        };

        // ttySC1 (GPS) - используем PL011 вместо HSCIF
        uart1: serial@e6550000 {
            compatible = "arm,pl011", "arm,primecell";
            reg = <0x0 0xe6550000 0x0 0x1000>;
            interrupts = <GIC_SPI 155 IRQ_TYPE_LEVEL_HIGH>;
            clocks = <&uartclk>;
            clock-names = "uartclk";
            status = "okay";
        };
    };

    vdevs {
        #address-cells = <2>;
        #size-cells = <2>;
        compatible = "simple-bus";
        ranges;

        // ttyAMA0 (QNX Console) - PL011 через virtio
        uart0: uart@1c090000 {
            compatible = "arm,pl011", "arm,primecell";
            reg = <0x0 0x1c090000 0x0 0x1000>;
            interrupts = <GIC_SPI 65 IRQ_TYPE_LEVEL_HIGH>;
            clocks = <&uartclk>;
            clock-names = "uartclk";
            status = "okay";
        };
    };
};
```

---

## 🛠️ ПЛАН РЕАЛИЗАЦИИ

### Этап 1: Базовая эмуляция PL011

1. ✅ Использовать встроенный PL011 для ttyAMA0
2. ✅ Настроить device tree для PL011
3. ✅ Подключить через chardev socket

### Этап 2: Эмуляция HSCIF (ttySC1, ttySC6)

**Вариант A: Замена на PL011 (быстро)**
1. Изменить device tree: HSCIF → PL011
2. Изменить адреса регистров
3. Адаптировать драйверы (или использовать generic)

**Вариант B: Кастомный HSCIF (точно)**
1. Реализовать `hw/char/renesas_hscif.c`
2. Эмулировать все регистры HSCIF
3. Поддержать прерывания и DMA
4. Интегрировать в QEMU

### Этап 3: Интеграция с эмулятором

1. Добавить UART устройства в машину g6sh
2. Настроить адреса регистров
3. Настроить прерывания
4. Подключить chardev для отладки

---

## 📝 КОМАНДЫ QEMU

### Базовая конфигурация

```bash
qemu-system-aarch64 \
    -M g6sh \
    -cpu cortex-a57 \
    -smp 4 \
    -m 2G \
    \
    # ttyAMA0 (QNX Console)
    -chardev socket,id=qnx_uart,host=localhost,port=1234,server,nowait \
    -device pl011,chardev=qnx_uart,id=uart0 \
    \
    # ttySC1 (GPS)
    -chardev socket,id=gps_uart,host=localhost,port=1235,server,nowait \
    -device pl011,chardev=gps_uart,id=uart1 \
    \
    # ttySC6 (Bluetooth)
    -chardev socket,id=bt_uart,host=localhost,port=1236,server,nowait \
    -device pl011,chardev=bt_uart,id=uart6 \
    \
    -kernel boot.img \
    -append "console=ttyAMA0,115200"
```

### С кастомным device tree

```bash
qemu-system-aarch64 \
    -M g6sh \
    -dtb g6sh-emu.dtb \
    -chardev socket,id=qnx_uart,host=localhost,port=1234,server,nowait \
    -device pl011,chardev=qnx_uart,id=uart0,base=0x1c090000 \
    -chardev socket,id=gps_uart,host=localhost,port=1235,server,nowait \
    -device pl011,chardev=gps_uart,id=uart1,base=0xe6550000 \
    -chardev socket,id=bt_uart,host=localhost,port=1236,server,nowait \
    -device pl011,chardev=bt_uart,id=uart6,base=0xe6540000
```

---

## 🎯 ИТОГ

### Найденные UART устройства:

1. **ttyAMA0** - PL011 на `0x1c090000` (QNX Console)
2. **ttySC1** - HSCIF на `0xe6550000` (GPS)
3. **ttySC6** - HSCIF на `0xe6540000` (Bluetooth)

### Рекомендации:

1. **Для быстрого старта:** Использовать PL011 для всех UART
2. **Для точности:** Реализовать кастомный HSCIF эмулятор
3. **Для отладки:** Подключить через chardev socket

### Следующие шаги:

1. Создать device tree для эмулятора
2. Реализовать/адаптировать UART устройства
3. Интегрировать в машину g6sh
4. Протестировать подключение

