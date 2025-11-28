# Архитектура API для передачи данных из Yandex Maps

## Принцип работы

### Текущая архитектура:
```
┌─────────────────────────────────┐
│   Yandex Maps (модифицированный) │
│                                  │
│  ┌──────────────────────────┐   │
│  │  TiggoBridgeSender        │   │ ← Встроен в APK
│  │  (внутри Yandex Maps)     │   │
│  └──────────────────────────┘   │
│           │                      │
│           │ Broadcast Intent     │
│           ▼                      │
└──────────────────────────────────┘
           │
           │ com.desaysv.tiggo.bridge.*
           │
           ▼
┌─────────────────────────────────┐
│   TiggoBridgeService              │
│                                  │
│  ┌──────────────────────────┐   │
│  │  BroadcastReceiver        │   │ ← Слушает данные
│  │  - NAVIGATION_DATA        │   │
│  │  - MAP_DATA               │   │
│  │  - LOCATION_DATA          │   │
│  │  - ROUTE_DATA             │   │
│  └──────────────────────────┘   │
│           │                      │
│           │ Обработка            │
│           ▼                      │
│  ┌──────────────────────────┐   │
│  │  SystemSender             │   │
│  │  → QNX (приборная панель) │   │
│  └──────────────────────────┘   │
└──────────────────────────────────┘
```

## Типы данных (API Actions)

### 1. NAVIGATION_DATA
**Action:** `com.desaysv.tiggo.bridge.NAVIGATION_DATA`
**Частота:** Каждую секунду (при активной навигации)
**Данные:**
- `title` - название маневра
- `subtitle` - описание маневра
- `distanceLeft` - оставшееся расстояние
- `timeLeft` - оставшееся время
- `timeOfArrival` - время прибытия
- `currentLat` - текущая широта
- `currentLon` - текущая долгота
- `bearing` - направление движения
- `hasRoute` - есть ли маршрут
- `isHeadsUp` - режим навигации

### 2. MAP_DATA
**Action:** `com.desaysv.tiggo.bridge.MAP_DATA`
**Частота:** Каждую секунду (постоянно, даже без маршрута)
**Данные:**
- `mapImage` - Bitmap карты (byte[])
- `mapWidth` - ширина карты (1920)
- `mapHeight` - высота карты (720)
- `centerLat` - широта центра карты
- `centerLon` - долгота центра карты
- `zoom` - уровень масштаба
- `bearing` - поворот карты

### 3. LOCATION_DATA
**Action:** `com.desaysv.tiggo.bridge.LOCATION_DATA`
**Частота:** Каждые 0.5 секунды (постоянно)
**Данные:**
- `latitude` - широта
- `longitude` - долгота
- `bearing` - направление
- `speed` - скорость
- `accuracy` - точность
- `timestamp` - время получения

### 4. ROUTE_DATA
**Action:** `com.desaysv.tiggo.bridge.ROUTE_DATA`
**Частота:** При изменении маршрута
**Данные:**
- `routeCoordinates` - координаты маршрута (JSON)
- `routeDistance` - длина маршрута
- `routeTime` - время маршрута
- `waypoints` - точки маршрута

## Улучшенный TiggoBridgeSender

### Основные методы:

```java
// Инициализация (вызывается из класса k.smali)
public static void init()

// Подключение к Guidance и начало отправки данных
public void attachToGuidanceAndNotificationDataManager(
    Object guidance, 
    Object notificationDataManager)

// Подключение к MapView для отправки карты
public void attachToMapView(Object mapView)

// Внутренние методы отправки (вызываются автоматически)
private void sendMapData()        // Каждую секунду
private void sendLocationData()   // Каждые 0.5 сек
private void sendNavigationData() // Каждую секунду
private void sendRouteData()      // При изменении
```

### Преимущества API-подхода:

1. **Разделение ответственности:**
   - Yandex Maps только транслирует данные
   - BridgeService обрабатывает и отправляет в QNX

2. **Отказоустойчивость:**
   - Если один тип данных недоступен, остальные продолжают работать
   - Каждый тип данных отправляется независимо

3. **Гибкость:**
   - Можно легко добавить новые типы данных
   - Можно изменить частоту отправки для каждого типа

4. **Производительность:**
   - Данные отправляются только при наличии
   - Разные интервалы для разных типов данных

## План улучшения

### Этап 1: Обновление TiggoBridgeSender в APK
1. Заменить текущий TiggoBridgeSender на TiggoBridgeSenderEnhanced
2. Добавить постоянную отправку всех типов данных
3. Добавить поддержку MapView

### Этап 2: Обновление BridgeService
1. Добавить BroadcastReceiver для всех типов данных
2. Обработка MAP_DATA → отправка в QNX
3. Обработка LOCATION_DATA → обновление NavigationData
4. Обработка NAVIGATION_DATA → существующая логика
5. Обработка ROUTE_DATA → сохранение маршрута

### Этап 3: Интеграция MapView
1. Найти MapView в Yandex Maps через рефлексию
2. Захватывать карту каждую секунду
3. Отправлять через MAP_DATA

## Текущее состояние

✅ TiggoBridgeSender встроен в APK Yandex Maps
✅ Вызывается из класса k.smali (конструктор)
✅ Отправляет NAVIGATION_DATA
⏳ Нужно добавить постоянную отправку всех типов данных
⏳ Нужно добавить поддержку карты

