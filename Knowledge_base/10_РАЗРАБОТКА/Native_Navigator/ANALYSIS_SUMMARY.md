# Итоговый отчет анализа TurboDog

## ✅ Что найдено

### 1. Нативная библиотека

**Файл:** `libFunctionLayer.so` (14 MB)  
**Тип:** C/C++ нативный код  
**Использование:** OpenGL ES рендеринг, навигационный движок

**Ключевые функции:**
- `CreateGL` / `CreateSecondaryGL` - создание OpenGL контекстов
- `RenderGL` / `RenderSecondaryWndGL` - рендеринг окон
- `AstrobGPSPostNMEA` - отправка GPS данных
- `onProtocolRequest` - обработка JSON протокола
- `jniCallOnNaviDispatch` - отправка данных обратно в Java

### 2. JNI слой

**Java класс:** `com.astrob.navi.astrobnavilib.JavaToJni`

**Все функции native:**
```java
// OpenGL
CreateGL(boolean, boolean)
CreateSecondaryGL(int, int, int, boolean, int, int, int, int)
RenderGL()
RenderSecondaryWndGL(int)
DestroyGL()
AddSecondaryWndGL(int, int, int, int, int, boolean, int, int, int, int, int)
DeleteSecondaryWndGL(int)
SetSecondaryWndSize(int, int, int, int, int, boolean)
SetWindowSizeGL(int, int)

// GPS/IMU
AstrobGPSPostNMEA(byte[], int)
AstrobDRPostIMU(byte[], int, double)

// Lifecycle
OnCreate(boolean)
OnDestroy()
OnInit(int, int)
OnPause()
OnResume()

// Протокол
onProtocolRequest(String) - JSON протокол для всех запросов
```

### 3. Обратный JNI (нативный код → Java)

**Java класс:** `com.astrob.navi.astrobnavilib.JniToJava`

**Метод:** `jniCallOnNaviDispatch(String json)`

Вызывается из нативного кода для отправки навигационных данных:
```java
public void jniCallOnNaviDispatch(String str) {
    m.a().a.onNaviDispatch(str);
}
```

### 4. Обработка данных

**Java класс:** `com.astrob.turbodog.H3NCustomCenter`

**Метод:** `onNaviDispatch(String json)`

Обрабатывает JSON и отправляет broadcast:
- Парсит JSON: `{"result": {"msgType": 1, "id": 124, "data": {...}}}`
- При `id == 124` извлекает навигационные данные
- Вызывает `onUptNavInfo()` и отправляет broadcast

### 5. SecondaryRenderThread

**Java класс:** `com.astrob.navi.astrobnavilib.SecondaryRenderThread`

**Функции:**
- Отдельный поток для рендеринга второго дисплея
- Использует EGL для OpenGL контекста
- Вызывает `JavaToJni.AddSecondaryWndGL()` для создания окна
- Вызывает `JavaToJni.RenderSecondaryWndGL()` для рендеринга

## 📋 Стиль кода TurboDog

### 1. Нативный код

**Соглашения:**
- Функции с префиксами: `CreateGL`, `DestroyGL`, `RenderGL`
- C/C++ код (видны C++ символы с name mangling)
- Структуры с префиксами: `SMF_READER__`, `SMF_ROAM__`

**Стиль:**
- Вероятно венгерская нотация внутри кода
- Префиксы для типов
- C/C++ смешанный стиль

### 2. Протокол обмена данными

**Формат:** JSON строки

**Запросы (Java → Native):**
```json
{
  "request": {
    "id": 25,
    "response": 1,
    "data": {
      "destPoint": {
        "name": "Москва",
        "lon": 37.6173,
        "lat": 55.7558
      }
    }
  }
}
```

**Ответы (Native → Java):**
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
      "curName": "Ленинградский проспект",
      "nextName": "Тверская улица",
      "roadCls": 1,
      "speed": 60
    }
  }
}
```

### 3. Многопоточность

- Отдельный поток для рендеринга второго дисплея
- Использует EGL для OpenGL контекста
- Синхронизация через mutex/condition variable

## 🎯 План интеграции

### 1. Структура проекта

**Интеграция с TurboDog:**
```
tiggo_navigator/
├── native/
│   ├── turbodog_existing/    # Существующий код TurboDog (НЕ ТРОГАЕМ)
│   │   └── libFunctionLayer.so
│   │
│   └── tiggo_extension/      # НАШ новый код на C
│       ├── engine/
│       │   ├── tiggo_engine.h
│       │   └── tiggo_engine.c
│       │
│       ├── render/
│       │   ├── render_gl.h
│       │   └── render_gl.c
│       │
│       └── jni/
│           └── jni_tiggo_bridge.c
│
└── java/
    ├── com/astrob/turbodog/  # Существующий код (НЕ ТРОГАЕМ)
    │
    └── com/tiggo/navigator/  # НАШ новый код
        ├── TiggoJavaToJni.java      # Аналог JavaToJni
        ├── TiggoJniToJava.java      # Аналог JniToJava
        ├── YandexMapKitBridge.java  # Мост к Yandex
        └── TiggoSecondaryRenderThread.java  # Аналог SecondaryRenderThread
