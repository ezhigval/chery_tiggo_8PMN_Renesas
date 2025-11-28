# Результаты извлечения данных из QNX - G6SH/T18FL3

**Дата:** 2025-11-27
**Статус:** ✅ Ключевые интерфейсы найдены

---

## 🎯 НАЙДЕННЫЕ ИНТЕРФЕЙСЫ ДЛЯ ОТПРАВКИ ДАННЫХ

### 1. BROADCAST ACTIONS ДЛЯ НАВИГАЦИИ

**Основные broadcast actions для отправки данных навигации:**

#### ✅ `turbodog.navigation.system.message`
- **Назначение:** Основной broadcast для штатной навигации TurboDog
- **Receiver:** `com.desaysv.vehicle.carplayapp` (PID: 2830)
- **Статус:** ✅ Найден и активен

#### ✅ `desay.thirdparty.navigation`
- **Назначение:** Broadcast для сторонних навигаторов (Yandex Navigator, 2GIS)
- **Receivers:**
  - `com.desaysv.vehicle.carplayapp` (PID: 2830)
  - `com.android.car` (PID: 2189)
- **Статус:** ✅ Найден и активен
- **Использование:** Для отправки данных от Yandex Navigator/2GIS в QNX

#### ✅ `desay.phonelink.navigation`
- **Назначение:** Broadcast для навигации через телефон (CarPlay/Android Auto)
- **Receiver:** `com.desaysv.vehicle.carplayapp` (PID: 2830)
- **Статус:** ✅ Найден и активен

---

## 🔧 КЛЮЧЕВЫЕ СЕРВИСЫ И ПРОЦЕССЫ

### Системные сервисы:

| Сервис | PID | Описание |
|--------|-----|----------|
| `vehicle.shmemslaver` | 2539 | Shared Memory Service для обмена данными с QNX |
| `vehicle.linkdevicemanager` | 2548 | Link Device Manager для управления устройствами |
| `dsv.carstate.service` | 2160 | Car State Service - управление состоянием автомобиля |
| `com.desaysv.carlan` | 2207 | Car LAN Service - сетевой сервис |
| `com.desaysv.vehicle.carplayapp` | 2830 | Vehicle CarPlay App - обработка навигации |

### Android Services:

| Сервис | Интерфейс | Описание |
|--------|-----------|----------|
| `car_service` | `android.car.ICar` | Android Car Service |
| `dsv_car_power` | `com.desaysv.ivi.platformadapter.app.carstate.ICarStateManager` | Car Power Manager |
| `linkdevicemanager` | `[linkdevicemanager]` | Link Device Manager Service |
| `shmemservice` | `[shmemservice]` | Shared Memory Service |

---

## 📦 КЛЮЧЕВЫЕ APK ДЛЯ АНАЛИЗА

### Приоритетные пакеты:

1. **`com.desaysv.vehicle.carplayapp`** ⭐⭐⭐
   - **Путь:** `/product/app/Carplay/Carplay.apk`
   - **Назначение:** Обработка навигационных данных и отправка в QNX
   - **Receivers:**
     - `turbodog.navigation.system.message`
     - `desay.thirdparty.navigation`
     - `desay.phonelink.navigation`
   - **Действие:** Извлечь и декомпилировать для анализа формата данных

2. **`com.desaysv.carlan`** ⭐⭐
   - **Назначение:** Car LAN Service
   - **Service:** `com.desaysv.carlan.ICarLan`
   - **Действие:** Изучить интерфейс сервиса

3. **`dsv.carstate.service`** ⭐⭐
   - **Назначение:** Car State Manager Service
   - **Service:** `dsv.intent.action.START_CARPOWER_SERVICE`
   - **Действие:** Изучить управление состоянием автомобиля

4. **`com.android.car`** ⭐
   - **Назначение:** Android Car Framework
   - **Receiver:** `desay.thirdparty.navigation`
   - **Действие:** Изучить интеграцию с Android Car API

---

## 🔍 СИСТЕМНЫЕ PROPERTIES

### QNX/Cluster Properties:

```bash
com.desaysv.cluster.display.info: 2.0-1.10-5.0.0_0123456789ABCDEFGHIJ_703001446AA_9ED
com.desaysv.cluster.pn: 703001446AA
com.desaysv.cluster.sn: 0123456789ABCDEFGHIJ
com.desaysv.cluster.supplierCode: 9ED
com.desaysv.cluster.version: 2.0-1.10-5.0.0
persist.sys.h3n.instrument: 10
```

### Vehicle Properties:

