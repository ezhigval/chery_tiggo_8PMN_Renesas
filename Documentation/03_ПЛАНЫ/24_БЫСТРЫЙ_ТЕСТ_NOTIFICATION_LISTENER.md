# Быстрый тест NotificationListenerService

## Шаг 1: Сборка

Если сборка через Gradle не работает, используйте Android Studio:
1. Откройте проект в Android Studio
2. Build → Make Project (Cmd+B / Ctrl+B)
3. Run → Run 'app' (или Shift+F10)

## Шаг 2: Установка

```bash
# Найти APK
find development/projects/TiggoBridgeService/app/build/outputs/apk/debug -name "*.apk"

# Установить
adb install -r development/projects/TiggoBridgeService/app/build/outputs/apk/debug/app-debug.apk
```

## Шаг 3: Включение NotificationListenerService

### Автоматическое включение (для автомобильного ГУ)

Приложение **автоматически пытается включить** NotificationListenerService при запуске!

**Как работает:**
1. При запуске `BridgeService` проверяет статус NotificationListenerService
2. Если не включен - пытается включить программно через `Settings.Secure`
3. Если не получается - показывает ADB команду в логах

**Проверка статуса:**
```bash
adb logcat | grep -E "(NotificationListenerHelper|NotificationListenerService)"
```

**Если автоматическое включение не работает:**

#### Вариант 1: Через ADB (для тестирования)
```bash
adb shell settings put secure enabled_notification_listeners com.desaysv.tiggo.bridge/.notification.NavigationNotificationListener
```

#### Вариант 2: Ручное включение (если есть стандартные настройки)
1. Откройте **Настройки** Android
2. Перейдите в **Специальные возможности** (Accessibility)
3. Найдите **Услуги** (Services) или **Уведомления** → **Доступ к уведомлениям**
4. Найдите **Tiggo Bridge** или **Navigation Notification Listener**
5. **Включите** переключатель
6. Подтвердите разрешение

## Шаг 4: Проверка через ADB

```bash
# Проверить, включен ли сервис
adb shell dumpsys notification_listener | grep -i "tiggo\|navigation"

# Проверить логи
adb logcat -c  # Очистить логи
adb logcat | grep -E "(NavNotificationListener|NotificationParser|BridgeService)"
```

## Шаг 5: Тестирование

1. **Запустите Yandex Navigator** на эмуляторе
2. **Постройте маршрут** и **начните навигацию**
3. **Проверьте логи:**
   ```bash
   adb logcat | grep -E "(NavNotificationListener|NotificationParser)"
   ```

Должны появиться сообщения:
- `=== Получено уведомление от Yandex Navigator ===`
- `Данные уведомления: title=..., text=...`
- `✓ Данные навигации извлечены`
- `✓ Данные отправлены в BridgeService`

## Шаг 6: Проверка в приложении

1. Откройте **Tiggo Bridge**
2. Перейдите на вкладку **Статус**
3. Должна быть **зеленая лампочка** "Навигация активна"
4. Перейдите на вкладку **Логи**
5. Должны быть сообщения о получении данных

## Устранение проблем

### NotificationListenerService не включается

```bash
# Проверить, установлен ли сервис
adb shell dumpsys package com.desaysv.tiggo.bridge | grep -A 10 "NotificationListenerService"

# Попробовать включить программно (требует root или специальных разрешений)
adb shell settings put secure enabled_notification_listeners com.desaysv.tiggo.bridge/.notification.NavigationNotificationListener
```

### Данные не приходят

1. Убедитесь, что навигация **активна** (построен маршрут)
2. Проверьте, что Yandex Navigator **показывает уведомления**
3. Проверьте логи парсера:
   ```bash
   adb logcat | grep NotificationParser
   ```

### Ошибки парсинга

Если парсер не может извлечь данные, проверьте формат уведомлений:
```bash
# Посмотреть все уведомления от Yandex Navigator
adb shell dumpsys notification | grep -A 20 "ru.yandex.yandexnavi"
```

## Ожидаемый результат

При активной навигации в логах должно быть:
```
NavNotificationListener: === Получено уведомление от Yandex Navigator ===
NavNotificationListener: Данные уведомления:
NavNotificationListener:   title: Поверните направо через 200 м
NavNotificationListener:   text: Осталось 5.2 км, 12 мин
NotificationParser: Парсинг: title='Поверните направо через 200 м', text='Осталось 5.2 км, 12 мин'
NotificationParser: Расстояние до маневра: 200м
NotificationParser: Оставшееся расстояние: 5200м
NotificationParser: Оставшееся время: 720сек
NavNotificationListener: ✓ Данные навигации извлечены:
NavNotificationListener:   TURN_TYPE: 1
NavNotificationListener:   TURN_DIST: 200м
NavNotificationListener:   REMAINING_DIST: 5200м
NavNotificationListener:   REMAINING_TIME: 720сек
NavNotificationListener: ✓ Данные отправлены в BridgeService
BridgeService: Получены данные навигации от NotificationListener
BridgeService: ✓ Данные от NotificationListener отправлены в QNX: TURN=1, DIST=200м
```

