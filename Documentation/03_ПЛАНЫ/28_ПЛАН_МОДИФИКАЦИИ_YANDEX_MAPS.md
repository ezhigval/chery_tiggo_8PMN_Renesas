# План модификации APK Yandex Maps для перехвата данных навигации

## Цель
Перехватывать данные навигации на этапе их получения и отрисовки в Yandex Maps, отправляя их в TiggoBridgeService.

## Стратегия перехвата

### Точка 1: Класс k.java (конструктор)
**Файл:** `ru/yandex/yandexmaps/integrations/auto_navigation/navikit/k.java`

**Место инъекции:** После получения `Guidance` в конструкторе (строка 37-44)

**Код для добавления:**
```java
// После строки 44: NotificationDataManager notificationDataManager = guidance.notificationDataManager();
// Инициализация TiggoBridgeSender (Context получается автоматически)
TiggoBridgeSender.init(); // Получает Context через ActivityThread.currentApplication()
TiggoBridgeSender.getInstance().attachToGuidance(guidance);
```

**Решение:** Используем `TiggoBridgeSender.init()` без параметров, который автоматически получает Context через `ActivityThread.currentApplication()`.

### Точка 2: Класс f.java (наследник k)
**Файл:** `ru/yandex/yandexmaps/integrations/auto_navigation/navikit/f.java`

**Место инъекции:** В конструкторе после вызова super()

**Преимущество:** Класс f получает Guidance в конструкторе и передает его в super (класс k)

### Точка 3: Guidance.addListener()
**Перехват:** Когда приложение регистрирует GuidanceListener, мы тоже регистрируем наш

**Место:** В методе `onHandlerReady()` класса k (строка 79)

**Код:**
```java
// После строки 81: super.onHandlerReady(handler);
// Регистрируем наш GuidanceListener
TiggoBridgeSender.getInstance().attachToGuidance(guidance);
```

## Данные для перехвата

### Из Guidance:
- `getCurrentRoute()` - текущий маршрут
- `getRoutePosition()` - позиция на маршруте
- `getRemainingDistance()` - оставшееся расстояние
- `getTimeToFinish()` - время до конца
- `getLocation()` - текущая локация
- `getCourse()` - курс движения

### Из Route:
- `getNextManeuver()` - следующий маневр
- `getMetadata()` - метаданные маршрута

### Из GuidanceListener:
- `onRouteChanged()` - маршрут изменился
- `onLocationUpdated()` - локация обновлена
- `onGuidanceResumedChanged()` - навигация возобновлена/приостановлена

## Структура TiggoBridgeSender

**Пакет:** `ru.yandex.yandexmaps.bridge` (встроен в APK)

**Методы:**
- `init(Context)` - инициализация
- `getInstance()` - получение экземпляра
- `attachToGuidance(Guidance)` - подключение к Guidance
- `detachFromGuidance()` - отключение

**Отправка данных:**
- Broadcast Intent: `com.desaysv.tiggo.bridge.NAVIGATION_DATA`
- Package: `com.desaysv.tiggo.bridge`

## Шаги модификации

### 1. Подготовка
```bash
# Установить инструменты
brew install apktool
# apksigner входит в Android SDK

# Создать keystore для подписи
keytool -genkey -v -keystore tiggo_maps.keystore -alias tiggo \
    -keyalg RSA -keysize 2048 -validity 10000
```

### 2. Декомпиляция APK
```bash
cd development/extracted_from_device
apktool d ru.yandex.yandexmaps.apk -o yandexmaps_decompiled
```

### 3. Поиск класса k
```bash
find yandexmaps_decompiled/smali -path "*auto_navigation/navikit/k.smali"
```

### 4. Добавление TiggoBridgeSender
- Скомпилировать TiggoBridgeSender.java в .class
- Конвертировать в dex
- Конвертировать dex в smali
- Скопировать в `yandexmaps_decompiled/smali/ru/yandex/yandexmaps/bridge/`

### 5. Модификация класса k.smali
Найти конструктор и добавить вызовы:
```smali
# После получения NotificationDataManager (после строки с iput-object для f180940a)
# Инициализация TiggoBridgeSender (Context получается автоматически)
invoke-static {}, Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;->init()V

# Подключение к Guidance (guidance находится в p4)
invoke-static {}, Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;->getInstance()Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;
move-result-object vX
invoke-virtual {vX, p4}, Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;->attachToGuidance(Lcom/yandex/navikit/guidance/Guidance;)V
```

**Примечание:** Параметры конструктора k: p0=this, p1=notificationManager, p2=notificationBuilder, p3=notificationClickReceiver, p4=guidance, p5=mainScheduler. Нужно проверить точную позицию в Smali коде после декомпиляции.

### 6. Ре-компиляция APK
```bash
cd yandexmaps_decompiled
apktool b . -o yandexmaps_modified.apk
```

### 7. Подпись APK
```bash
apksigner sign --ks tiggo_maps.keystore --ks-key-alias tiggo yandexmaps_modified.apk
```

### 8. Установка
```bash
adb uninstall ru.yandex.yandexmaps
adb install yandexmaps_modified.apk
```

## Альтернативные точки перехвата

### Вариант A: Перехват в Application классе
Найти Application класс Yandex Maps и инициализировать TiggoBridgeSender там.

### Вариант B: Перехват в MapActivity
Найти главную Activity и инициализировать там.

### Вариант C: Перехват через Proxy Guidance
Создать Proxy для Guidance и перехватывать все вызовы методов.

## Проверка работы

### Логи
```bash
adb logcat | grep -E "(TiggoBridgeSender|BridgeService|NAVIGATION_DATA)"
```

### Ожидаемые логи:
```
TiggoBridgeSender: TiggoBridgeSender инициализирован
TiggoBridgeSender: Подключение к Guidance: ...
TiggoBridgeSender: ✓ GuidanceListener зарегистрирован в Guidance
TiggoBridgeSender: === Извлечение данных навигации из Guidance ===
TiggoBridgeSender: ✓ Данные отправлены в TiggoBridgeService
BridgeService: Получены данные навигации от Yandex Maps
```

## Следующие шаги

1. ✅ Создать TiggoBridgeSender
2. ⏳ Найти способ получить Context в классе k
3. ⏳ Декомпилировать APK Yandex Maps
4. ⏳ Найти Smali файл класса k
5. ⏳ Добавить TiggoBridgeSender в APK
6. ⏳ Модифицировать класс k.smali
7. ⏳ Ре-скомпилировать и подписать APK
8. ⏳ Протестировать на виртуальной машине