```bash
persist.sys.car.brand: 00
persist.sys.car.config.fiv: 0802901400000f00
persist.sys.car.config.fou: 2800f02312000010
persist.sys.car.config.one: affc2de5
persist.sys.car.config.thr: 509ecc7003092a52
persist.sys.car.config.two: 5f01491f
persist.sys.car.part.number: 703000765AA
```

---

## 🔌 СЕТЕВЫЕ СОЕДИНЕНИЯ

### Активные соединения к QNX/MCU (192.168.2.1):

| Локальный порт | Удалённый порт | Статус |
|---------------|----------------|--------|
| 50622 | 10004 | ESTABLISHED |
| 53378 | 31040 | ESTABLISHED |
| 54868 | 31050 | ESTABLISHED |
| 57824 | 31030 | ESTABLISHED |

**Вывод:** Система активно обменивается данными с QNX через несколько портов.

---

## 📂 КОНФИГУРАЦИОННЫЕ ФАЙЛЫ

### Найденные конфигурации:

- `/system/etc/init/init.car.rc` - инициализация Car Service
- `/vendor/etc/init/init.desaysv.vehicle.rc` - инициализация Vehicle сервисов
- `/vendor/etc/init/android.hardware.automotive.vehicle@2.0-service.g6.rc` - Vehicle HAL
- `/vendor/etc/init/vehiclelan.proxy@1.0-service.rc` - Vehicle LAN Proxy

---

## 🛠️ БИНАРНИКИ И БИБЛИОТЕКИ

### Ключевые бинарники:

- `/system/bin/vehicle.shmemslaver` - Shared Memory Slave
- `/system/bin/vehicle.linkdevicemanager` - Link Device Manager
- `/vendor/bin/hw/android.hardware.automotive.vehicle@2.0-service.g6` - Vehicle HAL Service
- `/vendor/bin/hw/com.desaysv.vehiclelan.proxy@1.0-service` - Vehicle LAN Proxy

### Ключевые библиотеки:

- `/system/lib64/android.hardware.automotive.vehicle@2.0.so` - Vehicle HAL
- `/system/lib64/libdevice_vehicle.so` - Device Vehicle Library
- `/system/lib64/libcar-framework-service-jni.so` - Car Framework JNI
- `/system/lib64/com.desaysv.vehiclelan.proxy@1.0.so` - Vehicle LAN Proxy

---

## 📊 ПЛАН ДЕЙСТВИЙ

### Немедленные действия:

1. **Извлечь APK `com.desaysv.vehicle.carplayapp`:**
   ```bash
   adb pull /product/app/Carplay/Carplay.apk
   ```

2. **Декомпилировать APK** для анализа:
   - Найти обработчики broadcast'ов
   - Изучить формат данных для `desay.thirdparty.navigation`
   - Найти структуру Intent extras

3. **Мониторинг broadcast'ов:**
   ```bash
   adb shell "logcat | grep -iE 'desay.thirdparty.navigation|turbodog.navigation'"
   ```

4. **Анализ формата данных:**
   - Изучить, какие extra данные передаются в broadcast
   - Найти структуру данных навигации
   - Определить обязательные поля

### Средний приоритет:

5. **Изучить Shared Memory:**
   - Структура данных в shared memory
   - Протокол обмена
   - Формат сообщений

6. **Анализ сетевых протоколов:**
   - Захват трафика на портах 10004, 31030, 31040, 31050
   - Анализ протокола обмена
   - Структура пакетов

---

## 🎯 РЕКОМЕНДУЕМЫЙ ПОДХОД

### Для отправки данных навигации в QNX:

1. **Использовать broadcast `desay.thirdparty.navigation`:**
   ```java
   Intent intent = new Intent("desay.thirdparty.navigation");
   intent.putExtra("navigation_data", navigationData);
   sendBroadcast(intent);
   ```

2. **Изучить формат данных:**
   - Извлечь APK `com.desaysv.vehicle.carplayapp`
   - Декомпилировать и найти обработчик broadcast
   - Изучить, какие поля ожидаются

3. **Альтернативный подход:**
   - Использовать `vehicle.shmemslaver` для прямого обмена через shared memory
   - Изучить протокол обмена через сетевые порты

---

## 📝 СЛЕДУЮЩИЕ ШАГИ

1. ✅ Извлечь APK `com.desaysv.vehicle.carplayapp`
2. ✅ Декомпилировать APK (JADX)
3. ✅ Найти обработчик `desay.thirdparty.navigation`
4. ✅ Изучить формат данных
5. ✅ Создать тестовый broadcast с данными навигации
6. ✅ Проверить получение данных в QNX

---

**Статус:** Ключевые интерфейсы найдены, готов к извлечению APK и анализу

