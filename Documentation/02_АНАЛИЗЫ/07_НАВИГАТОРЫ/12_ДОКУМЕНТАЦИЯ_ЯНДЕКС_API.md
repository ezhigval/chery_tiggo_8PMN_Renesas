# Документация Яндекс API для навигации

## Официальные ресурсы

### 1. Яндекс для разработчиков

**Основной сайт:** https://yandex.ru/dev/

**Разделы:**
- **MapKit SDK:** https://yandex.ru/dev/mapkit/
- **NaviKit SDK:** (часть MapKit или отдельный SDK)
- **Запуск приложений:** https://yandex.ru/dev/yandex-apps-launch/navigator/

### 2. MapKit SDK

**Документация:** https://yandex.ru/dev/mapkit/doc/android/

**Основные компоненты:**
- Карты
- Поиск
- Маршрутизация
- Навигация

### 3. NaviKit SDK

**Статус:** NaviKit SDK - это часть MapKit SDK или отдельный SDK для навигации

**Пакеты в декомпилированном коде:**
- `com.yandex.navikit.*` - основной пакет NaviKit
- `com.yandex.mapkit.*` - основной пакет MapKit

## Ключевые классы из документации

### Guidance (Навигация)

**Пакет:** `com.yandex.navikit.guidance.Guidance`

**Интерфейс для управления навигацией:**
```java
public interface Guidance extends GuidanceProvider {
    // Получение данных
    NextManeuver getNextManeuver();
    DrivingRoute route();
    PolylinePosition getRoutePosition();
    ClassifiedLocation getLocation();
    
    // Управление
    void start(DrivingRoute route);
    void stop();
    void resume();
    void suspend();
    
    // Слушатели
    void addGuidanceListener(GuidanceListener listener);
    void removeGuidanceListener(GuidanceListener listener);
}
```

### GuidanceProvider

**Пакет:** `com.yandex.navikit.guidance.GuidanceProvider`

**Провайдер для получения компонентов:**
```java
public interface GuidanceProvider {
    NotificationDataManager notificationDataManager();
    GuidanceConfigurator configurator();
    RouteManager routeManager();
    BGGuidanceController bgGuidanceController();
}
```

### GenericGuidanceComponent

**Пакет:** `com.yandex.navikit.guidance.generic.GenericGuidanceComponent`

**Способ получения Guidance:**
```java
GenericGuidance genericGuidance = GenericGuidanceComponent.INSTANCE.getGenericGuidance();
```

**Проблема:** `GenericGuidance` - это интерфейс для регистрации Consumer, не сам `Guidance`

### NotificationDataManager

**Пакет:** `com.yandex.navikit.guidance.NotificationDataManager`

**Альтернативный способ получения данных:**
```java
NotificationDataManager manager = guidance.notificationDataManager();
NotificationData data = manager.notificationData();

// Данные:
String timeOfArrival = data.getTimeOfArrival();
String distanceLeft = data.getDistanceLeft();
String timeLeft = data.getTimeLeft();
String title = data.getTitle();
String subtitle = data.getSubtitle();
```

## Способы получения Guidance

### Способ 1: Через GenericGuidanceComponent (Reflection)

```java
// Получаем GenericGuidanceComponent
Class<?> componentClass = Class.forName(
    "com.yandex.navikit.guidance.generic.GenericGuidanceComponent");
Field instanceField = componentClass.getField("INSTANCE");
Object component = instanceField.get(null);

// Получаем GenericGuidance
Method getGenericGuidance = componentClass.getMethod("getGenericGuidance");
Object genericGuidance = getGenericGuidance.invoke(component);

// Проблема: GenericGuidance не является Guidance
// Нужно найти способ получить Guidance из GenericGuidance
```

### Способ 2: Через NotificationDataManager

```java
// Если удалось получить Guidance
Object guidance = ...;

// Получаем NotificationDataManager
Method getNotificationDataManager = guidance.getClass()
    .getMethod("notificationDataManager");
Object manager = getNotificationDataManager.invoke(guidance);

// Подписываемся на изменения
Class<?> listenerClass = Class.forName(
    "com.yandex.navikit.guidance.NotificationDataManagerListener");
Object listener = Proxy.newProxyInstance(...);
Method addListener = manager.getClass().getMethod("addListener", listenerClass);
addListener.invoke(manager, listener);

// Получаем текущие данные
Method getNotificationData = manager.getClass().getMethod("notificationData");
Object data = getNotificationData.invoke(manager);
```

### Способ 3: Через GuidanceListener

