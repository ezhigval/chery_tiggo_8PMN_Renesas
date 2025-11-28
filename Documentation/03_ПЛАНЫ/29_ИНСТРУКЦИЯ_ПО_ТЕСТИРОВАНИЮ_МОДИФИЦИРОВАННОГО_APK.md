# Инструкция по тестированию модифицированного APK Yandex Maps

## Расположение файлов

**Модифицированный APK:**
`development/apk_modification/yandexmaps_modified.apk`

**Keystore для подписи:**
`development/apk_modification/tiggo_maps.keystore`
- Пароль: `tiggo123`
- Alias: `tiggo`

## Что было сделано

1. ✅ Декомпилирован APK Yandex Maps
2. ✅ Создан класс `TiggoBridgeSender` в пакете `ru.yandex.yandexmaps.bridge`
3. ✅ Модифицирован класс `k.smali` - добавлены вызовы:
   - `TiggoBridgeSender.init()` - инициализация
   - `TiggoBridgeSender.getInstance().attachToGuidance(guidance)` - подключение к Guidance
4. ✅ APK пересобран и подписан

## Точка инъекции

**Файл:** `smali_classes9/ru/yandex/yandexmaps/integrations/auto_navigation/navikit/k.smali`

**Место:** После сохранения `NotificationDataManager` в поле `a` (строка 60)

**Добавленный код:**
```smali
# === TiggoBridgeSender: Инициализация и подключение к Guidance ===
invoke-static {}, Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;->init()V
invoke-static {}, Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;->getInstance()Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;
move-result-object v0
invoke-virtual {v0, p4}, Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;->attachToGuidance(Lcom/yandex/navikit/guidance/Guidance;)V
# === Конец TiggoBridgeSender ===
```

## Установка на виртуальную машину

```bash
# 1. Удалить оригинальный Yandex Maps (если установлен)
adb uninstall ru.yandex.yandexmaps

# 2. Установить модифицированный APK
adb install development/apk_modification/yandexmaps_modified.apk

# 3. Запустить Yandex Maps
adb shell am start -n ru.yandex.yandexmaps/.app.MapActivity
```

## Проверка работы

### 1. Проверить логи инициализации
```bash
adb logcat | grep -E "(TiggoBridgeSender|k\.smali)"
```

**Ожидаемые логи:**
```
TiggoBridgeSender: TiggoBridgeSender создан
TiggoBridgeSender: TiggoBridgeSender инициализирован (Context получен автоматически)
TiggoBridgeSender: attachToGuidance вызван (упрощенная версия)
```

### 2. Запустить навигацию
1. Открыть Yandex Maps
2. Построить маршрут
3. Начать навигацию

### 3. Проверить отправку данных
```bash
adb logcat | grep -E "(TiggoBridgeSender|NAVIGATION_DATA|BridgeService)"
```

**Ожидаемые логи:**
```
TiggoBridgeSender: === Извлечение данных навигации из Guidance ===
TiggoBridgeSender: ✓ Данные отправлены в TiggoBridgeService
BridgeService: Получены данные навигации от Yandex Maps
```

## Текущая реализация

**Упрощенная версия:**
- `attachToGuidance()` пока только сохраняет объект Guidance
- Полная реализация (создание Proxy listener, регистрация, извлечение данных) будет добавлена после проверки базовой функциональности

## Следующие шаги

1. ⏳ Протестировать базовую функциональность (инициализация, вызов attachToGuidance)
2. ⏳ Добавить полную реализацию `attachToGuidance()` в smali
3. ⏳ Протестировать извлечение и отправку данных
4. ⏳ Оптимизировать и доработать

## Отладка

### Проблема: APK не устанавливается
```bash
# Проверить подпись
apksigner verify yandexmaps_modified.apk

# Удалить оригинальный APK
adb uninstall ru.yandex.yandexmaps

# Установить с перезаписью
adb install -r yandexmaps_modified.apk
```

### Проблема: Приложение не запускается
```bash
# Проверить логи ошибок
adb logcat | grep -i "error\|exception\|crash"

# Проверить, что TiggoBridgeSender инициализирован
adb logcat | grep "TiggoBridgeSender"
```

### Проблема: Данные не отправляются
```bash
# Проверить, что Guidance получен
adb logcat | grep "attachToGuidance"

# Проверить, что BridgeService запущен
adb shell dumpsys activity services | grep BridgeService
```


