# Результаты анализа TurboDog APK

## Обнаруженные компоненты

### 1. Нативная библиотека

**Файл:** `libFunctionLayer.so`  
**Размер:** 14 MB  
**ABI:** arm64-v8a  
**Расположение:** `lib/arm64-v8a/libFunctionLayer.so`

**Важные функции (найдены в символах):**
- `CreateGL` - создание OpenGL контекста
- `CreateSecondaryGL` - создание вторичного OpenGL контекста для второго дисплея
- `AddSecondaryWndGL` - добавление второго окна (Presentation)
- `RenderGL` - рендеринг основного окна
- `RenderSecondaryWndGL` - рендеринг второго окна
- `DestroyGL` - уничтожение OpenGL контекста

**Другие функции:**
- `AstrobGPSPostNMEA` - отправка GPS данных в NMEA формате
- `AstrobDRPostIMU` - отправка IMU данных
- `OnInit`, `OnCreate`, `OnDestroy`, `OnResume`, `OnPause` - lifecycle методы
- `onProtocolRequest` - обработка протокольных запросов

### 2. JNI слой

**Java класс:** `com.astrob.navi.astrobnavilib.JavaToJni`

**Основные native методы:**

#### OpenGL функции:
```java
public static native int CreateGL(boolean z, boolean z2);
public static native int CreateSecondaryGL(int i, int i2, int i3, boolean z, int i4, int i5, int i6, int i7);
public static native void RenderGL();
public static native void RenderSecondaryWndGL(int i);
public static native void DestroyGL();
public static native int AddSecondaryWndGL(int i, int i2, int i3, int i4, int i5, boolean z, int i6, int i7, int i8, int i9, int i10);
public static native void DeleteSecondaryWndGL(int i);
public static native void SetSecondaryWndSize(int i, int i2, int i3, int i4, int i5, boolean z);
public static native void SetWindowSizeGL(int i, int i2);
```

#### GPS/IMU функции:
```java
public static native void AstrobGPSPostNMEA(byte[] bArr, int i);
public static native void AstrobDRPostIMU(byte[] bArr, int i, double d);
```

#### Lifecycle функции:
```java
public static native void OnCreate(boolean z);
public static native void OnDestroy();
public static native boolean OnInit(int i, int i2);
public static native void OnPause();
public static native void OnResume();
```

#### Протокол функции:
```java
public static native boolean onProtocolRequest(String str);
```

#### Другие функции:
```java
public static native void changeLanguage(int i);
public static native void setMeasureUnits(int i);
public static native int getMapVersion();
public static native String getMapVersion();
```

### 3. Обратный JNI (нативный код → Java)

**Java класс:** `com.astrob.navi.astrobnavilib.JniToJava`

**Метод:** `jniCallOnNaviDispatch(String str)`

```java
public void jniCallOnNaviDispatch(String str) {
    m.a().a.onNaviDispatch(str);
}
```

Это вызывается из нативного кода для отправки навигационных данных в Java.

### 4. Обработка навигационных данных

**Java класс:** `com.astrob.turbodog.H3NCustomCenter`

**Метод:** `onNaviDispatch(String str)`

Обрабатывает JSON строку с данными навигации и отправляет broadcast сообщения в систему.

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

### 5. SecondaryRenderThread

**Java класс:** `com.astrob.navi.astrobnavilib.SecondaryRenderThread`

Отдельный поток для рендеринга второго дисплея (Presentation окна).

**Ключевые методы:**
- `AddSecondaryWndGL()` - добавление второго окна
- `SetSecondaryWndSize()` - установка размера
- `RenderSecondaryWndGL()` - рендеринг второго окна

### 6. Стиль кода нативного кода

**Из анализа символов библиотеки:**

#### Соглашения об именовании:
- Функции с префиксом (например, `CreateGL`, `DestroyGL`)
- C++ стиль (видны символы типа `_Z10GetInterPt...` - C++ name mangling)
- Но также есть чистые C функции

#### Структуры данных:
- Видны символы типа `SMF_READER__`, `SMF_ROAM__`, `SMF_NAVTOR__`
- Используются структуры с префиксами

#### Многопоточность:
- `CreateThread` - создание потоков
- Вероятно используется pthread

### 7. Формат протокола

**Метод:** `onProtocolRequest(String str)`

Все запросы к нативному коду передаются через JSON строки.

**Примеры запросов:**
- Начало навигации: `{"request": {"id": 27, "response": 1}}`
- Остановка навигации: `{"request": {"id": 28, "response": 1}}`
- Установка пункта назначения: `{"request": {"id": 25, "response": 1, "data": {"destPoint": {"name": "...", "lon": ..., "lat": ...}}}}`

