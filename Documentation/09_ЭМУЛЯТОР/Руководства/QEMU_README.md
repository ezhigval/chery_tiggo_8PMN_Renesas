# Кастомизация QEMU для поддержки g6sh

## Быстрый старт

### 1. Клонировать QEMU
```bash
cd /Users/valentinezov/Projects/Tiggo/qemu_custom
git clone https://git.qemu.org/git/qemu.git
cd qemu
git checkout v8.2.0  # или последняя стабильная версия
```

### 2. Установить зависимости
```bash
brew install pkg-config glib pixman ninja python3
```

### 3. Настроить сборку
```bash
./configure --target-list=aarch64-softmmu --enable-debug
```

### 4. Собрать
```bash
make -j$(sysctl -n hw.ncpu)
```

## Структура изменений

После клонирования QEMU нужно будет добавить:

1. **hw/arm/g6sh.c** - описание машины g6sh
2. **hw/char/g6sh_scif.c** - эмуляция SCIF устройств
3. Изменения в конфигурационных файлах

## Следующие шаги

См. `../development/emulator/QEMU_CUSTOMIZATION_PLAN.md` для детального плана.

