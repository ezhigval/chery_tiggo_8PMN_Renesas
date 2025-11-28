# Статус эмуляции Android + QNX (29.11.2025)

## 1. Цель этого документа

Зафиксировать **фактическое состояние** проекта Chery Emulator на момент 29.11.2025:

- какие изменения внесены в QEMU, Python‑core и web‑UI;
- как сейчас запускаются **две виртуальные машины** (Android HU и QNX VM);
- что уже работает, что нет;
- какие следующие шаги нужны до полноценного «боевого» бута обеих систем.

Документ дополняет:

- `CHERY_Emulator_Design.md` — high‑level дизайн;
- `Documentation/11_QNX/*` — полная модель головы и анализ QNX;
- `Development/Chery_Emulator/qemu_scif_fork/README.md` — детали форка QEMU.

---

## 2. Текущее целевое поведение

Текущая целевая картинка для эмулятора:

- **Android HU** запускается из родного `boot_patched_adb_tcp.img` + `system/vendor/product.img`:
  - QEMU машина **g6sh** (`qemu_g6sh/qemu-system-aarch64`);
  - вывод на VNC `127.0.0.1:5900` → HU‑дисплей в UI;
  - консоль ядра/Android пишется в `logs/qemu_console.log`;
  - ADB проброшен на `127.0.0.1:5557`.

- **QNX VM / кластер** запускается как отдельная виртуалка:
  - QEMU машина **virt** (`qemu_scif_fork/qemu-system-aarch64`);
  - ядром является `hypervisor-ifs-rcar_h3-graphics.bin`, диск — `qnx_system.img`;
  - вывод на VNC `127.0.0.1:5901` → Cluster‑дисплей в UI;
  - консоль QNX должна идти через эмулируемый UART (SCIF0 или virtio‑console) на TCP‑сокет и в `/qnx/console`.

Главное правило по образам: **оригинальные `.img` НЕ модифицируются**, изменяется только эмулятор и обвязка.

---

## 3. Изменения в конфигурации эмулятора

### 3.1. `emulator_config.yaml`

Файл `Development/Chery_Emulator/emulator_config.yaml` приведён к такому состоянию:

- **Android:**
  - `boot_img`: `Development/Chery_Emulator/payload/boot_patched_adb_tcp.img`;
  - `system_img`, `vendor_img`, `product_img` указывают на реальные извлечённые образы.
- **QNX:**
  - `qnx_system_img`: `Development/Chery_Emulator/payload/qnx_system.img`;
  - `enable: false` — QNX‑образы **не монтируются** как диски в Android‑VM, чтобы избежать конфликтов блокировки.
- **QEMU (Android HU):**
  - `binary: Development/Chery_Emulator/qemu_g6sh/qemu-system-aarch64`;
  - `machine: "g6sh"`;
  - `dtb: Development/Chery_Emulator/qemu_g6sh/g6sh-emu.dtb`.
- **Graphics/VNC:**
  - HU: `127.0.0.1:5900`;
  - Cluster/QNX: `127.0.0.1:5901`.

---

## 4. Android HU виртуальная машина

### 4.1. Python‑core: `core/emulator.py`

Основные изменения:

- **Конфиг и валидация**:
  - `EmulatorConfig.load_default()` загружает пути к Android/QNX образам и бинарю QEMU из `emulator_config.yaml`.
  - `_validate_config()` теперь строго требует **все четыре** Android‑образа (boot, system, vendor, product).

- **Команда QEMU для HU** (`EmulatorManager.build_qemu_args()`):

  - QEMU:
    - `qemu_g6sh/qemu-system-aarch64`;
    - `-M g6sh`;
    - `-cpu cortex-a57`;
    - `-smp 4`;
    - `-m 4096`.
  - Консоль ядра:
    - `-serial file:logs/qemu_console.log` — лог ядра/Android.
  - DTB:
    - `-dtb qemu_g6sh/g6sh-emu.dtb`.
  - Ядро:
    - `-kernel boot_patched_adb_tcp.img`.
  - `cmdline` ядра:
    - `console=ttyAMA0,115200 earlycon=pl011,0x1c090000 androidboot.selinux=permissive androidboot.hardware=g6sh root=/dev/vda rootfstype=ext4 rw`.
  - Диски:
    - `system.img`, `vendor.img`, `product.img` как `virtio-blk-pci`.
  - QNX‑образы:
    - опциональные, но сейчас отключены через `qnx.enable: false`.
  - GPU и сеть:
    - `-device virtio-gpu-pci`;
    - `-netdev user,id=net0,hostfwd=tcp::5557-:5555`;
    - `-device virtio-net-pci,netdev=net0`.
  - **VNC для HU**:
    - `-display vnc=127.0.0.1:0` (порт 5900).

- **Запуск/остановка**:
  - `EmulatorManager.start()`:
    - записывает полную команду в `logs/qemu_command.txt`;
    - запускает QEMU, stdout → `logs/qemu_stdout.log`;
    - пробует запустить `adb logcat` → `logs/adb_android.log` (best‑effort).
  - `EmulatorManager.stop()`:
    - корректно завершает QEMU и процесс `adb logcat`.

