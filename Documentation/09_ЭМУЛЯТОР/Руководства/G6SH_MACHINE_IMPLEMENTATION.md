# Реализация машины G6SH для QEMU

## Описание

Машина `g6sh` - это кастомная ARM машина QEMU для эмуляции Chery T18FL3 головного устройства на базе Renesas R-Car G6SH SoC. Основная цель - запускать **оригинальные образы boot.img без модификаций**, эмулируя реальное железо настолько точно, чтобы система не понимала, что она работает в виртуалке.

## Архитектура

### Наследование от virt машины

Машина `g6sh` наследуется от стандартной ARM `virt` машины QEMU:

```
TYPE_VIRT_MACHINE (базовая ARM virt машина)
    ↓
TYPE_G6SH_MACHINE (наша кастомная машина)
```

Это позволяет:
- Использовать все возможности virt машины (GIC, UART, VirtIO, etc.)
- Переопределить только необходимые части для поддержки R-Car G6SH
- Легко расширять функциональность в будущем

### Файлы реализации

- `qemu_g6sh/qemu-src/hw/arm/g6sh.c` - основная реализация машины
- `qemu_g6sh/qemu-src/hw/arm/android_bootimg.c` - парсер Android boot.img

## Поддержка Android boot.img

### Автоматическая загрузка kernel

Машина автоматически распознает и загружает Android boot.img:

1. **Парсинг boot.img** - проверяется magic "ANDROID!" и извлекаются:
   - Адрес загрузки kernel (обычно `0x48080000`)
   - Адрес загрузки ramdisk (обычно `0x4a180000`)
   - Размеры kernel и ramdisk
   - Page size (обычно 2048 байт)

2. **Загрузка kernel** - kernel загружается по адресу из header boot.img
3. **Загрузка ramdisk** - ramdisk загружается по адресу из header boot.img

### Формат Android boot.img

```
+------------------+
|  Header (1632B)  |  Magic: "ANDROID!"
|  - kernel_addr   |  Адрес загрузки kernel (0x48080000)
|  - kernel_size   |  Размер kernel
|  - ramdisk_addr  |  Адрес загрузки ramdisk (0x4a180000)
|  - ramdisk_size  |  Размер ramdisk
|  - page_size     |  Размер страницы (обычно 2048)
+------------------+
|  Padding         |  До page_size
+------------------+
|  Kernel          |  Начинается с offset = page_size
|  (сжатый/raw)    |
+------------------+
|  Padding         |  До следующей границы page_size
+------------------+
|  Ramdisk         |  После kernel, выровнен по page_size
+------------------+
```

### Исправления парсера

**Проблема:** Исходный парсер использовал фиксированный размер заголовка `ANDROID_BOOT_IMAGE_HEADER_V1_SIZE` (16384 байт), но реальный Android boot.img имеет заголовок 1632 байт, а kernel начинается с offset = `page_size`.

**Решение:** Исправлен расчет offset для kernel:

```c
// Было:
kernel_offset = ANDROID_BOOT_IMAGE_HEADER_V1_SIZE;  // 16384

// Стало:
kernel_offset = page_size;  // Обычно 2048, из header boot.img
```

Это обеспечивает правильную загрузку kernel для всех версий Android boot.img (v1, v2, v3+).

## Инициализация машины

### Порядок вызова

1. **g6sh_machine_class_init()** - инициализация класса машины
   - Устанавливается описание: "Chery T18FL3 g6sh (Renesas R-Car G6SH, Android boot.img support)"
   - Переопределяется `mc->init = g6sh_machine_init`
   - Устанавливаются значения по умолчанию (4 CPU, 4GB RAM)

2. **g6sh_machine_init()** - инициализация экземпляра машины
   - Вызывается `machvirt_init()` для инициализации всей hardware виртуализации
   - virt машина автоматически:
     - Распознает boot.img по magic "ANDROID!"
     - Загружает kernel по адресу из header
     - Загружает ramdisk по адресу из header

### Вызов родительского init

```c
static void g6sh_machine_init(MachineState *machine)
{
    // Вызываем инициализацию базовой virt машины
    extern void machvirt_init(MachineState *machine);
    machvirt_init(machine);

    // Все настройки hardware, загрузка kernel/ramdisk происходят в machvirt_init
}
```

## Адреса устройств

### RAM и загрузка

- **RAM base**: `0x40000000` (устанавливается virt машиной)
- **Kernel load address**: `0x48080000` (из boot.img header)
- **Ramdisk load address**: `0x4a180000` (из boot.img header)

### UART устройства

