# Анализ алгоритма передачи данных TurboDog → QNX

## Обзор

Полный анализ декомпилированного кода TurboDog для понимания механизма передачи навигационных данных в систему QNX через Android broadcast.

## Архитектура потока данных

```
┌─────────────────────────────────────────────────────────────┐
│  Нативный код навигационного движка (JNI/C++)                │
│  - Вычисляет данные навигации                               │
│  - Формирует JSON с данными                                 │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ jniCallOnNaviDispatch(String json)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  JniToJava.jniCallOnNaviDispatch()                           │
│  → m.a().a.onNaviDispatch(str)                             │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ onNaviDispatch(String json)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  H3NCustomCenter.onNaviDispatch()                           │
│  - Парсит JSON                                               │
│  - При id=124 извлекает данные навигации                    │
│  - Вызывает onUptNavInfo()                                  │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ onUptNavInfo(turnType, turnDist, ...)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  H3NCustomCenter.onUptNavInfo()                             │
│  - Сохраняет данные в поля класса                           │
│  - Вызывает sendTBTMessage()                                │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ sendTBTMessage(...)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  H3NCustomCenter.sendTBTMessage()                           │
│  - Создает Intent с action                                  │
│    "turbodog.navigation.system.message"                     │
│  - Добавляет extras с данными                               │
│  - Отправляет через context.sendBroadcast()                 │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ Broadcast Intent
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Система Android / QNX Bridge                               │
│  (SVMeterInteraction или другой системный компонент)        │
│  - Получает broadcast                                       │
│  - Передает данные в QNX                                   │
│  - QNX отображает на приборной панели                      │
└─────────────────────────────────────────────────────────────┘
```

## Ключевые классы и методы

### 1. H3NCustomCenter.java

**Расположение:** `com.astrob.turbodog.H3NCustomCenter`

**Роль:** Главный класс для взаимодействия с системой автомобиля.

#### Ключевые константы:

```java
public static final String SEND_SYSTEM_MESSAGE = "turbodog.navigation.system.message";
public static final String RECV_MULTI_SCREEN_MESSAGE = "desay.broadcast.map.meter.interaction";

// Коды сообщений
public static final int SEND_TURNBYTURN_CODE = 201;  // Отправка данных навигации
public static final int SEND_NAVISTART_CODE = 202;   // Начало навигации
public static final int SEND_NAVISTOP_CODE = 203;     // Остановка навигации
public static final int SEND_APPEXIT_CODE = 205;      // Выход из приложения
public static final int SEND_APPSTARTRUN_CODE = 206;  // Запуск приложения
public static final int SEND_NAVIENGINE_INIT_FINISHED_CODE = 207; // Инициализация завершена

// Ключи для Intent extras
public static final String MESSAGE_CODE = "CODE";
public static final String MESSAGE_TURN_TYPE = "TURN_TYPE";
public static final String MESSAGE_TURN_DIST = "TURN_DIST";
public static final String MESSAGE_TURN_TIME = "TURN_TIME";
public static final String MESSAGE_REMAINING_DIST = "REMAINING_DIST";
public static final String MESSAGE_REMAINING_TIME = "REMAINING_TIME";
public static final String MESSAGE_CURRENT_ROAD = "CURRENT_ROAD";
public static final String MESSAGE_NEXT_ROAD = "NEXT_ROAD";
public static final String MESSAGE_ARRIVE_TIME = "ARRIVE_TIME";
```

#### Метод: onNaviDispatch(String str)

**Источник:** Вызывается из нативного кода через JNI.

**Параметры:** JSON строка с данными навигации.

**Формат JSON:**

```json
{
  "result": {
    "msgType": 1,
    "id": 124,
    "data": {
      "turnType": 1,
      "turnDis": 500.0,
      "turnTime": 30,
      "leftDis": 5000.0,
      "leftTime": 300,
      "curName": "Текущая дорога",
      "nextName": "Следующая дорога",
      "roadCls": 1,
      "speed": 60
    }
  }
}
```

**Обработка:**

- Проверяет `msgType == 1`
- При `id == 124` извлекает данные навигации
- Вызывает `onUptNavInfo()` с извлеченными данными

**Код метода (строки 782-851):**

```java
public void onNaviDispatch(String str) {
    try {
        JSONObject jSONObject = new JSONObject(str);
        JSONObject jSONObject2 = jSONObject.getJSONObject("result");
        if (jSONObject2.getInt("msgType") != 1) {
            return;
        }
        int i = jSONObject2.getInt("id");
        if (i == 124) {
            JSONObject jSONObject3 = jSONObject2.getJSONObject("data");
            int i3 = jSONObject3.getInt("turnType");
            int i4 = (int) jSONObject3.getDouble("turnDis");
            int i5 = (int) jSONObject3.getDouble("turnTime");
            int i6 = (int) jSONObject3.getDouble("leftDis");
            int i7 = jSONObject3.getInt("leftTime");
            String string = jSONObject3.getString("curName");
            String string2 = jSONObject3.getString("nextName");
            onUptNavInfo(i3, i4, i5, i6, i7, string, string2);
        }
    } catch (JSONException e) {
        e.printStackTrace();
    }
}
```

