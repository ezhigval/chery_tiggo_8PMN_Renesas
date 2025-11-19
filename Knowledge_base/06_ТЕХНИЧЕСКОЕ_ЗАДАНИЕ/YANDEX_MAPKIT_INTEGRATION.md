# Интеграция Yandex MapKit SDK вместо TurboDog

## Цель проекта

Заменить навигационное приложение **TurboDog** на **Yandex MapKit SDK**, сохранив при этом все функции интеграции с системой:

- ✅ Актуальные карты с пробками (Yandex Maps)
- ✅ Качественное построение маршрутов (Yandex Navigator)
- ✅ Вывод карты на второй дисплей (приборная панель/cluster)
- ✅ Отображение ограничений скорости на проекцию
- ✅ Отображение указателей/маневров на проекцию
- ✅ Интеграция с MapService и QNX системой

## Текущая архитектура (TurboDog)

```
┌─────────────────────────────────────┐
│  QNX система (приборка)             │
│  Инициирует показ карты             │
└──────────────┬──────────────────────┘
               │ CAN/шина
               ▼
┌─────────────────────────────────────┐
│  com.desaysv.mapservice             │
│  - SVCarLanManager                  │
│  - MeterControl                     │
│  - ActivityUtil                     │
│  - TurboDogAdapter                  │
└──────────────┬──────────────────────┘
               │ Broadcast: "показать карту"
               ▼
┌─────────────────────────────────────┐
│  com.astrob.turbodog                │
│  - WelcomeActivity                  │
│  - TurboDogGpsService               │
│  - NaviAIDLService                  │
│  - CTurboDogDlg                     │
└──────────────┬──────────────────────┘
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌─────────────┐  ┌──────────────┐
│ Display 0   │  │ Display 1    │
│ Основной    │  │ Presentation │
│ (1920x720)  │  │ (1920x720)   │
└─────────────┘  └──────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Приборная      │
              │  панель/cluster │
              └─────────────────┘

TurboDog → Broadcast:
- `turbodog.navigation.system.message` (CODE=202, DATA=1)
- MapService ловит и прокидывает в QNX
```

## Новая архитектура (Yandex MapKit)

```
┌─────────────────────────────────────┐
│  QNX система (приборка)             │
│  Инициирует показ карты             │
└──────────────┬──────────────────────┘
               │ CAN/шина
               ▼
┌─────────────────────────────────────┐
│  com.desaysv.mapservice             │
│  - SVCarLanManager                  │
│  - MeterControl                     │
│  - ActivityUtil                     │
│  - YandexMapAdapter (новый)         │  ← Модифицируем
└──────────────┬──────────────────────┘
               │ Broadcast: "показать карту"
               ▼
┌─────────────────────────────────────┐
│  Yandex Maps APK (модифицированный) │
│  - MapActivity                      │
│  - NavigationService                │
│  - YandexMapPresentation            │  ← Новый компонент
│  - TiggoBridgeService               │  ← Новый bridge
└──────────────┬──────────────────────┘
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌─────────────┐  ┌──────────────┐
│ Display 0   │  │ Display 1    │
│ Основной    │  │ Presentation │
│ (1920x720)  │  │ (1920x720)   │
│             │  │ Yandex карта │
└─────────────┘  └──────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Приборная      │
              │  панель/cluster │
              └─────────────────┘

Yandex Maps → TiggoBridgeService → Broadcast:
- `turbodog.navigation.system.message` (совместимый формат)
- MapService ловит и прокидывает в QNX
```

## Поток данных Yandex NaviKit → Система

