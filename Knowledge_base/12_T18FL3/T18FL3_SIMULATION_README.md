# Виртуальная симуляция T18FL3

## Обзор

Этот документ описывает процесс создания и запуска виртуальной симуляции головного устройства Chery Tiggo 8 PRO MAX T18FL3 с чипом 703000765AA.

## Архитектура системы

### Аппаратная часть

- **Процессор:** Renesas g6sh (703000765AA)
  - Архитектура: ARM64 (AArch64)
  - Совместимый CPU для эмуляции: Cortex-A57
  - Память: 4GB RAM (в эмуляции)
  - Ядра: 4 cores

- **DSP:** Analog Devices ADSP-21489
  - Цифровая обработка сигналов
  - Аудио обработка
  - Прошивка: ADSP-21489.ldr

- **Радио модуль:** Motorola S-Record формат
  - Прошивка: radio.bin

### Программная часть

#### Гибридная система: Android + QNX

**Android 9 (Pie):**
- SDK: 28
- Build: Renesas/g6sh_t18fl3_international/g6sh:9/PQ2A.190405.003/229
- SELinux: permissive
- Разделы:
  - boot.img (32 MB) - kernel + ramdisk
  - system.img (2.5 GB) - ext2
  - vendor.img (768 MB) - ext2
  - product.img (12 GB) - ext2

**QNX:**
- Real-time операционная система
- Разделы:
  - qnx_boot.img (64 MB) - FAT16
  - qnx_system.img (2.5 GB)

#### Дополнительные компоненты

- **Chime:** Звуковые сигналы (chime.bin, chime.data)
- **VR:** Голосовое управление iFlytek (vr/iflytek/)
- **Maps:** Навигация TurboDog (TurboDog/)
- **DSP:** Прошивка ADSP-21489

## Требования

### Программное обеспечение

1. **QEMU** (версия 10.1.2 или выше)
   ```bash
   brew install qemu  # macOS
   # или
   sudo apt-get install qemu-system-arm  # Linux
   ```

2. **Python 3** (для извлечения компонентов из boot.img)

3. **Инструменты для работы с файловыми системами:**
   - mkfs.ext2
   - mount (для монтирования образов)

4. **payload-dumper-go** (для распаковки payload.bin)
   ```bash
   brew install payload-dumper-go  # macOS
   ```

### Дисковое пространство

- Минимум 20 GB свободного места
- Рекомендуется 50 GB для комфортной работы

## Структура файлов

```
Tiggo/
├── T18FL3 703000765AA MOD SW 02.09.00 + CHIME + VR + DSP + MAPS/
│   └── T18FL3  703000765AA MOD SW 02.09.00 + CHIME + VR + DSP + MAPS/
│       ├── soc_update.zip          # Android OTA пакет
│       ├── radio.bin               # Прошивка радио
│       ├── chime.bin               # Звуковые сигналы
│       ├── chime.data              # Данные звуковых сигналов
│       ├── DSPUpgradeFile.tar.gz   # DSP прошивка
│       ├── TurboDog/               # Навигация
│       └── vr/                     # Голосовое управление
├── update_extracted/
│   └── payload/
│       ├── boot.img                # Android boot
│       ├── system.img              # Android system
│       ├── vendor.img              # Android vendor
│       ├── product.img             # Android product
│       ├── qnx_boot.img            # QNX boot
│       └── qnx_system.img          # QNX system
└── development/
    └── scripts/
        └── simulate_t18fl3_complete.sh  # Скрипт симуляции
```

## Использование

### Быстрый старт

1. **Распаковка образов (если еще не сделано):**
   ```bash
   cd "T18FL3 703000765AA MOD SW 02.09.00 + CHIME + VR + DSP + MAPS/T18FL3  703000765AA MOD SW 02.09.00 + CHIME + VR + DSP + MAPS"
   payload-dumper-go soc_update.zip/extracted/soc_update/payload.bin -o ../../update_extracted/payload
   ```

2. **Запуск симуляции:**
   ```bash
   cd development/scripts
   ./simulate_t18fl3_complete.sh
   ```

### Режимы запуска

#### Только Android
```bash
./simulate_t18fl3_complete.sh --android
```

#### Только QNX
```bash
./simulate_t18fl3_complete.sh --qnx
```

