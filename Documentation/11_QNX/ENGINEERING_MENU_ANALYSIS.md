# Анализ инженерного меню и скрытых функций - G6SH/T18FL3

**Дата:** 2025-11-27
**Цель:** Изучить все возможности инженерного меню и скрытые функции в Android и QNX

---

## 🎯 ИНЖЕНЕРНОЕ МЕНЮ (com.android.engmode)

### Основная информация

**Package:** `com.android.engmode`
**APK:** `/product/app/SVEngMode/SVEngMode.apk` (4.0 MB)
**Version:** `Common_SVEngMode_2508080237` (v27)
**Статус:** ✅ Успешно запущено и работает

### Компоненты приложения

#### Activities:
- `com.android.engmode/.MainActivity` - Главная активность
  - Intent Action: `android.intent.action.MAIN`
  - Category: `android.intent.category.DEFAULT`
  - ✅ Успешно запускается

#### Services:
- `com.android.engmode/.ui.ActJumpService` - Сервис для перехода между активностями

#### Receivers:
- `com.android.engmode/.util.EngModeReceiver` - Broadcast Receiver
  - Обрабатывает: `android.intent.action.BOOT_COMPLETED`
  - Broadcast: `com.android.engmode.ENTER_ENGMODE` (отправляется при входе)

### Разрешения (ключевые)

**Системные разрешения:**
- `android.permission.REBOOT` - Перезагрузка системы
- `android.permission.MASTER_CLEAR` - Сброс к заводским настройкам
- `android.permission.RECOVERY` - Доступ к recovery режиму
- `android.permission.WRITE_SECURE_SETTINGS` - Запись защищенных настроек
- `android.permission.WRITE_SETTINGS` - Запись настроек
- `android.permission.DELETE_PACKAGES` - Удаление пакетов
- `android.permission.SET_TIME` - Установка времени
- `android.permission.MODIFY_PHONE_STATE` - Модификация состояния телефона
- `android.permission.DEVICE_POWER` - Управление питанием устройства
- `android.permission.REMOVE_TASKS` - Удаление задач
- `android.permission.STOP_APP_SWITCHES` - Остановка переключения приложений
- `android.permission.INTERACT_ACROSS_USERS_FULL` - Полное взаимодействие между пользователями
- `android.permission.MANAGE_ACTIVITY_STACKS` - Управление стеками активностей
- `android.permission.CONFIRM_FULL_BACKUP` - Подтверждение полного бэкапа

**Сетевые разрешения:**
- `android.permission.ACCESS_WIFI_STATE` / `CHANGE_WIFI_STATE`
- `android.permission.INTERNET`
- `android.permission.ACCESS_NETWORK_STATE`

**Bluetooth разрешения:**
- `android.permission.BLUETOOTH` / `BLUETOOTH_ADMIN` / `BLUETOOTH_PRIVILEGED`

**Другие:**
- `android.permission.ACCESS_FINE_LOCATION` / `ACCESS_COARSE_LOCATION`
- `android.permission.RECORD_AUDIO`
- `android.permission.READ_PHONE_STATE` / `CALL_PHONE`
- `android.permission.READ_CONTACTS` / `WRITE_CONTACTS`
- `android.permission.READ_CALL_LOG` / `WRITE_CALL_LOG`
- `android.car.permission.CAR_VENDOR_EXTENSION` - Расширения для автомобиля

### Broadcast Actions

**Отправляемые:**
- `com.android.engmode.ENTER_ENGMODE` - При входе в инженерный режим

**Обрабатываемые:**
- `android.intent.action.BOOT_COMPLETED` - При загрузке системы
- `com.android.engmode.EXIT_CARPLAY` - Выход из CarPlay

### Интеграция с системой

**Подключения к сервисам:**
- `com.android.car/.CarService` - Car Framework Service
- `com.desaysv.carlan/.CarLanService` - Car LAN Service

**Статус:** Приложение активно подключено к системным сервисам

---

## 🔧 СКРЫТЫЕ ФУНКЦИИ ANDROID

### 1. Системные свойства

**Инженерные режимы:**
```bash
persist.sys.eng=1                    # Инженерный режим
persist.sys.dev=1                    # Режим разработчика
persist.sys.qnx=1                    # QNX режим
```

