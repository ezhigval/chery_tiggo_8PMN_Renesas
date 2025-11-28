# План сбора данных для полной копии головного устройства G6SH/T18FL3

**Цель:** дать **пошаговый чеклист** по сбору всей информации и образов, необходимых для создания полной копии головы в эмуляторе.
Теоретическая модель описана в `FULL_SYSTEM_REPLICATION_MODEL.md` — здесь только **практика и команды**.

⚠️ **Важное ограничение на этом этапе:**
Мы работаем **только в режиме чтения** (никаких записей в разделы, `dd` — только `if=... of=/sdcard/...`).
Все потенциально опасные шаги (fastboot, recovery, запись в разделы) — в отдельные планы установки.

---

## 0. Подготовка окружения

- **Требования на Mac:**
  - Установлен `adb`.
  - Есть каталог проекта `Tiggo` (уже есть).
  - Создать каталог для дампов:
    ```bash
    mkdir -p ~/Projects/Tiggo/Development/emulator/dumps/{logs,props,partitions,configs,protocols}
    ```
- **Требования на устройстве:**
  - ADB включен.
  - Engineering mode включён (см. `ENGINEERING_MODES_ANALYSIS.md`).
  - Соединение по USB стабильно.

---

## 1. Базовая системная информация (CPU, память, свойства)

**Цель:** зафиксировать «паспорт» устройства, чтобы эмулятор знал, какую платформу изображать.

```bash
cd ~/Projects/Tiggo/Development/emulator/dumps

# CPU, память, файлы конфигурации
adb shell "cat /proc/cpuinfo" > logs/proc_cpuinfo.txt
adb shell "cat /proc/meminfo" > logs/proc_meminfo.txt

# Общие системные свойства
adb shell "getprop" > props/getprop_all.txt

# Ключевые свойства для QNX/слотов/bootloader (дубль, чтобы было отдельно)
adb shell "getprop | grep -iE 'qnx|slot_suffix|bootloader|verity|oem_unlock|eng|ro.build|hardware'" > props/getprop_qnx_boot.txt

# Kernel cmdline (для воспроизведения параметров при запуске в QEMU)
adb shell "cat /proc/cmdline" > logs/proc_cmdline.txt

# Конфигурация ядра (если доступен /proc/config.gz)
adb shell "ls -la /proc/config.gz" > logs/proc_config_ls.txt
adb shell "cat /proc/config.gz 2>/dev/null" | gunzip > logs/kernel_config.txt 2>/dev/null || echo "no /proc/config.gz" >> logs/kernel_config.txt
```

**Куда сохраняем вывод:** `dumps/logs/*`, `dumps/props/*`.
**Ссылка на модель:** раздел 2.1 и 2.4 в `FULL_SYSTEM_REPLICATION_MODEL.md`.

---

## 2. Карта памяти, устройств и device tree

**Цель:** получить полную картину того, что видит ядро: адреса, IRQ, DT.

```bash
cd ~/Projects/Tiggo/Development/emulator/dumps

# Карта физической памяти и устройств
adb shell "cat /proc/iomem" > logs/proc_iomem.txt
adb shell "cat /proc/interrupts" > logs/proc_interrupts.txt

# Обзор /sys устройства
adb shell "ls -R /sys/devices/platform 2>/dev/null" > logs/sys_devices_platform_tree.txt
adb shell "ls -R /sys/bus 2>/dev/null" > logs/sys_bus_tree.txt

# Device tree (если доступен dtb/dts)
adb shell "ls -R /proc/device-tree /sys/firmware/devicetree/base 2>/dev/null" > logs/devicetree_tree.txt

# Ключевые ноды DT по UART, virtio, qnx
adb shell "find /sys/firmware/devicetree/base -maxdepth 6 -type d \\( -name '*serial*' -o -name '*virtio*' -o -name '*qnx*' \\) 2>/dev/null" > logs/devicetree_uart_virtio_paths.txt
```

**Куда сохраняем:** `dumps/logs/devicetree_*.txt`.
**Ссылка на модель:** раздел 2.1 и 2.2 в `FULL_SYSTEM_REPLICATION_MODEL.md`.

