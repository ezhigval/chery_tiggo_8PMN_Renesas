# Tiggo Bridge - Интеграция Yandex MapKit вместо TurboDog

## Описание

Bridge-сервис для интеграции **Yandex MapKit SDK** вместо навигационного приложения **TurboDog**, с сохранением всех функций интеграции с системой автомобиля:

- ✅ Актуальные карты Yandex с пробками
- ✅ Качественное построение маршрутов
- ✅ Вывод карты на второй дисплей (приборная панель/cluster)
- ✅ Отображение ограничений скорости на проекцию
- ✅ Отображение указателей/маневров на проекцию
- ✅ Полная интеграция с MapService и QNX системой

## Оптимизации производительности

### Два режима отображения карты

**Display 0 (Основной экран):**
- ✅ Полноценная карта со всеми деталями
- ✅ POI, события, пробки
- ✅ Полная детализация карты
- ✅ Все слои карты включены

**Display 1 (Приборная панель - Presentation):**
- ✅ Упрощенная карта без детализации
- ✅ Только линии маршрута
- ✅ Камеры скорости
- ✅ Дорожные события
- ✅ Минимальная нагрузка на систему

### Технические оптимизации

1. **Публичный API вместо Reflection:**
   - Прямой доступ к Yandex MapKit API
   - Нет накладных расходов Reflection
   - Лучшая производительность и стабильность

2. **Кеширование данных:**
   - Кеш валиден 300ms для минимизации вызовов API
   - Оптимизация частоты обновлений
   - Снижение нагрузки на CPU

3. **Асинхронная обработка:**
   - Обработка данных в фоновых потоках
   - Неблокирующий UI поток
   - Использование Handler и Timer

4. **Оптимизация рендеринга:**
   - Разные настройки для двух дисплеев
   - Минимизация объектов на упрощенной карте
   - Использование аппаратного ускорения (GPU)

5. **Оптимизация обновлений:**
   - Display 0: обновления по требованию
   - Display 1: обновления раз в 2 секунды (реже)
   - Кеширование для предотвращения лишних обновлений

## Архитектура

```
┌─────────────────────────────────────┐
│  Yandex NaviKit (встроенный в APK)  │
│  - Guidance                         │
│  - Windshield                       │
│  - DrivingRoute                     │
└──────────────┬──────────────────────┘
               │ Reflection API
               ▼
┌─────────────────────────────────────┐
│  TiggoBridgeService                 │
│  - Перехватывает данные NaviKit     │
│  - Извлекает ограничения скорости   │
│  - Извлекает маневры                │
│  - Извлекает маршрут                │
│  - Отправляет broadcast             │
└──────────────┬──────────────────────┘
               │ Broadcast Intent
               │ (совместимый с TurboDog)
               ▼
┌─────────────────────────────────────┐
│  com.desaysv.mapservice             │
│  - YandexMapAdapter                 │
│  - Прокидывает в QNX                │
└──────────────┬──────────────────────┘
               │
               ▼
        ┌──────────────┐
        │     QNX      │
        │  Приборка    │
        │  Проекция    │
        └──────────────┘
```

## Компоненты

### 1. TiggoBridgeService

Основной сервис для перехвата данных из Yandex NaviKit.

**Функции:**
- Перехват данных через Reflection API
- Извлечение ограничений скорости (`Guidance.getSpeedLimit()`)
- Извлечение маневров (`Windshield.getUpcomingManoeuvres()`)
- Извлечение маршрута (`Guidance.getCurrentRoute()`)
- Извлечение местоположения (`Guidance.getLocation()`)
- Отправка broadcast в формате, совместимом с TurboDog

**Период обновления:** 500ms

### 2. YandexMapPresentation

Presentation окно для отображения карты на втором дисплее (Display 1 - приборная панель).

**Функции:**
- Создание окна на Display 1 (`mDisplayId=1`)
- Отображение карты через `MapView`
- Интеграция с Guidance для навигации

### 3. MainMapActivity

Главная Activity для Yandex Maps с поддержкой двух дисплеев.

**Функции:**
- Создание основного окна на Display 0
- Создание Presentation окна на Display 1
- Запуск TiggoBridgeService
- Управление жизненным циклом карты

## Установка

### 1. Подготовка

1. Декомпилировать Yandex Maps APK:
   ```bash
   jadx -d yandexmaps_decompiled yandexmaps.apk
   ```

2. Изучить структуру NaviKit классов в декомпилированном коде

3. Создать модуль `tiggo_bridge` с классами:
   - `TiggoBridgeService.java`
   - `YandexMapPresentation.java`
   - `MainMapActivity.java`

### 2. Интеграция

1. Добавить классы в проект Yandex Maps APK

2. Модифицировать AndroidManifest.xml:
   - Добавить разрешения
   - Зарегистрировать сервис
   - Зарегистрировать Activity

3. Добавить зависимости на Yandex MapKit SDK в `build.gradle`

### 3. Компиляция

1. Собрать APK с помощью Android Studio или Gradle:
   ```bash
   ./gradlew assembleDebug
   ```

2. Подписать APK (если нужно)

3. Установить на устройство:
   ```bash
   adb install -r yandexmaps_modified.apk
   ```

## Использование

### Запуск навигации

1. **Через MapService (автоматический):**
   - QNX инициирует показ карты
   - MapService запускает Yandex Maps через Intent
   - MainMapActivity создает окна на двух дисплеях
   - TiggoBridgeService автоматически перехватывает данные

