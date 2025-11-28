# Архитектура Bridge Service для Яндекс Навигатора

## 🎯 Цель

Создать Bridge Service, который:
1. **Мониторит Яндекс Навигатор** - получает данные о навигации
2. **Извлекает данные** - маршрут, повороты, карта, расстояние
3. **Отрисовывает упрощенную карту** - создает упрощенную версию для приборной панели
4. **Отправляет на приборную панель** - через систему проекции (как TurboDog)

---

## 🏗️ Архитектура

```
┌─────────────────────────────────────────┐
│  Яндекс Навигатор                       │
│  (ru.yandex.yandexnavi)                 │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  UI с картой и навигацией          │ │
│  │  - Текущая позиция                 │ │
│  │  - Маршрут                         │ │
│  │  - Повороты                        │ │
│  │  - Расстояние/время                │ │
│  └───────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
               │ Мониторинг
               ▼
┌─────────────────────────────────────────┐
│  Bridge Service                         │
│  (com.desaysv.navibridge)              │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  NavigationMonitor                │ │
│  │  ├── AccessibilityService         │ │
│  │  ├── BroadcastReceiver           │ │
│  │  └── MediaProjection (опционально)│ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  DataExtractor                    │ │
│  │  ├── ExtractRoute()               │ │
│  │  ├── ExtractTurns()               │ │
│  │  ├── ExtractDistance()            │ │
│  │  └── ExtractMapImage()            │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  MapRenderer                       │ │
│  │  ├── RenderSimplifiedMap()         │ │
│  │  ├── RenderRoute()                 │ │
│  │  ├── RenderTurn()                  │ │
│  │  └── RenderInfo()                  │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  SystemSender                     │ │
│  │  ├── SendNavigationData()        │ │
│  │  ├── SendMapImage()               │ │
│  │  └── SendToCAN()                  │ │
│  └───────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
               │ Broadcast Intent
               │ "turbodog.navigation.system.message"
               ▼
┌─────────────────────────────────────────┐
│  Система автомобиля                      │
│  ├── SVMeterInteraction                 │
│  ├── QNX система                        │
│  └── CAN-шина                           │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Приборная панель                 │ │
│  │  - Упрощенная карта               │ │
│  │  - Индикатор поворота              │ │
│  │  - Расстояние/время                │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  HUD (Head-Up Display)            │ │
│  │  - Стрелка направления              │ │
│  │  - Расстояние до поворота          │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## 📦 Компоненты Bridge Service

### 1. NavigationMonitor

**Назначение:** Мониторинг Яндекс Навигатора

**Реализация:**
```java
public class NavigationMonitor {
    private AccessibilityService accessibilityService;
    private BroadcastReceiver broadcastReceiver;
    private MediaProjection mediaProjection;
    
    public void startMonitoring() {
        // 1. Запустить Accessibility Service
        startAccessibilityService();
        
        // 2. Зарегистрировать Broadcast Receiver
        registerBroadcastReceiver();
        
        // 3. (Опционально) Запросить MediaProjection
        requestMediaProjection();
    }
    
    private void startAccessibilityService() {
        // Мониторинг UI элементов Яндекс Навигатора
    }
    
    private void registerBroadcastReceiver() {
        // Слушаем события от Яндекс Навигатора
        IntentFilter filter = new IntentFilter();
        filter.addAction("ru.yandex.yandexnavi.NAVIGATION_STARTED");
        filter.addAction("ru.yandex.yandexnavi.NAVIGATION_UPDATED");
        // ...
    }
}
```

---

### 2. DataExtractor

**Назначение:** Извлечение данных из Яндекс Навигатора

**Реализация:**
```java
public class DataExtractor {
    public NavigationData extractFromAccessibility(AccessibilityEvent event) {
        NavigationData data = new NavigationData();
        
        // Извлекаем данные из UI
        if (event.getPackageName().equals("ru.yandex.yandexnavi")) {
            // Получаем текст
            String text = event.getText().toString();
            
            // Парсим данные
            data.setTurnDistance(parseDistance(text));
            data.setTurnType(parseTurnType(text));
            data.setRemainingDistance(parseRemainingDistance(text));
            // ...
        }
        
        return data;
    }
    
    public NavigationData extractFromImage(Bitmap mapImage) {
        NavigationData data = new NavigationData();
        
        // Обработка изображения карты
        // - Распознавание маршрута
        // - Определение позиции
        // - Извлечение поворотов
        
        return data;
    }
    
    public Bitmap captureMapImage() {
        // Используем MediaProjection для скриншота
        // Обрезаем только область карты
        return mapBitmap;
    }
}
```

---

### 3. MapRenderer

**Назначение:** Отрисовка упрощенной карты

**Реализация:**
```java
public class MapRenderer {
    private static final int MAP_WIDTH = 800;
    private static final int MAP_HEIGHT = 480;
    
    public Bitmap renderSimplifiedMap(NavigationData data) {
        Bitmap bitmap = Bitmap.createBitmap(
            MAP_WIDTH, MAP_HEIGHT, Bitmap.Config.ARGB_8888
        );
        Canvas canvas = new Canvas(bitmap);
        
        // Фон
        canvas.drawColor(Color.BLACK);
        
        // Рисуем маршрут
        drawRoute(canvas, data.getRoute());
        
        // Рисуем текущую позицию
        drawCurrentPosition(canvas, data.getCurrentPosition());
        
        // Рисуем поворот
        drawTurn(canvas, data.getNextTurn());
        
        // Рисуем информацию
        drawInfo(canvas, data);
        
        return bitmap;
    }
    