```
┌─────────────────────────────────────┐
│  Yandex NaviKit (встроенный в APK)  │
│  - Guidance                         │
│  - Windshield                       │
│  - DrivingRoute                     │
│  - Location                         │
└──────────────┬──────────────────────┘
               │ Reflection API
               ▼
┌─────────────────────────────────────┐
│  TiggoBridgeService                 │
│  - Перехватывает данные NaviKit     │
│  - Извлекает:                       │
│    • Ограничение скорости           │
│    • Маневры                        │
│    • Маршрут (геометрия)            │
│    • Текущее местоположение         │
│    • Статус маршрута                │
└──────────────┬──────────────────────┘
               │ Broadcast Intent
               │ (совместимый с TurboDog)
               ▼
┌─────────────────────────────────────┐
│  com.desaysv.mapservice             │
│  - YandexMapAdapter                 │
│  - Принимает broadcast              │
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

## TurboDog - Технологии

**Платформа:**
- Native C/C++ (JNI) для навигационного движка
- OpenGL ES для графического рендеринга
- NanoVG для векторной графики
- SecondaryRenderThread для второго дисплея

**Оптимизации TurboDog:**
1. Нативный код (C/C++) - высокая производительность
2. OpenGL ES - аппаратное ускорение на GPU
3. NanoVG - легковесная векторная графика
4. Многопоточность - параллельный рендеринг двух дисплеев
5. Оптимизация памяти - кеширование тайлов
6. Оптимизация батареи - эффективное использование GPS

**Подробнее:** См. `TURBODOG_TECHNOLOGY.md`

## Компоненты для реализации

### 1. Модификация Yandex Maps APK

**Файл:** `development/apk_modification/yandexmaps_modified/`

**Изменения:**
- Добавить класс `TiggoBridgeService` для перехвата данных NaviKit через **публичный API**
- Модифицировать `MapActivity` для создания Presentation окна на втором дисплее
- Добавить `YandexMapPresentation` для отображения **упрощенной** карты на Display 1
- Интегрировать перехват данных через **публичный Yandex MapKit API** (не Reflection)

**Оптимизации:**
- Display 0: Полноценная карта со всеми деталями
- Display 1: Упрощенная карта (только маршрут, камеры, события) для минимизации нагрузки
- Кеширование данных для снижения вызовов API
- Оптимизация частоты обновлений (Display 1 обновляется реже)

**Основные классы:**
```java
// Перехват данных из NaviKit через публичный API (не Reflection!)
public class TiggoBridgeService extends Service implements GuidanceListener {
    private Navigation navigation;
    private Guidance guidance;
    
    // Публичный API - быстро и стабильно
    void extractAndSendNavigationData() {
        // Ограничение скорости через публичный API
        LocalizedValue speedLimit = guidance.getSpeedLimit();
        
        // Маневры через публичный API
        Windshield windshield = guidance.getWindshield();
        List<Manoeuvre> manoeuvres = windshield.getUpcomingManoeuvres();
        
        // Маршрут через публичный API
        DrivingRoute route = guidance.getCurrentRoute();
        
        // Кеширование для оптимизации
        if (shouldUseCache()) {
            return cachedData;
        }
        
        // Отправка через Broadcast
        sendBroadcastCompatibleWithTurboDog(...);
    }
}

// Presentation окно для второго дисплея (УПРОЩЕННАЯ карта)
public class YandexMapPresentation extends Presentation {
    private MapView mapView;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        // Создаем MapView для отображения УПРОЩЕННОЙ карты на Display 1
        mapView = new MapView(getContext());
        
        // Настраиваем упрощенный режим (без детализации)
        map.setMapType(MapType.VECTOR);
        // Только: маршрут (полилиния), камеры, события
        // Без: POI, детальной карты, зданий
    }
}
```

### 2. Bridge Service для совместимости

**Файл:** `development/apk_modification/tiggo_bridge/`

**Функции:**
- Перехват данных из Yandex NaviKit через Reflection
- Преобразование в формат, совместимый с TurboDog
- Отправка broadcast сообщений в формате `turbodog.navigation.system.message`

**Совместимость с TurboDog:**
```java
// Формат broadcast от TurboDog:
// Intent { act=turbodog.navigation.system.message }
// Bundle[{CODE=202, DATA=1}]
// CODE=202: маршрут построен/активен

// Наш bridge отправляет аналогичный формат:
Intent intent = new Intent("turbodog.navigation.system.message");
intent.putExtra("CODE", 202);  // Статус маршрута
intent.putExtra("DATA", hasActiveRoute ? 1 : 0);
intent.putExtra("SPEED_LIMIT", speedLimitKmh);
intent.putExtra("MANEUVER_DISTANCE", maneuverDistanceMeters);
// ... и т.д.
```

### 3. Модификация MapService (опционально)

**Файл:** `development/sources/com/desaysv/mapservice/`

**Изменения:**
- Добавить `YandexMapAdapter` аналогично `TurboDogAdapter`
- Обрабатывать broadcast от Yandex Maps
- Прокидывать данные в QNX (как TurboDog)

**Альтернатива:**
- Не модифицировать MapService, а использовать существующий `TurboDogAdapter`
- Отправлять broadcast в формате, полностью совместимом с TurboDog

### 4. Presentation окно на втором дисплее

**Реализация:**
```java
public class MainMapActivity extends AppCompatActivity {
    private Display[] displays;
    private YandexMapPresentation presentation;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Получаем список дисплеев
        DisplayManager displayManager = (DisplayManager) getSystemService(Context.DISPLAY_SERVICE);
        displays = displayManager.getDisplays();
        
