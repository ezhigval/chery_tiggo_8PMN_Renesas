# Полная резервная копия системы Android

**Дата создания:** $(date)
**Устройство:** См. system_info/product_model.txt
**Android версия:** См. system_info/android_version.txt

## Структура backup

### system_info/
Информация о системе: свойства, версии, модель устройства, CPU, память, диск

### apps/
- **apks/** - APK файлы пользовательских приложений
- **data/** - Данные приложений (требует root)
- **details/** - Детальная информация о каждом приложении
- **all_packages.txt** - Все установленные пакеты

### qnx/
- **logs/** - Логи QNX системы (qnx_logs.txt, navigation_logs.txt, mapservice_logs.txt)
- **traffic/** - Broadcast трафик QNX (исторический и в реальном времени)
- **config/** - Конфигурация QNX (mapservice, turbodog, receivers, filters, сервисы, процессы)

### technical/
Полные технические данные: dumpsys всех сервисов, информация о железе, процессы, сервисы

### network/
Сетевая информация: конфигурация интерфейсов, маршруты

### logs/
Системные логи: logcat (полный, system, radio, events, crash)

## QNX данные

Все данные связанные с QNX системой находятся в папке `qnx/`:

- **qnx/logs/** - Логи навигации, mapservice, turbodog
- **qnx/traffic/** - Broadcast трафик (входящий/исходящий)
- **qnx/config/** - Конфигурация и дампы сервисов

## Восстановление

### Быстрое восстановление (APK)
```bash
for apk in apps/apks/*.apk; do
    adb install "$apk"
done
```

### ADB restore
```bash
adb restore backup.ab
```

## Примечания

- Некоторые данные требуют root доступа
- ADB backup может не включать все данные (ограничения Android)
- QNX трафик захватывается в реальном времени при выполнении скрипта