#### Метод: onUptNavInfo(...)

**Параметры:**

- `int turnType` - тип маневра (0=STRAIGHT, 1=LEFT, 2=RIGHT, 3=UTURN)
- `int turnDist` - расстояние до маневра (метры)
- `int turnTime` - время до маневра (секунды)
- `int remainDist` - оставшееся расстояние (метры)
- `int remainTime` - оставшееся время (секунды)
- `String curRoad` - название текущей дороги
- `String nextRoad` - название следующей дороги

**Действия:**

1. Сохраняет данные в поля класса
2. Вызывает `sendTBTMessage()`

**Код метода (строки 196-205):**

```java
private void onUptNavInfo(int i, int i2, int i3, int i4, int i5, String str, String str2) {
    this.mTurnType = i;
    this.mTurnDis = i2;
    this.mTurnTime = i3;
    this.mRemainDis = i4;
    this.mRemainTime = i5;
    this.mCurRoad = str;
    this.mNextRoad = str2;
    sendTBTMessage(i, i2, i3, i4, i5, str, str2);
}
```

#### Метод: sendTBTMessage(...)

**Роль:** Отправляет данные навигации в систему через broadcast.

**Код метода (строки 237-254):**

```java
private void sendTBTMessage(int i, int i2, int i3, int i4, int i5, String str, String str2) {
    Context context = getContext();
    if (context == null) {
        context = this.appContext;
    }
    long currentTimeMillis = System.currentTimeMillis();
    Intent intent = new Intent(SEND_SYSTEM_MESSAGE);
    intent.putExtra(MESSAGE_CODE, 201);
    intent.putExtra(MESSAGE_TURN_TYPE, i);
    intent.putExtra(MESSAGE_TURN_DIST, i2);
    intent.putExtra(MESSAGE_TURN_TIME, i3);
    intent.putExtra(MESSAGE_REMAINING_DIST, i4);
    intent.putExtra(MESSAGE_REMAINING_TIME, i5);
    intent.putExtra(MESSAGE_CURRENT_ROAD, str);
    intent.putExtra(MESSAGE_NEXT_ROAD, str2);
    intent.putExtra(MESSAGE_ARRIVE_TIME, i5 + (currentTimeMillis / 1000));
    context.sendBroadcast(intent);
}
```

**Формат Intent:**

- **Action:** `"turbodog.navigation.system.message"`
- **Extras:**
  - `"CODE"` = `201` (SEND_TURNBYTURN_CODE)
  - `"TURN_TYPE"` = тип маневра (int)
  - `"TURN_DIST"` = расстояние до маневра (int, метры)
  - `"TURN_TIME"` = время до маневра (int, секунды)
  - `"REMAINING_DIST"` = оставшееся расстояние (int, метры)
  - `"REMAINING_TIME"` = оставшееся время (int, секунды)
  - `"CURRENT_ROAD"` = название текущей дороги (String)
  - `"NEXT_ROAD"` = название следующей дороги (String)
  - `"ARRIVE_TIME"` = время прибытия (long, Unix timestamp в секундах)

### 2. JniToJava.java

**Расположение:** `com.astrob.navi.astrobnavilib.JniToJava`

**Роль:** Мост между нативным кодом (JNI) и Java.

**Метод:** `jniCallOnNaviDispatch(String str)`

```java
public void jniCallOnNaviDispatch(String str) {
    m.a().a.onNaviDispatch(str);
}
```

**Вызов:** Нативный код вызывает этот метод через JNI, передавая JSON строку с данными навигации.

### 3. Взаимодействие с системой

#### Получение команд от системы

**Broadcast Action:** `"desay.broadcast.map.meter.interaction"`

**Обработка:** В методе `handleProtocal()` класса `H3NCustomCenter`

**Коды команд:**

- `100` - Управление подсветкой (HEADLIGHT)
- `101` - Повторить голосовую подсказку (REPEAT)
- `102` - Сохранить данные (SAVE)
- `103` - Выход из приложения (EXIT)
- `104` - Масштабирование карты (ZOOM)
- `105` - Изменение перспективы (PERSPECTIVE)
- `106` - Обзор маршрута (PATH_OVERVIEW)
- `107` - Отмена навигации (CANCEL_NAVI)
- `108` - Вернуться на карту (BACK_TO_MAP)
- `109` - Сохранить текущую позицию (COLLECT)
- `110` - Перейти к избранному (FAV_LIST)
- `111` - Вернуться к позиции автомобиля (BACK_CAR_POS)
- `112` - Начать навигацию (START_NAVI)
- `113` - Навигация к пункту назначения (NAVI_TO_DEST)
- `114` - Поиск POI (SEARCH_POI)
- `115` - Поиск рядом (SEARCH_NEAR)
- `116` - Статус карты (MAP_STATUS)

