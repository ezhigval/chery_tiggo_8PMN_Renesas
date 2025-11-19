# Нативный навигатор на C/C++ с данными Yandex - Архитектура

## Цель проекта

Создать нативный навигатор на C/C++, максимально похожий на TurboDog, но использующий данные Yandex MapKit API.

**Преимущества:**
- ✅ Высокая производительность (нативный код)
- ✅ Аппаратное ускорение (OpenGL ES)
- ✅ Полный контроль над рендерингом
- ✅ Минимальное потребление батареи
- ✅ Оптимизация для автомобильных систем

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│  Android Java Layer                                         │
│  - MainActivity (UI)                                        │
│  - NavigationService (управление)                           │
│  - YandexMapKitBridge (JNI)                                │
└──────────────┬──────────────────────────────────────────────┘
               │ JNI
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Native C/C++ Core (libtiggo_navigator.so)                 │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Navigation Engine (навигационный движок)            │ │
│  │  - Route calculation                                  │ │
│  │  - GPS processing                                     │ │
│  │  - Navigation state                                   │ │
│  └───────────────────┬───────────────────────────────────┘ │
│                      │                                      │
│  ┌───────────────────▼───────────────────────────────────┐ │
│  │  Render Engine (рендеринг карты)                      │ │
│  │  - OpenGL ES renderer                                 │ │
│  │  - Map tile rendering                                 │ │
│  │  - Route polyline rendering                           │ │
│  │  - UI elements rendering                              │ │
│  └───────────────────┬───────────────────────────────────┘ │
│                      │                                      │
│  ┌───────────────────▼───────────────────────────────────┐ │
│  │  Async Task Queue (асинхронная обработка)             │ │
│  │  - Thread pool                                        │ │
│  │  - Task queue                                         │ │
│  │  - Async data loading                                 │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Data Bridge (мост к Yandex MapKit)                   │ │
│  │  - JNI callbacks                                      │ │
│  │  - Data conversion                                    │ │
│  │  - Cache management                                   │ │
│  └───────────────────────────────────────────────────────┘ │
└──────────────┬──────────────────────────────────────────────┘
               │ OpenGL ES
               ▼
┌─────────────────────────────────────────────────────────────┐
│  GPU (Hardware Acceleration)                                │
│  - OpenGL ES rendering                                      │
│  - Tile caching                                             │
│  - Hardware acceleration                                    │
└─────────────────────────────────────────────────────────────┘
```

## Структура проекта

```
tiggo_native_navigator/
├── android/
│   ├── app/
│   │   ├── src/
│   │   │   ├── main/
│   │   │   │   ├── java/
│   │   │   │   │   └── com/
│   │   │   │   │       └── tiggo/
│   │   │   │   │           └── navigator/
│   │   │   │   │               ├── MainActivity.java
│   │   │   │   │               ├── NavigationService.java
│   │   │   │   │               ├── YandexMapKitBridge.java
│   │   │   │   │               ├── GLSurfaceViewEx.java
│   │   │   │   │               └── PresentationActivity.java
│   │   │   │   ├── cpp/
│   │   │   │   │   └── jni_bridge.cpp
│   │   │   │   └── AndroidManifest.xml
│   │   │   └── build.gradle
│   │   └── build.gradle
│   └── CMakeLists.txt
│
├── native/
│   ├── core/
│   │   ├── navigator_engine.h/cpp
│   │   ├── route_calculator.h/cpp
│   │   ├── gps_processor.h/cpp
│   │   └── navigation_state.h/cpp
│   │
│   ├── render/
│   │   ├── render_engine.h/cpp
│   │   ├── map_renderer.h/cpp
│   │   ├── route_renderer.h/cpp
│   │   ├── ui_renderer.h/cpp
│   │   └── shaders/
│   │       ├── map.vert
│   │       ├── map.frag
│   │       ├── route.vert
│   │       └── route.frag
│   │
│   ├── async/
│   │   ├── task_queue.h/cpp
│   │   ├── thread_pool.h/cpp
│   │   └── async_loader.h/cpp
│   │
│   ├── data/
│   │   ├── yandex_bridge.h/cpp
│   │   ├── data_converter.h/cpp
│   │   └── cache_manager.h/cpp
│   │
│   ├── utils/
│   │   ├── math_utils.h/cpp
│   │   ├── geometry_utils.h/cpp
│   │   └── log_utils.h/cpp
│   │
│   └── jni/
│       ├── jni_navigator.cpp
│       ├── jni_renderer.cpp
│       └── jni_utils.h/cpp
│
└── docs/
    ├── ARCHITECTURE.md
    ├── BUILD.md
    └── API.md
```

## Основные компоненты

### 1. Navigation Engine (C++)

**Назначение:** Ядро навигационного движка

**Компоненты:**
- `NavigatorEngine` - главный класс навигационного движка
- `RouteCalculator` - расчет маршрутов
- `GpsProcessor` - обработка GPS данных
- `NavigationState` - состояние навигации

**Интерфейс:**
```cpp
class NavigatorEngine {
public:
    // Инициализация
    bool Initialize();
    void Shutdown();
    
