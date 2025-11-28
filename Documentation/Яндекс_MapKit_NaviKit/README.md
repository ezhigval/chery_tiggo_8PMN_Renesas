# Документация Yandex MapKit и NaviKit для Android

## Цель

Изучить полную документацию NaviKit для Android, чтобы понимать:

- Какие классы и методы использовать
- Где и как получать нужные данные
- В каком виде данные возвращаются

## Нужные данные для извлечения

1. **Карта** - текущее отображение карты, координаты, масштаб
2. **Маршрут (булини/полилинии)** - геометрия маршрута для отображения
3. **Маневры** - предстоящие маневры на маршруте
4. **Ограничения скорости** - текущие ограничения скорости на дороге
5. **События на карте** - камеры, дорожные события
6. **Статус маршрута** - состояние навигации, прогресс по маршруту

## Основные классы NaviKit

### Guidance

Основной класс для работы с навигацией.

**Методы для получения данных:**

- `getWindshield()` - @NonNull Windshield - данные для отображения на лобовом стекле
- `getSpeedLimit()` - @Nullable LocalizedValue - ограничение скорости на текущей дороге
- `getSpeedLimitStatus()` - @NonNull SpeedLimitStatus - статус ограничения скорости
- `getCurrentRoute()` - @Nullable DrivingRoute - текущий маршрут
- `getLocation()` - @Nullable Location - текущее местоположение
- `getRouteStatus()` - @NonNull RouteStatus - статус маршрута
- `getRoadName()` - @Nullable String - название текущей дороги

### Windshield

Данные для отображения на лобовом стекле (HUD).

**Методы:**

- `getSpeedLimit()` - ограничение скорости
- `getUpcomingManoeuvres()` - предстоящие маневры

### LocalizedValue

Значение с локализацией.

**Методы:**

- `getValue()` - double - значение в единицах СИ (для скорости - м/с)
- `getText()` - String - локализованный текст (например, "60 km/h")

### SpeedLimitStatus

Статус ограничения скорости.

### DrivingRoute

Текущий маршрут.

**Методы для получения геометрии:**

- Методы для получения полилиний маршрута

## Архитектура данных

```
Yandex Maps APK (модифицированный)
  ↓
  Извлекаем данные через Reflection:
    - Guidance.getWindshield()
    - Guidance.getSpeedLimit()
    - Guidance.getCurrentRoute()
    - Guidance.getLocation()
    - и т.д.
  ↓
  Отправляем через Broadcast Intent
  ↓
BridgeService
  ↓
  Разворачиваем данные до итоговых значений
  ↓
  ├─→ UI (Dashboard, HUD, Status)
  └─→ QNX (приборка, проекция)
```

## Ссылки на документацию

- [MapKit и NaviKit SDK](https://yandex.ru/maps-api/docs/mapkit/index.html)
- [NaviKit для Android](https://yandex.ru/maps-api/docs/navikit/android/index.html)
- [Guidance API](https://yandex.com/maps-api/docs/mapkit/android/generated/navigation/guidance.html)

## План действий

1. ✅ Скачать документацию
2. ⏳ Изучить структуру классов NaviKit
3. ⏳ Определить точные методы для получения каждого типа данных
4. ⏳ Обновить код извлечения данных согласно документации
5. ⏳ Реализовать отправку данных в BridgeService
6. ⏳ Реализовать разворачивание данных в BridgeService
7. ⏳ Реализовать отправку в QNX
