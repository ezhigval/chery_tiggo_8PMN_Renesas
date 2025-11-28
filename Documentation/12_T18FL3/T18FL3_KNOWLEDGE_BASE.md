# Информационная база: Chery Tiggo 8 PRO MAX T18FL3
> ⚠️ Файл знаний T18FL3_KNOWLEDGE_BASE.md является **основным справочником** по системе.  
> Просьба **не удалять** и не затирать существующий контент. Разрешены только дополнения и правки по существу.

## Общая информация

**Модель:** Chery Tiggo 8 PRO MAX 2023 (рестайлинг)  
**Головное устройство:** T18FL3  
**Чипсет:** 703000765AA (Renesas g6sh)  
**Версия ПО:** MOD SW 02.09.00  
**Дата сборки:** 2025-04-08 (для chime), 2025-10-31 (для VR)

## Архитектура системы

### Гибридная система: Android + QNX

Система использует **двойную загрузку** с двумя операционными системами:

1. **Android 9 (Pie)** - SDK 28
   - Build: `Renesas/g6sh_t18fl3_international/g6sh:9/PQ2A.190405.003/229:user/dev-keys`
   - Security patch: 2019-04-05
   - SELinux: permissive mode

2. **QNX** - Real-time операционная система для критичных функций

### Разделы системы

#### Android разделы:
- `boot.img` (32 MB) - Android boot image с kernel и ramdisk
- `system.img` (2.5 GB) - ext2 файловая система Android
- `vendor.img` (768 MB) - ext2 файловая система vendor
- `product.img` (12 GB) - ext2 файловая система product
- `vbmeta.img` (4 KB) - Android Verified Boot metadata
- `dtb.img` (1 MB) - Device Tree Blob
- `dtbo.img` (512 KB) - Device Tree Overlay
- `gan_boot.img` (64 MB) - FAT16 образ для Android загрузчика

#### QNX разделы:
- `qnx_boot.img` (64 MB) - FAT16 образ для QNX загрузчика
- `qnx_system.img` (2.5 GB) - QNX система

#### Общие разделы:
- `bootloader.img` (2.8 MB) - Загрузчик системы

## Аппаратная часть

### Процессор
- **Производитель:** Renesas
- **Модель:** g6sh (703000765AA)
- **Архитектура:** ARM64 (AArch64)
- **Совместимость для эмуляции:** Cortex-A57
- **Память:** 4 GB RAM (в эмуляции, реальное устройство может иметь другой объем)

### Дисплеи
- **Количество:** 2 изогнутых цифровых экрана
- **Размер:** 12.3 дюйма каждый
- **Назначение:** 
  - Один для приборной панели
  - Один для мультимедийной системы
- **Тип:** ЖК-экраны с сенсорным управлением

### DSP (Digital Signal Processor)
- **Модель:** Analog Devices ADSP-21489
- **Прошивка:** `ADSP-21489.ldr`
- **Версия:** CHERY_DSP_FW_20250423_21
- **MD5:** be5695c2d05cfce2e5d31e938bccf04c
- **Назначение:** 
  - Обработка аудио сигналов
  - Высококачественное звучание
  - Многоканальный звук (10 динамиков Sony)

### Радио модуль
- **Формат:** Motorola S-Record
- **Файл:** `radio.bin` (1.5 MB)
- **Назначение:** Прошивка радио модуля
- **Функции:** FM/AM радио, возможно DAB+

### Звуковые сигналы (Chime)
- **Формат:** Кастомный бинарный формат
- **Файлы:** 
  - `chime.bin` (3.8 MB) - заголовок: "T18_Chime_20250408_R"
  - `chime.data` (3.8 MB) - данные звуковых сигналов
- **Назначение:** Системные звуковые сигналы и оповещения

### Консоль, UART и загрузочные параметры (из реального устройства)

- **Платформа:** `ro.board.platform = r8a7795` → Renesas R-Car H3 (R-Car Gen3).
- **Драйверы символьных устройств (`/proc/devices`):**
  - `204 ttySC` — семейство последовательных портов Renesas SCIF/HSCIF.
  - `204 ttyAMA` — PL011‑совместимый UART.
- **Реальные UART‑узлы из Device Tree (`/sys/firmware/devicetree/base` → `device_tree_sys.dts`):**
  - `/soc/serial@e6540000`
    - `reg = <0x00 0xe6540000 0x00 0x60>`
    - `compatible = "renesas,hscif-r8a7795", "renesas,rcar-gen3-hscif", "renesas,hscif"`
    - `status = "okay"`
    - `interrupts = <0x00 0x9a 0x04>`
    - алиасы: `serial6`, `hscif0`
  - `/soc/serial@e6550000`
    - `reg = <0x00 0xe6550000 0x00 0x60>`
    - `compatible = "renesas,hscif-r8a7795", "renesas,rcar-gen3-hscif", "renesas,hscif"`
    - `status = "okay"`
    - `interrupts = <0x00 0x9b 0x04>`
    - алиасы: `serial1`, `hscif1`
