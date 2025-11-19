# Проблема с путем NotificationListenerService

## Обнаруженная проблема

При включении NotificationListenerService через ADB использовался неправильный путь к классу.

### Неправильный путь:
```
com.desaysv.tiggo.bridge/com.desaysv.tiggo.bridge.notification.NavigationNotificationListener
```

### Правильный путь (как в манифесте):
```
com.desaysv.tiggo.bridge/.notification.NavigationNotificationListener
```

## Причина

В `AndroidManifest.xml` сервис зарегистрирован с коротким путем:
```xml
<service
    android:name=".notification.NavigationNotificationListener"
    ...
/>
```

Система Android разрешает этот путь в полный при регистрации, но при включении через `settings put secure enabled_notification_listeners` нужно использовать тот же формат, что и в манифесте.

## Решение

Использовать короткий путь при включении через ADB:
```bash
adb shell settings put secure enabled_notification_listeners com.desaysv.tiggo.bridge/.notification.NavigationNotificationListener
```

## Проверка

После включения с правильным путем:
1. Перезапустить приложение
2. Проверить логи на создание `NavigationNotificationListener`
3. Должно появиться: `NavigationNotificationListener создан`

## Статус

✅ Исправлено - используется правильный путь `.notification.NavigationNotificationListener`

