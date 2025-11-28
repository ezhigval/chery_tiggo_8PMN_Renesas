# Отчёт по обратной разработке G6SH/T18FL3

**Дата анализа:** 2025-11-21  
**Модель:** G6SH-r8a7795 (DesaySV G6SH H3N)  
**Android версия:** 9 (API level 28)  
**Kernel:** Linux 4.14.133+  
**Процессор:** Renesas R-Car H3 (ARM Cortex-A53/A57)

---

## 1. ИНФОРМАЦИЯ О СИСТЕМЕ

### CPU Info

- **Архитектура:** ARMv8 (AArch64)
- **Процессоры:** 5 ядер (4x Cortex-A53 + 1x Cortex-A57)
- **BogoMIPS:** 16.66
- **Features:** fp, asimd, evtstrm, aes, pmull, sha1, sha2, crc32, cpuid

### System Properties (ключевые)

```
ro.build.version.sdk: 28 (Android 9)
ro.build.fingerprint: [требуется уточнение]
ro.boot.slot_suffix_qnx: _b
persist.qnx.serial.enable: 1 ✅
sys.qnx.uart.enable: 1 ✅
persist.sys.eng: 1 ✅
persist.sys.qnx: 1 ✅
sys.usb.config: mtp,adb,serial ✅
```

### Kernel Messages (ключевые находки)

```
console=ttyAMA0 - консольный UART
qnx-virtio-du - QNX virtio display driver найден
1c050000.qnx,guest_shm - QNX shared memory устройство
ttyAMA0, ttySC1, ttySC6 - UART порты обнаружены
```

### Device Nodes

**Найденные TTY устройства:**

- `/dev/ttyAMA0` - PL011 UART (console, root only)
- `/dev/ttySC1` - HSCIF UART (GPS, gps:system)
- `/dev/ttySC6` - HSCIF UART (Bluetooth, bluetooth:bluetooth)

**QNX разделы:**

- `/dev/block/by-name/qnx_boot_a`
- `/dev/block/by-name/qnx_boot_b`
- `/dev/block/by-name/qnx_system_a`
- `/dev/block/by-name/qnx_system_b`
- `/dev/block/by-name/qnx_appdata`
- `/dev/block/by-name/qnx_userdata`
- `/dev/block/by-name/qnx_appcfg`
- `/dev/block/by-name/qnx_firmware`

---

## 2. ПРОВЕРКА ПРИВИЛЕГИЙ

### Current User

```
uid=2000(shell) gid=2000(shell)
groups=2000(shell),1004(input),1007(log),1011(adb),1015(sdcard_rw),1028(sdcard_r),3001(net_bt_admin),3002(net_bt),3003(inet),3006(net_bw_stats),3009(readproc),3011(uhid)
context=u:r:shell:s0
```

### Root Access

- ❌ **SU недоступен** - `su` binary не найден
- ⚠️ **SELinux:** permissive режим (androidboot.selinux=permissive)

### Installed Packages (Desay/QNX)

```
com.desaysv.carlan
com.desaysv.bluetooth.phone
com.desaysv.logmanager
com.desaysv.vehicle.carplayapp
com.desaysv.service.link
com.desaysv.mediaservice
com.desaysv.assistant
com.desaysv.launcher
com.desaysv.setting
```

### System Services

- `car_service` - Android Car Service
- `dsv_car_power` - Desay Car Power Manager
- `SvAdapterAccess` - Desay Adapter Service
- `linkdevicemanager` - Link Device Manager
- `shmemservice` - Shared Memory Service
- `vehiclelan_service` - Vehicle LAN Service

---

## 3. СЕТЕВЫЕ ПОРТЫ

### Открытые порты