- **Алиасы UART (узел `/aliases`):**
  - `serial1 = "/soc/serial@e6550000"`
  - `serial6 = "/soc/serial@e6540000"`
- **Bootargs (узел `/chosen/bootargs` реального ГУ):**
  - `console=ttyAMA0`
  - `androidboot.selinux=permissive`
  - `androidboot.hardware=g6sh`
  - `init=/init`
  - `loop.max_part=7`
  - `androidboot.revision=1.1`
  - `androidboot.board_id=0x0779611`
  - `init_time=1577808000`
  - `androidboot.serialno=00002260`
  - `skip_initramfs`
  - `androidboot.slot_suffix_bootloader=_b`
  - `androidboot.slot_suffix_qnx=_b`
  - `androidboot.slot_suffix=_b`
  - `androidboot.veritymode=eio`
  - `rootwait`
  - `ro`
  - `root=/dev/vda25`
  - `rootfstype=ext4`
  - `lpj=33333`
  - `quiet`
  - `cma=64M`
  - `clk_ignore_unused`
  - `blkdevparts=vdb:4194304(bootloader_a);vdc:4194304(bootloader_b)`

> Вывод: ядро Android на реальном ГУ рассчитывает на конфигурацию R-Car H3 с HSCIF‑UARTами (`renesas,hscif`) и консолью, указанной как `ttyAMA0` в bootargs, при этом DT описывает реальные UART‑узлы по адресам `0xe6540000` и `0xe6550000`. Для корректной эмуляции необходимо либо реализовать поддержку этих UART в QEMU, либо смэппить их на доступные виртуальные UART‑девайсы, сохраняя семантику консоли.

### Коммуникационные модули
- **Bluetooth:** Поддержка подключения мобильных устройств
- **Wi-Fi:** Беспроводная сеть для обновлений и интернета
- **GPS:** Глобальная система позиционирования для навигации
- **4G/LTE:** Возможна поддержка сотовой связи (требует проверки)

### Интерфейсы автомобиля
- **CAN-шина:** Взаимодействие с электронными модулями автомобиля
  - Климат-контроль
  - Системы помощи водителю (ADAS)
  - Датчики парковки
  - Камеры кругового обзора
- **Телематика:** Chery Connect для удаленного управления
- **Система кругового обзора:** 540° обзор (включая рельеф под автомобилем)

## Компоненты системы

### 1. Навигационная система (TurboDog)
- **Расположение:** `TurboDog/`
- **Компоненты:**
  - Карты: `mapdata/` - карты России и других регионов
  - Голосовые данные: `rundir/Voice/` - TTS голоса на разных языках
  - Форматы: `.smf`, `.rdx`, `.vt`, `.dat`, `.idx`

### 2. Голосовое управление (VR - Voice Recognition)
- **Производитель:** iFlytek (科大讯飞)
- **Расположение:** `vr/iflytek/`
- **Версия ресурсов:** `3.x.en.ar.es.ru.fa.t18fl3.2025.10.31.1055`
- **Компоненты:**
  - **MVWRes** - Multi-Voice Wake-up (многоголосое пробуждение)
  - **SRRes** - Speech Recognition (распознавание речи)
  - **TTSRes** - Text-to-Speech (синтез речи)
  - **SERes** - Speech Enhancement (улучшение речи)
  - **CataRes** - Каталог ресурсов
- **Поддерживаемые языки:**
  - Английский (en_us)
  - Русский (ru_ru)
  - Арабский (ar)
  - Испанский (es)
  - Персидский (fa)
  - Португальский (pt_br)
- **Бизнес-логика:** `business.ini` - конфигурация голосовых команд

### 3. DSP обновление
- **Архив:** `DSPUpgradeFile.tar.gz` (180 KB)
- **Содержимое:**
  - `ADSP-21489.ldr` - загрузчик DSP
  - `dsp_upgrade.cfg` - конфигурация обновления
  - `dsp_version_file` - версия прошивки

## Форматы файлов

### ⚠️ КРИТИЧЕСКИ ВАЖНО: Ext2 файловые системы БЕЗ MBR/GPT

**system.img, vendor.img, product.img:**
- **Формат:** Raw ext2 файловые системы (НЕ разделы с MBR/GPT!)
- **Структура:**
  - Начинаются с **суперблока ext2** по смещению **0x400 (1024 байта)**
  - Магическое число: **0xEF53**
  - Размер блока: **4096 байт** (4 KB)
  - **НЕТ** MBR/GPT заголовков
- **Для QEMU:** Использовать `format=raw` для прямого монтирования ext2
- **UUID:**
  - system.img: 5397fe43-8f26-4a99-a045-47df0f9e675d
  - vendor.img: 8c5f9ae2-5adf-4313-b9e8-60ac50f9a249 (label="vendor")
  - product.img: 1c8d6645-91ea-4a99-8126-239116b020b4 (label="product")

