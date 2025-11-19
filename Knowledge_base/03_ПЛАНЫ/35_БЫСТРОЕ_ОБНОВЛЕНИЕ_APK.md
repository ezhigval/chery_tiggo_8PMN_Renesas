# Быстрое обновление APK с новым TiggoBridgeSender

## Автоматический способ

### Использование скрипта:

```bash
cd development/apk_modification
./update_tiggo_bridge_sender.sh
```

Скрипт автоматически:
1. ✅ Компилирует TiggoBridgeSender.java в .class
2. ✅ Конвертирует .class в .dex
3. ✅ Конвертирует .dex в smali
4. ✅ Обновляет пакет (ru.yandex.yandexmaps.bridge)
5. ✅ Копирует в декомпилированный APK
6. ✅ Проверяет интеграцию

### После выполнения скрипта:

```bash
# 1. Скомпилировать APK
cd yandexmaps_decompiled
apktool b . -o ../yandexmaps_modified_v7.apk

# 2. Подписать
cd ..
apksigner sign --ks tiggo_maps.keystore \
    --ks-key-alias tiggo \
    yandexmaps_modified_v7.apk

# 3. Установить
adb uninstall ru.yandex.yandexmaps
adb install yandexmaps_modified_v7.apk
```

## Ручной способ

Если скрипт не работает, можно сделать вручную:

### 1. Компиляция Java → .class

```bash
cd development/projects/TiggoBridgeService

# Найти android.jar
ANDROID_JAR=$(find $ANDROID_HOME/platforms -name "android.jar" | head -1)

# Компилировать
javac -d /tmp/tiggo_classes \
    -cp "$ANDROID_JAR" \
    -sourcepath app/src/main/java \
    app/src/main/java/com/desaysv/tiggo/bridge/navigation/TiggoBridgeSender.java
```

### 2. Конвертация .class → .dex

```bash
# Используя d8 (рекомендуется)
d8 /tmp/tiggo_classes/com/desaysv/tiggo/bridge/navigation/TiggoBridgeSender.class \
    --output /tmp

# Или используя dx
dx --dex --output=/tmp/tiggo_bridge.dex /tmp/tiggo_classes
```

### 3. Конвертация .dex → smali

```bash
baksmali d /tmp/classes.dex -o /tmp/tiggo_smali
```

### 4. Обновление пакета

```bash
# Заменить пакет в smali файле
sed -i '' 's/Lcom\/desaysv\/tiggo\/bridge\/navigation\/TiggoBridgeSender;/Lru\/yandex\/yandexmaps\/bridge\/TiggoBridgeSender;/g' \
    /tmp/tiggo_smali/com/desaysv/tiggo/bridge/navigation/TiggoBridgeSender.smali

# Переместить в правильную директорию
mkdir -p development/apk_modification/yandexmaps_decompiled/smali_classes9/ru/yandex/yandexmaps/bridge
cp /tmp/tiggo_smali/com/desaysv/tiggo/bridge/navigation/TiggoBridgeSender.smali \
    development/apk_modification/yandexmaps_decompiled/smali_classes9/ru/yandex/yandexmaps/bridge/
```

### 5. Обновление класса в smali

В файле `TiggoBridgeSender.smali` нужно заменить:
- `.class public Lcom/desaysv/tiggo/bridge/navigation/TiggoBridgeSender;` 
  → `.class public Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;`

- Все ссылки на `Lcom/desaysv/tiggo/bridge/utils/Logger;` 
  → `Lru/yandex/yandexmaps/bridge/Logger;` (или удалить, если Logger не используется)

## Проверка интеграции

Проверьте, что в `k.smali` есть вызовы:

```smali
# После строки с iput-object для NotificationDataManager
invoke-static {}, Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;->init()V

invoke-static {}, Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;->getInstance()Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;
move-result-object v0
invoke-virtual {v0, p4, p1}, Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;->attachToGuidanceAndNotificationDataManager(Lcom/yandex/navikit/guidance/Guidance;Lcom/yandex/navikit/guidance/NotificationDataManager;)V
```

## Что изменилось в новом TiggoBridgeSender

### Новые возможности:
1. ✅ Постоянная отправка местоположения (каждые 0.5 сек)
2. ✅ Постоянная отправка навигации (каждую секунду)
3. ✅ Постоянная отправка карты (каждую секунду)
4. ✅ API-подход: разные Actions для разных типов данных

### Новые методы:
- `startContinuousDataSending()` - запуск постоянной отправки
- `startMapSending()` - отправка карты
- `startLocationSending()` - отправка местоположения
- `startNavigationSending()` - отправка навигации
- `attachToMapView(Object)` - подключение к MapView

### Новые Actions:
- `com.desaysv.tiggo.bridge.MAP_DATA`
- `com.desaysv.tiggo.bridge.LOCATION_DATA`
- `com.desaysv.tiggo.bridge.ROUTE_DATA`
- `com.desaysv.tiggo.bridge.NAVIGATION_DATA` (улучшено)

## Проверка после установки

```bash
# Проверка логов
adb logcat | grep -E "(TiggoBridgeSender|Отправка.*запущена)"

# Ожидаемые логи:
# TiggoBridgeSender: Отправка местоположения запущена (каждые 0.5 сек)
# TiggoBridgeSender: Отправка навигации запущена (каждую секунду)
# TiggoBridgeSender: Местоположение отправлено: ...
# TiggoBridgeSender: ✓ Навигационные данные отправлены
```

## Устранение проблем

### Проблема: "cannot find symbol: Logger"
**Решение:** Удалите использование Logger или создайте простую версию Logger в пакете `ru.yandex.yandexmaps.bridge`

### Проблема: "VerifyError"
**Решение:** Убедитесь, что все методы правильно объявлены и используются правильные типы регистров

### Проблема: "ClassNotFoundException"
**Решение:** Проверьте, что пакет правильно обновлен в smali файле