### 4.2. Фактическое поведение HU

- QEMU успешно поднимается, на HU VNC (`5900`) видно **кольцевую анимацию Android**, что подтверждает:
  - корректность путей к образам;
  - нормальный старт ядра + ramdisk.
- ADB по `127.0.0.1:5557` пока **не коннектится** — Android ещё не дошёл до стадии полноценных сервисов.
- Консольный лог `qemu_console.log` сейчас практически пустой; дальнейшая отладка Android‑бута будет делаться уже после стабилизации QNX.

---

## 5. QNX виртуальная машина

### 5.1. Python‑core: `core/qnx_vm.py`

`QnxVmManager` реализует отдельную VM для QNX:

- **QEMU команда** (`build_qemu_args()`):
  - бинарь: `Development/Chery_Emulator/qemu_scif_fork/qemu-system-aarch64`;
  - `-M virt`;
  - `-cpu cortex-a57`;
  - `-smp 2`;
  - `-m 2048`;
  - `-display vnc=127.0.0.1:1` (порт 5901);
  - `-kernel qemu_g6sh/hypervisor-ifs-rcar_h3-graphics.bin`;
  - `-drive if=none,file=qnx_system.img,format=raw,read-only=on,id=qnxsys`;
  - `-device virtio-blk-pci,drive=qnxsys`.

- **Логи**:
  - команда QEMU записывается в `logs/qnx_qemu_command.txt`;
  - stdout/stderr QEMU → `logs/qnx_qemu_stdout.log`.

- **API** (`core/api.py`):
  - `/qnx/start`, `/qnx/stop`, `/qnx/state` — управление этой VM;
  - `/qnx/console` использует `QnxConsole` (пока больше для будущего virtio/SCIF‑консоли).

### 5.2. Состояние форка QEMU (SCIF / UART / virtio-console)

В `qemu_scif_fork/qemu-src` реализованы:

- **Новый UART‑девайс `renesas-hscif`**:
  - `hw/char/renesas_hscif.c` + `include/hw/char/renesas_hscif.h`;
  - `SysBusDevice` с MMIO‑областью 0x1000;
  - регистры: SMR, BRR, SCR, TDR, SSR, RDR;
  - `CharBackend` + обработчики RX/TX;
  - отладочный лог:
    - `HSCIF[inst_id]: WRITE addr=...`;
    - `HSCIF[inst_id]: READ  addr=...`.
  - свойство `inst-id` для различения адресов.

- **Интеграция в virt‑машину** (`hw/arm/virt.c`):
  - хедер `hw/char/renesas_hscif.h` подключён;
  - в `virt_machine_class_init()`:
    - `machine_class_allow_dynamic_sysbus_dev(mc, TYPE_RENESAS_HSCIF);`
  - функция `virt_create_qnx_scif(VirtMachineState *vms, MemoryRegion *sysmem)`:
    - создаёт **три** HSCIF‑инстанса без chardev с разными базовыми адресами:
      - `0xe6e80000` — SCIF0 (по нашей документации);
      - `0xe6540000` — `serial@e6540000` из DT (HSCIF/SCIF6);
      - `0xe6550000` — `serial@e6550000` из DT (HSCIF/SCIF1);
    - каждому задаётся `inst-id = 0/1/2`;
    - MMIO мапится через `memory_region_add_subregion_overlap`.
  - `virt_create_qnx_scif()` вызывается из `machvirt_init()` сразу после `create_gic()`.

- **Результат на сейчас**:
  - QNX‑VM (hypervisor‑IFS + qnx_system.img) стабильно работает на `-M virt` + нашем форке.
  - В `qnx_qemu_stdout.log` **нет ни одной строки `HSCIF[...]`**, то есть драйвер `devc-serscif scif0` в текущем IFS:
    - либо не запускается;
    - либо использует другой UART (например, через `vdev-virtio-console` или `devc-pty`).

Итого:

- SCIF‑поддержка в форке реализована и протестирована с точки зрения сборки/маппинга, но текущий IFS ею явно **не пользуется** как консолью.
- Дополнительно в команду QNX‑VM добавлен virtio‑console:
  - `-device virtio-serial-pci,id=qnx_virtio_serial0`;
  - `-chardev socket,id=qnx_virtcon,host=localhost,port=1236,server=on,wait=off`;
  - `-device virtconsole,chardev=qnx_virtcon,name=qnx-virtcon0`.
  - В Python‑core добавлен клиент `QnxVirtioConsole` и endpoint `/qnx/virtconsole`, а также источник логов `QNX-VIRTCON` в `/logs/combined`.
- На момент фиксации документа сокет `127.0.0.1:1236` открыт QEMU, но соединения `nc`/`QnxVirtioConsole` получают timeout → требуется дальнейшая отладка virtio‑console (handshake/протокол) и подтверждение, что именно он используется как консоль QNX.