```
TCP LISTEN:
- 127.0.0.1:53 (DNS)
- 192.168.33.10:53 (DNS)
- 0.0.0.0:10005 (неизвестный сервис)
- :::2121 (FTP?)
- :::8020 (неизвестный сервис)

TCP ESTABLISHED:
- Множество соединений к 192.168.2.1 (возможно, QNX/MCU)
- Соединения к внешним серверам (124.243.226.*)

UDP:
- 0.0.0.0:5353 (mDNS)
- 0.0.0.0:30490, 48090
- 0.0.0.0:67 (DHCP server)
```

---

## 4. UART/QNX ИНТЕРФЕЙСЫ

### TTY Devices

| Устройство     | Тип        | Назначение | Права доступа                    |
| -------------- | ---------- | ---------- | -------------------------------- |
| `/dev/ttyAMA0` | PL011 UART | Console    | root:root (crw-------)           |
| `/dev/ttySC1`  | HSCIF      | GPS        | gps:system (crw-rw----)          |
| `/dev/ttySC6`  | HSCIF      | Bluetooth  | bluetooth:bluetooth (crw-rw----) |

### Kernel UART Messages

```
[    2.937501] 1c090000.uart: ttyAMA0 at MMIO 0x1c090000 (irq = 12)
[    3.167259] e6540000.serial: ttySC6 at MMIO 0xe6540000 (irq = 20)
[    3.167719] e6550000.serial: ttySC1 at MMIO 0xe6550000 (irq = 21)
```

### QNX/Diag Devices

**QNX блоки:**

- `/dev/block/by-name/qnx_*` - все QNX разделы найдены

**QNX системные пути:**

- `/sys/devices/platform/vdevs/1c050000.qnx,guest_shm` - QNX virtio устройство
- `/sys/bus/platform/drivers/qnx-virtio-du` - QNX display driver
- `/proc/irq/11/qnx-virtio-du-irq` - QNX interrupt

**Serial устройства:**

- `/sys/devices/platform/soc/e6540000.serial` - ttySC6
- `/sys/devices/platform/soc/e6550000.serial` - ttySC1
- `/sys/bus/virtio/drivers/virtio_rproc_serial` - virtio serial driver

---

## 5. СЕРВИСНЫЕ БИНАРНИКИ

### System Binaries

- ✅ `/system/bin/dexdiag` - диагностический инструмент найден

### Vendor Binaries

- Не найдено специфичных QNX/MCU бинарников в `/vendor/bin`

### OEM Directory

- Пуст или недоступен

### Persist Directory

- Требуется дальнейшая проверка

---

## 6. СЕРВИСНЫЕ РЕЖИМЫ DESAY

### Engineering Broadcast

```bash
adb shell am broadcast -a com.desaysv.engineering.START
```

✅ **Результат:** Broadcast completed (result=0)

### Engineering Activity

```bash
adb shell am start -n com.desaysv.engineering/.MainActivity
```

❌ **Результат:** Activity не найдена

### Engineering Properties

```bash
adb shell setprop persist.sys.eng 1
adb shell setprop persist.sys.qnx 1
```

✅ **Результат:** Свойства установлены успешно

**Дополнительные свойства:**

- `persist.sv.debug.adb_enable: 1`
- `persist.sv.debug_logcat: 1`
- `persist.sv.debug_service: 1`
- `ro.sys.eng.encrypt.enabled: 1`
- `ro.sys.eng.slaver.enabled: 1`

---

## 7. ПОИСК QNX БИНАРНИКОВ

### QNX Files

**Найдены QNX разделы:**

- `/dev/block/by-name/qnx_boot_a/b`
- `/dev/block/by-name/qnx_system_a/b`
- `/dev/block/by-name/qnx_appdata`
- `/dev/block/by-name/qnx_userdata`
- `/dev/block/by-name/qnx_appcfg`
- `/dev/block/by-name/qnx_firmware`

**QNX системные пути:**

- `/sys/devices/platform/vdevs/1c050000.qnx,guest_shm`
- `/sys/bus/platform/drivers/qnx-virtio-du`
- `/sys/module/qnx_virtio_du`
- `/proc/irq/11/qnx-virtio-du-irq`

