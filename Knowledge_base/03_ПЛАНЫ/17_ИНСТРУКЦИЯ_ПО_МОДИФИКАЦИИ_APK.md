# Инструкция по модификации APK Yandex Navigator

## Подготовка

### Необходимые инструменты

1. **apktool** - декомпиляция/компиляция APK
   ```bash
   # Установка через Homebrew (macOS)
   brew install apktool
   
   # Или скачать с https://ibotpeaches.github.io/Apktool/
   ```

2. **apksigner** - подпись APK (входит в Android SDK)
   ```bash
   # Путь: $ANDROID_HOME/build-tools/<version>/apksigner
   ```

3. **jadx** - декомпиляция в Java (для чтения кода)
   ```bash
   # Скачать с https://github.com/skylot/jadx/releases
   ```

4. **Java JDK** - для компиляции

5. **Android SDK** - для подписи APK

### Создание keystore для подписи

```bash
keytool -genkey -v -keystore tiggo_navigator.keystore -alias tiggo -keyalg RSA -keysize 2048 -validity 10000
```

## Процесс модификации

### Шаг 1: Получение APK

**Вариант A: С устройства**
```bash
# Найти package name
adb shell pm list packages | grep yandex

# Извлечь APK
adb pull $(adb shell pm path ru.yandex.yandexnavi | cut -d: -f2) yandexnavi.apk
```

**Вариант B: Скачать с APKMirror или другого источника**

### Шаг 2: Декомпиляция APK

```bash
# Декомпиляция
apktool d yandexnavi.apk -o yandexnavi_source

# Результат будет в папке yandexnavi_source/
```

### Шаг 3: Изучение структуры

```bash
# Просмотр структуры
cd yandexnavi_source
ls -la

# Основные папки:
# - smali/ - декомпилированный код (Smali)
# - res/ - ресурсы
# - AndroidManifest.xml - манифест
```

### Шаг 4: Поиск точки внедрения

**Найти Application класс:**
```bash
# Ищем в AndroidManifest.xml
grep -r "android:name.*Application" AndroidManifest.xml

# Или ищем в коде
find smali -name "*Application*.smali" | head -5
```

**Найти главную Activity:**
```bash
# Ищем LAUNCHER activity
grep -A 5 "LAUNCHER" AndroidManifest.xml
```

### Шаг 5: Добавление класса-моста

**Вариант A: Добавить Java класс и скомпилировать**

1. Создать Java файл:
   ```
   yandexnavi_source/smali/ru/yandex/yandexmaps/bridge/TiggoBridgeSender.java
   ```
   (Использовать готовый файл из `development/projects/TiggoNavigatorBridge/`)

2. Скомпилировать в Smali:
   ```bash
   # Компилируем Java в class
   javac -cp <android.jar> TiggoBridgeSender.java
   
   # Конвертируем class в dex
   dx --dex --output=classes.dex TiggoBridgeSender.class
   
   # Конвертируем dex в smali
   baksmali d classes.dex -o smali/
   ```

**Вариант B: Написать напрямую в Smali (сложнее)**

Использовать готовый шаблон Smali кода.

### Шаг 6: Интеграция с NotificationDataManager

**Найти класс, который использует NotificationDataManager:**
```bash
# Найденный класс: ru/yandex/yandexmaps/integrations/auto_navigation/navikit/k.java
# Нужно найти его Smali эквивалент
find smali -path "*auto_navigation/navikit/k.smali"
```

**Модифицировать класс:**
- Добавить поле для TiggoBridgeSender
- В методе, где получается NotificationDataManager, вызвать `attachToNotificationDataManager()`

### Шаг 7: Инициализация моста

**Найти Application класс или главную Activity:**
```bash
# Ищем onCreate метод
grep -r "onCreate" smali/ru/yandex/yandexmaps/*.smali | head -5
```

**Добавить инициализацию:**
В `onCreate()` добавить:
```smali
invoke-static {p0}, Lru/yandex/yandexmaps/bridge/TiggoBridgeSender;->init(Landroid/content/Context;)V
```

### Шаг 8: Ре-компиляция APK

```bash
# Вернуться в корневую папку
cd yandexnavi_source

# Компиляция
apktool b . -o yandexnavi_modified.apk

# Если ошибки - исправить и повторить
```

### Шаг 9: Подпись APK

```bash
# Подпись
apksigner sign --ks tiggo_navigator.keystore --ks-key-alias tiggo yandexnavi_modified.apk

# Проверка подписи
apksigner verify yandexnavi_modified.apk
```

### Шаг 10: Установка

```bash
# Удалить оригинальный навигатор (если нужно)
adb uninstall ru.yandex.yandexnavi

# Установить модифицированный
adb install yandexnavi_modified.apk
```

## Альтернативный подход: Использование JADX

Если работа с Smali слишком сложна, можно:

1. **Декомпилировать в Java:**
   ```bash
   jadx -d yandexnavi_java yandexnavi.apk
   ```

2. **Модифицировать Java код**

3. **Скомпилировать обратно:**
   ```bash
   # Создать Android проект
   # Скопировать модифицированные файлы
   # Собрать APK через Android Studio или Gradle
   ```

## Проверка работы

1. **Запустить навигатор**
2. **Построить маршрут**
3. **Начать навигацию**
4. **Проверить логи:**
   ```bash
   adb logcat | grep -E "(TiggoBridgeSender|turbodog.navigation)"
   ```
5. **Проверить, что данные приходят в TiggoBridgeService**

## Отладка

### Проблема: APK не компилируется

**Решение:**
- Проверить синтаксис Smali
- Убедиться, что все зависимости на месте
- Проверить AndroidManifest.xml

### Проблема: APK не устанавливается

**Решение:**
- Проверить подпись
- Убедиться, что оригинальный навигатор удален
- Проверить версию Android

### Проблема: Приложение не запускается

**Решение:**
- Проверить логи: `adb logcat | grep -i error`
- Убедиться, что все классы на месте
- Проверить, что инициализация выполнена

### Проблема: Данные не отправляются

**Решение:**
- Проверить, что NotificationDataManager получен
- Проверить, что listener зарегистрирован
- Проверить логи TiggoBridgeSender

## Автоматизация

Создать скрипт для автоматической модификации:

```bash
#!/bin/bash
# modify_navigator.sh

APK_FILE=$1
OUTPUT_FILE="yandexnavi_modified.apk"

# Декомпиляция
apktool d $APK_FILE -o temp_source

# Копирование модифицированных файлов
cp -r modifications/* temp_source/

# Компиляция
apktool b temp_source -o temp_unsigned.apk

# Подпись
apksigner sign --ks tiggo_navigator.keystore --ks-key-alias tiggo temp_unsigned.apk -o $OUTPUT_FILE

# Очистка
rm -rf temp_source temp_unsigned.apk

echo "Готово: $OUTPUT_FILE"
```

## Важные замечания

1. **Резервная копия:** Всегда сохраняйте оригинальный APK
2. **Версии:** Модификации нужно делать для каждой версии навигатора
3. **Обновления:** Отключите автоматические обновления в Play Store
4. **Тестирование:** Тщательно тестируйте после каждой модификации

## Следующие шаги

1. ✅ Подготовить инструменты
2. ✅ Декомпилировать APK
3. ✅ Найти точку внедрения
4. ✅ Добавить класс-мост
5. ✅ Интегрировать с NotificationDataManager
6. ✅ Ре-скомпилировать и протестировать