    private void drawRoute(Canvas canvas, Route route) {
        Paint paint = new Paint();
        paint.setColor(Color.WHITE);
        paint.setStrokeWidth(4);
        paint.setStyle(Paint.Style.STROKE);
        
        Path path = new Path();
        for (Point point : route.getPoints()) {
            if (path.isEmpty()) {
                path.moveTo(point.x, point.y);
            } else {
                path.lineTo(point.x, point.y);
            }
        }
        
        canvas.drawPath(path, paint);
    }
    
    private void drawCurrentPosition(Canvas canvas, Point position) {
        Paint paint = new Paint();
        paint.setColor(Color.BLUE);
        canvas.drawCircle(position.x, position.y, 12, paint);
        
        // Стрелка направления
        drawDirectionArrow(canvas, position, bearing);
    }
    
    private void drawTurn(Canvas canvas, TurnInfo turn) {
        if (turn == null) return;
        
        // Иконка поворота
        Bitmap turnIcon = getTurnIcon(turn.getType());
        canvas.drawBitmap(turnIcon, turn.getX(), turn.getY(), null);
        
        // Расстояние до поворота
        Paint textPaint = new Paint();
        textPaint.setColor(Color.WHITE);
        textPaint.setTextSize(28);
        textPaint.setTextAlign(Paint.Align.CENTER);
        
        String distance = formatDistance(turn.getDistance());
        canvas.drawText(distance, turn.getX(), turn.getY() + 60, textPaint);
    }
    
    private void drawInfo(Canvas canvas, NavigationData data) {
        Paint textPaint = new Paint();
        textPaint.setColor(Color.WHITE);
        textPaint.setTextSize(24);
        
        // Оставшееся расстояние
        String remaining = formatDistance(data.getRemainingDistance());
        canvas.drawText("Осталось: " + remaining, 20, 40, textPaint);
        
        // Оставшееся время
        String time = formatTime(data.getRemainingTime());
        canvas.drawText("Время: " + time, 20, 70, textPaint);
    }
}
```

---

### 4. SystemSender

**Назначение:** Отправка данных в систему автомобиля

**Реализация:**
```java
public class SystemSender {
    public void sendNavigationData(NavigationData data, Bitmap mapImage) {
        // Отправка через Broadcast Intent (как TurboDog)
        Intent intent = new Intent("turbodog.navigation.system.message");
        
        // Основные данные
        intent.putExtra("CODE", 200);
        intent.putExtra("DATA", 0);
        
        // Поворот
        intent.putExtra("TURN_TYPE", data.getTurnType());
        intent.putExtra("TURN_DIST", data.getTurnDistance());
        intent.putExtra("TURN_TIME", data.getTurnTime());
        
        // Маршрут
        intent.putExtra("REMAINING_DIST", data.getRemainingDistance());
        intent.putExtra("REMAINING_TIME", data.getRemainingTime());
        intent.putExtra("ARRIVE_TIME", data.getArriveTime());
        
        // Дороги
        intent.putExtra("CURRENT_ROAD", data.getCurrentRoad());
        intent.putExtra("NEXT_ROAD", data.getNextRoad());
        
        // Изображение карты (если поддерживается)
        if (mapImage != null) {
            byte[] imageBytes = bitmapToByteArray(mapImage);
            intent.putExtra("MAP_IMAGE", imageBytes);
        }
        
        sendBroadcast(intent);
    }
    
    private byte[] bitmapToByteArray(Bitmap bitmap) {
        ByteArrayOutputStream stream = new ByteArrayOutputStream();
        bitmap.compress(Bitmap.CompressFormat.PNG, 100, stream);
        return stream.toByteArray();
    }
}
```

---

## 🔄 Поток данных

### 1. Мониторинг

```
Яндекс Навигатор обновляет UI
    ↓
AccessibilityService получает событие
    ↓
NavigationMonitor обрабатывает событие
    ↓
DataExtractor извлекает данные
```

### 2. Отрисовка

```
NavigationData получен
    ↓
MapRenderer создает упрощенную карту
    ↓
Bitmap готов
```

### 3. Отправка

```
Bitmap + NavigationData готовы
    ↓
SystemSender формирует Broadcast Intent
    ↓
Отправка в систему
    ↓
Система отображает на приборной панели
```

---

## 📋 Структура проекта

```
BridgeService/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/
│   │   │   │   └── com/desaysv/navibridge/
│   │   │   │       ├── NavigationMonitor.java
│   │   │   │       ├── DataExtractor.java
│   │   │   │       ├── MapRenderer.java
│   │   │   │       ├── SystemSender.java
│   │   │   │       ├── NavigationData.java
│   │   │   │       ├── NavigationAccessibilityService.java
│   │   │   │       └── BridgeService.java
│   │   │   ├── res/
│   │   │   │   └── drawable/
│   │   │   │       ├── turn_left.png
│   │   │   │       ├── turn_right.png
│   │   │   │       └── ...
│   │   │   └── AndroidManifest.xml
│   │   └── test/
│   └── build.gradle
└── README.md
```

---

## 🎯 Преимущества подхода

1. ✅ **Профессионально:** Упрощенная карта выглядит как в TurboDog
2. ✅ **Надежно:** Не зависит от UI Яндекс Навигатора
3. ✅ **Гибко:** Можно настроить отображение
4. ✅ **Совместимо:** Использует тот же формат что TurboDog
5. ✅ **Эффективно:** Минимальная нагрузка на систему

---

**Дата:** 2024  
**Версия:** 1.0

