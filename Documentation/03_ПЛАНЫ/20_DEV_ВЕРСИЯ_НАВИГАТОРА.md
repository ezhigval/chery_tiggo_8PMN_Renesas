# Dev-версия Yandex Navigator для отладки

## Цель

Создать dev-версию навигатора с открытым кодом для:
1. Понимания, как работает навигация
2. Отслеживания потока данных
3. Тестирования интеграции с TiggoBridgeSender
4. Отладки без модификации оригинального APK

## Структура проекта

```
YandexNavigatorDev/
├── app/
│   ├── src/main/
│   │   ├── java/ru/yandex/yandexnavi/dev/
│   │   │   └── MainActivity.java          # Главная Activity с навигацией
│   │   ├── java/ru/yandex/yandexmaps/bridge/
│   │   │   └── TiggoBridgeSender.java     # Класс-мост (скопирован)
│   │   ├── res/
│   │   │   └── layout/
│   │   │       └── activity_main.xml      # UI с картой
│   │   └── AndroidManifest.xml
│   └── build.gradle
├── build.gradle
└── settings.gradle
```

## Что делает приложение

1. **Инициализация MapKit:**
   - Инициализирует Yandex MapKit SDK
   - Создает карту

2. **Инициализация навигации:**
   - Получает `GenericGuidanceComponent.INSTANCE`
   - Получает `Navigation` через MapKit
   - Получает `Guidance` из Navigation
   - Получает `NotificationDataManager` из Guidance
   - Подключает `TiggoBridgeSender` к `NotificationDataManager`

3. **Построение маршрута:**
   - Использует `DrivingRouter` для построения маршрута
   - Отображает маршрут на карте

4. **Запуск навигации:**
   - Вызывает `guidance.start(route)`
   - Подписывается на `GuidanceListener` для отладки
   - Подписывается на `NotificationDataManagerListener` для отладки

5. **Логирование:**
   - Все этапы логируются для понимания потока данных
   - Можно отследить, когда и откуда приходят данные

## Преимущества

✅ **Открытый код:** Видим весь процесс работы навигации  
✅ **Отладка:** Можем ставить breakpoints и логировать  
✅ **Тестирование:** Можем тестировать интеграцию без модификации APK  
✅ **Понимание:** Видим, как данные проходят через систему  

## Использование

### 1. Получить API ключ MapKit

1. Зарегистрироваться на https://yandex.ru/dev/
2. Создать приложение
3. Получить API ключ для MapKit

### 2. Добавить API ключ

В `MainActivity.java` раскомментировать:
```java
MapKitFactory.setApiKey("YOUR_API_KEY");
MapKitFactory.initialize(this);
```

### 3. Собрать и запустить

```bash
cd development/projects/YandexNavigatorDev
./gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

### 4. Запустить и протестировать

1. Открыть приложение
2. Построить маршрут (кнопка "Построить маршрут")
3. Начать навигацию (кнопка "Начать навигацию")
4. Смотреть логи:
   ```bash
   adb logcat | grep -E "(YandexNavigatorDev|TiggoBridgeSender|NotificationData|Guidance)"
   ```

## Что можно отследить

1. **Инициализация:**
   - Когда создается `GenericGuidanceComponent`
   - Когда получается `Guidance`
   - Когда получается `NotificationDataManager`

2. **Данные навигации:**
   - Когда вызывается `onNotificationDataUpdated`
   - Какие данные приходят
   - Когда вызывается `onRoutePositionUpdated`
   - Какие данные в `NextManeuver`

3. **Интеграция с мостом:**
   - Когда `TiggoBridgeSender` получает данные
   - Когда данные отправляются в `TiggoBridgeService`
   - Когда данные отправляются в QNX

## Следующие шаги

1. ✅ Создать структуру проекта
2. ⏳ Добавить API ключ MapKit
3. ⏳ Собрать и запустить
4. ⏳ Протестировать инициализацию
5. ⏳ Протестировать построение маршрута
6. ⏳ Протестировать навигацию
7. ⏳ Протестировать интеграцию с мостом

## Важные замечания

⚠️ **API ключ обязателен:** Без API ключа MapKit не будет работать

⚠️ **Зависимости:** Нужны правильные версии MapKit SDK

⚠️ **Разрешения:** Нужны разрешения на местоположение

