# План анализа TurboDog - Понимание архитектуры и стиля кода

## Цель

Понять архитектуру и стиль кода TurboDog, чтобы дописывать наши компоненты на C в том же стиле и интегрировать с существующим кодом.

## Шаг 1: Извлечение и анализ TurboDog APK

### 1.1 Найти TurboDog APK

```bash
# TurboDog APK должен быть здесь:
ls apks/com.astrob.turbodog.apk
# или
ls development/apk/com.astrob.turbodog.apk
```

### 1.2 Декомпиляция APK

```bash
# Используем JADX для декомпиляции Java кода
jadx -d turbodog_decompiled apks/com.astrob.turbodog.apk

# Или APKTool для извлечения ресурсов и нативных библиотек
apktool d apks/com.astrob.turbodog.apk -o turbodog_extracted
```

### 1.3 Извлечение нативных библиотек (.so)

```bash
# После декомпиляции ищем нативные библиотеки
find turbodog_extracted -name "*.so"
# Обычно находятся в:
# turbodog_extracted/lib/armeabi-v7a/
# turbodog_extracted/lib/arm64-v8a/
```

### 1.4 Анализ нативных библиотек

```bash
# Используем readelf для анализа библиотек
readelf -h libturbodog.so  # или какое имя у библиотеки
readelf -s libturbodog.so  # символы

# Используем nm для просмотра символов
nm -D libturbodog.so

# Используем objdump для дизассемблирования (опционально)
objdump -d libturbodog.so > turbodog_disasm.txt
```

### 1.5 Поиск исходного кода (если есть)

```bash
# Ищем C/C++ исходники в декомпилированном проекте
find turbodog_decompiled -name "*.c"
find turbodog_decompiled -name "*.cpp"
find turbodog_decompiled -name "*.h"
```

## Шаг 2: Анализ архитектуры

### 2.1 JNI слой

**Ищем в Java коде:**
```java
// Ищем классы с native методами
grep -r "native" turbodog_decompiled/

// Примеры:
// class JniToJava {
//     public native void jniCallOnNaviDispatch(String str);
// }

// Ищем загрузку библиотек
grep -r "System.loadLibrary" turbodog_decompiled/
// Обычно: System.loadLibrary("turbodog");
```

### 2.2 Нативные функции

**Ищем символы в .so:**
```bash
# JNI функции обычно имеют имена типа:
# Java_com_astrob_turbodog_ClassName_methodName
nm -D libturbodog.so | grep Java_

# Или ищем общие функции:
nm -D libturbodog.so | grep -i "turbodog\|navi\|render\|gl"
```

### 2.3 Структура классов в Java

**Анализируем Java классы:**
```java
// Из документации знаем:
// - CTurboDogDlg - основной класс навигации (нативный)
// - TurboDog_CreateGL - создание OpenGL контекста
// - TurboDog_CreateNVG - создание NanoVG
// - SecondaryRenderThread - отдельный поток рендеринга

// Ищем в декомпилированном коде:
grep -r "CTurboDogDlg\|TurboDog_CreateGL\|SecondaryRenderThread" turbodog_decompiled/
```

### 2.4 OpenGL и NanoVG

**Ищем использование OpenGL/NanoVG:**
```bash
# В нативной библиотеке ищем OpenGL функции
nm -D libturbodog.so | grep -i "gl\|egl\|nvg"

# В Java коде ищем упоминания
grep -r -i "opengl\|glsurface\|nvg\|nano" turbodog_decompiled/
```

## Шаг 3: Понимание стиля кода

### 3.1 Соглашения об именовании

**Нативный код (C):**
```c
// TurboDog использует стиль:
// - CTurboDogDlg - классы с префиксом C
// - TurboDog_CreateGL - функции с префиксом TurboDog_
// - m_pSomething - указатели (Hungarian notation?)

// Примеры:
// CTurboDogDlg* pDlg = ...;
// TurboDog_CreateGL(pDlg);
// SecondaryRenderThread* pThread = ...;
```

### 3.2 Структура данных

**Анализируем структуры данных:**
```c
// Ищем определения структур (если есть заголовки)
// или анализируем использование в JNI

// Типичные структуры:
typedef struct {
    int turnType;
    int turnDist;
    int turnTime;
    char* curRoad;
    char* nextRoad;
} NaviData;

typedef struct {
    double latitude;
    double longitude;
    float bearing;
    float speed;
} GpsData;
```

### 3.3 Управление памятью

**Понимаем паттерны:**
```c
// TurboDog вероятно использует:
// - malloc/free для динамической памяти
// - Собственные функции управления памятью
// - Возможно пулы памяти для оптимизации

// Примеры:
// NaviData* pData = (NaviData*)malloc(sizeof(NaviData));
// // использование
// free(pData);
```