        // Находим второй дисплей (Display 1)
        if (displays.length > 1) {
            Display secondaryDisplay = displays[1];
            
            // Создаем Presentation окно
            presentation = new YandexMapPresentation(this, secondaryDisplay);
            presentation.show();
            
            // Настраиваем карту на Presentation
            presentation.setupMapView(guidance);
        }
    }
}
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
  → для каждого маневра: getTitle(), getSubtitle(), getDistance()
```

### 3. Маршрут (геометрия)
```java
Guidance.getCurrentRoute() → DrivingRoute
  → getGeometry() или getPolyline() → список точек
```

### 4. Текущее местоположение
```java
Guidance.getLocation() → Location
  → getPosition() → Point (lat, lon)
  → getBearing() → float (направление)
```

### 5. Статус маршрута
```java
Guidance.getRouteStatus() → RouteStatus
  → isActive(), isCompleted(), getProgress()
```

## Этапы реализации

### Этап 1: Подготовка (1-2 дня)
- [ ] Изучить Yandex MapKit/NaviKit SDK документацию
- [ ] Найти методы для получения всех необходимых данных
- [ ] Подготовить окружение для модификации APK
- [ ] Создать базовую структуру проекта

### Этап 2: Bridge Service (2-3 дня)
- [ ] Создать `TiggoBridgeService` для перехвата данных
- [ ] Реализовать извлечение данных через Reflection API
- [ ] Реализовать отправку broadcast в совместимом формате
- [ ] Протестировать перехват данных

### Этап 3: Presentation окно (2-3 дня)
- [ ] Создать `YandexMapPresentation` для Display 1
- [ ] Интегрировать MapView в Presentation
- [ ] Настроить отображение карты на втором дисплее
- [ ] Протестировать на эмуляторе

### Этап 4: Интеграция с системой (1-2 дня)
- [ ] Настроить запуск Yandex Maps при запросе от QNX
- [ ] Обеспечить совместимость broadcast с MapService
- [ ] Протестировать интеграцию с MapService

### Этап 5: Тестирование (2-3 дня)
- [ ] Тестирование на эмуляторе
- [ ] Тестирование всех функций навигации
- [ ] Проверка отображения на втором дисплее
- [ ] Проверка интеграции с QNX

### Этап 6: Оптимизация (1-2 дня)
- [ ] Оптимизация производительности
- [ ] Оптимизация батареи
- [ ] Финальная полировка

## Требования

### Технические
- Android SDK для модификации APK
- Yandex MapKit SDK ключ API
- Доступ к исходникам или декомпилированный APK Yandex Maps
- Инструменты: jadx, apktool, Android Studio

### Функциональные
- Совместимость с существующим MapService
- Совместимость с QNX системой
- Сохранение всех функций TurboDog
- Поддержка тем/скинов системы

## Риски и решения

### Риск 1: Yandex MapKit SDK требует интернет
**Решение:** 
- Поддержка оффлайн карт (если доступно в SDK)
- Кеширование тайлов карт
- Graceful degradation при отсутствии интернета

### Риск 2: Лицензия Yandex MapKit SDK
**Решение:**
- Проверить условия лицензии для коммерческого использования
- Возможно, использовать публичный API вместо SDK

### Риск 3: Производительность на старом железе
**Решение:**
- Оптимизация рендеринга карты
- Использование аппаратного ускорения
- Упрощение отображения для Presentation окна

### Риск 4: Совместимость с существующим MapService
**Решение:**
- Тщательное тестирование broadcast сообщений
- При необходимости модификация MapService (если есть исходники)

## Ожидаемый результат

✅ **Идеальный навигатор:**
- Актуальные карты Yandex с пробками
- Качественное построение маршрутов
- Вывод карты на приборную панель
- Отображение ограничений скорости и указателей на проекцию
- Полная интеграция с системой автомобиля

## Ссылки

- [Yandex MapKit SDK документация](https://yandex.ru/maps-api/docs/mapkit/index.html)
- [Yandex NaviKit документация](https://yandex.ru/maps-api/docs/navikit/android/index.html)
- [Документация проекта](Документация/Яндекс_MapKit_NaviKit/)
- [TurboDog архитектура](docs/turbodog_navigation.md)

