# Настройка Полного Окружения Разработки

## Обзор

Этот набор скриптов позволяет создать полное окружение разработки для работы с ГУ (Головным Устройством), включающее:

- **Android эмулятор ГУ** - эмуляция Android части системы
- **QNX окружение** - эмуляция QNX части системы (приборная панель, проекция)
- **Интеграция** - тестирование связи между Android и QNX

## Быстрый Старт

### Комплексная настройка (рекомендуется)

```bash
./development/scripts/setup_complete_environment.sh
```

Этот скрипт:

1. Создаст Android эмулятор с характеристиками ГУ
2. Настроит QNX окружение
3. Создаст скрипты для запуска всего окружения

### Пошаговая настройка

#### 1. Android Эмулятор ГУ

```bash
./development/scripts/create_gu_emulator.sh GU_Emulator
```

Создает новый AVD с характеристиками:

- Модель: G6SH-r8a7795
- Производитель: Renesas
- Android: 9 (API 28)
- RAM: 4GB

#### 2. QNX Окружение

```bash
./development/scripts/setup_qnx_environment.sh
```

Настраивает:

- QNX образы из пакета обновления
- Конфигурацию QNX SDK
- Скрипты для запуска QNX эмулятора
- Тестирование связи Android-QNX

#### 3. Запуск Окружения

```bash
./development/scripts/start_full_environment.sh
```

Запускает:

- Android эмулятор в фоне
- QNX эмулятор (опционально)
- Ожидает подключения устройств

## Структура Скриптов

### Android Эмулятор

- `create_gu_emulator.sh` - Создание нового AVD с характеристиками ГУ
- `clean_emulator.sh` - Очистка эмулятора от лишних приложений
- `configure_emulator_as_gu.sh` - Настройка эмулятора под ГУ
- `install_extracted_data.sh` - Установка данных из пакета обновления

### QNX Окружение

- `setup_qnx_environment.sh` - Настройка QNX окружения разработки
- `qnx_environment/scripts/start_qnx_emulator.sh` - Запуск QNX эмулятора
- `qnx_environment/scripts/test_android_qnx_connection.sh` - Тестирование связи

### Пакет Обновления

- `extract_update_package.sh` - Извлечение данных из OTA пакета
- `extract_apks_from_images.sh` - Извлечение APK из образов системы

### Комплексные

- `setup_complete_environment.sh` - Полная настройка окружения
- `start_full_environment.sh` - Запуск всего окружения

## Требования

### Обязательные

- **Android SDK** - с установленными системными образами
- **ADB** - Android Debug Bridge
- **Python 3** - для payload_dumper

### Опциональные

- **QNX SDK 7.1** - для работы с QNX (можно использовать Community Edition)
- **QEMU** - для эмуляции QNX (если нет реального оборудования)

  ```bash
  # macOS
  brew install qemu

  # Linux
  sudo apt-get install qemu-system-arm
  ```

## Использование

### 1. Создание и Настройка Эмуляторов

```bash
# Создать Android эмулятор
./development/scripts/create_gu_emulator.sh GU_Emulator

# Настроить QNX окружение
./development/scripts/setup_qnx_environment.sh
```

### 2. Запуск Окружения

```bash
# Запустить все окружение
./development/scripts/start_full_environment.sh

# Или запустить отдельно
emulator -avd GU_Emulator &
./qnx_environment/scripts/start_qnx_emulator.sh &
```

### 3. Установка Данных из Пакета Обновления

```bash
# Извлечь данные из пакета обновления
./development/scripts/extract_update_package.sh

# Установить на Android эмулятор
./development/scripts/install_extracted_data.sh <device_id>

# Настроить характеристики ГУ
./development/scripts/configure_emulator_as_gu.sh <device_id>
```

### 4. Тестирование Связи Android-QNX

```bash
# После запуска обоих эмуляторов
./qnx_environment/scripts/test_android_qnx_connection.sh <android_device_id> <qnx_ip>
```

## Структура Директорий

```
development/
├── scripts/
│   ├── create_gu_emulator.sh          # Создание Android эмулятора
│   ├── setup_qnx_environment.sh       # Настройка QNX
│   ├── setup_complete_environment.sh  # Комплексная настройка
│   ├── start_full_environment.sh      # Запуск окружения
│   └── ...
│
qnx_environment/
├── images/                            # QNX образы
│   ├── qnx_system.img
│   └── qnx_boot.img
├── config/                            # Конфигурация
│   └── qnx_config.sh
├── scripts/                           # Скрипты QNX
│   ├── start_qnx_emulator.sh
│   └── test_android_qnx_connection.sh
└── README.md                          # Документация QNX

update_extracted/
├── payload/                           # Распакованные образы
│   ├── system.img
│   ├── vendor.img
│   ├── qnx_system.img
│   └── ...
├── metadata/                          # Метаданные обновления
└── config/                            # Конфигурационные файлы
```

## Тестирование Навигационных Данных

После настройки окружения можно тестировать отправку навигационных данных:

```bash
# Отправка тестовых данных на QNX
adb -s <device_id> shell am broadcast \
    -a turbodog.system.navigation.message \
    --ei REMAINING_DISTANCE "1000" \
    --ei TURN_DISTANCE "50" \
    --ei TURN_TYPE "1" \
    --ei SPEED_LIMIT "60"
```

## Отладка

### Проверка Подключения Android

```bash
adb devices
```

### Проверка QNX

```bash
# Если QNX запущен через QEMU
ps aux | grep qemu

# Проверка логов QNX
tail -f qnx_environment/logs/qnx_logs.txt
```

### Логи Android

```bash
adb logcat | grep -i "navigation\|qnx\|turbodog"
```

## Примечания

- **QNX SDK** требует лицензию для коммерческого использования
- Для разработки можно использовать **QNX Community Edition**
- Эмуляция QNX через QEMU может быть медленной
- Для лучшей производительности используйте реальное оборудование
- Системные свойства Android могут сброситься после перезагрузки
- Для постоянных изменений нужно модифицировать build.prop

## Решение Проблем

### Android эмулятор не запускается

1. Проверьте наличие системного образа:

   ```bash
   sdkmanager --list_installed | grep system-images
   ```

2. Установите нужный образ:
   ```bash
   sdkmanager "system-images;android-28;google_apis;x86_64"
   ```

### QNX эмулятор не запускается

1. Проверьте установку QNX SDK
2. Установите QEMU:
   ```bash
   brew install qemu  # macOS
   ```

### Связь Android-QNX не работает

1. Проверьте сетевые настройки эмуляторов
2. Убедитесь, что оба эмулятора запущены
3. Проверьте broadcast receivers в QNX

## Дополнительные Ресурсы

- [QNX Documentation](https://www.qnx.com/developers/docs/)
- [Android Emulator Guide](https://developer.android.com/studio/run/emulator)
- [QEMU Documentation](https://www.qemu.org/documentation/)
