# Извлеченные данные из пакета обновления

**Дата извлечения:** Sat Nov 15 20:35:43 MSK 2025
**Исходный пакет:** ./T18FL3 703000765AA MOD SW 02.09.00 + CHIME + VR + DSP + MAPS/T18FL3  703000765AA MOD SW 02.09.00 + CHIME + VR + DSP + MAPS/soc_update.zip

## Структура

### metadata/
Метаданные обновления:
- `META-INF/com/android/metadata` - метаданные OTA
- `payload_properties.txt` - свойства payload
- `care_map.txt` - карта ухода за разделами
- `compatibility/` - данные совместимости

### payload/
- `payload.bin` - основной payload (требует распаковки)
- Распакованные образы (если payload_dumper использован)

### images/
Образы системы:
- `radio.bin` - образ радио
- `radio.bin.md5` - контрольная сумма

### config/
Конфигурационные файлы:
- `modelConfig.txt` - конфигурация модели
- `materialsConfig.txt` - конфигурация материалов
- `module.txt` - информация о модулях

### apks/
APK файлы из обновления (если найдены)

## Распаковка payload.bin

Для полной распаковки payload.bin установите payload_dumper:

```bash
pip install payload_dumper
payload_dumper payload/payload.bin -o payload/
```

Или используйте онлайн инструменты для распаковки payload.bin.
