# План кастомизации QEMU для поддержки g6sh

## Цель
Добавить поддержку Renesas R-Car g6sh (r8a7795) в QEMU для правильной эмуляции с реальными адресами устройств.

## Шаги

### 1. Подготовка окружения
```bash
# Клонировать QEMU
git clone https://git.qemu.org/git/qemu.git
cd qemu
git checkout v8.2.0  # или последняя стабильная версия

# Установить зависимости
brew install pkg-config glib pixman ninja
```

### 2. Создание новой машины g6sh

**Файл: `hw/arm/g6sh.c`**
- Описать машину g6sh
- Настроить память, CPU, устройства
- Добавить SCIF устройства с правильными адресами (0xe6e80000, 0xe6e88000)

### 3. Реализация SCIF устройств

**Файл: `hw/char/g6sh_scif.c`**
- Эмуляция SCIF (Serial Communication Interface)
- Регистры, прерывания, clock
- Маппинг на QEMU serial backend

### 4. Интеграция в QEMU

**Изменения в:**
- `hw/arm/Kconfig` - добавить опцию g6sh
- `hw/arm/meson.build` - добавить файлы в сборку
- `include/hw/arm/g6sh.h` - заголовочные файлы

### 5. Сборка и тестирование

```bash
./configure --target-list=aarch64-softmmu
make -j$(nproc)
```

## Структура файлов

```
qemu/
├── hw/
│   ├── arm/
│   │   ├── g6sh.c          # Описание машины
│   │   └── Kconfig         # Конфигурация
│   └── char/
│       └── g6sh_scif.c     # SCIF устройство
└── include/
    └── hw/
        └── arm/
            └── g6sh.h      # Заголовки
```

## Ключевые адреса g6sh

- SCIF0: 0xe6e80000
- SCIF1: 0xe6e88000
- CAN: 0xe6c00000
- Ethernet: 0xee700000

## Следующие шаги

1. Клонировать QEMU
2. Создать базовую структуру машины
3. Реализовать SCIF устройство
4. Интегрировать в сборку
5. Протестировать

