# AutoRemoteTunnelService - Полностью автоматизированное решение

## Описание

Полностью автоматизированный Android сервис для удаленного доступа к ГУ:
- ✅ Автозапуск при загрузке
- ✅ Автоматическое отключение firewall через root
- ✅ Подключение к серверу через интернет
- ✅ Работа в фоне без подключения к ПК
- ✅ Устойчивость к перезапускам

## Компоненты

1. **AutoRemoteTunnelService.java** - основной сервис
   - Автоматическое отключение firewall
   - Подключение к серверу
   - Обработка команд от сервера
   - Screen capture и touch input

2. **AutoBootReceiver.java** - автозапуск
   - Запуск сервиса при BOOT_COMPLETED
   - Запуск при обновлении пакета

3. **AndroidManifest.xml** - конфигурация
   - Разрешения (INTERNET, RECEIVE_BOOT_COMPLETED)
   - Регистрация сервиса и receiver
   - persistent="true" для надежности

## Функции

### Автоматическое отключение firewall

При каждом запуске сервис:
1. Устанавливает persist свойства
2. Останавливает процессы firewall
3. Очищает правила iptables
4. Разрешает порт 22222

### Подключение к серверу

- Автоматическое подключение при старте
- Автоматическое переподключение при разрыве
- Keep-alive каждые 30 секунд
- Обработка изменения сети

### Команды от сервера

- `DISABLE_FIREWALL` - отключить firewall
- `ENABLE_FIREWALL` - включить firewall
- `START_SCREEN_CAPTURE` - начать захват экрана
- `STOP_SCREEN_CAPTURE` - остановить захват экрана
- `TOUCH:x,y` - имитация touch события
- `SET_SERVER:host:port` - изменить адрес сервера

## Установка

### Требования

- Root доступ на ГУ
- ADB подключение
- Собранный APK

### Быстрая установка

```bash
# 1. Собрать APK (если еще не собрано)
cd RemoteTunnel
./gradlew assembleDebug

# 2. Автоматическая установка с root
cd ..
./Knowledge_base/11_QNX/auto_install_root.sh
```

### Ручная установка

```bash
# 1. Получить root
adb root
adb remount

# 2. Установить APK
adb install RemoteTunnel/app/build/outputs/apk/debug/app-debug.apk

# 3. Скопировать в /system/app/ (опционально)
adb push RemoteTunnel/app/build/outputs/apk/debug/app-debug.apk /system/app/RemoteTunnel/
adb shell chmod 644 /system/app/RemoteTunnel/app-debug.apk

# 4. Запустить сервис
adb shell "am startservice -n com.desaysv.remotetunnel/.AutoRemoteTunnelService"

# 5. Перезагрузить для проверки автозапуска
adb reboot
```

## Настройка IP сервера

### Вариант 1: Изменить в коде

В `AutoRemoteTunnelService.java`:
```java
private static final String DEFAULT_SERVER_HOST = "your-mac-ip-or-domain.com";
```

### Вариант 2: Через команду сервера

После подключения отправить:
```
SET_SERVER:192.168.0.117:22222
```

### Вариант 3: Через SharedPreferences

```bash
adb shell "run-as com.desaysv.remotetunnel sh -c 'echo \"server_host=192.168.0.117\" > /data/data/com.desaysv.remotetunnel/shared_prefs/RemoteTunnelPrefs.xml'"
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

## Логи

```bash
# Все логи сервиса
adb logcat | grep AutoRemoteTunnel

# Только ошибки
adb logcat | grep -E "AutoRemoteTunnel.*ERROR"

# Firewall операции
adb logcat | grep -E "AutoRemoteTunnel.*firewall"
```

## Удаление

```bash
# Остановить сервис
adb shell "am stopservice com.desaysv.remotetunnel/.AutoRemoteTunnelService"

# Удалить приложение
adb uninstall com.desaysv.remotetunnel

# Удалить из /system/app/ (если установлено)
adb root
adb remount
adb shell "rm -rf /system/app/RemoteTunnel"
```

## Особенности

1. **Root доступ**: Требуется для отключения firewall
2. **Persistent**: Приложение помечено как persistent для надежности
3. **START_STICKY**: Сервис перезапускается при падении
4. **Автопереподключение**: При разрыве соединения автоматически переподключается

## Troubleshooting

### Сервис не запускается

1. Проверить root доступ: `adb shell "id"`
2. Проверить логи: `adb logcat | grep AutoRemoteTunnel`
3. Проверить разрешения в AndroidManifest.xml

### Firewall не отключается

1. Проверить root доступ
2. Проверить логи firewall операций
3. Попробовать вручную: `adb shell "su -c 'iptables -F'"`

### Не подключается к серверу

1. Проверить IP сервера в коде или SharedPreferences
2. Проверить что сервер запущен на Mac
3. Проверить firewall на Mac
4. Проверить сеть: `adb shell "ping -c 2 <server_ip>"`