**Debug свойства:**
```bash
persist.sv.debug.adb_enable=1       # ADB включен
persist.sv.debug_logcat=1            # Logcat включен
persist.sv.debug_service=1           # Debug сервис включен
```

**QNX свойства:**
```bash
persist.qnx.serial.enable=1          # QNX Serial включен
persist.qnx.screen.size=123          # Размер экрана QNX
persist.qnxScreenVersion=2.0-1.10-5.0.0_...
sys.qnx.uart.enable=1                # QNX UART включен
sys.qnx.screen.version=2.0-1.10-5.0.0_...
```

**MCU свойства:**
```bash
sys.ivi.mcu.checksum=2518
sys.ivi.mcu.version=T18_IC2563_18_01_40.202_250808_R
system.mcu.version=T18_IC2563_18_01_40.202_250808_R
```

**Системные флаги:**
```bash
ro.sys.eng.encrypt.enabled=1         # Шифрование в инженерном режиме
ro.sys.eng.slaver.enabled=1          # Slaver режим включен
```

### 2. Debug сервисы

**svdebug:**
- Путь: `/vendor/bin/svdebugservice`
- Активация: `persist.sv.debug_service=1`
- Статус: ✅ Запущен

**svresetfactory:**
- Путь: `/vendor/bin/svresetfactory`
- Активация: `sys.sv.svresetfactory_service=1`
- Назначение: Сброс к заводским настройкам

### 3. Broadcast Actions для активации режимов

**Engineering:**
```bash
com.desaysv.engineering.START      # ✅ Работает
com.desaysv.engineering.ENABLE      # ✅ Работает
```

**Factory:**
```bash
com.desaysv.factory.ENABLE          # ✅ Работает
```

**Diagnostic:**
```bash
com.desaysv.diag.ENABLE              # ✅ Работает
```

### 4. Скрытые настройки

**Settings Global:**
```bash
car_reserved_2=com.desaysv.vehicle.test/.Test  # Тестовое приложение
device_name=G6SH-r8a7795
device_provisioned=1
```

**Settings System:**
```bash
sys.vehicle.state.engine=1
```

### 5. Init Scripts (скрытые команды)

**Из `/vendor/etc/init/*.rc`:**
```bash
# CPU тестирование
setprop sys.testcpu 1
write /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor userspace
write /sys/devices/system/cpu/cpu0/cpufreq/scaling_setspeed 500000

# Debug сервисы
service svdebug /vendor/bin/svdebugservice init
on property:persist.sv.debug_service=1
    start svdebug

# Factory reset
service svresetfactory /vendor/bin/svresetfactory 2
on property:sys.sv.svresetfactory_service=1
    start svresetfactory

# ADB режим
on property:persist.sv.debug.adb_enable=1 && property:sys.boot_completed=1
    write /sys/devices/soc/6a00000.ssusb/mode "peripheral"
```

---

## 🔌 СКРЫТЫЕ ФУНКЦИИ QNX

### 1. Сетевые соединения

**Активные порты:**
- `10005` - LISTEN на `0.0.0.0` (Android)
- `10004` - ESTABLISHED к `192.168.2.1` (QNX/MCU)
- `31030` - ESTABLISHED к `192.168.2.1` (QNX/MCU)
- `31040` - ESTABLISHED к `192.168.2.1` (QNX/MCU)
- `31050` - ESTABLISHED к `192.168.2.1` (QNX/MCU)

**IP адреса:**
- Android: `192.168.2.2` (eth0)
- QNX/MCU: `192.168.2.1`

### 2. QNX Shared Memory

**Путь:** `/sys/devices/platform/vdevs/1c050000.qnx,guest_shm`

**Информация из uevent:**
```
DRIVER=qnx-virtio-du
OF_NAME=qnx,guest_shm
OF_FULLNAME=/vdevs/qnx,guest_shm@1c050000
OF_COMPATIBLE_0=qvm,guest_shm
MODALIAS=of:Nqnx,guest_shmT<NULL>Cqvm,guest_shm
```

