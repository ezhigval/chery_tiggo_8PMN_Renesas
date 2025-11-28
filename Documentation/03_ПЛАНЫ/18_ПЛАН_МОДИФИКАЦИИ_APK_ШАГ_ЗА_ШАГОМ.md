# План модификации APK Yandex Navigator - Шаг за шагом

## Подготовка

### 1. Установка инструментов

**apktool:**
```bash
# macOS
brew install apktool

# Или скачать с https://ibotpeaches.github.io/Apktool/
```

**apksigner** (входит в Android SDK):
```bash
# Путь: $ANDROID_HOME/build-tools/<version>/apksigner
# Или установить через Android Studio
```

**jadx** (опционально, для чтения кода):
```bash
# Скачать с https://github.com/skylot/jadx/releases
```

### 2. Создание keystore для подписи

```bash
keytool -genkey -v -keystore tiggo_navigator.keystore -alias tiggo \
    -keyalg RSA -keysize 2048 -validity 10000
```

### 3. Получение APK

**Вариант A: С устройства**
```bash
adb pull $(adb shell pm path ru.yandex.yandexnavi | cut -d: -f2) yandexnavi.apk
```

**Вариант B: Скачать с APKMirror или другого источника**

## Процесс модификации

### Шаг 1: Декомпиляция APK

```bash
apktool d yandexnavi.apk -o yandexnavi_source
```

**Результат:**
- `yandexnavi_source/smali/` - декомпилированный код
- `yandexnavi_source/res/` - ресурсы
- `yandexnavi_source/AndroidManifest.xml` - манифест

### Шаг 2: Изучение структуры

**Найти класс k.java:**
```bash
find yandexnavi_source/smali -path "*auto_navigation/navikit/k.smali"
```

**Или через jadx (для чтения):**
```bash
jadx -d yandexnavi_java yandexnavi.apk
# Затем найти: ru/yandex/yandexmaps/integrations/auto_navigation/navikit/k.java
```

### Шаг 3: Добавление TiggoBridgeSender

**Вариант A: Через Java (проще)**

1. Скопировать `TiggoBridgeSender.java` в проект
2. Скомпилировать в class файл
3. Конвертировать в dex
4. Конвертировать dex в smali

**Вариант B: Написать напрямую в Smali (сложнее)**

Использовать готовый шаблон Smali кода.

### Шаг 4: Интеграция с классом k

**Найти конструктор класса k:**
```smali
.method public <init>(...)
```

**Добавить инициализацию TiggoBridgeSender:**
```smali
# После получения NotificationDataManager
# (строка ~44 в Java коде)

# Инициализация TiggoBridgeSender
invoke-static {p0}, Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;->init(Landroid/content/Context;)V

# Подключение к NotificationDataManager
# (после строки где получается notificationDataManager)
invoke-static {}, Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;->getInstance()Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;
move-result-object vX
invoke-virtual {vX, vY}, Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;->attachToNotificationDataManager(Lcom/yandex/navikit/guidance/NotificationDataManager;)V
```

### Шаг 5: Ре-компиляция APK

```bash
cd yandexnavi_source
apktool b . -o yandexnavi_modified.apk
```

**Если ошибки:**
- Проверить синтаксис Smali
- Убедиться, что все классы на месте
- Проверить AndroidManifest.xml

### Шаг 6: Подпись APK

```bash
apksigner sign --ks tiggo_navigator.keystore --ks-key-alias tiggo yandexnavi_modified.apk
```

**Проверка подписи:**
```bash
apksigner verify yandexnavi_modified.apk
```

### Шаг 7: Установка

```bash
# Удалить оригинальный (если нужно)
adb uninstall ru.yandex.yandexnavi

# Установить модифицированный
adb install yandexnavi_modified.apk
```

## Детальная инструкция по интеграции

### Найти точку внедрения в классе k

