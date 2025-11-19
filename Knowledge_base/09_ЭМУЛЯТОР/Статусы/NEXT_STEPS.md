# Следующие шаги для кастомизации QEMU

## Что сделано

1. ✅ Клонирован QEMU в `/Users/valentinezov/Projects/Tiggo/qemu_custom/qemu`
2. ✅ Создан базовый файл `hw/arm/g6sh.c` с машиной g6sh
3. ✅ Добавлен в `meson.build` и `Kconfig`
4. ✅ Исправлены основные ошибки (GIC инициализация, правильные API)

## Что нужно сделать

### 1. Исправить оставшиеся ошибки компиляции

В `g6sh.c` могут быть ошибки:
- `GIC_STATE` макрос может не существовать - нужно использовать правильный способ получения GIC state
- Инициализация CPU может быть неправильной
- Нужно добавить правильную инициализацию таймеров и других устройств

### 2. Собрать QEMU

```bash
cd /Users/valentinezov/Projects/Tiggo/qemu_custom/qemu
./configure --target-list=aarch64-softmmu --enable-debug
make -j$(sysctl -n hw.ncpu)
```

### 3. Протестировать с новой машиной

После сборки нужно обновить `qemu_manager.py` чтобы использовать кастомный QEMU:

```python
# В qemu_manager.py изменить путь к QEMU:
QEMU_BINARY = "/Users/valentinezov/Projects/Tiggo/qemu_custom/qemu/build/qemu-system-aarch64"
# И использовать машину g6sh:
-machine g6sh
```

### 4. Исправить проблемы по мере их появления

После первого запуска могут быть проблемы:
- Неправильные адреса устройств
- Проблемы с прерываниями
- Проблемы с памятью

## Файлы для работы

- `/Users/valentinezov/Projects/Tiggo/qemu_custom/qemu/hw/arm/g6sh.c` - основная машина
- `/Users/valentinezov/Projects/Tiggo/qemu_custom/qemu/hw/arm/meson.build` - сборка
- `/Users/valentinezov/Projects/Tiggo/qemu_custom/qemu/hw/arm/Kconfig` - конфигурация

## Полезные команды

```bash
# Проверить ошибки компиляции
cd /Users/valentinezov/Projects/Tiggo/qemu_custom/qemu
./configure --target-list=aarch64-softmmu 2>&1 | grep -i error

# Собрать только g6sh.c
make hw/arm/g6sh.o

# Проверить синтаксис
gcc -I. -Iinclude -c hw/arm/g6sh.c -o /dev/null
```

