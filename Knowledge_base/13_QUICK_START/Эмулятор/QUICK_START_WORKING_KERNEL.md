# Быстрый старт: Рабочее ядро для тестирования приложений

## Шаг 1: Получите рабочее Android ядро

Самый простой способ - использовать ядро из готового Android образа для ARM64.

### Вариант A: Использовать ядро из вашего boot.img (временно, пока не найдете лучшее)

```bash
cd /Users/valentinezov/Projects/Tiggo
python3 -c "
import struct
from pathlib import Path

boot_img = Path('ext_SOC_Playload/boot.img')
if boot_img.exists():
    with open(boot_img, 'rb') as f:
        header = f.read(1632)
        if header[0:8] == b'ANDROID!':
            page_size = struct.unpack('<I', header[36:40])[0]
            kernel_size = struct.unpack('<I', header[8:12])[0]
            f.seek(page_size)
            kernel = f.read(kernel_size)
            kernel_path = Path('development/emulator/kernels/android_kernel_arm64')
            kernel_path.parent.mkdir(parents=True, exist_ok=True)
            with open(kernel_path, 'wb') as k:
                k.write(kernel)
            print(f'✅ Kernel extracted: {kernel_path} ({kernel_size} bytes)')
        else:
            print('❌ Invalid boot.img format')
else:
    print('❌ boot.img not found')
"
```

**Примечание:** Это ядро может не работать, но можно попробовать.

### Вариант B: Скачать готовое ядро (рекомендуется)

1. Найдите готовый Android образ для ARM64 (например, из LineageOS)
2. Извлеките ядро из образа
3. Сохраните в `development/emulator/kernels/android_kernel_arm64`

## Шаг 2: Включите режим рабочего ядра

```bash
cd /Users/valentinezov/Projects/Tiggo/development/emulator
export T18FL3_USE_WORKING_KERNEL=1
python3 main.py
```

## Шаг 3: Проверьте логи

Эмулятор должен вывести:

```
🔧 Using WORKING KERNEL mode with virt machine
   This mode uses a working kernel for fast app testing
   Your original system.img and vendor.img will be used
✅ Using working kernel: /path/to/kernel
✅ Using original system.img: /path/to/system.img
✅ Using original vendor.img: /path/to/vendor.img
```

## Что дальше?

После успешного запуска:

1. Тестируйте ваши модифицированные приложения
2. Используйте ADB для установки APK
3. Проверяйте логи через интерфейс эмулятора
4. Создавайте пакеты обновления для реального автомобиля

## Проблемы?

См. `README_WORKING_KERNEL.md` для подробной информации и устранения проблем.

