# Полное решение для доступа к QNX - G6SH/T18FL3

**Дата:** 2025-11-27
**Цель:** Создать полное решение для доступа к QNX системе

---

## 🔍 ВСЕ ИЗВЕСТНЫЕ МЕТОДЫ ДОСТУПА К QNX

### 1. USB Serial/UART (QNX Console)
- **Порт:** `/dev/ttyUSB0` или `/dev/tty.usbserial-*` на Mac
- **Скорость:** Обычно 115200 baud
- **Статус:** ⚠️ Порт не отвечает, требует активации

### 2. Network (TCP/IP)
- **IP QNX:** `192.168.2.1`
- **Порты:**
  - `10005` - QNX сервис (LISTEN)
  - `31030, 31040, 31050` - QNX соединения (ESTABLISHED)
- **Статус:** ✅ Соединения установлены, но нет интерактивного доступа

### 3. Shared Memory (qnx,guest_shm)
- **Путь:** `/sys/devices/platform/vdevs/1c050000.qnx,guest_shm`
- **Драйвер:** `qnx-virtio-du`
- **Статус:** ✅ Обнаружен, но формат данных неизвестен

### 4. Virtio устройства
- **UART:** `1c090000.uart` - QNX Console через virtio
- **Block:** `1c0d0000.virtio_blk` - Диски
- **Статус:** ✅ Обнаружены, но доступ ограничен

### 5. Android TTY устройства
- **ttyAMA0:** PL011 UART (QNX Console) - Permission denied
- **ttySC1:** HSCIF (GPS)
- **ttySC6:** HSCIF (Bluetooth)
- **Статус:** ⚠️ Требуется root доступ

---

## 🎯 ПОЛНОЕ РЕШЕНИЕ

### Компонент 1: QNX Network Access

**Использовать существующие TCP соединения:**
```bash
# Порт 10005 слушает на QNX
# Можно попробовать подключиться через port forwarding
adb forward tcp:10005 tcp:10005
nc localhost 10005
```

### Компонент 2: QNX Shared Memory Reader

**Читать данные из shared memory:**
```bash
# Проверить доступные файлы
adb shell "ls -la /sys/devices/platform/vdevs/1c050000.qnx,guest_shm/"
adb shell "cat /sys/devices/platform/vdevs/1c050000.qnx,guest_shm/uevent"
```

### Компонент 3: QNX через Android приложения

**Использовать Android приложения как посредник:**
- `com.desaysv.vehicle.*` - работают с QNX
- `vehicle.shmemslaver` - читает shared memory
- `vehicle.linkdevicemanager` - управляет связью

### Компонент 4: QNX Screen Capture

**Методы получения экрана приборной панели:**
1. Через shared memory (если там есть данные экрана)
2. Через Android приложения (если они получают данные от QNX)
3. Через QNX команды (если есть доступ)

---

## 🛠️ РЕАЛИЗАЦИЯ

### Шаг 1: QNX Network Shell

```python
# qnx_network_shell.py
import socket
import subprocess

def connect_qnx():
    # Port forwarding
    subprocess.run(["adb", "forward", "tcp:10005", "tcp:10005"])

    # Подключение
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("localhost", 10005))

    # Отправка команд
    sock.send(b"help\n")
    response = sock.recv(4096)
    print(response.decode())
```

### Шаг 2: QNX Shared Memory Reader

```python
# qnx_shared_memory_reader.py
import subprocess

def read_qnx_shared_memory():
    # Читаем uevent
    result = subprocess.run(
        ["adb", "shell", "cat", "/sys/devices/platform/vdevs/1c050000.qnx,guest_shm/uevent"],
        capture_output=True,
        text=True
    )
    print(result.stdout)

    # Пытаемся найти другие файлы
    result = subprocess.run(
        ["adb", "shell", "find", "/sys/devices/platform/vdevs/1c050000.qnx,guest_shm/", "-type", "f"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
```

### Шаг 3: QNX через Android приложения

```python
# qnx_via_android.py
import subprocess

def get_qnx_data_via_android():
    # Используем vehicle.shmemslaver
    result = subprocess.run(
        ["adb", "shell", "/system/bin/vehicle.shmemslaver", "--help"],
        capture_output=True,
        text=True
    )
    print(result.stdout)

    # Используем dumpsys для получения данных
    result = subprocess.run(
        ["adb", "shell", "dumpsys", "activity", "services", "com.desaysv.vehicle.*"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
```

---

## 📋 ПЛАН ДЕЙСТВИЙ

1. ⏳ Протестировать все методы доступа
2. ⏳ Найти рабочий метод
3. ⏳ Создать универсальный клиент
4. ⏳ Интегрировать в reverse tunnel
5. ⏳ Добавить screen capture для QNX

---

**Статус:** Собираем все методы в единое решение

