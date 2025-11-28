# QNX Окружение Разработки

## Структура

- `images/` - QNX образы (qnx_system.img, qnx_boot.img)
- `config/` - Конфигурационные файлы
- `scripts/` - Скрипты для работы с QNX
- `logs/` - Логи QNX
- `workspace/` - Рабочая директория для разработки

## Установка QNX SDK

1. Скачайте QNX Software Development Platform (SDP) 7.1
2. Установите в `$HOME/qnx710` или укажите путь через `QNX_TARGET`
3. Настройте переменные окружения:
   ```bash
   source config/qnx_config.sh
   ```

## Запуск QNX Эмулятора

```bash
./scripts/start_qnx_emulator.sh
```

## Тестирование связи Android-QNX

```bash
./scripts/test_android_qnx_connection.sh <android_device_id> <qnx_ip>
```

## Интеграция с Android Эмулятором

1. Запустите Android эмулятор ГУ
2. Запустите QNX эмулятор
3. Настройте сетевую связь между ними
4. Используйте broadcast для отправки данных:
   - `turbodog.system.navigation.message` - прямой broadcast
   - `desay.thirdparty.navigation` - через mapservice

## QNX Образы

QNX образы извлечены из пакета обновления:

- `qnx_system.img` - системный образ QNX
- `qnx_boot.img` - загрузочный образ QNX

## Подключение к реальному устройству

### Подключение через ADB

1. Подключите ГУ к ПК через USB кабель
2. Включите "Отладку по USB" на устройстве
3. Разрешите отладку при появлении запроса
4. Проверьте подключение:
   ```bash
   ./connect_device.sh
   ```

### Подключение к QNX через USB Serial/UART

1. **Подключите ГУ через mini USB кабель** (USB-to-Serial интерфейс)

2. **Установите драйверы USB-to-Serial** (если необходимо):

   - **CP2102**: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
   - **PL2303**: https://www.prolific.com.tw/US/ShowProduct.aspx?p_id=225&pcid=41
   - **FT232**: https://www.ftdichip.com/Drivers/VCP.htm

   После установки драйверов перезагрузите Mac и подключите устройство снова.

3. **Установите инструменты** (если еще не установлены):

   ```bash
   brew install minicom
   ```

4. **Найдите serial порт**:

   ```bash
   ls -la /dev/tty.* /dev/cu.* | grep -i usb
   ```

   Обычно порты имеют вид: `/dev/tty.usbserial-XXXX` или `/dev/cu.usbserial-XXXX`

5. **Подключитесь к QNX**:

   ```bash
   ./connect_qnx.sh
   ```

   Или укажите порт вручную:

   ```bash
   export QNX_PORT=/dev/tty.usbserial-1410
   export QNX_BAUD=115200
   ./connect_qnx.sh
   ```

   Или с параметрами:

   ```bash
   ./connect_qnx.sh -p /dev/tty.usbserial-1410 -b 115200
   ```

6. **Параметры подключения** (обычно для QNX):
   - **Скорость (baud rate)**: 115200
   - **Биты данных**: 8
   - **Четность**: Нет
   - **Стоп-биты**: 1
   - **Управление потоком**: Нет

### Скрипты для работы с устройством

- `connect_device.sh` - Проверка и подключение через ADB
- `connect_qnx.sh` - Подключение к QNX через Serial порт
- `reset_adb_keys.sh` - Сброс ключей авторизации ADB
- `activate_all_modes.sh` - Активация всех инженерных и сервисных режимов

## Инженерные и сервисные режимы

### Быстрый доступ

**Активация всех режимов:**
```bash
./activate_all_modes.sh
```

**Запуск инженерного режима:**
```bash
adb shell am start -n com.android.engmode/.MainActivity
```

### Найденные режимы

1. **Android Engineering Mode** (`com.android.engmode`)
   - ✅ Найден и успешно запущен
   - APK: `SVEngMode.apk` (4.0 MB)
   - Разрешения: REBOOT, MASTER_CLEAR, WRITE_SECURE_SETTINGS, RECOVERY

2. **Desay SV Engineering Broadcasts**
   - `com.desaysv.engineering.START`
   - `com.desaysv.engineering.ENABLE`
   - `com.desaysv.factory.ENABLE`
   - `com.desaysv.diag.ENABLE`

3. **Debug Services**
   - `svdebug` - Debug сервис
   - `svresetfactory` - Сброс к заводским настройкам

**Документация:**
- `ENGINEERING_MODES_ANALYSIS.md` - Анализ инженерных режимов
- `ENGINEERING_MENU_ANALYSIS.md` - Детальный анализ инженерного меню и скрытых функций
- `activate_all_modes.sh` - Скрипт для активации всех режимов

## Извлеченные файлы

### Статус извлечения

**Всего файлов:** 20
**Общий размер:** ~10 MB

**Расположение:** `extracted_files/`

### Категории:

1. **APK приложения** (8 файлов, ~9.5 MB):
   - Инженерные: `SVEngMode.apk`
   - QNX/Vehicle: `CarLanService.apk`, `CarStateManagerService.apk`, `Carplay.apk`
   - Сервисы: `CommonLinkService.apk`, `PlatformAdapter.apk`, `SVMapService.apk`
   - Утилиты: `LogManagerService.apk`

2. **Бинарники** (6 файлов, ~550 KB):
   - Vehicle: `vehicle.shmemslaver`, `vehicle.linkdevicemanager`
   - Debug: `svdebugservice`, `svresetfactory`
   - HAL: `android.hardware.automotive.vehicle@2.0-service.g6`

3. **Init Scripts** (5 файлов, ~5.3 KB):
   - Vehicle инициализация
   - HAL сервисы
   - Phone Link

**Полный список:** `extracted_files/EXTRACTED_FILES_LIST.md`

## Device Tree и UART устройства

### Анализ device tree

**Документация:**
- `DEVICE_TREE_UART_ANALYSIS.md` - Полный анализ device tree и UART устройств
- `QEMU_UART_INTEGRATION.md` - План интеграции UART в QEMU эмулятор
- `g6sh-emu.dts` - Device tree для эмулятора

### Найденные UART устройства:

1. **ttyAMA0** - PL011 на `0x1c090000` (QNX Console)
   - Используется как системная консоль (`console=ttyAMA0`)
   - Через virtio (`/vdevs/uart@1c090000`)

2. **ttySC1** - HSCIF на `0xe6550000` (GPS)
   - Renesas HSCIF UART
   - Используется для GPS модуля

3. **ttySC6** - HSCIF на `0xe6540000` (Bluetooth)
   - Renesas HSCIF UART
   - Используется для Bluetooth модуля
   - Поддерживает RTS/CTS flow control

### Имитация для эмулятора:

Для эмуляции в QEMU рекомендуется:
- Использовать PL011 для всех UART (замена HSCIF на PL011)
- Создать device tree для эмулятора (`g6sh-emu.dts`)
- Интегрировать UART устройства в машину g6sh

**См. детали:** `QEMU_UART_INTEGRATION.md`

## Примечания

- QNX требует лицензию для коммерческого использования
- Для разработки можно использовать QNX Community Edition
- Эмуляция QNX через QEMU может быть медленной
- Для лучшей производительности используйте реальное оборудование
- При работе с реальным устройством через Serial порт убедитесь, что кабель поддерживает передачу данных (не только зарядку)
