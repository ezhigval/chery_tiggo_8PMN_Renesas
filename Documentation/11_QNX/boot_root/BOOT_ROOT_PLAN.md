# План получения полного root через патч boot.img (через QNX)

## Структура на Mac

- `Knowledge_base/11_QNX/boot_root/backup/` — сюда кладём сырые образы с ГУ
  - `boot_a.orig.img`
  - (опционально) `boot_b.orig.img`
- `Knowledge_base/11_QNX/boot_root/patched/` — сюда складываются пропатченные образы
  - `boot_a.patched.img`

Скрипт патча (уже есть):
- `Knowledge_base/11_QNX/patch_boot_for_root.sh`

## Шаг 1. Бэкап boot на QNX

На QNX:

1. Найти нужный раздел (пример):
   ```sh
   ls /dev
   fdisk /dev/emmc0      # смотрим разметку (только чтение)
   ```

2. Снять образ (ПРИМЕР, адаптируй номер tXX и путь к USB):
   ```sh
   dd if=/dev/emmc0tXX of=/fs/usb/boot_a.orig.img bs=4M
   sync
   ```

3. Скопировать `boot_a.orig.img` с USB на Mac в:
   ```
   Knowledge_base/11_QNX/boot_root/backup/boot_a.orig.img
   ```

## Шаг 2. Патч boot на Mac

На Mac:

```bash
cd /Users/valentinezov/Projects/Tiggo

BOOT_ORIG="Knowledge_base/11_QNX/boot_root/backup/boot_a.orig.img"
BOOT_PATCHED="Knowledge_base/11_QNX/boot_root/patched/boot_a.patched.img"

chmod +x Knowledge_base/11_QNX/patch_boot_for_root.sh
./Knowledge_base/11_QNX/patch_boot_for_root.sh "$BOOT_ORIG" "$BOOT_PATCHED"
```

Скрипт выведет, какие строки заменены (`ro.secure`, `ro.adb.secure` и т.д.).

## Шаг 3. Прошивка патченного boot через QNX

Снова на QNX:

1. Скопировать `boot_a.patched.img` с Mac на QNX (USB/сеть).
2. Прошить:
   ```sh
   dd if=/fs/usb/boot_a.patched.img of=/dev/emmc0tXX bs=4M
   sync
   ```
   **ВНИМАНИЕ:** `tXX` должен быть ТОЧНО тот же, что и для бэкапа.

## Шаг 4. Проверка после ребута

Перезагружаем ГУ (через QNX или кнопкой):

```bash
adb wait-for-device
adb root
adb shell id
adb remount
```

Ожидаемый результат:
- `adb root` **не** пишет `cannot run as root`.
- `adb shell id` → `uid=0(root)`.
- `adb remount` монтирует `/system` в RW.

После этого у нас постоянный ADB root, дальше можно ставить su/Magisk и переносить сервис в `/system/priv-app`.
