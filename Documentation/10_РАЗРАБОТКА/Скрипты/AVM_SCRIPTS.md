# AVM Scripts

Скрипты для автоматизации работы с Android Virtual Machines (AVD) с характеристиками ГУ Chery Tiggo 8 Pro Max T18FL3.

## Структура

- `scripts/` - все исполняемые скрипты

## Документация

Подробная инструкция по настройке AVD:
- [Knowledge_base/04_ИНСТРУКЦИИ/НАСТРОЙКА_AVD_ANDROID_STUDIO.md](../../Knowledge_base/04_ИНСТРУКЦИИ/НАСТРОЙКА_AVD_ANDROID_STUDIO.md)

## Важная информация о двух дисплеях

**Android Emulator не поддерживает два физических дисплея напрямую.** Параметр `-multidisplay` существует, но работает нестабильно.

### Обходной путь: Presentation API

Для работы со вторым дисплеем (как на реальном ГУ, где второй дисплей - приборная панель через HDMI) используйте **Presentation API** в приложении:

```java
DisplayManager displayManager = (DisplayManager) getSystemService(Context.DISPLAY_SERVICE);
Display[] displays = displayManager.getDisplays();

// Найти второй дисплей (если создан)
Display secondaryDisplay = null;
for (Display display : displays) {
    if (display.getDisplayId() != Display.DEFAULT_DISPLAY) {
        secondaryDisplay = display;
        break;
    }
}

if (secondaryDisplay != null) {
    Presentation presentation = new Presentation(this, secondaryDisplay);
    presentation.setContentView(R.layout.presentation_layout);
    presentation.show();
}
```

## Скрипты

### Основные скрипты

- **create_avd.sh** - Создание AVD с характеристиками ГУ
  ```bash
  ./scripts/create_avd.sh
  ```

- **start_avd.sh** - Запуск основного эмулятора (один дисплей, порт 5554)
  ```bash
  ./scripts/start_avd.sh
  ```

- **stop_avd.sh** - Остановка основного эмулятора
  ```bash
  ./scripts/stop_avd.sh
  ```

- **check_status.sh** - Проверка статуса и характеристик эмулятора
  ```bash
  ./scripts/check_status.sh
  ```

### Скрипты для работы с двумя дисплеями

- **start_avd_dual.sh** - Запуск второго эмулятора (порт 5556) для тестирования Presentation API
  ```bash
  ./scripts/start_avd_dual.sh
  ```
  **Примечание:** Эмулятор запускается с одним дисплеем. Второй дисплей создается через Presentation API в приложении.

- **stop_avd_dual.sh** - Остановка второго эмулятора
  ```bash
  ./scripts/stop_avd_dual.sh
  ```

- **check_dual_display.sh** - Проверка дисплеев на втором эмуляторе
  ```bash
  ./scripts/check_dual_display.sh
  ```

- **create_virtual_display.sh** - Попытка создать виртуальный дисплей через API (экспериментально)
  ```bash
  ./scripts/create_virtual_display.sh [порт]
  ```

- **test_presentation.sh** - Информация о тестировании Presentation API
  ```bash
  ./scripts/test_presentation.sh
  ```

- **test_second_display.sh** - Тестирование Second Display Receiver приложения
  ```bash
  ./scripts/test_second_display.sh [порт]
  ```
  Автоматически устанавливает и запускает приложение, отправляет тестовые данные на второй дисплей.

## Использование

Все скрипты должны запускаться из корня проекта или из папки `ai_scripts/AVM/`:

```bash
cd ai_scripts/AVM
./scripts/start_avd.sh
```

Или из корня проекта:

```bash
./ai_scripts/AVM/scripts/start_avd.sh
```

## Порты ADB

- **Первый эмулятор (Tiggo_T18FL3):** `emulator-5554`
- **Второй эмулятор (Tiggo_T18FL3_dual):** `emulator-5556`

Для работы с конкретным эмулятором используйте:
```bash
adb -s emulator-5554 <команда>  # Первый эмулятор
adb -s emulator-5556 <команда>  # Второй эмулятор
```
