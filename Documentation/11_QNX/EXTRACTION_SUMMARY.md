# Итоговая сводка: Извлечение и анализ файлов - G6SH/T18FL3

**Дата:** 2025-11-27
**Статус:** ✅ Файлы извлечены, инженерное меню проанализировано

---

## ✅ ВЫПОЛНЕНО

### 1. Извлечение файлов

**APK приложения (8 файлов, ~9.5 MB):**
- ✅ `SVEngMode.apk` (4.0 MB) - Инженерный режим
- ✅ `Carplay.apk` (41 KB) - CarPlay
- ✅ `CarLanService.apk` (213 KB) - Car LAN Service
- ✅ `CarStateManagerService.apk` (879 KB) - Car State Manager
- ✅ `CommonLinkService.apk` (2.0 MB) - Common Link
- ✅ `SVMapService.apk` (575 KB) - Map Service
- ✅ `PlatformAdapter.apk` (1.4 MB) - Platform Adapter
- ✅ `LogManagerService.apk` (403 KB) - Log Manager

**Бинарники (6 файлов, ~550 KB):**
- ✅ `vehicle.shmemslaver` (68 KB) - QNX Shared Memory
- ✅ `vehicle.linkdevicemanager` (200 KB) - Link Device Manager
- ✅ `svdebugservice` (3.6 KB) - Debug Service
- ✅ `svresetfactory` (517 B) - Factory Reset
- ✅ `com.desaysv.vehiclelan.proxy@1.0-service` (11 KB)
- ✅ `android.hardware.automotive.vehicle@2.0-service.g6` (266 KB)

**Init Scripts (5 файлов, ~5.3 KB):**
- ✅ `init.car.rc`
- ✅ `init.desaysv.vehicle.rc`
- ✅ `init.desaysv.phonelink.hicar.rc`
- ✅ `android.hardware.automotive.vehicle@2.0-service.g6.rc`
- ✅ `vehiclelan.proxy@1.0-service.rc`

**Всего:** 20 файлов, ~10 MB

---

### 2. Анализ инженерного меню

**Найденные компоненты:**
- ✅ `MainActivity` - Главная активность
- ✅ `ActJumpService` - Сервис переходов
- ✅ `EngModeReceiver` - Broadcast Receiver
- ✅ Broadcast: `com.android.engmode.ENTER_ENGMODE`

**Разрешения (ключевые):**
- ✅ `REBOOT`, `MASTER_CLEAR`, `RECOVERY`
- ✅ `WRITE_SECURE_SETTINGS`, `DELETE_PACKAGES`
- ✅ `MODIFY_PHONE_STATE`, `DEVICE_POWER`
- ✅ `MANAGE_ACTIVITY_STACKS`, `INTERACT_ACROSS_USERS_FULL`

**Интеграция:**
- ✅ Подключен к `CarService`
- ✅ Подключен к `CarLanService`
- ✅ Активно работает на устройстве

---

### 3. Скрытые функции Android

**Системные свойства:**
- ✅ `persist.sys.eng=1` - Инженерный режим
- ✅ `persist.sys.dev=1` - Режим разработчика
- ✅ `persist.sv.debug_service=1` - Debug сервис
- ✅ `persist.sv.debug.adb_enable=1` - ADB включен

**Broadcast Actions:**
- ✅ `com.desaysv.engineering.START` / `ENABLE`
- ✅ `com.desaysv.factory.ENABLE`
- ✅ `com.desaysv.diag.ENABLE`

**Debug сервисы:**
- ✅ `svdebug` - Запущен
- ✅ `svresetfactory` - Найден

**Init Scripts:**
- ✅ CPU тестирование (`sys.testcpu`)
- ✅ USB режим переключение
- ✅ Debug сервисы автозапуск

---

### 4. Скрытые функции QNX

**Сетевые соединения:**
- ✅ Порт `10005` - LISTEN на Android
- ✅ Порты `10004`, `31030`, `31040`, `31050` - ESTABLISHED к QNX
- ✅ IP: Android `192.168.2.2`, QNX `192.168.2.1`

**QNX Shared Memory:**
- ✅ Найдено: `/sys/devices/platform/vdevs/1c050000.qnx,guest_shm`
- ✅ Driver: `qnx-virtio-du`
- ✅ Compatible: `qvm,guest_shm`

**QNX UART:**
- ✅ `/dev/ttyAMA0` - PL011 на `0x1c090000`
- ✅ Свойства: `persist.qnx.serial.enable=1`, `sys.qnx.uart.enable=1`

**QNX версии:**
- ✅ Cluster: `2.0-1.10-5.0.0`
- ✅ IVI: `2.0-1.10-13.0.0`
- ✅ MCU: `T18_IC2563_18_01_40.202_250808_R`

---

## 📚 СОЗДАННАЯ ДОКУМЕНТАЦИЯ

1. **`ENGINEERING_MODES_ANALYSIS.md`** - Анализ инженерных режимов
2. **`ENGINEERING_MENU_ANALYSIS.md`** - Детальный анализ инженерного меню и скрытых функций
3. **`EXTRACTED_FILES_LIST.md`** - Список всех извлеченных файлов
4. **`activate_all_modes.sh`** - Скрипт активации режимов
5. **`extract_all_files.sh`** - Скрипт извлечения файлов

---

## 🎯 КЛЮЧЕВЫЕ НАХОДКИ

### Инженерный режим:
- ✅ Полный доступ к системным функциям
- ✅ Возможность перезагрузки и сброса
- ✅ Управление пакетами и задачами
- ✅ Доступ к защищенным настройкам

### QNX взаимодействие:
- ✅ Сетевые порты для связи
- ✅ Shared Memory для обмена данными
- ✅ UART для консоли
- ✅ Версии и конфигурация найдены

### Скрытые функции:
- ✅ Debug сервисы
- ✅ Factory режим
- ✅ Diagnostic режим
- ✅ CPU тестирование
- ✅ USB режим переключение

---

## ⏳ СЛЕДУЮЩИЕ ШАГИ

1. ⏳ Декомпилировать `SVEngMode.apk` (JADX) для анализа всех функций
2. ⏳ Проанализировать бинарники (strings, objdump, IDA)
3. ⏳ Изучить сетевые протоколы QNX
4. ⏳ Найти способы чтения QNX Shared Memory
5. ⏳ Создать инструменты для взаимодействия с QNX

---

## 📁 СТРУКТУРА ФАЙЛОВ

```
Knowledge_base/11_QNX/
├── extracted_files/
│   ├── apk/              # APK приложения (8 файлов)
│   ├── binaries/         # Бинарники (6 файлов)
│   ├── init_scripts/     # Init scripts (5 файлов)
│   └── EXTRACTED_FILES_LIST.md
├── ENGINEERING_MODES_ANALYSIS.md
├── ENGINEERING_MENU_ANALYSIS.md
├── activate_all_modes.sh
└── extract_all_files.sh
```

---

**Статус:** ✅ Все основные файлы извлечены и проанализированы. Готово к декомпиляции и детальному анализу.