**ID запросов:**
- 1-3: Zoom карты
- 4-9: Перспектива карты
- 10: DN Mode (day/night)
- 11: Exit App
- 12: Revert Data
- 13: Power Off
- 14: Save User Data
- 15: Back to Main Map
- 16: Back Car Position
- 17: Collect Current Position
- 19: Goto Favorite List
- 20: Move Map
- 21: Search POI
- 22: Search Nearby
- 23: Request Current Location
- 24: Search Nearby (с GPS)
- 25: Set Navi Destination
- 26: Goto Favorite/Home/Company
- 27: Start Navigation
- 28: End Navigation
- 29: Repeat Navi Voice
- 30: Route Overview
- 31: Change Route Option
- 32: Set Speeding Alert
- 33: Set Speak Mute
- 34: Resume Navi
- 36-38: VR POI List
- 39: Request Favorite Point
- 40: Request Next Road
- 41: Add Navi Waypoint
- 42: Goto Search Dialog
- 43: Continue Last Navi

## Архитектура TurboDog

```
┌─────────────────────────────────────────┐
│  Java Layer (Android)                   │
│                                         │
│  - WelcomeActivity                      │
│  - H3NCustomCenter                      │
│  - JavaToJni                            │
│  - JniToJava                            │
│  - SecondaryRenderThread                │
└────────────┬────────────────────────────┘
             │ JNI
             ▼
┌─────────────────────────────────────────┐
│  Native C/C++ Layer                     │
│  (libFunctionLayer.so)                  │
│                                         │
│  - CreateGL / CreateSecondaryGL        │
│  - RenderGL / RenderSecondaryWndGL     │
│  - AstrobGPSPostNMEA                   │
│  - onProtocolRequest                   │
│  - jniCallOnNaviDispatch               │
└────────────┬────────────────────────────┘
             │ OpenGL ES
             ▼
┌─────────────────────────────────────────┐
│  GPU (Hardware Acceleration)            │
│                                         │
│  - OpenGL ES rendering                  │
│  - Secondary window rendering           │
└─────────────────────────────────────────┘
```

## Стиль кода TurboDog

### 1. Соглашения об именовании

**Функции:**
- Префикс для функций (например, `CreateGL`, `DestroyGL`, `RenderGL`)
- CamelCase для методов
- Префиксы для типов модулей

**Структуры:**
- Префиксы для структур (например, `SMF_READER__`, `SMF_ROAM__`)
- Вероятно венгерская нотация в коде

### 2. Управление памятью

- C/C++ стиль (malloc/free или new/delete)
- Вероятно собственные функции управления памятью

### 3. Многопоточность

- Отдельный поток для второго дисплея (SecondaryRenderThread)
- Вероятно pthread для потоков
- Mutex для синхронизации

### 4. Протокол обмена данными

- JSON для обмена данными между Java и Native
- NMEA для GPS данных
- Binary для IMU данных

## Выводы для нашего проекта

### 1. Структура JNI

**Нужно создать:**
```java
// TiggoJavaToJni.java (аналог JavaToJni)
public class TiggoJavaToJni {
    static {
        System.loadLibrary("tiggo_navigator");
    }
    
    // OpenGL функции
    public static native int CreateGL(boolean simplified);
    public static native void RenderGL();
    public static native void DestroyGL();
    
    // Данные от Yandex
    public static native void OnYandexSpeedLimit(int speedLimitKmh, String text);
    public static native void OnYandexRoute(double[] routePoints, int distance, int time);
    // ...
}
```

### 2. Обратный JNI

**Нужно создать:**
```java
// TiggoJniToJava.java (аналог JniToJava)
public class TiggoJniToJava {
    public void jniCallOnNavigationData(String json) {
        // Обработка данных от нативного кода
        // Отправка broadcast
    }
}
```

### 3. Стиль нативного кода

**Использовать:**
- Префиксы для функций: `Tiggo_CreateGL()`, `Tiggo_RenderGL()`
- Структуры с префиксами: `TIGGO_ENGINE`, `TIGGO_ROUTE`
- Венгерская нотация в коде
- C стиль (не C++)

### 4. Интеграция

**План:**
1. Расширить существующий JavaToJni класс (если возможно)
2. Или создать параллельный TiggoJavaToJni класс
3. Использовать тот же протокол JSON для обмена данными
4. Использовать тот же формат broadcast сообщений

## Следующие шаги

1. ✅ Анализ завершен
2. ⏳ Создать JNI слой в стиле TurboDog
3. ⏳ Реализовать OpenGL функции (CreateGL, RenderGL)
4. ⏳ Реализовать обработку данных от Yandex
5. ⏳ Интегрировать с существующим кодом TurboDog

