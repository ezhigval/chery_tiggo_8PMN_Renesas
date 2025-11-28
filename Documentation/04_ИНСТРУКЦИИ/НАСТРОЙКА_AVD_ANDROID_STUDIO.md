# Настройка AVD (Android Virtual Device) для тестирования

Инструкция по созданию виртуальной машины в Android Studio с характеристиками, максимально приближенными к ГУ Chery Tiggo 8 Pro Max T18FL3.

## Характеристики реального ГУ

На основе системной информации из `Knowledge_base/16_СИСТЕМНАЯ_ИНФОРМАЦИЯ/`:

### Основные параметры

- **Версия Android**: 9 (Pie)
- **API Level**: 28
- **Архитектура**: arm64-v8a (ARM 64-bit)
- **Разрешение экрана**: 1920 x 720 пикселей
- **Плотность экрана (DPI)**: 160 dpi
- **Ориентация**: Landscape (горизонтальная)
- **Характеристики устройства**: tablet, nosdcard
- **Платформа**: Renesas r8a7795 (G6SH)

### Дополнительные параметры

- **OpenGL ES версия**: 3.0 (196610)
- **Zygote**: zygote64_32 (поддержка 32 и 64 бит)
- **VNDK версия**: 28
- **Минимальный поддерживаемый SDK**: 17

## Создание AVD в Android Studio

### Шаг 1: Установка системного образа

1. Откройте Android Studio
2. Перейдите в **Tools → Device Manager** (или **Tools → AVD Manager**)
3. Нажмите **Create Device**
4. Выберите категорию **Automotive** или **Tablet**
5. Выберите устройство или создайте **New Hardware Profile**

### Шаг 2: Создание Hardware Profile (если нужно)

Если нет подходящего устройства, создайте новый профиль:

1. В окне выбора устройства нажмите **New Hardware Profile**
2. Задайте параметры:
   - **Name**: `Tiggo 8 Pro Max T18FL3`
   - **Screen Size**: 10.1" (или другое, близкое к реальному)
   - **Resolution**: 
     - Width: `1920`
     - Height: `720`
   - **Screen Density**: `mdpi` (160 dpi)
   - **Orientation**: Landscape
   - **Memory**: 4GB RAM (или больше, если доступно)
   - **Input**: Touchscreen
   - **Navigation**: Hardware buttons (или Software buttons)
   - **DPAD**: Hardware
   - **Keyboard**: Hardware
   - **Camera**: None (или Front/Back, если нужно)
   - **Sensors**: 
     - Accelerometer: Yes
     - Gyroscope: Yes (опционально)
     - GPS: Yes
     - Proximity: No
   - **Add Device**: Нажмите для сохранения

### Шаг 3: Выбор системного образа

1. После выбора/создания устройства нажмите **Next**
2. Выберите системный образ:
   - **Release Name**: Android 9.0 (Pie)
   - **API Level**: 28
   - **Target**: Android 9.0 (Google APIs) или **Android 9.0 (Automotive)**
   - **ABI**: **arm64-v8a** (важно!)
   - **Download** если образ не установлен

### Шаг 4: Настройка AVD

1. После выбора образа нажмите **Next**
2. В окне **Verify Configuration** настройте:

#### Advanced Settings:

- **Graphics**: 
  - Рекомендуется: **Hardware - GLES 2.0** (для лучшей производительности)
  - Или: **Automatic** (если есть проблемы)
  
- **Camera**:
  - Front: None
  - Back: None

- **Network Speed**: Full (или Emulated, если нужно ограничение)

- **Network Latency**: None (или Emulated)

- **Memory and Storage**:
  - RAM: 4096 MB (или больше, если позволяет система)
  - VM heap: 512 MB
  - Internal Storage: 4096 MB (или больше)

- **SD Card**:
  - Size: 0 MB (так как `nosdcard` в характеристиках)

- **Emulated Performance**:
  - Graphics: Hardware - GLES 2.0
  - Multi-core CPU: Да (если доступно)
  - Snapshot: Включить (для быстрого запуска)