### Android OTA пакет
- **Формат:** ZIP архив с подписью SignApk
- **Структура:**
  - `payload.bin` - основной payload (1.8 GB)
  - `payload_properties.txt` - свойства payload
  - `care_map.txt` - карта разделов
  - `compatibility.zip` - данные совместимости
  - `META-INF/` - метаданные и подписи

### Boot image
- **Формат:** Android Boot Image v1
- **Структура:**
  - Magic: "ANDROID!"
  - Заголовок: 1632 байта
  - Kernel: 9098310 байт @ 0x48080000 (выровнен по page_size=2048)
  - Ramdisk: 5519955 байт @ 0x4a180000 (выровнен по page_size=2048)
  - Page size: **2048 байт** (2 KB)
  - Cmdline: `androidboot.selinux=permissive buildvariant=user`

### QNX образы
- **qnx_boot.img:** FAT16 с MBR boot sector (OEM-ID: "MSWIN4.1")
- **qnx_system.img:** MBR boot sector с QNX Boot Loader v1.2b
- **Назначение:** Real-time функции автомобиля
- **Особенность:** QNX boot loader может требовать специальной конфигурации

### Chime файлы
- **Формат:** Кастомный бинарный
- **Структура:** Заголовок с метаданными + данные

## Конфигурация

### Модель устройства
- **Файл:** `modelConfig.txt`
- **Содержимое:** `IC2563#` - идентификатор модели чипа

### Материалы
- **Файл:** `materialsConfig.txt`
- **Содержимое:** `{"wifi/bt":"88335"}` - конфигурация WiFi/BT модуля

## Особенности системы

1. **Гибридная архитектура:** Android для приложений, QNX для критичных функций
2. **Двойная загрузка:** Возможность выбора между Android и QNX
3. **Кастомные компоненты:** Chime, DSP, навигация TurboDog
4. **Мультиязычность:** Поддержка множества языков для TTS и распознавания речи
5. **Интеграция с автомобилем:** Связь с CAN-шиной, датчиками, системами автомобиля
6. **Двойной дисплей:** Два экрана 12.3" для приборной панели и мультимедиа
7. **ADAS интеграция:** Системы помощи водителю (ACC, FCW, AEB)
8. **Премиальная аудиосистема:** 10 динамиков Sony с DSP обработкой
9. **Телематика:** Chery Connect для удаленного управления
10. **Система кругового обзора:** 540° обзор с камерами

## Пути в системе

### Android разделы (ext2):
- `/system/` - системные файлы Android
- `/vendor/` - vendor специфичные файлы
- `/product/` - product специфичные файлы

### QNX разделы:
- Загрузчик: FAT16 образ
- Система: Кастомный формат

### Данные:
- `/vr/` - голосовое управление iFlytek
- `/TurboDog/` - навигационная система
- `/etc/adi_dsp_ldr/ADSP-21489.ldr` - DSP прошивка
- `/etc/ChimeTest.wav` - тестовый звуковой файл

## Инструменты для работы

1. **payload-dumper-go** - распаковка Android OTA payload.bin
2. **QEMU** - эмуляция аппаратной части
3. **fastboot** - прошивка устройств
4. **adb** - отладка Android
5. **mkfs.ext2** - создание ext2 файловых систем

## Примечания

- Система использует нестандартную конфигурацию Android
- QNX система требует специальных инструментов для анализа
- DSP процессор требует специфичной прошивки
- Радио модуль использует Motorola S-Record формат
- Chime файлы имеют кастомный формат, требующий анализа

## Виртуальная симуляция

### Скрипт симуляции
- **Файл:** `development/scripts/simulate_t18fl3_complete.sh`
- **Функции:**
  - Извлечение kernel и ramdisk из boot.img
  - Создание userdata и cache образов
  - Запуск QEMU с правильными параметрами
  - Поддержка Android и QNX режимов

### Параметры эмуляции
- **CPU:** Cortex-A57 (совместим с Renesas g6sh)
- **Machine:** virt,highmem=on
- **Memory:** 4 GB
- **SMP:** 4 cores
- **Диски:** VirtIO с writeback cache

### Режимы запуска
- `--android` - только Android
- `--qnx` - только QNX
- `--both` - Android + QNX (по умолчанию)

## Следующие шаги

1. ✅ Распаковка и анализ всех компонентов
2. ✅ Создание информационной базы
3. ✅ Создание виртуальной симуляции с QEMU
4. ⏳ Анализ структуры QNX системы
5. ⏳ Настройка загрузчика для двойной загрузки
6. ⏳ Эмуляция DSP процессора
7. ⏳ Интеграция всех компонентов (Chime, VR, Maps)
8. ⏳ Тестирование и оптимизация

