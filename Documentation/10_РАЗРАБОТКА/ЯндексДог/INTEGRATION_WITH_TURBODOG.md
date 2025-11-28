# Интеграция нового кода с TurboDog - План

## Принцип работы

**Вместо замены TurboDog, мы:**
1. Берем существующий нативный код TurboDog (C)
2. Дописываем наши компоненты на C в том же стиле
3. Интегрируем через существующий JNI слой
4. Используем те же паттерны и архитектуру

## Архитектура интеграции

```
┌─────────────────────────────────────────────────────────┐
│  Android Java Layer                                      │
│                                                          │
│  ┌────────────────────┐  ┌──────────────────────────┐ │
│  │ TurboDog Java      │  │ Tiggo Extension Java     │ │
│  │ (существующий)     │  │ (новый)                  │ │
│  └────────┬───────────┘  └────────────┬─────────────┘ │
│           │                            │               │
│           └────────────┬───────────────┘               │
│                        │ JNI                           │
└────────────────────────┼───────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Native C Layer                                         │
│                                                          │
│  ┌────────────────────┐  ┌──────────────────────────┐ │
│  │ TurboDog Native    │  │ Tiggo Extension Native   │ │
│  │ (существующий)     │  │ (новый, в том же стиле)  │ │
│  │                    │  │                          │ │
│  │ - NavigatorEngine  │  │ - YandexBridge           │ │
│  │ - RenderEngine     │  │ - DataConverter          │ │
│  │ - JNI layer        │  │ - JNI extension          │ │
│  └────────┬───────────┘  └────────────┬─────────────┘ │
│           │                            │               │
│           └────────────┬───────────────┘               │
│                        │ API                           │
│                        ▼                               │
│              ┌───────────────────┐                     │
│              │ Shared Data Layer │                     │
│              │ (NavigationState) │                     │
│              └───────────────────┘                     │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Yandex MapKit   │
                │ (Java API)      │
                └─────────────────┘
```

## Стиль кода TurboDog

### 1. Соглашения об именовании

**Классы/Структуры:**
```c
// Префикс C для классов/структур
typedef struct {
    int m_nValue;        // m_ для членов, n для int
    char* m_pName;       // p для указателей
    float m_fSpeed;      // f для float
} CTiggoEngine;

// Создание/уничтожение
CTiggoEngine* Tiggo_CreateEngine();
void Tiggo_DestroyEngine(CTiggoEngine* pEngine);
```

**Функции:**
```c
// Префикс модуля для функций
// TurboDog_* для существующих
// Tiggo_* для наших новых

// Инициализация
int Tiggo_Initialize(CTiggoEngine* pEngine);
void Tiggo_Shutdown(CTiggoEngine* pEngine);

// Обновление
void Tiggo_Update(CTiggoEngine* pEngine, float fDeltaTime);

// Данные
void Tiggo_OnYandexSpeedLimit(CTiggoEngine* pEngine, int nSpeedLimitKmh);
void Tiggo_OnYandexRoute(CTiggoEngine* pEngine, const RouteData* pRoute);
```

**Переменные:**
```c
// Hungarian notation
int nValue;              // n для int
float fValue;            // f для float
double dValue;           // d для double
char* pName;             // p для указателя
const char* pcName;      // pc для const pointer
BOOL bFlag;              // b для bool
```

### 2. Структуры данных

**Навигационные данные:**
```c
// Используем тот же формат, что и TurboDog
typedef struct {
    int nTurnType;       // 0=STRAIGHT, 1=LEFT, 2=RIGHT, 3=UTURN
    int nTurnDist;       // метры
    int nTurnTime;       // секунды
    int nRemainDist;     // метры
    int nRemainTime;     // секунды
    char* pcCurRoad;     // текущая дорога
    char* pcNextRoad;    // следующая дорога
} NaviData;

// GPS данные
typedef struct {
    double dLatitude;
    double dLongitude;
    float fBearing;
    float fSpeed;
} GpsData;

// Ограничение скорости
typedef struct {
    int nValueKmh;
    char* pcText;
    BOOL bValid;
} SpeedLimit;
```

