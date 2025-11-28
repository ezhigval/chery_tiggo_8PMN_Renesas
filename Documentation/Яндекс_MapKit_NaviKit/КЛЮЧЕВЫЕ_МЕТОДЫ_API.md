# Ключевые методы Yandex NaviKit API для перехвата

## Guidance - Основные методы

### Ограничение скорости

```java
// Метод API
LocalizedValue getSpeedLimit()
SpeedLimitStatus getSpeedLimitStatus()
SpeedLimitsPolicy getSpeedLimitsPolicy()

// Где искать в коде:
// - Вызовы: guidance.getSpeedLimit()
// - Сохранение: speedLimit = ..., currentSpeedLimit = ...
// - Обновление UI с ограничением скорости
```

### Маневры

```java
// Метод API
Windshield getWindshield()
List<Manoeuvre> getUpcomingManoeuvres() // через Windshield

// Где искать в коде:
// - Вызовы: windshield.getUpcomingManoeuvres()
// - Сохранение: manoeuvres = ..., nextManeuver = ...
// - Обновление UI с маневрами
```

### Маршрут

```java
// Метод API
DrivingRoute getCurrentRoute()
RouteStatus getRouteStatus()

// Где искать в коде:
// - Вызовы: guidance.getCurrentRoute()
// - Сохранение: currentRoute = ..., route = ...
// - Обновление карты с маршрутом
```

### Местоположение

```java
// Метод API
Location getLocation()
String getRoadName()

// Где искать в коде:
// - Вызовы: guidance.getLocation()
// - Сохранение: location = ..., currentLocation = ...
// - Обновление карты с позицией
```

## Windshield - Методы для HUD

```java
// Метод API
Object getSpeedLimit() // возвращает объект с getValue()
List<Manoeuvre> getUpcomingManoeuvres()

// Где искать в коде:
// - Вызовы: windshield.getSpeedLimit()
// - Сохранение: windshieldSpeedLimit = ...
// - Обновление HUD
```

## DrivingRoute - Методы для маршрута

```java
// Метод API (нужно найти в документации)
// Геометрия маршрута
getGeometry() или getPolyline() или getPoints()

// Где искать в коде:
// - Вызовы методов получения геометрии
// - Сохранение: routePoints = ..., routePolyline = ...
// - Отрисовка маршрута на карте
```

## MapTileProvider - Методы для карты

```java
// Метод API (нужно найти в документации)
// Тайлы карты
getTiles() или getTile() или getMapData()

// Где искать в коде:
// - Вызовы методов получения тайлов
// - Сохранение: mapTiles = ..., tiles = ...
// - Отрисовка карты
```

## Стратегия поиска в коде

### 1. Поиск вызовов API

```bash
# Ищем вызовы методов
grep -r "getSpeedLimit" decompiled/
grep -r "getUpcomingManoeuvres" decompiled/
grep -r "getCurrentRoute" decompiled/
```

### 2. Поиск сохранения результатов

```bash
# Ищем присваивания
grep -r "speedLimit\s*=" decompiled/
grep -r "manoeuvres\s*=" decompiled/
grep -r "currentRoute\s*=" decompiled/
```

### 3. Поиск обновления UI

```bash
# Ищем обновление UI компонентов
grep -r "setSpeedLimit" decompiled/
grep -r "updateManeuver" decompiled/
grep -r "drawRoute" decompiled/
```

## Примеры перехвата

### Пример 1: Ограничение скорости

```java
// Оригинальный код:
LocalizedValue speedLimit = guidance.getSpeedLimit();
this.currentSpeedLimit = speedLimit;

// Модифицированный код:
LocalizedValue speedLimit = guidance.getSpeedLimit();
this.currentSpeedLimit = speedLimit;
// Перехватываем:
if (speedLimit != null) {
    double value = speedLimit.getValue();
    int kmh = (int) Math.round(value * 3.6); // м/с -> км/ч
    TiggoBridgeSender.sendSpeedLimit(kmh);
}
```

### Пример 2: Маневры

```java
// Оригинальный код:
List<Manoeuvre> manoeuvres = windshield.getUpcomingManoeuvres();
this.upcomingManoeuvres = manoeuvres;

// Модифицированный код:
List<Manoeuvre> manoeuvres = windshield.getUpcomingManoeuvres();
this.upcomingManoeuvres = manoeuvres;
// Перехватываем:
if (manoeuvres != null && !manoeuvres.isEmpty()) {
    Manoeuvre next = manoeuvres.get(0);
    TiggoBridgeSender.sendManeuver(next);
}
```

### Пример 3: Геометрия маршрута

```java
// Оригинальный код:
Polyline routePolyline = route.getPolyline();
this.routeGeometry = routePolyline;

// Модифицированный код:
Polyline routePolyline = route.getPolyline();
this.routeGeometry = routePolyline;
// Перехватываем:
if (routePolyline != null) {
    List<Point> points = routePolyline.getPoints();
    TiggoBridgeSender.sendRouteGeometry(points);
}
```
