# Анализ SVMapService и SVMeterInteraction

## Статус декомпиляции

### SVMapService.apk
- ✅ Декомпиляция завершена
- ⚠️ Исходный код не извлечен (обфускация или нативный код)
- ✅ AndroidManifest.xml извлечен
- ✅ Ресурсы извлечены

### SVMeterInteraction.apk
- ✅ Декомпиляция завершена
- ⚠️ Исходный код не извлечен (обфускация или нативный код)
- ✅ AndroidManifest.xml извлечен
- ✅ Ресурсы извлечены

---

## Анализ AndroidManifest.xml

### SVMapService.apk

**Package:** `com.desaysv.mapservice`

**Компоненты:**
1. **Application:** `com.desaysv.mapservice.MapApplication`
   - `android:persistent="true"` - приложение постоянно в памяти
   
2. **Services:**
   - `com.desaysv.mapservice.service.LocalService` - локальный сервис
   - `com.desaysv.mapservice.external.MapService` - внешний сервис карт
   
3. **Broadcast Receivers:**
   - `com.desaysv.mapservice.receiver.BootBroadcastReceiver` - автозапуск

**Protected Broadcasts:**
- `AUTONAVI_STANDARD_BROADCAST_RECV` - стандартный Broadcast от AutoNavi
- `THINKWARE_TO_QNX_BROADCAST_RECV` - Broadcast от Thinkware к QNX

**Выводы:**
- SVMapService использует Broadcast для коммуникации с QNX
- Поддерживает AutoNavi (китайский навигатор)
- Поддерживает Thinkware (корейский навигатор)

### SVMeterInteraction.apk

**Package:** `com.desaysv.meterinteraction`

**Компоненты:**
1. **Application:** `com.desaysv.meterinteraction.MeterApplication`
   - `android:directBootAware="true"` - работает до разблокировки устройства
   
2. **Service:**
   - `com.desaysv.meterinteraction.service.MeterService` - сервис взаимодействия с приборной панелью
   
3. **Broadcast Receivers:**
   - `com.desaysv.meterinteraction.receive.BootCompleteReceiver` - автозапуск
     - Приоритет: 900 (высокий)
     - Слушает: `LOCKED_BOOT_COMPLETED`, `BOOT_COMPLETED`

**Выводы:**
- SVMeterInteraction отвечает за взаимодействие с приборной панелью
- Запускается очень рано (directBootAware)
- Имеет высокий приоритет при загрузке

---

## Известные механизмы коммуникации

### 1. Broadcast Intent: `turbodog.navigation.system.message`

**Источник:** NS.apk (GoNavi.java)

**Формат:**
```java
Intent intent = new Intent("turbodog.navigation.system.message");
intent.putExtra("CODE", code);                    // Код сообщения
intent.putExtra("DATA", data);                    // Данные
intent.putExtra("TURN_TYPE", turnType);           // Тип поворота
intent.putExtra("TURN_DIST", turnDist);          // Расстояние до поворота
intent.putExtra("TURN_TIME", turnTime);           // Время до поворота
intent.putExtra("REMAINING_DIST", remainingDist); // Оставшееся расстояние
intent.putExtra("REMAINING_TIME", remainingTime); // Оставшееся время
intent.putExtra("ARRIVE_TIME", arriveTime);       // Время прибытия
intent.putExtra("CURRENT_ROAD", currentRoad);     // Текущая дорога
intent.putExtra("NEXT_ROAD", nextRoad);           // Следующая дорога
sendBroadcast(intent);
```

**Получатель:** Вероятно, SVMeterInteraction или QNX система

### 2. Broadcast Intent: `desay.broadcast.map.meter.interaction`

**Источник:** Система автомобиля (QNX?)

**Формат:**
```java
Intent intent = new Intent("desay.broadcast.map.meter.interaction");
intent.putExtra("map_area", area); // 1 = приборная панель, 2 = основной экран
sendBroadcast(intent);
```

**Получатель:** NS.apk (MyReceiver)

### 3. Protected Broadcasts

**AutoNavi:**
- `AUTONAVI_STANDARD_BROADCAST_RECV` - стандартный формат AutoNavi

**Thinkware:**
- `THINKWARE_TO_QNX_BROADCAST_RECV` - формат Thinkware для QNX

---

## Предположения о механизме работы

### Отправка данных на приборную панель:

1. **Навигационные данные (маневры, маршрут):**
   - Отправляются через Broadcast Intent: `turbodog.navigation.system.message`
   - Получатель: SVMeterInteraction или QNX система
   - Формат: Intent с extras (CODE, TURN_TYPE, TURN_DIST, и т.д.)

2. **Карта:**
   - Возможно, отправляется через другой механизм:
     - Shared Memory
     - Unix Socket
     - System Properties
     - Или через Broadcast с изображением (bitmap)

3. **Ограничение скорости:**
   - Вероятно, отправляется через:
     - System Properties (например, `sys.speed.limit`)
     - Broadcast Intent (специальный action)
     - Или через тот же `turbodog.navigation.system.message` с дополнительным полем

### Получение данных системой:

1. **SVMeterInteraction:**
   - Слушает Broadcast Intents
   - Получает данные от навигации
   - Отправляет на QNX через:
     - System Properties
     - Unix Socket
     - Shared Memory
     - Или напрямую через CAN-bus

2. **QNX система:**
   - Читает данные из System Properties
   - Или получает через Unix Socket
   - Отображает на приборной панели

---

## Следующие шаги

### 1. Изучить логи системы
- Найти примеры Broadcast Intents в логах
- Определить формат данных для карты
- Найти механизм отправки ограничения скорости

### 2. Изучить нативные библиотеки
- Проверить .so файлы (если есть)
- Изучить JNI интерфейсы
- Найти функции для отправки данных в QNX

### 3. Экспериментальный подход
- Установить Bridge Service
- Отправлять тестовые Broadcast Intents
- Мониторить реакцию системы
- Логировать все Broadcast Intents

### 4. Изучить другие компоненты
- Проверить другие системные приложения
- Найти примеры использования Broadcast Intents
- Изучить документацию Desay (если доступна)

---

## Выводы

### Известно:
- ✅ Формат Broadcast Intent для навигационных данных
- ✅ Механизм запуска навигации на приборной панели
- ✅ Компоненты системы (SVMapService, SVMeterInteraction)

### Требует исследования:
- ⏳ Механизм отправки карты на приборную панель
- ⏳ Механизм отправки ограничения скорости
- ⏳ Формат данных для карты (изображение или координаты)
- ⏳ Способ коммуникации с QNX (System Properties, Socket, Shared Memory)

### Рекомендации:
1. **Экспериментальный подход:**
   - Создать Bridge Service
   - Отправлять тестовые данные через известный формат
   - Мониторить реакцию системы
   
2. **Обратная инженерия:**
   - Изучить логи системы
   - Найти примеры Broadcast Intents
   - Проанализировать трафик между компонентами

3. **Альтернативный подход:**
   - Использовать известный формат `turbodog.navigation.system.message`
   - Добавить дополнительные поля для карты и ограничения скорости
   - Экспериментировать с форматом данных

---

**Дата:** 2024  
**Версия:** 1.0

