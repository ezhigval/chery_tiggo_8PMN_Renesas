# QEMU SCIF Fork for QNX / g6sh

## Цель

Сделать отдельный, чистый форк QEMU, который:

- **Эмулирует реальное железо g6sh** на уровне UART для QNX:
  - SCIF0 (`scif0` на `0xe6e80000`) для `devc-serscif`;
  - при желании позже — SCIF1/SCIF6 для GPS/BT.
- **Не меняет образы** (`hypervisor-ifs-rcar_h3-graphics.bin`, `qnx_boot.img`,
  `qnx_system.img`, Android `.img`).
- Даёт консоль QNX через TCP‑сокет (telnet/nc) и встраивается в наш Python‑core
  через уже готовый `QnxVmManager`.

Этот каталог — **отдельный подпроект**, чтобы не ломать существующий
`qemu_g6sh` и иметь возможность экспериментировать с QEMU как с полноценным
форком.

---

## Структура

```text
Development/Chery_Emulator/qemu_scif_fork/
  README.md                 # этот файл
  setup_scif_qemu.sh        # скрипт клонирования/сборки форка
  patches/
    0001-g6sh-base-machine.patch        # (TODO) базовая машина g6sh
    0002-renesas-hscif-device.patch     # (TODO) HSCIF/SCIF UART
    0003-wire-scif0-into-g6sh.patch     # (TODO) интеграция в машину
```

Патчи из `patches/` описаны концептуально; их можно наполнять по мере
разработки, не рискуя затёреть рабочий код.

---

## Быстрый старт форка

```bash
cd /Users/valentinezov/Projects/Tiggo/Development/Chery_Emulator/qemu_scif_fork
bash setup_scif_qemu.sh
```

Скрипт:

1. Клонирует **чистый QEMU** в `qemu-src/` (ветка `v8.2.0` или та, которую
   зададим).
2. Применяет патчи из `patches/` (по очереди, чтобы было видно конфликты).
3. Собирает `aarch64-softmmu` и кладёт бинарь
   `qemu-system-aarch64` в корень `qemu_scif_fork/`.

> Важно: этот форк никак не трогает существующий `qemu_g6sh`. Он живёт
> отдельно и может эволюционировать независимо.

---

## План патчей (концептуально)

### 0001-g6sh-base-machine.patch

- Создать новую ARM‑машину `g6sh`:
  - Файл `hw/arm/g6sh.c` + `hw/arm/g6sh.h`;
  - Родитель — `TYPE_VIRT_MACHINE`, но **без зависимостей от SuperH**.
- Настроить:
  - CPU: `cortex-a57`, SMP=4,
  - RAM: 4 GiB,
  - базовую карту устройств (GIC, MMIO) можно взять из `virt.c`.
- Зарегистрировать машину:
  - `hw/arm/meson.build`, `hw/arm/Kconfig`,
  - `configs/devices/arm-softmmu/default.mak` (`CONFIG_G6SH=y`).

### 0002-renesas-hscif-device.patch

- Новый deivce: `hw/char/renesas_hscif.c` + `include/hw/char/renesas_hscif.h`.
- Интерфейс:
  - `SysBusDevice` с MMIO‑областью размером 0x1000,
  - `CharBackend` (чтение/запись байтов в сокет),
  - минимальный набор регистров, достаточный для `devc-serscif`:
    - SMR, BRR, SCR, TDR/RDR, SSR/FSR, FCR.
- Встроить в сборку:
  - `hw/char/meson.build` (`CONFIG_RENESAS_HSCIF`),
  - `hw/char/Kconfig` (`config RENESAS_HSCIF`).

### 0003-wire-scif0-into-g6sh.patch

- В `g6sh.c`:
  - создать инстанс `renesas-hscif` со свойством:
    - `base = 0xe6e80000` (SCIF0),
    - IRQ совпадает с тем, что в DT g6sh (см. `DEVICE_TREE_UART_ANALYSIS.md`).
  - повесить его на `SysBusDevice`:
    - `sysbus_mmio_map` на `0xe6e80000`,
    - `sysbus_connect_irq` на нужный GIC‑SPI.
- Добавить параметр командной строки:

```bash
-chardev socket,id=qnx_scif,host=localhost,port=1234,server=on,wait=off \
-device renesas-hscif,chardev=qnx_scif
```

---

## Интеграция с Python‑core

После того как форк будет собран и отлажен:

1. В `emulator_config.yaml` задать:

```yaml
qemu:
  binary: Development/Chery_Emulator/qemu_scif_fork/qemu-system-aarch64
  machine: "g6sh"
```

2. В `core/qnx_vm.py` оставить только:

```python
-chardev socket,id=qnx_scif,host=localhost,port=1234,server=on,wait=off
-device renesas-hscif,chardev=qnx_scif
```

3. Дальше `/qnx/start`, `/qnx/state`, `/qnx/console` продолжат работать как
   сейчас, но консоль QNX будет идти через настоящий SCIF0 внутри форка.

---

## Почему так безопаснее и быстрее

- Мы **не ломаем текущий рабочий `qemu_g6sh`**, а строим отдельный playground
  для экспериментов с UART и картой устройств.
- Любые агрессивные C‑изменения (новые девайсы, IRQ, DTB) живут только тут.
- В любой момент можно:
  - удалить `qemu_scif_fork/`,
  - клонировать свежий QEMU,
  - применить/пересобрать патчи начисто.


