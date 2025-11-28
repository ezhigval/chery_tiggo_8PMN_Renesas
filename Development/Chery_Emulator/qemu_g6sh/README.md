# qemu_g6sh – кастомный QEMU для Chery T18FL3

Цель: собрать отдельный QEMU с машиной **g6sh**, которая использует реальные адреса устройств
и даёт консоль ядра на `ttyAMA0` (PL011 на `0x1c090000`), как в настоящем блоке.

## Структура

```text
Development/Chery_Emulator/qemu_g6sh/
  README.md              # это файл
  setup_qemu_g6sh.sh     # скрипт клонирования/сборки
  qemu-src/              # (после клона) исходники QEMU
  build/                 # артефакты сборки
  qemu-system-aarch64    # собранный бинарь с машиной g6sh
```

## Быстрый старт

```bash
cd Development/Chery_Emulator/qemu_g6sh
bash setup_qemu_g6sh.sh
```

Скрипт:

1. Клонирует QEMU в подкаталог `qemu-src` (ветка `v8.2.0`).
2. Конфигурирует сборку `aarch64-softmmu`.
3. Собирает бинарь `qemu-system-aarch64` и кладёт симлинк в `qemu_g6sh/`.

После успешной сборки можно в `Development/Chery_Emulator/emulator_config.yaml`
установить:

```yaml
qemu:
  binary: Development/Chery_Emulator/qemu_g6sh/qemu-system-aarch64
  machine: "g6sh"
  dtb: Documentation/11_QNX/g6sh-emu.dtb
```

> ⚠️ Машина `g6sh` пока должна быть добавлена вручную в исходники QEMU
> (`hw/arm/g6sh.c`, `hw/arm/Kconfig`, `hw/arm/meson.build` и др.) по плану в
> `Documentation/09_ЭМУЛЯТОР/Руководства/QEMU_CUSTOMIZATION_PLAN.md`.