#### Android + QNX (по умолчанию)
```bash
./simulate_t18fl3_complete.sh --both
# или просто
./simulate_t18fl3_complete.sh
```

## Параметры виртуальной машины

### CPU и память
- **CPU:** Cortex-A57 (совместим с Renesas g6sh)
- **Память:** 4 GB RAM
- **Ядра:** 4 cores (SMP)

### Диски
- **system.img** - Android system раздел
- **vendor.img** - Android vendor раздел
- **product.img** - Android product раздел
- **userdata.img** - Создается автоматически (6 GB)
- **cache.img** - Создается автоматически (512 MB)
- **qnx_boot.img** - QNX загрузчик (если включен)
- **qnx_system.img** - QNX система (если включен)

### Сеть
- **Режим:** User networking (NAT)
- **Проброс портов:**
  - 5555 - ADB
  - 8080 - HTTP (если нужно)

### Графика
- **Тип:** VirtIO GPU
- **Дисплей:** Default (SDL/VNC)

## Подключение к системе

### ADB (Android Debug Bridge)

После запуска системы можно подключиться через ADB:

```bash
adb connect localhost:5555
adb shell
```

### Монитор QEMU

В консоли QEMU доступен монитор:
- Нажмите `Ctrl+A`, затем `C` для входа в монитор
- Команды:
  - `info registers` - регистры CPU
  - `info mem` - информация о памяти
  - `info block` - информация о дисках
  - `quit` - выход из QEMU

## Отладка

### Логи QEMU

Логи сохраняются в `/tmp/t18fl3_qemu_YYYYMMDD_HHMMSS.log`

Просмотр логов:
```bash
tail -f /tmp/t18fl3_qemu_*.log
```

### Типичные проблемы

1. **QEMU не найден:**
   ```bash
   brew install qemu
   # или проверьте путь: which qemu-system-aarch64
   ```

2. **Образы не найдены:**
   - Убедитесь, что payload.bin распакован
   - Проверьте пути в скрипте

3. **Недостаточно памяти:**
   - Уменьшите размер userdata.img в скрипте
   - Или увеличьте RAM хоста

4. **Система не загружается:**
   - Проверьте логи QEMU
   - Убедитесь, что kernel и ramdisk извлечены правильно
   - Проверьте параметры загрузки (cmdline)

## Интеграция компонентов

### DSP эмуляция

DSP процессор ADSP-21489 требует специальной эмуляции. В текущей версии он не эмулируется напрямую, но прошивка доступна в системе.

### Chime

Файлы chime.bin и chime.data должны быть скопированы в систему:
```bash
# После загрузки Android
adb push chime.bin /system/etc/
adb push chime.data /system/etc/
```

### VR (Голосовое управление)

Ресурсы iFlytek находятся в `vr/iflytek/` и должны быть смонтированы в `/vr/` в системе.

### Maps (Навигация)

TurboDog навигация находится в `TurboDog/` и должна быть смонтирована в соответствующую директорию.

## Производительность

### Рекомендации

- Используйте SSD для образов
- Выделите достаточно RAM (минимум 8 GB на хосте)
- Используйте KVM/QEMU acceleration если доступно

### Оптимизация

В скрипте используются параметры:
- `cache=writeback` - для дисков
- `highmem=on` - для больших объемов памяти
- VirtIO устройства - для лучшей производительности

## Безопасность

⚠️ **Важно: Система запускается с SELinux в permissive режиме для отладки.

В продакшене это должно быть исправлено.

## Дальнейшее развитие

1. ✅ Базовая симуляция Android
2. ⏳ Полная интеграция QNX
3. ⏳ Эмуляция DSP процессора
4. ⏳ Интеграция всех компонентов (Chime, VR, Maps)
5. ⏳ Создание автоматизированных тестов
6. ⏳ Оптимизация производительности

## Полезные ссылки

- [QEMU Documentation](https://www.qemu.org/documentation/)
- [Android Emulator Guide](https://developer.android.com/studio/run/emulator)
- [Renesas g6sh Documentation](https://www.renesas.com/)
- [QNX Documentation](https://www.qnx.com/developers/docs/)

## Поддержка

При возникновении проблем:
1. Проверьте логи QEMU
2. Убедитесь, что все зависимости установлены
3. Проверьте версии инструментов
4. Изучите информационную базу: `T18FL3_KNOWLEDGE_BASE.md`