В будущем можно добавить эмуляцию реальных UART адресов R-Car G6SH:
- `0x1c090000` - PL011 (системная консоль)
- `0xe6e80000` - SCIF (специфичные устройства)

Пока используются стандартные virt UART устройства.

## Использование

### Командная строка QEMU

```bash
qemu-system-aarch64 \
  -M g6sh \
  -kernel boot.img \
  -dtb g6sh-emu.dtb \
  -append "console=ttyAMA0,115200 ..." \
  -drive file=system.img,format=raw,if=virtio
```

### Через эмулятор

Машина используется автоматически при указании в `emulator_config.yaml`:

```yaml
qemu:
  binary: Development/Chery_Emulator/qemu_g6sh/qemu-system-aarch64
  machine: g6sh
  dtb: Development/Chery_Emulator/qemu_g6sh/g6sh-emu.dtb
```

## Автоматическая работа

### Без модификаций boot.img

Машина **автоматически**:
1. ✅ Распознает Android boot.img по magic
2. ✅ Извлекает адреса загрузки из header
3. ✅ Загружает kernel по правильному адресу (0x48080000)
4. ✅ Загружает ramdisk по правильному адресу (0x4a180000)
5. ✅ Поддерживает сжатые kernel (LZ4, gzip) - QEMU распаковывает автоматически

**Не требуется:**
- ❌ Извлечение kernel из boot.img
- ❌ Распаковка kernel
- ❌ Модификация boot.img
- ❌ Ручная настройка адресов загрузки

### Поддержка различных образов

Машина работает с любыми Android boot.img образами для R-Car G6SH:
- Разные версии boot.img (v1, v2, v3+)
- Сжатые и несжатые kernel
- Разные page_size (обычно 2048, но может быть другим)

## Расширение функциональности

### Планы на будущее

1. **Реальные адреса устройств R-Car G6SH**
   - Эмуляция SCIF UART на реальных адресах
   - Эмуляция CAN контроллеров
   - Эмуляция специфичных устройств G6SH

2. **Device Tree**
   - Автоматическая генерация DTB для g6sh
   - Поддержка реальных адресов устройств в DTB

3. **Дополнительные устройства**
   - Эмуляция GPU R-Car G6SH
   - Эмуляция специфичных периферийных устройств

## Логирование

Машина логирует все важные события:

- `/tmp/qemu_g6sh.log` - общие логи машины
- `stderr` - критические сообщения (для отладки)
- Логи Android boot.img парсера (в stdout/stderr QEMU)

Пример логов:
```
=== g6sh_machine_init CALLED ===
kernel_filename=Development/Chery_Emulator/payload/boot.img
=== load_android_bootimg CALLED ===
Android boot.img detected: kernel_addr=0x48080000, ramdisk_addr=0x4a180000
Loading Android kernel to 0x48080000 (size 9098310 bytes)
Loading Android ramdisk to 0x4a180000 (size 5519955 bytes)
Android boot.img loaded successfully
```

## История изменений

### 2025-01-XX: Исправление загрузки boot.img

**Проблема:** Kernel загружался по неправильному адресу (0x40080000 вместо 0x48080000), система не запускалась с ошибкой "Undefined Instruction".

**Решение:**
1. ✅ Исправлен Android boot.img парсер - использует `page_size` как offset для kernel вместо фиксированного размера заголовка (16384 байт)
2. ✅ Упрощена реализация g6sh машины - не переопределяем init, используем родительский init от virt машины
3. ✅ Настроена автоматическая загрузка kernel/ramdisk по адресам из boot.img header
4. ✅ QEMU пересобран с исправлениями
5. ✅ Добавлена полная документация реализации

**Результат:** Система теперь автоматически загружает оригинальный boot.img без модификаций. Kernel загружается по адресу 0x48080000 из boot.img header, ramdisk по 0x4a180000.

**Измененные файлы:**
- `qemu_g6sh/qemu-src/hw/arm/android_bootimg.c` - исправлен расчет kernel offset
- `qemu_g6sh/qemu-src/hw/arm/g6sh.c` - упрощена реализация (использует родительский init)
- `Development/Chery_Emulator/core/emulator.py` - обновлена загрузка boot.img для g6sh
- `Development/Chery_Emulator/core/boot_extractor.py` - новый модуль (резерв, пока не используется)

## См. также

- `Documentation/02_АНАЛИЗЫ/KERNEL_COMPATIBILITY.md` - Совместимость ядра
- `Documentation/02_АНАЛИЗЫ/BOOT_SANDWICH_GUIDE.md` - Создание boot.img
- `Development/Chery_Emulator/qemu_g6sh/README.md` - Сборка QEMU