    // Навигация
    bool StartNavigation(const Route& route);
    void StopNavigation();
    NavigationState GetState() const;
    
    // Обновление
    void Update(float deltaTime);
    void OnGpsUpdate(const GpsData& gps);
    void OnRouteUpdate(const Route& route);
    
    // Получение данных
    SpeedLimit GetSpeedLimit() const;
    Maneuver GetNextManeuver() const;
    Location GetCurrentLocation() const;
};
```

### 2. Render Engine (C++)

**Назначение:** Рендеринг карты и UI через OpenGL ES

**Компоненты:**
- `RenderEngine` - главный класс рендеринга
- `MapRenderer` - рендеринг карты (тайлы)
- `RouteRenderer` - рендеринг маршрута (полилинии)
- `UIRenderer` - рендеринг UI элементов

**Интерфейс:**
```cpp
class RenderEngine {
public:
    // Инициализация
    bool Initialize(ANativeWindow* window, int width, int height);
    void Shutdown();
    
    // Рендеринг
    void Render(float deltaTime);
    void RenderMap();
    void RenderRoute(const Route& route);
    void RenderUI();
    
    // Обновление
    void OnSurfaceChanged(int width, int height);
    void OnCameraUpdate(const Camera& camera);
    
    // Режимы
    void SetRenderMode(RenderMode mode); // FULL или SIMPLIFIED
    void SetSimplifiedMode(bool enabled);
};
```

### 3. Async Task Queue (C++)

**Назначение:** Асинхронная обработка задач

**Компоненты:**
- `TaskQueue` - очередь задач
- `ThreadPool` - пул потоков
- `AsyncLoader` - асинхронная загрузка данных

**Интерфейс:**
```cpp
class TaskQueue {
public:
    // Задачи
    void EnqueueTask(std::function<void()> task);
    void EnqueueTaskWithCallback(std::function<void()> task, 
                                 std::function<void()> callback);
    
    // Управление
    void ProcessTasks();
    void WaitForCompletion();
    
    // Оптимизация
    void SetMaxConcurrentTasks(int count);
};
```

### 4. Yandex Data Bridge (C++ <-> Java JNI)

**Назначение:** Мост между нативным кодом и Yandex MapKit API

**Компоненты:**
- `YandexBridge` - мост к Yandex API через JNI
- `DataConverter` - конвертация данных
- `CacheManager` - кеширование данных

**Интерфейс:**
```cpp
class YandexBridge {
public:
    // Инициализация
    bool Initialize(JNIEnv* env, jobject yandexMapKit);
    
    // Данные от Yandex (вызываются из Java)
    void OnSpeedLimitReceived(int speedLimitKmh);
    void OnManeuverReceived(const ManeuverData& maneuver);
    void OnRouteReceived(const RouteData& route);
    void OnLocationReceived(const LocationData& location);
    
    // Запросы к Yandex (через JNI)
    void RequestSpeedLimit();
    void RequestRoute(const Point& from, const Point& to);
    void RequestLocation();
};
```

### 5. Android Java Layer

**Назначение:** Интеграция с Android системой

**Компоненты:**
- `MainActivity` - главная Activity
- `NavigationService` - сервис навигации
- `YandexMapKitBridge` - мост к Yandex MapKit
- `GLSurfaceViewEx` - расширенный GLSurfaceView
- `PresentationActivity` - Activity для второго дисплея

**Интерфейс:**
```java
public class MainActivity extends AppCompatActivity {
    private GLSurfaceViewEx mapView;
    private YandexMapKitBridge yandexBridge;
    private NavigationService navigationService;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        // Инициализация Yandex MapKit
        yandexBridge = new YandexMapKitBridge(this);
        yandexBridge.setNativeCallback(nativeCallback);
        
        // Инициализация нативного движка
        nativeInitNavigator();
        
        // Создание GLSurfaceView
        mapView = new GLSurfaceViewEx(this);
        mapView.setEGLContextClientVersion(3); // OpenGL ES 3.0
        mapView.setRenderer(new NativeRenderer());
        setContentView(mapView);
    }
}
```

## Потоки и синхронизация

### Потоки:

1. **Main Thread (UI Thread):**
   - UI обновления
   - Взаимодействие с Android

2. **Render Thread:**
   - OpenGL ES рендеринг
   - Обновление камеры
   - Рендеринг карты

3. **Navigation Thread:**
   - Обработка GPS данных
   - Расчет маршрутов
   - Обновление навигационного состояния

4. **Data Loading Thread:**
   - Загрузка тайлов карты
   - Загрузка данных от Yandex
   - Кеширование данных

5. **Worker Threads (Thread Pool):**
   - Асинхронные задачи
   - Обработка данных
   - Конвертация данных

### Синхронизация:

```cpp
// Используем std::mutex, std::condition_variable, std::atomic
class ThreadSafeQueue {
private:
    std::mutex mutex_;
    std::condition_variable condition_;
    std::queue<Task> queue_;
    
public:
    void Enqueue(const Task& task) {
        std::lock_guard<std::mutex> lock(mutex_);
        queue_.push(task);
        condition_.notify_one();
    }
    