**Структура:**
- `driver` -> `../../../../bus/platform/drivers/qnx-virtio-du`
- `drm/` - Direct Rendering Manager
- `graphics/` - Графические интерфейсы
- `uevent` - Информация об устройстве

**Статус:** Найдено, но требует root для чтения данных

### 3. QNX UART

**Устройства:**
- `/dev/ttyAMA0` - PL011 UART (QNX Console)
  - Адрес: `0x1c090000`
  - IRQ: 65
  - Статус: ✅ Активен (системная консоль)

**Свойства:**
```bash
persist.qnx.serial.enable=1
sys.qnx.uart.enable=1
```

### 4. QNX версии

**Cluster (приборная панель):**
```bash
com.desaysv.cluster.version=2.0-1.10-5.0.0
com.desaysv.cluster.pn=703001446AA
com.desaysv.cluster.supplierCode=9ED
```

**IVI (головное устройство):**
```bash
com.desaysv.ivi.version=2.0-1.10-13.0.0
com.desaysv.ivi.pn=703001446AA
com.desaysv.ivi.supplierCode=9ED
```

---

## 🎛️ КОМАНДЫ ДЛЯ АКТИВАЦИИ СКРЫТЫХ ФУНКЦИЙ

### Инженерный режим

```bash
# Запуск инженерного меню
adb shell am start -n com.android.engmode/.MainActivity

# Активация через broadcast
adb shell am broadcast -a com.android.engmode.ENTER_ENGMODE
```

### Debug режимы

```bash
# Включение debug сервиса
adb shell setprop persist.sv.debug_service 1

# Включение ADB
adb shell setprop persist.sv.debug.adb_enable 1

# Включение logcat
adb shell setprop persist.sv.debug_logcat 1
```

### Factory/Diag режимы

```bash
# Factory режим
adb shell am broadcast -a com.desaysv.factory.ENABLE
adb shell setprop sys.sv.svresetfactory_service 1

# Diagnostic режим
adb shell am broadcast -a com.desaysv.diag.ENABLE
```

### QNX функции

```bash
# Включение QNX Serial
adb shell setprop persist.qnx.serial.enable 1
adb shell setprop sys.qnx.uart.enable 1

# Проверка QNX соединений
adb shell netstat -an | grep 192.168.2.1
```

---

## 📋 ИЗВЛЕЧЕННЫЕ ФАЙЛЫ

### APK приложения:
- `SVEngMode.apk` (4.0 MB) - Инженерный режим
- `Carplay.apk` (41 KB) - CarPlay приложение
- `CarLanService.apk` (213 KB) - Car LAN Service
- `CarStateManagerService.apk` (879 KB) - Car State Manager
- `CommonLinkService.apk` (2.0 MB) - Common Link Service
- `SVMapService.apk` (575 KB) - Map Service
- `PlatformAdapter.apk` (1.4 MB) - Platform Adapter
- `LogManagerService.apk` (403 KB) - Log Manager

### Бинарники:
- `vehicle.shmemslaver` (69 KB) - Shared Memory Slaver
- `vehicle.linkdevicemanager` (204 KB) - Link Device Manager
- `svdebugservice` (3.7 KB) - Debug Service
- `svresetfactory` (517 B) - Factory Reset
- `com.desaysv.vehiclelan.proxy@1.0-service` (10.8 KB)
- `android.hardware.automotive.vehicle@2.0-service.g6` (272 KB)

### Init Scripts:
- `init.car.rc`
- `init.desaysv.vehicle.rc`
- `init.desaysv.phonelink.hicar.rc`
- `android.hardware.automotive.vehicle@2.0-service.g6.rc`
- `vehiclelan.proxy@1.0-service.rc`

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

1. ✅ Извлечь все APK и бинарники
2. ⏳ Декомпилировать `SVEngMode.apk` для анализа всех функций
3. ⏳ Изучить init scripts для скрытых команд
4. ⏳ Проанализировать сетевые протоколы QNX
5. ⏳ Изучить структуру QNX Shared Memory
6. ⏳ Найти способы взаимодействия с QNX через сетевые порты

---

**Статус:** Основные файлы извлечены, инженерное меню проанализировано. Требуется декомпиляция APK для полного анализа функций.