**В Java коде (через jadx):**
```java
public k(..., Guidance guidance, ...) {
    // ...
    NotificationDataManager notificationDataManager = guidance.notificationDataManager();
    this.f180940a = notificationDataManager;
    // <-- ЗДЕСЬ добавить инициализацию TiggoBridgeSender
}
```

**В Smali коде:**
```smali
.method public <init>(...)V
    # ... существующий код ...
    
    # Получение NotificationDataManager (примерно строка 44)
    invoke-interface {vX}, Lcom/yandex/navikit/guidance/Guidance;->notificationDataManager()Lcom/yandex/navikit/guidance/NotificationDataManager;
    move-result-object vY
    
    # Сохранение в поле (существующий код)
    iput-object vY, p0, Lru/yandex/yandexmaps/integrations/auto_navigation/navikit/k;->f180940a:Lcom/yandex/navikit/guidance/NotificationDataManager;
    
    # <-- ДОБАВИТЬ ЗДЕСЬ:
    # Инициализация TiggoBridgeSender (если еще не инициализирован)
    invoke-static {p1}, Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;->init(Landroid/content/Context;)V
    
    # Подключение к NotificationDataManager
    invoke-static {}, Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;->getInstance()Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;
    move-result-object vZ
    invoke-virtual {vZ, vY}, Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;->attachToNotificationDataManager(Lcom/yandex/navikit/guidance/NotificationDataManager;)V
    
    # ... остальной код ...
.end method
```

## Проверка работы

### 1. Запустить навигатор
```bash
adb shell am start -n ru.yandex.yandexnavi/.MainActivity
```

### 2. Построить маршрут и начать навигацию

### 3. Проверить логи
```bash
adb logcat | grep -E "(TiggoBridgeSender|BridgeService|NAVIGATION_DATA)"
```

**Ожидаемые логи:**
```
TiggoBridgeSender: TiggoBridgeSender инициализирован
TiggoBridgeSender: Подключен к NotificationDataManager
TiggoBridgeSender: Данные отправлены в TiggoBridgeService: ...
BridgeService: Получены данные навигации от Yandex Navigator
BridgeService: Данные отправлены в QNX: TURN=..., DIST=...м
```

### 4. Проверить, что данные приходят в QNX

## Отладка

### Проблема: APK не компилируется

**Решение:**
- Проверить синтаксис Smali
- Убедиться, что все зависимости на месте
- Проверить AndroidManifest.xml

### Проблема: APK не устанавливается

**Решение:**
- Проверить подпись: `apksigner verify yandexnavi_modified.apk`
- Убедиться, что оригинальный навигатор удален
- Проверить версию Android

### Проблема: Приложение не запускается

**Решение:**
- Проверить логи: `adb logcat | grep -i error`
- Убедиться, что все классы на месте
- Проверить, что инициализация выполнена

### Проблема: Данные не отправляются

**Решение:**
- Проверить, что TiggoBridgeSender инициализирован
- Проверить, что NotificationDataManager получен
- Проверить, что listener зарегистрирован
- Проверить логи TiggoBridgeSender

## Автоматизация

Использовать готовый скрипт:
```bash
./development/scripts/modify_navigator.sh yandexnavi.apk
```

Скрипт выполнит:
1. Декомпиляцию
2. Копирование файлов
3. Подготовку к ручной модификации

## Важные замечания

1. **Резервная копия:** Всегда сохраняйте оригинальный APK
2. **Версии:** Модификации нужно делать для каждой версии навигатора
3. **Обновления:** Отключите автоматические обновления в Play Store
4. **Тестирование:** Тщательно тестируйте после каждой модификации

## Следующие шаги

1. ✅ Подготовить инструменты
2. ⏳ Получить APK Yandex Navigator
3. ⏳ Декомпилировать APK
4. ⏳ Найти класс k и точку внедрения
5. ⏳ Добавить TiggoBridgeSender
6. ⏳ Интегрировать с NotificationDataManager
7. ⏳ Ре-скомпилировать и протестировать