### 3. Управление памятью

```c
// Собственные функции управления памятью (как в TurboDog)
void* Tiggo_Malloc(size_t nSize);
void Tiggo_Free(void* pPtr);

// Использование
NaviData* pData = (NaviData*)Tiggo_Malloc(sizeof(NaviData));
if (pData != NULL) {
    // использование
    Tiggo_Free(pData);
}
```

### 4. Многопоточность

```c
// Используем pthread (как TurboDog)
#include <pthread.h>

// Mutex для синхронизации
static pthread_mutex_t g_dataMutex = PTHREAD_MUTEX_INITIALIZER;

// Блокировка/разблокировка
void Tiggo_LockData() {
    pthread_mutex_lock(&g_dataMutex);
}

void Tiggo_UnlockData() {
    pthread_mutex_unlock(&g_dataMutex);
}

// Поток рендеринга (как SecondaryRenderThread в TurboDog)
typedef struct {
    CTiggoEngine* pEngine;
    BOOL bRunning;
} RenderThreadData;

void* RenderThreadFunc(void* pArg) {
    RenderThreadData* pData = (RenderThreadData*)pArg;
    while (pData->bRunning) {
        Tiggo_RenderFrame(pData->pEngine);
    }
    return NULL;
}
```

## Интеграция с существующим кодом

### 1. Расширение JNI слоя

**Существующий код TurboDog:**
```java
// com.astrob.turbodog.JniToJava
public class JniToJava {
    public native void jniCallOnNaviDispatch(String str);
}
```

**Наш новый код (расширяем):**
```java
// com.tiggo.navigator.TiggoJniBridge
public class TiggoJniBridge {
    // Инициализация нашего расширения
    public static native boolean nativeInitTiggo();
    
    // Данные от Yandex (вызываются из Java)
    public static native void nativeOnYandexSpeedLimit(int speedLimitKmh, String text);
    public static native void nativeOnYandexManeuver(int type, int distance, String title, String subtitle);
    public static native void nativeOnYandexRoute(double[] routePoints, int distance, int time);
    public static native void nativeOnYandexLocation(double lat, double lon, float bearing, String roadName);
    
    // Обновление (вызывается из Java каждый кадр)
    public static native void nativeUpdateTiggo(float deltaTime);
    
    // Получение данных (вызываются из нативного кода)
    public static void onNavigationDataChanged(NaviData data) {
        // Отправляем broadcast (совместимый с TurboDog)
        Intent intent = new Intent("turbodog.navigation.system.message");
        intent.putExtra("CODE", 201);
        intent.putExtra("TURN_TYPE", data.turnType);
        // ... и т.д.
        context.sendBroadcast(intent);
    }
}
```

**JNI реализация (нативный C):**
```c
// jni/jni_tiggo_bridge.c
#include <jni.h>
#include "tiggo_engine.h"

// Глобальный указатель на движок
static CTiggoEngine* g_pTiggoEngine = NULL;

JNIEXPORT jboolean JNICALL
Java_com_tiggo_navigator_TiggoJniBridge_nativeInitTiggo(JNIEnv* env, jclass clazz) {
    if (g_pTiggoEngine != NULL) {
        return JNI_TRUE;
    }
    
    g_pTiggoEngine = Tiggo_CreateEngine();
    if (g_pTiggoEngine == NULL) {
        return JNI_FALSE;
    }
    
    if (!Tiggo_Initialize(g_pTiggoEngine)) {
        Tiggo_DestroyEngine(g_pTiggoEngine);
        g_pTiggoEngine = NULL;
        return JNI_FALSE;
    }
    
    return JNI_TRUE;
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJniBridge_nativeOnYandexSpeedLimit(
    JNIEnv* env, jclass clazz, jint speedLimitKmh, jstring text) {
    
    if (g_pTiggoEngine == NULL) return;
    
    const char* pcText = (*env)->GetStringUTFChars(env, text, NULL);
    Tiggo_OnYandexSpeedLimit(g_pTiggoEngine, speedLimitKmh, pcText);
    (*env)->ReleaseStringUTFChars(env, text, pcText);
}

// ... остальные JNI функции
```