---

## 6. Web‑UI и отображение

### 6.1. HU / Cluster дисплеи

- Web‑страница `web/index.html`:
  - HU display:
    - берёт PNG кадры по `GET /display/hu/frame` → `display_manager.next_hu_frame()` → `hu_vnc_frame()` (VNC 5900);
  - Cluster display:
    - берёт PNG кадры по `GET /display/cluster/frame` → `display_manager.next_cluster_frame()` → `cluster_vnc_frame()` (VNC 5901).

- `core/graphics_vnc.py`:
  - читает VNC‑конфиг из `emulator_config.yaml`;
  - создаёт два `VncClient`:
    - HU: `127.0.0.1:5900`;
    - Cluster: `127.0.0.1:5901`;
  - `get_frame_png()` выдаёт PNG‑кадр или `None` (без ошибок наружу).

- Фактическое поведение:
  - HU: полноэкранное кольцо загрузки Android (размер ~200×200, живой PNG).
  - Cluster: узкая полоска/чёрный фон (PNG ~252×7) — QNX‑кластер пока не отрисовывает полноценный UI.

### 6.2. Логи и состояние

- `GET /logs/combined` агрегирует:
  - `qemu_console.log`, `qemu_stdout.log`, `qemu_serial.log`;
  - `emulator_core.log`, `adb_android.log`;
  - `qnx_qemu_stdout.log`;
  - `QnxConsole.tail()` (пока возвращает пустой список).
- UI табличкой показывает логи с метками `ANDROID`, `QNX`, `EMU` и т.п.
- Блок `Emulator control` в UI отображает:
  - статус эмулятора;
  - PID Android‑QEMU;
  - ignition state (`ENGINE_RUNNING` и т.д.).

---

## 7. Подытог: что уже достигнуто

1. **Две системы реально крутятся параллельно**:
   - Android HU: `qemu_g6sh` + груженый Android boot/system/vendor/product.
   - QNX VM: форк `qemu_scif_fork` + hypervisor‑IFS + `qnx_system.img`.
2. **Графика**:
   - HU‑дисплей показывает реальную анимацию Android через VNC.
   - Cluster‑дисплей подключен к QNX‑VNC и отдаёт кадры (пока пустые/минимальные).
3. **Изоляция образов**:
   - Android и QNX используют свои VM и наборы дисков;
   - QNX‑образы не монтируются в Android‑VM, чтобы не было блокировок.
4. **Форк QEMU**:
   - собран и использует новый девайс `renesas-hscif`;
   - интегрирован в `virt`‑машину;
   - готов к дальнейшему расширению (IRQ, дополнительные UART, virtio‑console).

---

## 8. Что осталось сделать для полноценного QNX‑бута

1. **Найти реальный канал консоли QNX**:
   - анализ по IFS показал наличие:
     - `devc-serscif ... scif0`;
     - `devc-pty`;
     - `vdev-virtio-console.so`.
   - текущий эксперимент с HSCIF (`0xe6e80000`, `e6540000`, `e6550000`) показал **отсутствие MMIO‑трафика** → вероятно, активная консоль идёт через virtio‑console или PTY.

2. **Доделать virtio‑console в контуре QNX‑VM**:
   - уверенно подтвердить, что текущий virtio‑console (`port=1236`) действительно подхватывается `vdev-virtio-console.so` внутри QNX;
   - довести подключение к этому сокету до стабильного состояния (сейчас `nc`/`QnxVirtioConsole` получают timeout при connect);
   - сделать virtio‑console основным источником `/qnx/console` и `QNX-VIRTCON` в комбинированных логах.

3. **Довести QNX‑boot до пользовательского уровня**:
   - получить полный текстовый лог загрузки;
   - убедиться, что гипервизор поднимает нужные сервисы (кластер, CAN‑подсистему, MCU‑клиента);
   - добиться осмысленного изображения на VNC 5901 (кластерный UI).

4. **После этого вернуться к Android‑boot**:
   - восстановить полноценный консольный лог (подробный `dmesg` / init‑скрипты);
   - довести Android до рабочей точки (ADB online, launcher/UI, системные сервисы).

---

## 9. Рекомендации по следующему этапу

- Фокус №1: **virtio‑console в QNX‑VM**:
  - реализовать как основной канал `/qnx/console`;
  - оставить SCIF/HSCIF в форке для будущих задач (GPS/BT, низкоуровневый UART).
- Фокус №2: **логика кластерного вывода**:
  - изучить, какие драйверы/серверы QNX используют для отрисовки приборки (через virtio‑du, shared memory или прямой framebuffer);
  - при необходимости добавить соответствующее virtio‑устройство в QEMU и привязать его к VNC/фреймбуферу.

Когда эти шаги будут выполнены, эмулятор достигнет стадии:

- Android HU + QNX кластер стабильно грузятся из родных образов;
- оба экрана видны в UI;
- есть полные текстовые логи загрузки обеих систем для дальнейшей отладки и эмуляции CAN/MCU.