### MCU Files

- Не найдено явных MCU бинарников в файловой системе Android

### Serial Files

- `/sys/bus/virtio/drivers/virtio_rproc_serial` - virtio serial driver
- `/sys/devices/platform/soc/*.serial` - hardware serial устройства

---

## 8. USB GADGET РЕЖИМЫ

### Android USB State

```
/sys/class/android_usb/android0/state: CONFIGURED
```

### USB Gadget Config

```
/config/usb_gadget/g1 - найден USB gadget конфигуратор
```

### USB Functions

После выполнения команд:

```
sys.usb.config: mtp,adb,serial ✅
```

**Результат:** USB режим изменён на `mtp,adb,serial` - добавлен serial интерфейс!

---

## 9. ADB TCP РЕЖИМ

### Enable TCP ADB

```bash
adb shell setprop service.adb.tcp.port 5555
adb tcpip 5555
```

✅ **Результат:** `restarting in TCP mode port: 5555`

**Примечание:** После переключения в TCP режим устройство временно отключилось от USB ADB.

---

## 10. РЕЗУЛЬТАТЫ АНАЛИЗА

### ✅ Обнаруженные порты

**На устройстве (Android):**

- `ttyAMA0` - консольный UART (root only)
- `ttySC1` - GPS UART (gps:system)
- `ttySC6` - Bluetooth UART (bluetooth:bluetooth)

**Сетевые порты:**

- TCP: 53, 10005, 2121, 8020
- UDP: 53, 5353, 30490, 48090, 67

**ADB TCP:**

- Порт 5555 активирован

### ✅ Потенциальные QNX endpoints

1. **QNX Virtio интерфейс:**

   - `/sys/devices/platform/vdevs/1c050000.qnx,guest_shm`
   - Interrupt vector: 11
   - Shared memory индекс: 2

2. **QNX UART (через virtio):**

   - `/sys/bus/virtio/drivers/virtio_rproc_serial`
   - Возможно доступен через `/dev/tty*` после активации

3. **QNX через USB Serial:**

   - USB config изменён на `mtp,adb,serial`
   - Требуется проверка на Mac после переподключения

4. **QNX через сеть:**
   - Соединения к 192.168.2.1 (возможно, QNX/MCU)
   - Порт 10005 может быть QNX сервисом

### ✅ Пути к бинарникам

**Диагностика:**

- `/system/bin/dexdiag` - найден

**QNX разделы:**

- Все QNX разделы доступны через `/dev/block/by-name/qnx_*`

**Сервисы Desay:**

- Множество пакетов `com.desaysv.*` установлены
- Сервисы доступны через `service list`

### ✅ Сервисные интерфейсы

**Desay сервисы:**

- `dsv_car_power` - Car Power Manager
- `SvAdapterAccess` - Adapter Service
- `linkdevicemanager` - Link Device Manager
- `shmemservice` - Shared Memory Service
- `vehiclelan_service` - Vehicle LAN Service

**Engineering режим:**

- `persist.sys.eng: 1` ✅
- `persist.sys.qnx: 1` ✅
- `persist.sv.debug.*: 1` ✅

### ⚠️ Точки повышения привилегий

1. **SELinux permissive:**

   - `androidboot.selinux=permissive` - позволяет больше действий
   - Но `su` binary отсутствует

2. **Engineering режим активирован:**

   - `persist.sys.eng: 1` - может открыть дополнительные возможности

3. **Debug свойства:**

   - `persist.sv.debug.*: 1` - debug режимы включены

4. **USB Serial добавлен:**

   - `sys.usb.config: mtp,adb,serial` - serial интерфейс активирован

5. **QNX свойства:**
   - `persist.qnx.serial.enable: 1`
   - `sys.qnx.uart.enable: 1`

### 🔍 Рекомендуемые следующие шаги

#### Немедленные действия:

1. **Переподключить устройство:**

   ```bash
   # Переподключить USB кабель
   adb kill-server && adb start-server
   adb devices
   ```

