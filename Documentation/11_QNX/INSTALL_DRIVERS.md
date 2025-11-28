# Установка драйверов USB-to-Serial для macOS

Для подключения к QNX через USB Serial/UART порт необходимо установить соответствующие драйверы.

## Определение типа чипа

1. Подключите устройство к Mac
2. Проверьте системную информацию:
   ```bash
   system_profiler SPUSBDataType | grep -A 10 -i "serial\|uart"
   ```
3. Или проверьте через ioreg:
   ```bash
   ioreg -p IOUSB -l -w 0 | grep -i "serial\|uart" -A 5
   ```

## Драйверы по типам чипов

### CP2102 (Silicon Labs)

1. Скачайте драйверы с официального сайта:
   https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers

2. Установите пакет `.pkg`

3. Перезагрузите Mac

4. После перезагрузки подключите устройство и проверьте порт:
   ```bash
   ls -la /dev/tty.* | grep -i usb
   ```

### PL2303 (Prolific)

1. Скачайте драйверы:
   https://www.prolific.com.tw/US/ShowProduct.aspx?p_id=225&pcid=41

2. Установите драйверы

3. Перезагрузите Mac

4. Проверьте порт:
   ```bash
   ls -la /dev/tty.* | grep -i usb
   ```

### FT232 (FTDI)

1. Скачайте драйверы VCP:
   https://www.ftdichip.com/Drivers/VCP.htm

2. Установите драйверы

3. Перезагрузите Mac

4. Проверьте порт:
   ```bash
   ls -la /dev/tty.* | grep -i usb
   ```

## Проверка установки

После установки драйверов и перезагрузки:

1. Подключите устройство
2. Проверьте наличие порта:
   ```bash
   ls -la /dev/tty.* /dev/cu.* | grep -i usb
   ```
3. Попробуйте подключиться:
   ```bash
   ./connect_qnx.sh
   ```

## Устранение проблем

### Порт не появляется

1. Проверьте, что устройство подключено:
   ```bash
   system_profiler SPUSBDataType
   ```

2. Убедитесь, что драйверы установлены:
   ```bash
   kextstat | grep -i "usbserial\|ftdi\|prolific\|silabs"
   ```

3. Попробуйте переподключить устройство

4. Проверьте настройки безопасности macOS (Системные настройки → Безопасность)

### Ошибки доступа к порту

Если получаете ошибку "Permission denied":

```bash
sudo chmod 666 /dev/tty.usbserial-XXXX
```

Или добавьте пользователя в группу `dialout` (если существует):
```bash
sudo dseditgroup -o edit -a $(whoami) -t user dialout
```

### Порт определяется, но нет связи

1. Проверьте скорость передачи (baud rate) - обычно 115200 для QNX
2. Убедитесь, что кабель поддерживает передачу данных (не только зарядку)
3. Проверьте настройки порта в терминальной программе

## Альтернативные инструменты

Если стандартные драйверы не работают, можно попробовать:

- **Serial** (GUI приложение для macOS): https://www.decisivetactics.com/products/serial/
- **CoolTerm** (бесплатное): http://freeware.the-meiers.org/




