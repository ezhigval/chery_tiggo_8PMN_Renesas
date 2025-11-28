# Список извлеченных файлов - G6SH/T18FL3

**Дата:** 2025-11-27
**Статус:** ✅ Основные файлы извлечены

---

## 📦 APK ПРИЛОЖЕНИЯ

### Инженерные и системные:
- `SVEngMode.apk` (4.0 MB) - Инженерный режим (com.android.engmode)
- `LogManagerService.apk` (403 KB) - Менеджер логов

### QNX и Vehicle:
- `Carplay.apk` (41 KB) - CarPlay приложение
- `CarLanService.apk` (213 KB) - Car LAN Service
- `CarStateManagerService.apk` (879 KB) - Car State Manager Service
- `CommonLinkService.apk` (2.0 MB) - Common Link Service
- `PlatformAdapter.apk` (1.4 MB) - Platform Adapter Service

### Навигация и карты:
- `SVMapService.apk` (575 KB) - Map Service

**Всего APK:** 8 файлов (~9.5 MB)

---

## 🔧 БИНАРНИКИ

### Vehicle сервисы:
- `vehicle.shmemslaver` (68 KB) - Shared Memory Slaver для QNX
- `vehicle.linkdevicemanager` (200 KB) - Link Device Manager

### Debug и Factory:
- `svdebugservice` (3.6 KB) - Debug Service
- `svresetfactory` (517 B) - Factory Reset Service

### HAL сервисы:
- `com.desaysv.vehiclelan.proxy@1.0-service` (11 KB) - Vehicle LAN Proxy
- `android.hardware.automotive.vehicle@2.0-service.g6` (266 KB) - Vehicle HAL Service

**Всего бинарников:** 6 файлов (~550 KB)

---

## 📜 INIT SCRIPTS

- `init.car.rc` (106 B) - Car init script
- `init.desaysv.vehicle.rc` (4.0 KB) - Desay SV Vehicle init
- `init.desaysv.phonelink.hicar.rc` (925 B) - Phone Link HiCar init
- `android.hardware.automotive.vehicle@2.0-service.g6.rc` (162 B) - Vehicle HAL init
- `vehiclelan.proxy@1.0-service.rc` (132 B) - Vehicle LAN Proxy init

**Всего init scripts:** 5 файлов (~5.3 KB)

---

## 📊 СТАТИСТИКА

**Всего файлов:** 19
**Общий размер:** ~10 MB

---

## 🎯 КЛЮЧЕВЫЕ ФАЙЛЫ ДЛЯ АНАЛИЗА

### Приоритет 1 (критичные):
1. `SVEngMode.apk` - Инженерный режим (все функции)
2. `vehicle.shmemslaver` - Взаимодействие с QNX
3. `vehicle.linkdevicemanager` - Управление устройствами
4. `init.desaysv.vehicle.rc` - Конфигурация Vehicle

### Приоритет 2 (важные):
5. `CarLanService.apk` - Car LAN Service
6. `CarStateManagerService.apk` - Car State Manager
7. `SVMapService.apk` - Map Service
8. `android.hardware.automotive.vehicle@2.0-service.g6` - Vehicle HAL

### Приоритет 3 (дополнительные):
9. `CommonLinkService.apk` - Common Link
10. `PlatformAdapter.apk` - Platform Adapter
11. `svdebugservice` - Debug Service
12. Остальные init scripts

---

## 📝 СЛЕДУЮЩИЕ ШАГИ

1. ⏳ Декомпилировать `SVEngMode.apk` (JADX)
2. ⏳ Проанализировать бинарники (strings, objdump)
3. ⏳ Изучить init scripts
4. ⏳ Найти все скрытые функции и команды

---

**Расположение:** `Knowledge_base/11_QNX/extracted_files/`