2. **Проверить USB Serial порт на Mac:**

   ```bash
   ls -la /dev/tty.* /dev/cu.* | grep -v "Bluetooth" | grep -v "debug"
   # Если появился новый порт - попробовать подключиться:
   screen /dev/tty.XXX 115200
   minicom -D /dev/tty.XXX -b 115200
   ```

3. **Попробовать TCP ADB:**

   ```bash
   # Узнать IP устройства
   adb shell ip addr show
   # Подключиться по TCP
   adb connect <IP>:5555
   ```

4. **Проверить QNX через сеть:**
   ```bash
   # Попробовать подключиться к порту 10005
   telnet <device_ip> 10005
   nc <device_ip> 10005
   ```

#### Дальнейший анализ:

5. **Исследовать QNX разделы:**

   ```bash
   adb shell ls -la /dev/block/by-name/qnx*
   adb shell mount | grep qnx
   # Попробовать смонтировать QNX разделы
   ```

6. **Проверить доступ к ttyAMA0:**

   ```bash
   # Попробовать получить доступ к консольному UART
   adb shell cat /dev/ttyAMA0
   # Или через stty/screen на устройстве
   ```

7. **Исследовать virtio serial:**

   ```bash
   adb shell ls -la /sys/bus/virtio/drivers/virtio_rproc_serial/
   adb shell cat /sys/bus/virtio/drivers/virtio_rproc_serial/*/uevent
   ```

8. **Проверить QNX shared memory:**

   ```bash
   adb shell cat /sys/devices/platform/vdevs/1c050000.qnx,guest_shm/uevent
   adb shell ls -la /sys/devices/platform/vdevs/1c050000.qnx,guest_shm/
   ```

9. **Исследовать dexdiag:**

   ```bash
   adb shell /system/bin/dexdiag --help
   adb shell strings /system/bin/dexdiag | grep -i "qnx\|mcu\|uart"
   ```

10. **Проверить сервисы Desay:**
    ```bash
    adb shell dumpsys | grep -A 10 "dsv_car_power\|SvAdapterAccess"
    adb shell service call dsv_car_power
    ```

#### Для доступа к QNX:

11. **Физический QNX порт:**

    - Убедиться, что кабель подключён к порту "QNX" (не "ADB")
    - Установить драйверы USB-to-Serial (FTDI/CP2102/PL2303)
    - Проверить порты на Mac после переподключения

12. **Через virtio:**

    - Исследовать `/sys/bus/virtio/drivers/virtio_rproc_serial/`
    - Попробовать создать симлинк или активировать устройство

13. **Через сеть:**
    - Проверить порт 10005 на устройстве
    - Исследовать соединения к 192.168.2.1

---

## КРИТИЧЕСКИЕ НАХОДКИ

1. ✅ **USB Serial активирован:** `sys.usb.config: mtp,adb,serial`
2. ✅ **QNX разделы найдены:** все QNX блоки доступны
3. ✅ **QNX virtio driver активен:** `qnx-virtio-du` работает
4. ✅ **Engineering режим включён:** `persist.sys.eng: 1`
5. ✅ **QNX serial enable:** `persist.qnx.serial.enable: 1`
6. ⚠️ **SU недоступен:** требуется альтернативный путь к root
7. ✅ **SELinux permissive:** больше возможностей для действий

---

## СЛЕДУЮЩИЕ ШАГИ (приоритет)

1. **Переподключить устройство и проверить USB Serial порт на Mac**
2. **Попробовать подключиться к TCP ADB (порт 5555)**
3. **Исследовать порт 10005 (возможно, QNX сервис)**
4. **Проверить доступ к ttyAMA0 (консольный UART)**
5. **Исследовать virtio_rproc_serial для QNX доступа**

---

**Отчёт сформирован:** 2025-11-21  
**Статус:** Анализ выполнен, требуется переподключение устройства для проверки USB Serial порта
