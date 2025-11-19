# Команды ADB для работы с приложением

## Сброс авторизованных подключений ADB

### Полный сброс (Windows)
```powershell
adb kill-server
Remove-Item $env:USERPROFILE\.android\adbkey -Force
Remove-Item $env:USERPROFILE\.android\adbkey.pub -Force
adb start-server
```

### Полный сброс (Mac/Linux)
```bash
adb kill-server
rm ~/.android/adbkey
rm ~/.android/adbkey.pub
adb start-server
```

### Быстрый способ (только перезапуск сервера)
```bash
adb kill-server
adb start-server
```

**Используйте скрипт:** `.\development\scripts\reset_adb_auth.ps1`

## Базовые команды

### Проверка подключенных устройств
```bash
adb devices
```

### Установка APK
```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```
Флаг `-r` означает переустановку (reinstall), если приложение уже установлено.

### Запуск приложения
```bash
adb shell am start -n com.desaysv.tiggo.bridge/com.desaysv.tiggo.bridge.ui.MainActivity
```

### Остановка приложения
```bash
adb shell am force-stop com.desaysv.tiggo.bridge
```

### Перезапуск приложения
```bash
adb shell am force-stop com.desaysv.tiggo.bridge
adb shell am start -n com.desaysv.tiggo.bridge/com.desaysv.tiggo.bridge.ui.MainActivity
```

## Просмотр логов

### Все логи приложения
```bash
adb logcat | grep "com.desaysv.tiggo.bridge"
```

### Логи с фильтрацией по тегам
```bash
adb logcat -s TiggoBridge:* NavigationMonitor:* NavDataInterceptor:* BridgeService:*
```

### Логи в реальном времени (только наши теги)
```bash
adb logcat -s TiggoBridge:* NavigationMonitor:* NavDataInterceptor:* BridgeService:* ReflectionHelper:*
```

### Очистка логов
```bash
adb logcat -c
```

### Сохранение логов в файл
```bash
adb logcat > logs.txt
```

## Отладка

### Получение информации о приложении
```bash
adb shell dumpsys package com.desaysv.tiggo.bridge
```

### Проверка запущенных процессов
```bash
adb shell ps | grep tiggo
```

### Проверка разрешений
```bash
adb shell dumpsys package com.desaysv.tiggo.bridge | grep permission
```

### Установка разрешений вручную
```bash
adb shell pm grant com.desaysv.tiggo.bridge android.permission.ACCESS_FINE_LOCATION
adb shell pm grant com.desaysv.tiggo.bridge android.permission.ACCESS_COARSE_LOCATION
adb shell pm grant com.desaysv.tiggo.bridge android.permission.QUERY_ALL_PACKAGES
```

## Работа с файлами

### Копирование файла с устройства
```bash
adb pull /sdcard/file.txt ./
```

### Копирование файла на устройство
```bash
adb push file.txt /sdcard/
```

### Просмотр файлов приложения
```bash
adb shell run-as com.desaysv.tiggo.bridge ls -la
```

## Перезапуск ADB

### Перезапуск ADB сервера
```bash
adb kill-server
adb start-server
```

### Перезапуск ADB в режиме TCP/IP
```bash
adb tcpip 5555
```

## Полезные команды для отладки навигации

### Проверка запущен ли навигатор
```bash
adb shell ps | grep yandexnavi
```

### Запуск Яндекс Навигатора
```bash
adb shell am start -n ru.yandex.yandexnavi/.ui.MainActivity
```

### Проверка разрешений навигатора
```bash
adb shell dumpsys package ru.yandex.yandexnavi | grep permission
```

### Просмотр всех broadcast'ов
```bash
adb shell dumpsys activity broadcasts | grep yandex
```

## Создание скриншотов

### Скриншот и сохранение на ПК (Windows)
```powershell
adb exec-out screencap -p > screenshot.png
```

### Скриншот и сохранение на ПК (Mac/Linux)
```bash
adb exec-out screencap -p > screenshot.png
```

### Альтернативный метод (через временный файл)
```bash
adb shell screencap -p /sdcard/screenshot.png
adb pull /sdcard/screenshot.png ./
adb shell rm /sdcard/screenshot.png
```

**Используйте скрипт:** 
- Windows: `.\development\scripts\screenshot_device.ps1`
- Mac/Linux: `./development/scripts/screenshot_device.sh`

Скриншоты сохраняются в папку `development/screenshots/`

## Автоматизация

Используйте скрипт `development/scripts/run_app_on_device.ps1` для автоматического запуска приложения.