```java
// Создаем listener через Proxy
Class<?> listenerClass = Class.forName(
    "com.yandex.navikit.guidance.GuidanceListener");
Object listener = Proxy.newProxyInstance(
    classLoader,
    new Class[]{listenerClass},
    new InvocationHandler() {
        @Override
        public Object invoke(Object proxy, Method method, Object[] args) {
            String methodName = method.getName();
            if (methodName.equals("onLocationUpdated")) {
                // Обработка обновления локации
            } else if (methodName.equals("onRoutePositionUpdated")) {
                // Обработка обновления позиции на маршруте
            }
            return null;
        }
    }
);

// Регистрируем listener
if (guidance != null) {
    Method addListener = guidance.getClass()
        .getMethod("addGuidanceListener", listenerClass);
    addListener.invoke(guidance, listener);
}
```

## Полезные ссылки

### Официальная документация

1. **Яндекс для разработчиков:**
   - https://yandex.ru/dev/

2. **MapKit SDK для Android:**
   - https://yandex.ru/dev/mapkit/doc/android/
   - https://yandex.ru/dev/mapkit/doc/android/quickstart.html

3. **Запуск Яндекс.Навигатора:**
   - https://yandex.ru/dev/yandex-apps-launch/navigator/

4. **GitHub (возможно):**
   - Поиск: "yandex mapkit android github"
   - Поиск: "yandex navikit android github"

### Примеры кода

1. **Официальные примеры:**
   - В документации MapKit SDK должны быть примеры
   - Возможно, есть репозитории на GitHub

2. **Декомпилированный код:**
   - `development/extracted_from_device/decompiled/ru.yandex.yandexmaps/`
   - Можно изучать, как сам Яндекс Навигатор использует API

## Рекомендации

### 1. Изучить официальную документацию

**Приоритет:** Высокий

**Действия:**
- Зарегистрироваться на https://yandex.ru/dev/
- Получить API ключ (если требуется)
- Изучить документацию MapKit SDK
- Найти раздел про NaviKit SDK

### 2. Изучить примеры

**Приоритет:** Высокий

**Действия:**
- Найти примеры использования в документации
- Проверить GitHub на наличие примеров
- Изучить декомпилированный код Яндекс Навигатора

### 3. Экспериментировать с Reflection

**Приоритет:** Средний

**Действия:**
- Продолжить попытки получения `Guidance` через Reflection
- Попробовать `NotificationDataManager` как альтернативу
- Изучить внутреннюю структуру `GenericGuidanceImpl`

### 4. Обратиться в поддержку

**Приоритет:** Низкий (если документация не поможет)

**Действия:**
- Написать в поддержку Яндекс для разработчиков
- Задать вопрос о доступе к данным навигации из другого приложения
- Уточнить, есть ли публичный API для получения данных навигации

## Важные замечания

### Ограничения API

1. **Публичный API:**
   - MapKit SDK предназначен для встраивания карт и навигации в свои приложения
   - Не предназначен для получения данных из уже запущенного Яндекс Навигатора

2. **Приватный API:**
   - `com.yandex.navikit.*` - это внутренний API Яндекс Навигатора
   - Не документирован публично
   - Может изменяться между версиями

3. **Reflection:**
   - Единственный способ получить доступ к приватному API
   - Нестабилен и может перестать работать после обновления

### Альтернативные подходы

1. **File Monitoring:**
   - Мониторить файлы навигатора
   - Искать JSON/XML с данными

2. **SharedPreferences:**
   - Проверить, сохраняет ли навигатор данные в SharedPreferences

3. **AccessibilityService:**
   - Если станет доступен в системе

## Следующие шаги

1. ✅ **Завершено:** Поиск информации о документации
2. ⏳ **В процессе:** Изучение официальной документации
3. ⏳ **Запланировано:** Регистрация на yandex.ru/dev (если требуется)
4. ⏳ **Запланировано:** Изучение примеров кода
5. ⏳ **Запланировано:** Эксперименты с Reflection на основе документации

## Важное понимание

⚠️ **MapKit SDK предназначен для создания навигации в своем приложении, а не для получения данных из уже запущенного Яндекс.Навигатора.**

**Официального API для получения данных из Яндекс.Навигатора нет.** 

См. также: [Изучение официальной документации](13_ИЗУЧЕНИЕ_ОФИЦИАЛЬНОЙ_ДОКУМЕНТАЦИИ.md)

## Полезные команды для поиска

```bash
# Поиск в декомпилированном коде
grep -r "Guidance" development/extracted_from_device/decompiled/ru.yandex.yandexmaps/sources/com/yandex/navikit/

# Поиск примеров использования
grep -r "getGenericGuidance\|GenericGuidanceComponent" development/extracted_from_device/decompiled/ru.yandex.yandexmaps/

# Поиск NotificationDataManager
grep -r "NotificationDataManager" development/extracted_from_device/decompiled/ru.yandex.yandexmaps/
```

