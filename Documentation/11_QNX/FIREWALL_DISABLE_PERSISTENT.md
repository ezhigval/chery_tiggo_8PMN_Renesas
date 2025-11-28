# Отключение Firewall при перезагрузке ГУ

## Проблема
Firewall (`iptables-firewall`) автоматически запускается при загрузке системы и блокирует сетевые соединения.

## Решение

### 1. Установка persist свойств
Свойства с префиксом `persist.` сохраняются после перезагрузки:

```bash
setprop persist.sys.firewall.disabled 1
setprop persist.sys.firewall.enabled 0
```

### 2. Скрипт отключения при загрузке
Создан скрипт `/data/local/tmp/disable_firewall_on_boot.sh` который:
- Устанавливает persist свойства
- Останавливает процессы firewall
- Очищает правила iptables (если есть root)

### 3. Автозапуск скрипта
Несколько методов для автозапуска:

#### Метод 1: Через init.d (если доступен)
```bash
cp /data/local/tmp/disable_firewall_on_boot.sh /system/etc/init.d/99disable_firewall
chmod 755 /system/etc/init.d/99disable_firewall
```

#### Метод 2: Через Magisk (если установлен)
```bash
cp /data/local/tmp/disable_firewall_on_boot.sh /data/adb/service.d/disable_firewall.sh
chmod 755 /data/adb/service.d/disable_firewall.sh
```

#### Метод 3: Через setprop и boot_completed
Скрипт `/data/local/tmp/boot_receiver.sh` проверяет `sys.boot_completed` и запускает отключение firewall.

### 4. Проверка после перезагрузки
После перезагрузки проверить:
```bash
adb shell "getprop | grep firewall"
adb shell "ps | grep iptables"
adb shell "/data/local/tmp/disable_firewall_on_boot.sh"
```

## Файлы
- `/data/local/tmp/disable_firewall_on_boot.sh` - основной скрипт отключения
- `/data/local/tmp/install_firewall_disable.sh` - установка автозапуска
- `/data/local/tmp/create_boot_script.sh` - создание boot скриптов
- `/data/local/tmp/boot_receiver.sh` - проверка boot_completed

## Важно
- Persist свойства сохраняются в `/data/property/`
- Скрипты в `/data/local/tmp/` сохраняются после перезагрузки
- Для изменения `/system/etc/init.d/` требуется root или remount

