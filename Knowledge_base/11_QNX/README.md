# QNX Окружение Разработки

## Структура

- `images/` - QNX образы (qnx_system.img, qnx_boot.img)
- `config/` - Конфигурационные файлы
- `scripts/` - Скрипты для работы с QNX
- `logs/` - Логи QNX
- `workspace/` - Рабочая директория для разработки

## Установка QNX SDK

1. Скачайте QNX Software Development Platform (SDP) 7.1
2. Установите в `$HOME/qnx710` или укажите путь через `QNX_TARGET`
3. Настройте переменные окружения:
   ```bash
   source config/qnx_config.sh
   ```

## Запуск QNX Эмулятора

```bash
./scripts/start_qnx_emulator.sh
```

## Тестирование связи Android-QNX

```bash
./scripts/test_android_qnx_connection.sh <android_device_id> <qnx_ip>
```

## Интеграция с Android Эмулятором

1. Запустите Android эмулятор ГУ
2. Запустите QNX эмулятор
3. Настройте сетевую связь между ними
4. Используйте broadcast для отправки данных:
   - `turbodog.system.navigation.message` - прямой broadcast
   - `desay.thirdparty.navigation` - через mapservice

## QNX Образы

QNX образы извлечены из пакета обновления:
- `qnx_system.img` - системный образ QNX
- `qnx_boot.img` - загрузочный образ QNX

## Примечания

- QNX требует лицензию для коммерческого использования
- Для разработки можно использовать QNX Community Edition
- Эмуляция QNX через QEMU может быть медленной
- Для лучшей производительности используйте реальное оборудование