---

## 3. Разделы eMMC и QNX (карта + размеры)

**Цель:** получить **логику разметки** и подготовиться к съёму образов.

```bash
cd ~/Projects/Tiggo/Development/emulator/dumps/partitions

# Список всех именованных разделов
adb shell "ls -la /dev/block/by-name" > partitions_by_name.txt

# Информация о разделах (blkid)
adb shell "blkid" > partitions_blkid.txt 2>/dev/null || echo "blkid not available" > partitions_blkid.txt

# Размеры разделов (только чтение)
adb shell "
  for p in /dev/block/by-name/*; do
    name=\$(basename \$p);
    size=\$(blockdev --getsize64 \$p 2>/dev/null);
    echo \"\$name \$p \$size\";
  done
" > partitions_sizes.txt

# Если доступен базовый блочный девайс (mmcblk0, mmcblk1 и т.п.)
adb shell "ls -la /dev/block | grep -i 'mmcblk'" > base_block_devices.txt
```

После этого вручную в Knowledge Base составляем **таблицу**: имя раздела → путь → размер → назначение.
**Ссылка на модель:** раздел 2.3 в `FULL_SYSTEM_REPLICATION_MODEL.md`.

---

## 4. Базовые образы разделов (безопасный read-only dd)

⚠️ **Только чтение, без записи на сами разделы.**
Образы сохраняем сначала на `/sdcard`, потом тянем на Mac.

Пример для нескольких ключевых разделов:

```bash
cd ~/Projects/Tiggo/Development/emulator/dumps/partitions

# Функция-образец: dd + pull для одного раздела
PARTS="boot_a boot_b system_a system_b vendor product \
qnx_boot_a qnx_boot_b qnx_system_a qnx_system_b qnx_appcfg qnx_appdata qnx_userdata qnx_firmware"

for name in $PARTS; do
  echo "Dumping $name..."
  adb shell "dd if=/dev/block/by-name/$name of=/sdcard/${name}.img bs=4M" \
    && adb pull "/sdcard/${name}.img" "./${name}.img" \
    && adb shell "rm /sdcard/${name}.img";
done
```

Если **какой-то** из разделов недоступен (permission denied) — фиксируем это в отдельном лог-файле и **не пытаемся обойти силой** на этом этапе.
**Ссылка на модель:** раздел 2.3 и 2.5 в `FULL_SYSTEM_REPLICATION_MODEL.md`.

---

## 5. Android ядро, init и system/vendor/product

**Цель:** понять, как поднимаются сервисы, какие бинарники и библиотеки участвуют в automotive/QNX/vehicle.

```bash
cd ~/Projects/Tiggo/Development/emulator/dumps/configs

# Init-скрипты (часть уже есть в extracted_files/init_scripts, но делаем общий дамп)
adb shell "ls -la /init*.rc /system/etc/init /vendor/etc/init 2>/dev/null" > init_scripts_list.txt
adb shell "cat /init*.rc 2>/dev/null" > init_root_rc_all.txt
adb shell "find /system/etc/init /vendor/etc/init -maxdepth 1 -name '*.rc' -print0 2>/dev/null | xargs -0 -I {} sh -c 'echo ===== {}; cat {}; echo'" > init_all_rc.txt

# Список бинарников, относящихся к vehicle/QNX
adb shell "find /system/bin /vendor/bin /system/xbin -maxdepth 1 -type f \\( -iname '*vehicle*' -o -iname '*qnx*' -o -iname '*mcu*' -o -iname '*cluster*' -o -iname '*link*' \\) 2>/dev/null" > binaries_vehicle_qnx_list.txt

# Информация по нескольким ключевым бинарникам (file + strings)
adb shell "for f in \$(cat /tmp/binaries_vehicle_qnx_list 2>/dev/null || echo); do echo ===== \$f; file \$f; strings \$f | head -50; echo; done" 2>/dev/null > binaries_vehicle_qnx_info.txt || echo "manual step: copy list locally and iterate"
```

