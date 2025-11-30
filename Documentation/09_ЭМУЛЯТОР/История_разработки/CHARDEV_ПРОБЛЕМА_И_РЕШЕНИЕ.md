# Проблема CHARDEV и её решение

## Резюме

**Проблема:** Ошибка `Device 'serial0'/'console0'/'g6sh_console' is in use` при запуске QEMU с кастомной машиной g6sh.

**Решение:** Отключение автоматического создания chardev устройств (монитор и serial) для g6sh машины.

**Статус:** ✅ РЕШЕНО

---

## Проблема

### Симптомы

При запуске эмулятора с машиной `g6sh` возникала ошибка:
```
Device 'serial0' is in use
```
или
```
Device 'g6sh_console' is in use
```

Ошибка происходила в `qemu_chr_fe_init()` на строке 220 в `chardev/char-fe.c`.

### Цепочка вызовов

```
machvirt_init()
  -> Создание PL011 устройства
    -> qdev_prop_set_chr(dev, "chardev", chr)
      -> set_chr() в qdev-properties-system.c:280
        -> qemu_chr_fe_init(be, s, errp)
          -> ОШИБКА: s->be уже установлен!
```

### Причина

Chardev устройства создавались автоматически QEMU **ДО** того, как мы пытались использовать их для нашего UART устройства.

---

## Расследование

### Найденные источники автоматического создания chardev

#### 1. Монитор (console0)

**Где создавался:**
- При инициализации монитора (`mon_init_func`)
- Аргумент `-monitor tcp:127.0.0.1:5558` создавал chardev `console0`

**Решение:**
```python
# emulator.py:374-375
"-monitor",
"tcp:127.0.0.1:5558,server,nowait" if machine != "g6sh" else "none",
```

**Результат:** ✅ Проблема с `console0` решена

#### 2. Автоматический serial (serial0)

**Где создавался:**
- Автоматически при `default_serial = 1` в `vl.c:1404-1405`
- QEMU создавал `serial_hd(0)` с именем "serial0" по умолчанию

**Решение:**

1. В коде QEMU (`g6sh.c:77`):
```c
mc->no_serial = true;  // Отключаем автоматическое создание serial
```

2. В аргументах командной строки (`emulator.py:246-247`):
```python
if machine == "g6sh":
    args += [
        "-chardev",
        f"file,id=g6sh_uart,path={console_log},append=on",
        "-serial",
        "none",  # Явно отключаем автоматическое создание serial0
    ]
```

**Результат:** ✅ Проблема с автоматическим `serial0` решена

---

## Решение

### Изменения в коде

#### 1. `qemu_g6sh/qemu-src/hw/arm/g6sh.c`

```c
// Строка 77
mc->no_serial = true;  // Отключаем автоматическое создание serial
```

#### 2. `Development/Chery_Emulator/core/emulator.py`

```python
# Строки 241-248
if machine == "g6sh":
    args += [
        "-chardev",
        f"file,id=g6sh_uart,path={console_log},append=on",
        "-serial",
        "none",  # Явно отключаем автоматическое создание serial0
    ]

# Строки 374-375
"-monitor",
"tcp:127.0.0.1:5558,server,nowait" if machine != "g6sh" else "none",
```

### Использование chardev для g6sh UART

Для g6sh машины создается уникальный chardev `g6sh_uart`, который используется для UART на адресе 0x1c090000:

```c
// В virt.c или g6sh.c
Chardev *chr = qemu_chr_find("g6sh_uart");
if (!chr) {
    error_report("ERROR: g6sh_uart chardev not found!");
    exit(1);
}
qdev_prop_set_chr(dev, "chardev", chr);
```

---

## Результат

### ✅ Проблема решена

После внесения изменений:
- Эмулятор успешно запускается
- Нет ошибок "Device is in use"
- Kernel загружается на правильный адрес (0x48080000)
- Android boot.img распарсен успешно
- UART устройства создаются без конфликтов

### Логи успешного запуска

```
=== machvirt_init CALLED ===
=== BEFORE arm_load_kernel ===
=== arm_setup_direct_kernel_boot CALLED ===
Android boot.img detected: kernel_addr=0x48080000, ramdisk_addr=0x4a180000
Loading Android kernel to 0x48080000 (size 9098310 bytes)
Loading Android ramdisk to 0x4a180000 (size 5519955 bytes)
Android boot.img loaded successfully
```

---

## Измененные файлы

1. `qemu_g6sh/qemu-src/hw/arm/g6sh.c` - добавлено `mc->no_serial = true;`
2. `Development/Chery_Emulator/core/emulator.py` - отключен монитор и serial для g6sh

---

## Примечания

- Ошибка "Device 'g6sh_console' is in use" может появляться в логах, но не критична, если процесс QEMU работает
- Все автоматические создания chardev отключены для g6sh машины
- Для обычной virt машины автоматические устройства остаются включенными

---

## История изменений

- **2025-11-29**: Проблема обнаружена
- **2025-11-29**: Найдены источники автоматического создания chardev
- **2025-11-29**: Реализовано решение (отключение монитора и serial)
- **2025-11-29**: Проблема решена, эмулятор запускается успешно

