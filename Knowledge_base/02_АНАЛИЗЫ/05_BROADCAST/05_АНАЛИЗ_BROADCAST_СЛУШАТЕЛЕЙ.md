# Анализ Broadcast слушателей

## Найденные Broadcast механизмы

### SVMapService

**Protected Broadcasts (объявленные):**
1. `AUTONAVI_STANDARD_BROADCAST_RECV`
   - Объявлен как protected-broadcast
   - Используется для коммуникации с AutoNavi навигатором
   
2. `THINKWARE_TO_QNX_BROADCAST_RECV`
   - Объявлен как protected-broadcast
   - Используется для коммуникации с Thinkware навигатором и передачи данных в QNX

**Broadcast Receivers:**
1. `com.desaysv.mapservice.receiver.BootBroadcastReceiver`
   - Слушает: `android.intent.action.BOOT_COMPLETED`
   - Назначение: автозапуск сервиса

**Services:**
1. `com.desaysv.mapservice.service.LocalService`
   - Экспортирован (exported="true")
   
2. `com.desaysv.mapservice.external.MapService`
   - Экспортирован (exported="true")
   - Вероятно, основной сервис для работы с навигаторами

### SVMeterInteraction

**Broadcast Receivers:**
1. `com.desaysv.meterinteraction.receive.BootCompleteReceiver`
   - Слушает:
     - `android.intent.action.LOCKED_BOOT_COMPLETED`
     - `android.intent.action.BOOT_COMPLETED`
     - `com.desaysv.meter.test`
   - Приоритет: 900 (очень высокий)
   - Назначение: автозапуск сервиса взаимодействия с приборной панелью

**Services:**
1. `com.desaysv.meterinteraction.service.MeterService`
   - Вероятно, слушает навигационные Broadcast Intents
   - Отправляет данные на приборную панель

---

## Известные Broadcast Actions

### От навигатора к системе:
1. `AUTONAVI_STANDARD_BROADCAST_RECV`
   - Формат AutoNavi для отправки навигационных данных
   - Protected broadcast (только системные приложения могут отправлять)

2. `THINKWARE_TO_QNX_BROADCAST_RECV`
   - Формат Thinkware для отправки данных в QNX
   - Protected broadcast

3. `turbodog.navigation.system.message`
   - Формат TurboDog для отправки навигационных данных
   - Используется в NS.apk
   - НЕ protected broadcast (может отправлять любое приложение)

### От системы к навигатору:
1. `desay.broadcast.map.meter.interaction`
   - Управление навигацией от системы
   - Параметр: `map_area` (1 = приборная панель, 2 = основной экран)

---

## Кто слушает навигационные Broadcast?

### Проблема:
- Не найдено явных Broadcast Receivers, которые слушают:
  - `AUTONAVI_STANDARD_BROADCAST_RECV`
  - `THINKWARE_TO_QNX_BROADCAST_RECV`
  - `turbodog.navigation.system.message`

### Возможные варианты:

1. **Слушатели регистрируются динамически:**
   - В коде Services (LocalService, MapService, MeterService)
   - Через `registerReceiver()` в рантайме
   - Не видны в манифесте

2. **Слушатели в QNX системе:**
   - QNX может слушать Broadcast через специальный механизм
   - Или через System Properties / Unix Socket

3. **Слушатели в нативных библиотеках:**
   - Могут быть в .so файлах
   - Не видны в декомпилированном Java коде

---

## Выводы

1. **SVMapService объявляет protected broadcasts:**
   - Это означает, что SVMapService ОТПРАВЛЯЕТ эти broadcasts
   - Но не обязательно СЛУШАЕТ их

2. **SVMeterInteraction вероятно слушает:**
   - Может слушать навигационные broadcasts в MeterService
   - Код обфусцирован, поэтому не видно явных слушателей

3. **Формат `turbodog.navigation.system.message`:**
   - НЕ protected broadcast
   - Может отправлять любое приложение
   - Вероятно, слушается системой (QNX или SVMeterInteraction)

---

## Следующие шаги

1. ⏳ Проверить payload.bin на наличие APK навигации
2. ⏳ Изучить нативные библиотеки (.so файлы) на наличие слушателей
3. ⏳ Попробовать найти код, который регистрирует слушателей динамически
4. ⏳ Изучить формат данных для AUTONAVI_STANDARD_BROADCAST_RECV

---

**Дата:** 2024  
**Версия:** 1.0