**APK/servicies:** уже частично разобраны в `EXTRACTION_SUMMARY.md` и `QNX_DATA_EXTRACTION_PLAN.md`, но этот шаг даёт системный контекст.
**Ссылка на модель:** раздел 2.4 в `FULL_SYSTEM_REPLICATION_MODEL.md`.

---

## 6. QNX интеграция: virtio, shared memory, serial, сеть

**Цель:** сформировать полную картину каналов Android ↔ QNX/MCU.

### 6.1. Shared memory и virtio

```bash
cd ~/Projects/Tiggo/Development/emulator/dumps/protocols

# QNX shared memory uevent + структура
adb shell "ls -la /sys/devices/platform/vdevs/1c050000.qnx,guest_shm" > qnx_guest_shm_ls.txt
adb shell "cat /sys/devices/platform/vdevs/1c050000.qnx,guest_shm/uevent" > qnx_guest_shm_uevent.txt

# Попытка чтения (если доступно без root)
adb shell "dd if=/dev/qnx_guest_shm of=/sdcard/qnx_guest_shm.bin bs=4k count=256 2>/dev/null" \
  && adb pull /sdcard/qnx_guest_shm.bin ./qnx_guest_shm_head.bin \
  && adb shell "rm /sdcard/qnx_guest_shm.bin" || echo "no access to /dev/qnx_guest_shm" > qnx_guest_shm_access.txt

# Virtio serial driver
adb shell "ls -la /sys/bus/virtio/drivers/virtio_rproc_serial" > virtio_rproc_serial_ls.txt
adb shell "find /dev -maxdepth 2 -type c \\( -name '*virtio*' -o -name '*vport*' -o -name '*hvc*' \\) 2>/dev/null" > virtio_serial_devices.txt
```

### 6.2. Сетевая интеграция (192.168.2.x)

```bash
cd ~/Projects/Tiggo/Development/emulator/dumps/protocols

# IP-конфигурация
adb shell "ip addr show" > ip_addr_show.txt
adb shell "ip route show" > ip_route_show.txt

# Текущие соединения к 192.168.2.1
adb shell "netstat -an | grep 192.168.2.1" > netstat_qnx_mcu_connections.txt

# Открытые порты (дубль, но фиксируем)
adb shell "netstat -an" > netstat_all.txt
```

**Ссылка на модель:** раздел 2.5 и 2.6 в `FULL_SYSTEM_REPLICATION_MODEL.md`, дополняет `QNX_CONNECTION_ANALYSIS.md` и `QNX_DATA_EXTRACTION_PLAN.md`.

---

## 7. Протоколы Android ↔ QNX/MCU (логирование при действиях)

**Цель:** привязать реальные действия пользователя/авто к сетевым/virtio/serial-сообщениям.

### 7.1. Общий подход

1. Включаем продвинутый лог на Android:
   ```bash
   adb logcat -c
   adb logcat > ~/Projects/Tiggo/Development/emulator/dumps/protocols/logcat_full_session.txt
   ```
2. Делаем `adb tcpdump` (если доступен) или `tcpdump` на самом устройстве (если он установлен).
3. Прогоняем **набор сценариев**:
   - Включение зажигания / головы.
   - Старт/стоп двигателя.
   - Переход в R (задний ход, парктроник/камера).
   - Начало движения (скорость > 0), ускорение/торможение.
   - Открытие/закрытие дверей.
   - Изменение громкости/медиа/климата.

### 7.2. Пример команд

```bash
cd ~/Projects/Tiggo/Development/emulator/dumps/protocols

# Port forwarding для ключевых портов
adb forward tcp:10004 tcp:10004
adb forward tcp:10005 tcp:10005
adb forward tcp:31030 tcp:31030
adb forward tcp:31040 tcp:31040
adb forward tcp:31050 tcp:31050

# tcpdump, если есть (можно заранее положить бинарник)
adb shell "tcpdump -i any host 192.168.2.1 -w /sdcard/qnx_mcu_traffic.pcap" &

# После выполнения сценариев:
adb pull /sdcard/qnx_mcu_traffic.pcap ./qnx_mcu_traffic.pcap
adb shell "rm /sdcard/qnx_mcu_traffic.pcap"
```

