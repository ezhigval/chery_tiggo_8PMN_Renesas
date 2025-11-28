# Сборка и установка AutoRemoteTunnelService

## Требования

1. Android SDK
2. Android Studio или командная строка
3. Root доступ на ГУ
4. ADB подключение

## Шаги сборки

### 1. Создание Android проекта

```bash
# Создать новый Android проект
android create project \
  --target android-29 \
  --name RemoteTunnel \
  --path ./RemoteTunnel \
  --activity MainActivity \
  --package com.desaysv.remotetunnel
```

### 2. Копирование файлов

```bash
# Скопировать Java файлы
cp AutoRemoteTunnelService.java RemoteTunnel/app/src/main/java/com/desaysv/remotetunnel/
cp AutoBootReceiver.java RemoteTunnel/app/src/main/java/com/desaysv/remotetunnel/
cp AndroidManifest.xml RemoteTunnel/app/src/main/
```

### 3. Сборка APK

```bash
cd RemoteTunnel
./gradlew assembleDebug
# APK будет в: app/build/outputs/apk/debug/app-debug.apk
```

## Установка как системное приложение (требует root)

### Вариант 1: Через ADB с root

```bash
# 1. Установить APK
adb install app-debug.apk

# 2. Получить root доступ
adb root
adb remount

# 3. Скопировать в /system/app/
adb push app-debug.apk /system/app/RemoteTunnel/
adb shell chmod 644 /system/app/RemoteTunnel/app-debug.apk

# 4. Перезагрузить
adb reboot
```

### Вариант 2: Через Magisk (если установлен)

```bash
# 1. Установить APK
adb install app-debug.apk

# 2. Скопировать в Magisk модуль
adb shell "mkdir -p /data/adb/modules/remote_tunnel/system/app/RemoteTunnel"
adb push app-debug.apk /data/adb/modules/remote_tunnel/system/app/RemoteTunnel/
adb shell "chmod 644 /data/adb/modules/remote_tunnel/system/app/RemoteTunnel/app-debug.apk"

# 3. Перезагрузить
adb reboot
```

### Вариант 3: Через init.d скрипт

```bash
# Создать скрипт для автозапуска
adb shell "cat > /data/local/tmp/start_remote_tunnel.sh << 'EOF'
#!/system/bin/sh
am startservice -n com.desaysv.remotetunnel/.AutoRemoteTunnelService
EOF"
adb shell "chmod 755 /data/local/tmp/start_remote_tunnel.sh"

# Добавить в автозагрузку
adb shell "cp /data/local/tmp/start_remote_tunnel.sh /system/etc/init.d/99remote_tunnel"
adb shell "chmod 755 /system/etc/init.d/99remote_tunnel"
```

## Настройка IP сервера

### Через SharedPreferences (в коде)

Изменить в `AutoRemoteTunnelService.java`:

```java
private static final String DEFAULT_SERVER_HOST = "your-mac-ip-or-domain.com";
```

### Через команду сервера

После подключения отправить команду:

```
SET_SERVER:192.168.0.117:22222
```

## Проверка работы

```bash
# Проверить что сервис запущен
adb shell "ps | grep AutoRemoteTunnel"

# Проверить логи
adb logcat | grep AutoRemoteTunnel

# Проверить подключение к серверу
# На Mac: tail -f /tmp/remote_desktop_server.log
```

## Автоматическая установка (скрипт)

```bash
#!/bin/bash
# auto_install_remote_tunnel.sh

APK_FILE="app-debug.apk"
PACKAGE_NAME="com.desaysv.remotetunnel"

echo "=== Установка AutoRemoteTunnelService ==="

# 1. Проверка root
adb root
if [ $? -ne 0 ]; then
    echo "❌ Требуется root доступ"
    exit 1
fi

# 2. Установка APK
echo "Установка APK..."
adb install -r "$APK_FILE"

# 3. Копирование в system (опционально)
echo "Копирование в /system/app/..."
adb remount
adb shell "mkdir -p /system/app/RemoteTunnel"
adb push "$APK_FILE" /system/app/RemoteTunnel/
adb shell "chmod 644 /system/app/RemoteTunnel/$APK_FILE"

# 4. Запуск сервиса
echo "Запуск сервиса..."
adb shell "am startservice -n $PACKAGE_NAME/.AutoRemoteTunnelService"

# 5. Проверка
echo "Проверка..."
sleep 3
adb shell "ps | grep AutoRemoteTunnel"

echo "✅ Установка завершена"
echo "После перезагрузки сервис запустится автоматически"
```