    Task Dequeue() {
        std::unique_lock<std::mutex> lock(mutex_);
        condition_.wait(lock, [this] { return !queue_.empty(); });
        Task task = queue_.front();
        queue_.pop();
        return task;
    }
};
```

## Рендеринг

### OpenGL ES 3.0

**Шейдеры:**
- `map.vert/frag` - рендеринг тайлов карты
- `route.vert/frag` - рендеринг маршрута (полилинии)
- `ui.vert/frag` - рендеринг UI элементов

**Оптимизации:**
- VBO/VAO для геометрии
- Texture atlases для тайлов
- Instanced rendering для повторяющихся элементов
- Frustum culling для видимых объектов

### Два режима рендеринга:

1. **Full Mode (Display 0):**
   - Все тайлы карты
   - POI и события
   - Полная детализация

2. **Simplified Mode (Display 1):**
   - Только маршрут (полилиния)
   - Камеры и события
   - Минимальная детализация карты

## Интеграция с системой

### Broadcast совместимость с TurboDog:

```cpp
// В нативном коде отправляем через JNI
void SendNavigationBroadcast(const NavigationData& data) {
    // Вызываем Java метод через JNI
    JNIEnv* env = GetJNIEnv();
    jclass activityClass = env->FindClass("com/tiggo/navigator/MainActivity");
    jmethodID method = env->GetStaticMethodID(activityClass, 
                                              "sendNavigationBroadcast",
                                              "(IIIIILjava/lang/String;Ljava/lang/String;)V");
    env->CallStaticVoidMethod(activityClass, method, ...);
}
```

### Presentation окно:

```java
public class PresentationActivity extends Presentation {
    private GLSurfaceViewEx mapView;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Создаем упрощенный GLSurfaceView
        mapView = new GLSurfaceViewEx(getContext());
        mapView.setSimplifiedMode(true); // Упрощенный режим
        mapView.setRenderer(new NativeRenderer());
        setContentView(mapView);
    }
}
```

## Этапы разработки

### Этап 1: Базовая инфраструктура (1-2 недели)
- [ ] Настройка CMake и Android NDK
- [ ] Создание JNI слоя
- [ ] Базовая интеграция с Yandex MapKit
- [ ] Инициализация OpenGL ES

### Этап 2: Navigation Engine (2-3 недели)
- [ ] Реализация NavigatorEngine
- [ ] GPS обработка
- [ ] Интеграция данных от Yandex
- [ ] Расчет навигационного состояния

### Этап 3: Render Engine (3-4 недели)
- [ ] Реализация RenderEngine
- [ ] Рендеринг тайлов карты
- [ ] Рендеринг маршрута
- [ ] UI рендеринг

### Этап 4: Оптимизация (2-3 недели)
- [ ] Асинхронная архитектура
- [ ] Кеширование данных
- [ ] Оптимизация рендеринга
- [ ] Два режима отображения

### Этап 5: Интеграция (1-2 недели)
- [ ] Интеграция с Android системой
- [ ] Presentation окно
- [ ] Broadcast совместимость
- [ ] Тестирование

## Технологии

### C/C++:
- C++17 (или C++14)
- STL (std::thread, std::mutex, std::queue)
- OpenGL ES 3.0

### Android:
- Android NDK
- CMake
- JNI
- GLSurfaceView

### Yandex:
- Yandex MapKit SDK
- Yandex NaviKit API

## Преимущества нативного подхода

1. **Производительность:**
   - Нативный код в 10-100 раз быстрее Java
   - Прямой доступ к OpenGL ES
   - Минимальные накладные расходы

2. **Контроль:**
   - Полный контроль над рендерингом
   - Оптимизация под конкретное железо
   - Гибкая архитектура

3. **Совместимость:**
   - Максимальная похожесть на TurboDog
   - Та же архитектура
   - Те же оптимизации

4. **Интеграция:**
   - Легкая интеграция с системой
   - Совместимость с TurboDog broadcast
   - Presentation окно для второго дисплея

## Следующие шаги

1. **Настройка окружения:**
   - Android Studio
   - Android NDK
   - CMake

2. **Создание базовой структуры:**
   - CMakeLists.txt
   - JNI мост
   - Базовая Activity

3. **Интеграция Yandex MapKit:**
   - Java слой для Yandex API
   - JNI мост
   - Нативный код для обработки данных

4. **Реализация рендеринга:**
   - OpenGL ES инициализация
   - Базовый рендеринг
   - Оптимизация

