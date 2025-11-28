# Анализ декомпилированного кода NS.apk

## 📊 Структура приложения

### Основные классы:

1. **MainActivity** - главная Activity
2. **boot** - сервис для автозапуска
3. **GoNavi** - класс для работы с навигацией
4. **MyReceiver** - Broadcast Receiver
5. **SystemMessageReceiver** - Receiver для системных сообщений

---

## 🔍 Ключевые методы

### MainActivity.DispMap() - Запуск Activity

**Назначение:** Запускает Activity приложения на указанном дисплее

**Код:**
```java
private void DispMap(View v, int d, String pkg) {
    DisplayManager displayManager = (DisplayManager) getApplicationContext().getSystemService("display");
    Display[] dis = displayManager.getDisplays();
    if (dis.length > 1) {
        Intent i = getPackageManager().getLaunchIntentForPackage(pkg);
        if (i != null) {
            ActivityOptions options = ActivityOptions.makeBasic().setLaunchDisplayId(dis[d].getDisplayId());
            startActivity(i, options.toBundle());
            return;
        } else {
            if (v != null) {
                Snackbar.make(v, "Not install PKG", 0).setAction("Action", (View.OnClickListener) null).show();
                return;
            }
            return;
        }
    }
    if (v != null) {
        Snackbar.make(v, "Two display NULL", 0).setAction("Action", (View.OnClickListener) null).show();
    }
}
```

**Как работает:**
1. Получает список дисплеев через `DisplayManager`
2. Использует `getLaunchIntentForPackage(pkg)` для получения Intent запуска
3. Создает `ActivityOptions` с указанием дисплея
4. Запускает Activity через `startActivity()`

**Ключевые моменты:**
- ✅ Использует `getLaunchIntentForPackage()` - стандартный Android API
- ✅ Поддерживает запуск на разных дисплеях (для проекции)
- ✅ Не требует QUERY_ALL_PACKAGES для этого метода (но нужен для получения списка)

---

### boot.java - Сервис автозапуска

**Назначение:** Фоновый сервис для автозапуска приложений

**Ключевые методы:**
- `onCreate()` - инициализация
- `onStartCommand()` - обработка команд
- `DispMap()` - запуск Activity (аналогично MainActivity)

**Использование:**
- Запускается через `startForegroundService()`
- Получает package name из SharedPreferences
- Автоматически запускает приложение при загрузке системы

---

### GoNavi.java - Работа с навигацией

**Назначение:** Класс для отправки системных сообщений

**Ключевые константы:**
```java
public static final String SEND_SYSTEM_MESSAGE = "...";
public static final String MESSAGE_CODE = "...";
public static final String MESSAGE_DATA = "...";
```

**Использование:**
- Отправка Broadcast Intent в систему
- Интеграция с системой навигации

---

## 💡 Выводы для нашего проекта

### Механизм запуска Activity:

**Простой способ (из NS.apk):**
```java
// Получение Intent для запуска приложения
Intent i = getPackageManager().getLaunchIntentForPackage(packageName);

// Запуск на основном дисплее
if (i != null) {
    startActivity(i);
}

// Запуск на втором дисплее (для проекции)
if (i != null && displays.length > 1) {
    ActivityOptions options = ActivityOptions.makeBasic()
        .setLaunchDisplayId(displays[1].getDisplayId());
    startActivity(i, options.toBundle());
}
```

**Преимущества:**
- ✅ Простота - использует стандартный Android API
- ✅ Не требует QUERY_ALL_PACKAGES для запуска
- ✅ Поддерживает проекцию на второй дисплей

**Ограничения:**
- ⚠️ `getLaunchIntentForPackage()` возвращает только главную Activity
- ⚠️ Для запуска конкретной Activity нужен другой подход

### Для запуска конкретной Activity:

```java
// Прямой запуск Activity
Intent intent = new Intent();
intent.setComponent(new ComponentName(packageName, activityName));
intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
startActivity(intent);
```

**Этот подход требует:**
- QUERY_ALL_PACKAGES - для получения списка Activity
- Или знание точного имени Activity

---

## 🎯 Применение для Bridge Service

### Запуск Яндекс Навигатора:

```java
public class BridgeService {
    public void launchYandexNavigator() {
        // Способ 1: Через getLaunchIntentForPackage (проще)
        Intent intent = getPackageManager().getLaunchIntentForPackage("ru.yandex.yandexnavi");
        if (intent != null) {
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(intent);
        }
        
        // Способ 2: Прямой запуск MainActivity (если знаем имя)
        // Intent intent = new Intent();
        // intent.setComponent(new ComponentName(
        //     "ru.yandex.yandexnavi",
        //     "ru.yandex.yandexnavi.MainActivity"
        // ));
        // intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        // startActivity(intent);
    }
}
```