Дальше анализ через Wireshark + сопоставление с логами Android (`logcat_full_session.txt`).
**Ссылка на модель:** раздел 2.6, 2.7, 2.8 в `FULL_SYSTEM_REPLICATION_MODEL.md`.

---

## 8. Дисплей, разрешение, input-устройства

**Цель:** точно воспроизвести экран и ввод в эмуляторе.

```bash
cd ~/Projects/Tiggo/Development/emulator/dumps/configs

# Экран
adb shell "wm size" > display_wm_size.txt
adb shell "wm density" > display_wm_density.txt
adb shell "dumpsys display" > display_dumpsys.txt

# Input-устройства
adb shell "getevent -pl" > input_getevent_pl.txt

# Маппинг кнопок руля/панели
adb shell "getevent" > input_getevent_raw_session.txt
```

В момент записи `getevent` выполняем:

- Нажатия на кнопки руля.
- Магнитолу/энкодеры.
- Touch-скрины, если нужно.

**Ссылка на модель:** раздел 2.1, 2.7 в `FULL_SYSTEM_REPLICATION_MODEL.md`.

---

## 9. Системные сервисы, состояния и «правила»

**Цель:** зафиксировать, кто за что отвечает и как система принимает решения.

```bash
cd ~/Projects/Tiggo/Development/emulator/dumps/logs

# Общий список процессов
adb shell "ps -A" > ps_all.txt

# Сервисы, связанные с vehicle/QNX/etc.
adb shell "service list" > service_list_all.txt
adb shell "service list | grep -iE 'vehicle|qnx|cluster|mcu|car|dsv'" > service_list_vehicle_qnx.txt

# dumpsys по ключевым сервисам (выбирать по факту из service_list_vehicle_qnx.txt)
for svc in car_service vehicle_service vehiclelan_service dsv_car_power; do
  adb shell "dumpsys $svc 2>/dev/null" > "dumpsys_${svc}.txt" || true
done

# Логи с фильтром по qnx/mcu/cluster
adb shell "logcat -d | grep -iE 'qnx|mcu|cluster|vehicle|dsv' " > logcat_vehicle_qnx_filtered.txt
```

Эти данные используются при восстановлении **логики и правил**: кто меняет проперти, кто отвечает за переключение режимов, кто реагирует на MCU/CAN и т.п.
**Ссылка на модель:** раздел 2.4 и 2.8 в `FULL_SYSTEM_REPLICATION_MODEL.md`.

---

## 10. Организация в Knowledge Base

После выполнения шагов выше:

- Раскладываем файлы по структуре, например:
  - `Knowledge_base/16_СИСТЕМНАЯ_ИНФОРМАЦИЯ/XX_...` — сырые дампы (`proc_*`, `getprop`, `netstat`, `dumpsys`, и т.д.).
  - `Knowledge_base/11_QNX/` — сводки и анализ:
    - `FULL_SYSTEM_REPLICATION_MODEL.md` — модель.
    - `FULL_SYSTEM_DATA_COLLECTION_PLAN.md` — этот файл (чеклист).
    - `QNX_DATA_EXTRACTION_RESULTS.md`, `QNX_EXTRACTION_SUMMARY.md` — результаты по QNX.
    - Новые сводные файлы по разделам, протоколам, дисплеям.
- В отчётах **делаем ссылки** на сырые файлы из `16_СИСТЕМНАЯ_ИНФОРМАЦИЯ`, чтобы не дублировать большие логи.

---

## 11. Статус и дальнейшие шаги

На текущем этапе:

- Этот план закрывает **сбор информации и подготовку**, без модификации устройства.
- Следующий логичный шаг:
  - На основе собранных дампов составить:
    - Таблицу разделов и их ролей.
    - Таблицу устройств и их маппинга (DT → /dev → сервисы).
    - Первую версию карты протоколов Android ↔ QNX/MCU.

Эти агрегированные таблицы уже можно будет напрямую использовать при настройке QEMU-платы и при разработке MCU/CAN-симулятора поверх эмулятора.