### 2. Интеграция с существующим NavigationEngine

**Наш код использует те же структуры данных:**
```c
// tiggo_engine.c
#include "turbodog_navigator.h"  // Используем существующие определения

// Интеграция с существующим движком TurboDog
void Tiggo_OnYandexSpeedLimit(CTiggoEngine* pEngine, int nSpeedLimitKmh, const char* pcText) {
    // Конвертируем в формат TurboDog
    SpeedLimit limit;
    limit.nValueKmh = nSpeedLimitKmh;
    limit.pcText = (char*)pcText;
    limit.bValid = TRUE;
    
    // Используем существующие функции TurboDog для обновления
    // (если есть доступ) или сохраняем в общую структуру данных
    
    // Отправляем через существующий механизм
    NaviData data;
    // ... заполняем данные
    
    // Вызываем существующую функцию TurboDog (если доступна)
    // или используем наш callback для отправки broadcast
    Tiggo_NotifyNavigationDataChanged(&data);
}
```

### 3. Использование существующего RenderEngine

**Если возможно, используем существующий рендеринг:**
```c
// Расширяем существующий рендеринг TurboDog
void Tiggo_RenderFrame(CTiggoEngine* pEngine) {
    // Используем существующие функции TurboDog
    // TurboDog_BeginRender(pEngine);
    
    // Наш дополнительный рендеринг (если нужно)
    Tiggo_RenderYandexData(pEngine);
    
    // TurboDog_EndRender(pEngine);
}
```

## Структура проекта

```
tiggo_navigator_integrated/
├── native/
│   ├── turbodog_existing/      # Существующий код TurboDog (НЕ ТРОГАЕМ)
│   │   ├── navigator/
│   │   ├── render/
│   │   └── jni/
│   │
│   └── tiggo_extension/        # НАШ новый код на C
│       ├── engine/
│       │   ├── tiggo_engine.h
│       │   ├── tiggo_engine.c
│       │   └── yandex_bridge.c
│       │
│       ├── data/
│       │   ├── data_converter.h
│       │   └── data_converter.c
│       │
│       └── jni/
│           ├── jni_tiggo_bridge.c
│           └── jni_utils.h
│
└── java/
    ├── com/astrob/turbodog/    # Существующий Java код (НЕ ТРОГАЕМ)
    │
    └── com/tiggo/navigator/    # НАШ новый Java код
        ├── TiggoJniBridge.java
        ├── YandexMapKitBridge.java
        └── TiggoNavigationService.java
```

## Этапы разработки

### Этап 1: Анализ TurboDog
- [ ] Декомпилировать TurboDog APK
- [ ] Найти нативные библиотеки (.so)
- [ ] Проанализировать JNI функции
- [ ] Понять структуры данных
- [ ] Понять стиль кода

### Этап 2: Создание базовой структуры
- [ ] Создать структуру проекта
- [ ] Определить API интеграции
- [ ] Создать базовые заголовки

### Этап 3: Реализация Yandex Bridge
- [ ] Реализовать tiggo_engine.c
- [ ] Реализовать yandex_bridge.c
- [ ] Реализовать data_converter.c
- [ ] Интегрировать с существующим кодом

### Этап 4: JNI слой
- [ ] Реализовать jni_tiggo_bridge.c
- [ ] Создать Java классы
- [ ] Интегрировать с Yandex MapKit

### Этап 5: Тестирование
- [ ] Тестирование интеграции
- [ ] Тестирование производительности
- [ ] Оптимизация