### 3.4 Многопоточность

**Анализируем использование потоков:**
```c
// TurboDog использует:
// - SecondaryRenderThread для второго дисплея
// - pthread вероятно для потоков
// - Mutex для синхронизации

// Примеры:
// pthread_t renderThread;
// pthread_create(&renderThread, NULL, RenderThreadFunc, NULL);
// pthread_mutex_t g_dataMutex = PTHREAD_MUTEX_INITIALIZER;
```

## Шаг 4: Интеграция с существующим кодом

### 4.1 Структура проекта

**План интеграции:**
```
turbodog_existing/
├── native/              # Существующий нативный код TurboDog
│   ├── navigator/      # Навигационный движок
│   ├── render/         # Рендеринг
│   └── jni/            # JNI слой
│
└── java/               # Java код TurboDog
    ├── com/astrob/turbodog/
    └── ...

tiggo_extension/
├── native/              # НАШ новый код на C
│   ├── yandex_bridge/  # Мост к Yandex (новый)
│   ├── data_converter/ # Конвертер данных (новый)
│   └── jni/            # Новые JNI функции (новый)
│
└── java/               # Новый Java код
    └── com/tiggo/navigator/
```

### 4.2 Стиль кода - Соглашения

**Используем тот же стиль, что и TurboDog:**
```c
// ✅ Стиль TurboDog (используем)
typedef struct {
    int value;
    char* name;
} TiggoData;

void Tiggo_Initialize(TiggoEngine* pEngine);
void Tiggo_Shutdown(TiggoEngine* pEngine);
void Tiggo_OnYandexData(TiggoEngine* pEngine, const YandexData* pData);

// ❌ НЕ используем (C++ стиль)
class TiggoEngine {
    void Initialize();
    void OnYandexData(const YandexData& data);
};
```

### 4.3 Интеграция через JNI

**Расширяем существующий JNI слой:**
```java
// Существующий код TurboDog:
public class JniToJava {
    public native void jniCallOnNaviDispatch(String str);
}

// НАШ новый код (добавляем):
public class TiggoJniBridge {
    // Новые функции для Yandex данных
    public native void nativeOnYandexSpeedLimit(int speedLimitKmh);
    public native void nativeOnYandexRoute(RouteData route);
    public native void nativeOnYandexLocation(LocationData location);
}
```

## Шаг 5: План действий

### День 1: Анализ TurboDog
- [ ] Декомпилировать TurboDog APK
- [ ] Извлечь нативные библиотеки (.so)
- [ ] Проанализировать символы в библиотеках
- [ ] Найти JNI функции
- [ ] Найти структуры данных

### День 2: Понимание архитектуры
- [ ] Проанализировать Java код (JniToJava, CTurboDogDlg и т.д.)
- [ ] Понять структуру навигационного движка
- [ ] Понять структуру рендеринга
- [ ] Понять многопоточность

### День 3: Определение стиля кода
- [ ] Соглашения об именовании
- [ ] Структуры данных
- [ ] Управление памятью
- [ ] Паттерны кода

### День 4: Создание плана интеграции
- [ ] Определить точки интеграции
- [ ] Создать структуру нового кода
- [ ] Определить API между старым и новым кодом

### День 5: Начало реализации
- [ ] Создать базовую структуру проекта
- [ ] Реализовать базовые функции в стиле TurboDog
- [ ] Интегрировать с существующим JNI слоем

## Инструменты для анализа

### 1. JADX
```bash
# Декомпиляция Java кода
jadx -d output apk_file.apk
```

### 2. APKTool
```bash
# Извлечение ресурсов и библиотек
apktool d apk_file.apk -o output
```

### 3. readelf / nm / objdump
```bash
# Анализ нативных библиотек
readelf -h lib.so
nm -D lib.so
objdump -d lib.so
```

### 4. IDA Pro / Ghidra (опционально)
```bash
# Глубокий анализ нативного кода
# IDA Pro - коммерческий
# Ghidra - бесплатный от NSA
```

## Результаты анализа

После анализа у нас должно быть:

1. **Структура нативного кода TurboDog:**
   - Какие функции есть
   - Какие структуры данных используются
   - Как организована память

2. **Стиль кода:**
   - Соглашения об именовании
   - Паттерны кода
   - Управление памятью

3. **Точки интеграции:**
   - Где можно добавить новый код
   - Как интегрироваться с существующим кодом
   - Как расширить JNI слой

4. **План реализации:**
   - Структура проекта
   - API между старым и новым кодом
   - Этапы разработки

## Следующие шаги

1. **Найти TurboDog APK** в проекте
2. **Декомпилировать** его
3. **Проанализировать** нативный код
4. **Понять стиль** и архитектуру
5. **Создать план интеграции**
6. **Начать реализацию** в том же стиле