2. **Вручную:**
   ```bash
   adb shell am start -n ru.yandex.yandexmaps/.tiggo.MainMapActivity
   ```

### Проверка работы

1. **Проверить broadcast сообщения:**
   ```bash
   adb logcat | grep -i "turbodog.navigation.system.message"
   ```

2. **Проверить Bridge Service:**
   ```bash
   adb logcat | grep -i "TiggoBridge"
   ```

3. **Проверить Presentation окно:**
   ```bash
   adb shell dumpsys window windows | grep -i "Presentation"
   ```

## Формат broadcast сообщений

### Совместимый с TurboDog

```java
Intent intent = new Intent("turbodog.navigation.system.message");

// Базовые данные (совместимые с TurboDog)
intent.putExtra("CODE", 202);  // Маршрут активен
intent.putExtra("DATA", hasActiveRoute ? 1 : 0);

// Дополнительные данные
intent.putExtra("SPEED_LIMIT", speedLimitKmh);  // км/ч
intent.putExtra("SPEED_LIMIT_TEXT", "60 km/h");
intent.putExtra("MANEUVER_TITLE", "Поверните налево");
intent.putExtra("MANEUVER_SUBTITLE", "на улицу Ленина");
intent.putExtra("MANEUVER_DISTANCE", distanceMeters);  // метры
intent.putExtra("ROUTE_ACTIVE", hasRoute);
intent.putExtra("ROUTE_DISTANCE", distanceMeters);
intent.putExtra("ROUTE_DURATION", durationSeconds);
intent.putExtra("CURRENT_LAT", latitude);
intent.putExtra("CURRENT_LON", longitude);
intent.putExtra("BEARING", bearing);  // градусы
intent.putExtra("ROAD_NAME", "улица Ленина");

sendBroadcast(intent);
```

## Данные для перехвата

### 1. Ограничение скорости

```java
Guidance.getSpeedLimit() → LocalizedValue
  → getValue() → double (м/с) → конвертировать в км/ч
  → getText() → String ("60 km/h")
```

### 2. Маневры

```java
Windshield.getUpcomingManoeuvres() → List<Manoeuvre>
  → для каждого маневра:
    - getTitle() → String ("Поверните налево")
    - getSubtitle() → String ("на улицу Ленина")
    - getDistance() → LocalizedValue (метры)
```

### 3. Маршрут (геометрия)

```java
Guidance.getCurrentRoute() → DrivingRoute
  → getPolyline() → Polyline
    → getPoints() → List<Point> (координаты маршрута)
  → getDistance() → LocalizedValue (метры)
  → getDuration() → LocalizedValue (секунды)
```

### 4. Текущее местоположение

```java
Guidance.getLocation() → Location
  → getPosition() → Point
    → getLatitude() → double
    → getLongitude() → double
  → getBearing() → float (направление движения)
  
Guidance.getRoadName() → String ("улица Ленина")
```

### 5. Статус маршрута

```java
Guidance.getRouteStatus() → RouteStatus
  → isActive() → boolean
  → isCompleted() → boolean
  → getProgress() → double (0.0 - 1.0)
```

## Отладка

### Логирование

Все компоненты логируют в `logcat` с тегом `TiggoBridge`:

```bash
adb logcat -s TiggoBridge:D
```

### Проверка Reflection

Если Reflection API не работает, проверьте:

1. Правильность имен классов NaviKit
2. Правильность имен методов
3. Доступность классов (не proguard)

### Проверка Presentation окна

Проверить, что Presentation окно создано на правильном дисплее:

```bash
adb shell dumpsys window displays
adb shell dumpsys window windows | grep Presentation
```

Должно быть:
- `mDisplayId=1`
- `ty=PRESENTATION`
- `package=ru.yandex.yandexmaps`

## Требования

- Android SDK 21+ (Android 5.0+)
- Yandex MapKit SDK
- Поддержка нескольких дисплеев (DisplayManager API)
- Разрешения: ACCESS_FINE_LOCATION, INTERNET, SYSTEM_ALERT_WINDOW

## Известные проблемы

1. **Reflection API может не работать:**
   - Если Yandex Maps использует ProGuard/R8
   - Решение: использовать публичные API вместо Reflection

2. **Presentation окно может не создаваться:**
   - Если второй дисплей недоступен
   - Решение: проверить DisplayManager и список дисплеев

3. **Broadcast может не доходить до MapService:**
   - Если MapService не зарегистрирован на broadcast
   - Решение: проверить IntentFilter в MapService

## Дальнейшее развитие

- [ ] Поддержка оффлайн карт
- [ ] Оптимизация производительности
- [ ] Поддержка тем/скинов системы
- [ ] Улучшение отображения на втором дисплее
- [ ] Поддержка голосовых подсказок

## Ссылки

- [Архитектурный документ](../../../Документация/06_ТЕХНИЧЕСКОЕ_ЗАДАНИЕ/YANDEX_MAPKIT_INTEGRATION.md)
- [Yandex MapKit SDK документация](https://yandex.ru/maps-api/docs/mapkit/index.html)
- [Yandex NaviKit документация](https://yandex.ru/maps-api/docs/navikit/android/index.html)
- [TurboDog архитектура](../../../docs/turbodog_navigation.md)