- **Device Frame**:
  - Enable Device Frame: По желанию

3. Нажмите **Finish**

### Шаг 5: Дополнительная настройка через командную строку (опционально)

После создания AVD можно дополнительно настроить параметры через командную строку:

```bash
# Найти путь к AVD
# Обычно: ~/.android/avd/<имя_avd>.avd/config.ini

# Отредактировать config.ini и добавить/изменить:
hw.lcd.density=160
hw.lcd.width=1920
hw.lcd.height=720
hw.ramSize=4096
disk.dataPartition.size=4096M
```

## Проверка настроек AVD

После запуска эмулятора проверьте параметры:

```bash
# Подключитесь к эмулятору
adb devices

# Проверьте версию Android
adb shell getprop ro.build.version.release
# Должно быть: 9

# Проверьте API Level
adb shell getprop ro.build.version.sdk
# Должно быть: 28

# Проверьте архитектуру
adb shell getprop ro.product.cpu.abi
# Должно быть: arm64-v8a

# Проверьте разрешение экрана
adb shell wm size
# Должно быть: Physical size: 1920x720

# Проверьте плотность
adb shell wm density
# Должно быть: Physical density: 160

# Проверьте характеристики
adb shell getprop ro.build.characteristics
# Должно содержать: tablet
```

## Альтернативный способ: создание через командную строку

Можно создать AVD через командную строку:

```bash
# Список доступных системных образов
avdmanager list system-images

# Создание AVD
avdmanager create avd \
  -n "Tiggo_T18FL3" \
  -k "system-images;android-28;google_apis;arm64-v8a" \
  -d "pixel_2" \
  --force

# Или с кастомным устройством
avdmanager create avd \
  -n "Tiggo_T18FL3" \
  -k "system-images;android-28;google_apis;arm64-v8a" \
  -d "Tiggo_8_Pro_Max_T18FL3" \
  --force
```

Затем отредактируйте `~/.android/avd/Tiggo_T18FL3.avd/config.ini`:

```ini
hw.lcd.density=160
hw.lcd.width=1920
hw.lcd.height=720
hw.ramSize=4096
disk.dataPartition.size=4096M
hw.gpu.enabled=yes
hw.gpu.mode=host
```

## Запуск эмулятора

```bash
# Через Android Studio: Tools → Device Manager → Play

# Или через командную строку:
emulator -avd Tiggo_T18FL3
```

## Важные замечания

1. **Архитектура arm64-v8a**: Критически важно выбрать правильную архитектуру, иначе приложения могут не запуститься или работать некорректно.

2. **Разрешение 1920x720**: Это нестандартное разрешение (широкий формат). Убедитесь, что оно правильно установлено.

3. **DPI 160**: Соответствует категории `mdpi`. Это важно для правильного масштабирования UI.

4. **Android Automotive**: Если доступен образ Android Automotive для API 28, предпочтительно использовать его, так как ГУ является автомобильным устройством.

5. **Производительность**: Эмулятор может работать медленно. Убедитесь, что:
   - Включен Hardware Acceleration (HAXM/KVM)
   - Достаточно RAM на хосте
   - Используется GPU acceleration

## Устранение проблем

### Эмулятор не запускается
- Проверьте, что установлен HAXM (Intel) или KVM (Linux/Mac)
- Убедитесь, что в BIOS включена виртуализация
- Уменьшите RAM в настройках AVD

### Неправильное разрешение
- Проверьте `config.ini` в папке AVD
- Используйте `adb shell wm size 1920x720` для изменения размера

### Неправильная плотность
- Используйте `adb shell wm density 160` для изменения плотности

### Приложения не устанавливаются
- Проверьте архитектуру: `adb shell getprop ro.product.cpu.abi`
- Убедитесь, что APK поддерживает arm64-v8a или armeabi-v7a

## Ссылки

- [Android Emulator Documentation](https://developer.android.com/studio/run/emulator)
- [AVD Manager](https://developer.android.com/studio/run/managing-avds)
- [System Images](https://developer.android.com/studio/run/managing-avds#system-images)

