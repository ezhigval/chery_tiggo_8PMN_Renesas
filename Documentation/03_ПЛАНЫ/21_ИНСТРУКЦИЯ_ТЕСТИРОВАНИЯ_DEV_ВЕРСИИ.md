# Инструкция по тестированию dev-версии навигатора

## Проблема со сборкой

Dev-версия навигатора (`YandexNavigatorDev`) не собирается из-за несовместимости версий Java/Gradle.

**Ошибка:** `Unsupported class file major version 69` (Java 21, но Gradle 7.5 не поддерживает)

## Решение

### Вариант 1: Использовать Android Studio

1. Открыть проект `YandexNavigatorDev` в Android Studio
2. Android Studio автоматически настроит правильные версии
3. Собрать через `Build > Make Project`
4. Установить через `Run > Run 'app'`

### Вариант 2: Использовать готовый TiggoBridgeService

Для тестирования логирования можно использовать основной проект:

```bash
cd development/projects/TiggoBridgeService
./gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
adb shell am start -n com.desaysv.tiggo.bridge/.ui.MainActivity
```

### Вариант 3: Исправить версии вручную

1. Проверить версию Java:
   ```bash
   java -version
   ```

2. Если Java 21, использовать Gradle 8.5+:
   ```properties
   distributionUrl=https\://services.gradle.org/distributions/gradle-8.5-bin.zip
   ```

3. Обновить `build.gradle`:
   ```gradle
   classpath 'com.android.tools.build:gradle:8.1.0'
   ```

## Текущий статус

- ✅ Структура проекта создана
- ✅ Код написан
- ✅ API ключ сохранен
- ⚠️ Проблема со сборкой (версии Java/Gradle)
- ⏳ Нужно собрать через Android Studio или исправить версии

## Что тестировать

После успешной сборки:

1. **Логирование инициализации:**
   ```bash
   adb logcat | grep YandexNavigatorDev
   ```

2. **Поток данных:**
   - Проверить, что `TiggoBridgeSender` инициализируется
   - Проверить логи цепочки инициализации
   - Проверить отправку данных в `TiggoBridgeService`

3. **Интеграция:**
   - Убедиться, что данные доходят до `TiggoBridgeService`
   - Проверить преобразование данных
   - Проверить отправку в QNX

## Следующие шаги

1. ⏳ Собрать проект (через Android Studio или исправить версии)
2. ⏳ Установить на эмулятор
3. ⏳ Протестировать логирование
4. ⏳ Протестировать поток данных