### Запуск на втором дисплее (для проекции):

```java
public void launchOnSecondDisplay(String packageName) {
    DisplayManager displayManager = (DisplayManager) getSystemService(Context.DISPLAY_SERVICE);
    Display[] displays = displayManager.getDisplays();
    
    if (displays.length > 1) {
        Intent intent = getPackageManager().getLaunchIntentForPackage(packageName);
        if (intent != null) {
            ActivityOptions options = ActivityOptions.makeBasic()
                .setLaunchDisplayId(displays[1].getDisplayId());
            startActivity(intent, options.toBundle());
        }
    }
}
```

---

### boot.java - Foreground Service

**Назначение:** Фоновый сервис для автозапуска и управления приложениями

**Ключевые особенности:**

1. **Foreground Service:**
   - Создает Notification Channel "NaviStartService"
   - Работает в фоне постоянно

2. **Broadcast Receiver:**
   ```java
   registerReceiver(this.receiver, new IntentFilter("desay.broadcast.map.meter.interaction"));
   ```
   - Слушает Broadcast Intent: `"desay.broadcast.map.meter.interaction"`
   - Это может быть способ коммуникации с системой автомобиля!

3. **Автозапуск:**
   - Получает package name из SharedPreferences (по умолчанию: "ru.yandex.yandexmaps")
   - Запускает приложение на указанном дисплее при старте

4. **Системные сообщения:**
   ```java
   void ping() {
       Intent intent = new Intent(GoNavi.SEND_SYSTEM_MESSAGE);
       intent.putExtra(GoNavi.MESSAGE_CODE, 207);
       intent.putExtra(GoNavi.MESSAGE_DATA, 0);
       sendBroadcast(intent);
   }
   ```

---

### GoNavi.java - Системные сообщения навигации

**Назначение:** Константы для отправки навигационных данных в систему

**Ключевые константы:**
```java
public static final String SEND_SYSTEM_MESSAGE = "turbodog.navigation.system.message";
public static final String MESSAGE_CODE = "CODE";
public static final String MESSAGE_DATA = "DATA";
public static final String MESSAGE_TURN_TYPE = "TURN_TYPE";
public static final String MESSAGE_TURN_DIST = "TURN_DIST";
public static final String MESSAGE_TURN_TIME = "TURN_TIME";
public static final String MESSAGE_REMAINING_DIST = "REMAINING_DIST";
public static final String MESSAGE_REMAINING_TIME = "REMAINING_TIME";
public static final String MESSAGE_ARRIVE_TIME = "ARRIVE_TIME";
public static final String MESSAGE_CURRENT_ROAD = "CURRENT_ROAD";
public static final String MESSAGE_NEXT_ROAD = "NEXT_ROAD";
```

**Формат Broadcast Intent:**
```java
Intent intent = new Intent("turbodog.navigation.system.message");
intent.putExtra("CODE", messageCode);
intent.putExtra("DATA", data);
intent.putExtra("TURN_TYPE", turnType);
intent.putExtra("TURN_DIST", turnDistance);
// ... и т.д.
sendBroadcast(intent);
```

**Важно:** Это формат, который использует TurboDog для отправки навигационных данных в систему!

---

## 🔑 Ключевые находки

### 1. Broadcast Intent для коммуникации с системой

**Входящие сообщения:**
- `"desay.broadcast.map.meter.interaction"` - слушает boot.java
- Возможно, это команды от системы автомобиля

**Исходящие сообщения:**
- `"turbodog.navigation.system.message"` - отправка навигационных данных
- Используется для передачи данных на приборную панель

### 2. Механизм запуска на разных дисплеях

```java
// Получение дисплеев
DisplayManager displayManager = (DisplayManager) getSystemService("display");
Display[] displays = displayManager.getDisplays();

// Запуск на втором дисплее (для проекции)
if (displays.length > 1) {
    Intent intent = getPackageManager().getLaunchIntentForPackage(packageName);
    ActivityOptions options = ActivityOptions.makeBasic()
        .setLaunchDisplayId(displays[1].getDisplayId());
    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
    startActivity(intent, options.toBundle());
}
```

### 3. Автозапуск через Foreground Service

- Сервис запускается при старте системы
- Читает package name из SharedPreferences
- Автоматически запускает приложение

---

## 📝 Следующие шаги

1. ✅ Изучен механизм запуска Activity
2. ✅ Изучен boot.java (автозапуск и Broadcast)
3. ✅ Изучен GoNavi.java (системные сообщения)
4. ⏳ Декомпилировать SVMedia для изучения выбора источников
5. ⏳ Изучить как система обрабатывает "turbodog.navigation.system.message"

---

**Дата:** 2024  
**Версия:** 1.0