```

### 2. Стиль кода

**Использовать тот же стиль, что и TurboDog:**

```c
// Префиксы для функций
BOOL Tiggo_CreateGL(BOOL bSimplified);
void Tiggo_RestroyGL(void);
void Tiggo_RenderGL(void);
void Tiggo_RenderSecondaryWndGL(int nIndex);

// Префиксы для структур
typedef struct {
    int m_nValue;
    float m_fSpeed;
    BOOL m_bInitialized;
} CTiggoEngine;

// Венгерская нотация
int nValue;
float fSpeed;
BOOL bFlag;
char* pName;
```

### 3. JNI слой

**Создать аналогичный JavaToJni:**
```java
public class TiggoJavaToJni {
    static {
        System.loadLibrary("tiggo_navigator");
    }
    
    // OpenGL функции (в стиле TurboDog)
    public static native int CreateGL(boolean simplified);
    public static native int CreateSecondaryGL(int w, int h, int index, boolean simplified, ...);
    public static native void RenderGL();
    public static native void RenderSecondaryWndGL(int index);
    public static native void DestroyGL();
    
    // Данные от Yandex
    public static native void OnYandexSpeedLimit(int speedLimitKmh, String text);
    public static native void OnYandexRoute(double[] routePoints, int distance, int time);
    public static native void OnYandexLocation(double lat, double lon, float bearing, String road);
}
```

**Создать обратный JNI (JniToJava):**
```java
public class TiggoJniToJava {
    // Вызывается из нативного кода
    public void jniCallOnNavigationData(String json) {
        // Парсим JSON и отправляем broadcast
        // В формате, совместимом с TurboDog
    }
}
```

### 4. Протокол обмена данными

**Использовать JSON (как TurboDog):**

**Запросы к Yandex:**
```json
{
  "request": {
    "id": 201,
    "type": "yandex_route",
    "data": {
      "from": {"lat": 55.7558, "lon": 37.6173},
      "to": {"lat": 59.9343, "lon": 30.3351}
    }
  }
}
```

**Ответы от Yandex:**
```json
{
  "result": {
    "msgType": 1,
    "id": 201,
    "data": {
      "speedLimit": 60,
      "maneuver": {...},
      "route": {...}
    }
  }
}
```

### 5. OpenGL функции

**Реализовать в стиле TurboDog:**
```c
// tiggo_render_gl.c

BOOL Tiggo_CreateGL(BOOL bSimplified) {
    // Инициализация OpenGL контекста
    // Аналогично CreateGL в TurboDog
}

void Tiggo_RenderGL(void) {
    // Рендеринг основного окна
    // Полноценная карта
}

void Tiggo_RenderSecondaryWndGL(int nIndex) {
    // Рендеринг второго окна (Presentation)
    // Упрощенная карта (только маршрут, камеры, события)
}

void Tiggo_DestroyGL(void) {
    // Очистка OpenGL ресурсов
}
```

## 📊 Сравнение с нашим кодом

| Аспект | TurboDog | Наш проект | Статус |
|--------|----------|------------|--------|
| Язык | C/C++ | C | ✅ Совпадает |
| Стиль | Префиксы функций | Префиксы функций | ✅ Совпадает |
| JNI | JavaToJni | TiggoJavaToJni | ✅ Аналог создан |
| Обратный JNI | JniToJava | TiggoJniToJava | ⏳ Нужно создать |
| OpenGL | CreateGL/RenderGL | Tiggo_CreateGL/RenderGL | ⏳ Нужно реализовать |
| Протокол | JSON | JSON | ✅ Совпадает |
| Render Thread | SecondaryRenderThread | TiggoSecondaryRenderThread | ⏳ Нужно создать |

## 🚀 Следующие шаги

1. ✅ **Анализ завершен**
2. ✅ **Поняли архитектуру TurboDog**
3. ✅ **Поняли стиль кода**
4. ⏳ **Создать JNI слой в стиле TurboDog**
5. ⏳ **Реализовать OpenGL функции**
6. ⏳ **Реализовать SecondaryRenderThread**
7. ⏳ **Интегрировать с Yandex MapKit**

## 📁 Файлы анализа

- `ANALYSIS_RESULTS.md` - Детальные результаты анализа
- `extracted/` - Извлеченный APK
- `decompiled/` - Декомпилированный Java код
- `analysis_report.txt` - Краткий отчет

## 🎯 Выводы

1. **TurboDog использует C/C++** с нативными функциями
2. **Стиль кода:** Префиксы для функций, структуры с префиксами, вероятно венгерская нотация
3. **Протокол:** JSON для обмена данными между Java и Native
4. **OpenGL:** Отдельные функции для основного и второго дисплея
5. **Потоки:** Отдельный поток для рендеринга второго дисплея

**Наш проект уже соответствует стилю TurboDog:**
- ✅ Используем C (не C++)
- ✅ Префиксы функций (`Tiggo_*`)
- ✅ Префиксы структур (`C*`)
- ✅ Венгерская нотация

**Что нужно сделать:**
1. Создать JNI слой (`TiggoJavaToJni.java`)
2. Реализовать OpenGL функции (`Tiggo_CreateGL`, `Tiggo_RenderGL`)
3. Создать SecondaryRenderThread аналог
4. Интегрировать с Yandex MapKit