## Формат данных навигации

### Типы маневров (TURN_TYPE)

```java
0 = STRAIGHT    // Прямо
1 = LEFT        // Налево
2 = RIGHT       // Направо
3 = UTURN       // Разворот
```

### Единицы измерения

- **Расстояния:** метры (int)
- **Время:** секунды (int)
- **Время прибытия:** Unix timestamp в секундах (long)

### Пример Intent

```java
Intent intent = new Intent("turbodog.navigation.system.message");
intent.putExtra("CODE", 201);
intent.putExtra("TURN_TYPE", 2);              // Направо
intent.putExtra("TURN_DIST", 500);             // 500 метров
intent.putExtra("TURN_TIME", 30);              // 30 секунд
intent.putExtra("REMAINING_DIST", 5000);       // 5 км
intent.putExtra("REMAINING_TIME", 300);       // 5 минут
intent.putExtra("CURRENT_ROAD", "Ленинградский проспект");
intent.putExtra("NEXT_ROAD", "Тверская улица");
intent.putExtra("ARRIVE_TIME", 1700000000);   // Unix timestamp
context.sendBroadcast(intent);
```

## Другие типы сообщений

### Начало навигации (CODE = 202)

```java
Intent intent = new Intent(SEND_SYSTEM_MESSAGE);
intent.putExtra(MESSAGE_CODE, 202);
intent.putExtra(MESSAGE_DATA, 1);  // 1 = реальная навигация, 2 = симуляция
context.sendBroadcast(intent);
```

### Остановка навигации (CODE = 203)

```java
Intent intent = new Intent(SEND_SYSTEM_MESSAGE);
intent.putExtra(MESSAGE_CODE, 203);
context.sendBroadcast(intent);
```

### Статус карты (CODE = 116)

```java
Intent intent = new Intent(SEND_SYSTEM_MESSAGE);
intent.putExtra(MESSAGE_CODE, 116);
intent.putExtra(MESSAGE_DATA, 207);  // 207 = инициализация завершена
context.sendBroadcast(intent);
```

## Полный алгоритм для реализации

### Шаг 1: Получение данных от навигатора

Для Yandex Navigator или другого навигатора нужно:

1. Перехватывать данные навигации (через AccessibilityService, BroadcastReceiver, или другие методы)
2. Преобразовывать в формат TurboDog

### Шаг 2: Формирование Intent

```java
private void sendNavigationData(NavigationData data) {
    Intent intent = new Intent("turbodog.navigation.system.message");
    intent.putExtra("CODE", 201);

    // Преобразование типа маневра
    int turnType = convertManeuverType(data.getManeuverType());

    intent.putExtra("TURN_TYPE", turnType);
    intent.putExtra("TURN_DIST", (int) data.getManeuverDistance());
    intent.putExtra("TURN_TIME", calculateTurnTime(data));
    intent.putExtra("REMAINING_DIST", (int) data.getRemainingDistance());
    intent.putExtra("REMAINING_TIME", data.getRemainingTime());
    intent.putExtra("CURRENT_ROAD", data.getCurrentRoad() != null ? data.getCurrentRoad() : "");
    intent.putExtra("NEXT_ROAD", data.getNextRoad() != null ? data.getNextRoad() : "");

    long arriveTime = System.currentTimeMillis() / 1000 + data.getRemainingTime();
    intent.putExtra("ARRIVE_TIME", arriveTime);

    context.sendBroadcast(intent);
}

private int convertManeuverType(String maneuverType) {
    if (maneuverType == null) return 0;
    switch (maneuverType.toUpperCase()) {
        case "LEFT": return 1;
        case "RIGHT": return 2;
        case "UTURN": return 3;
        default: return 0; // STRAIGHT
    }
}
```

### Шаг 3: Отправка в систему

Просто вызвать `context.sendBroadcast(intent)`. Система автоматически перехватит broadcast и передаст в QNX.

## Важные замечания

1. **Broadcast не требует разрешений** - это системный broadcast, доступный всем приложениям
2. **Формат данных строгий** - все значения должны быть в правильных типах (int для расстояний и времени)
3. **Время прибытия** - вычисляется как `currentTime + remainingTime` в секундах
4. **Строки могут быть пустыми** - если данных нет, передавать пустую строку, а не null
5. **Код 201** - это код для данных навигации (TURN-BY-TURN), другие коды для других событий

## Следующие шаги

1. ✅ Анализ завершен - алгоритм понятен
2. ⏳ Реализовать преобразование данных Yandex Navigator в формат TurboDog
3. ⏳ Протестировать на реальном устройстве
4. ⏳ Добавить обработку других типов сообщений (начало/остановка навигации)

## Ссылки на исходный код

- `H3NCustomCenter.java` - строки 196-254, 782-851
- `JniToJava.java` - строка 236-238
- Константы определены в `H3NCustomCenter.java` - строки 35-78
