# Инструкция по сборке YandexNavigatorDev

## Проблема

Проект не собирается через командную строку из-за несовместимости версий Java/Gradle:
- Установлена Java 25 (class file major version 69)
- Gradle 8.10.2 поддерживает только до Java 23

## Решение

### Вариант 1: Собрать через Android Studio (РЕКОМЕНДУЕТСЯ)

1. Откройте проект `YandexNavigatorDev` в Android Studio
2. Android Studio автоматически настроит правильные версии
3. Соберите через `Build > Make Project` или `Build > Build Bundle(s) / APK(s) > Build APK(s)`
4. APK будет в `app/build/outputs/apk/debug/app-debug.apk`

### Вариант 2: Использовать Java 23 или ниже

Если у вас установлена Java 23 или ниже:

```bash
export JAVA_HOME=$(/usr/libexec/java_home -v 23)
cd development/projects/YandexNavigatorDev
./gradlew assembleDebug
```

### Вариант 3: Установить Java 23

```bash
# Через Homebrew
brew install openjdk@23

# Установить как JAVA_HOME
export JAVA_HOME=$(/usr/libexec/java_home -v 23)
```

## Текущая конфигурация

- **Gradle:** 8.10.2
- **Android Gradle Plugin:** 8.1.4
- **Compile SDK:** 28
- **Target SDK:** 28
- **Min SDK:** 26

## После успешной сборки

1. Установить на эмулятор:
   ```bash
   adb install -r app/build/outputs/apk/debug/app-debug.apk
   ```

2. Запустить:
   ```bash
   adb shell am start -n ru.yandex.yandexnavi.dev/.MainActivity
   ```

3. Смотреть логи:
   ```bash
   adb logcat | grep YandexNavigatorDev
   ```

## Альтернатива

Если сборка не работает, можно тестировать основной проект `TiggoBridgeService`, который уже успешно собирается и установлен на эмуляторе.

