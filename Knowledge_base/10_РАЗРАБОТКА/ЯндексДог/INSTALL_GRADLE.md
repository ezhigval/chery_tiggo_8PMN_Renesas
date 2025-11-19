# 📦 Установка Gradle в Android Studio

## 🔍 Проверка наличия Gradle

Сначала проверим, установлен ли Gradle:

### Вариант 1: Через Android Studio

1. **File → Settings** (или `Cmd+,` / `Ctrl+Alt+S`)
2. Перейдите: **Build, Execution, Deployment → Gradle**
3. Посмотрите настройку **"Use Gradle from"**

### Вариант 2: Через терминал

```bash
cd /Users/valentinezov/Projects/Tiggo/development/ЯндексДог
./gradlew --version
```

Если команда не работает, значит Gradle Wrapper не установлен.

## 🚀 Установка Gradle (3 способа)

### Способ 1: Gradle Wrapper (Рекомендуется) ⭐

**Gradle Wrapper** - это автоматическая установка Gradle. Нужно создать файлы wrapper.

#### Шаг 1: Проверьте наличие файла `gradle/wrapper/gradle-wrapper.properties`

Если файл есть - всё готово! Android Studio автоматически установит Gradle.

#### Шаг 2: Если файла нет, создайте его:

**1. Создайте папку wrapper:**

```bash
mkdir -p gradle/wrapper
```

**2. Создайте файл `gradle/wrapper/gradle-wrapper.properties`:**

```properties
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-7.5-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
```

**3. Скачайте Gradle Wrapper скрипты:**

**Для macOS/Linux:**

```bash
# Скачайте gradlew и gradlew.bat
curl -L https://raw.githubusercontent.com/gradle/gradle/master/gradle/wrapper/gradlew \
     -o gradlew
chmod +x gradlew
```

**Для Windows (PowerShell):**

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/gradle/gradle/master/gradle/wrapper/gradlew.bat" -OutFile "gradlew.bat"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/gradle/gradle/master/gradle/wrapper/gradlew" -OutFile "gradlew"
```

**4. Или создайте файл `gradlew` вручную:**
Скопируйте скрипт Gradle Wrapper из официального репозитория:
https://github.com/gradle/gradle/blob/master/gradle/wrapper/gradlew

### Способ 2: Через Android Studio (Автоматически)

Android Studio может автоматически создать Gradle Wrapper:

**1. Откройте проект в Android Studio**

- **File → Open** → выберите папку `ЯндексДог`

**2. Если появится предложение "Create Gradle Wrapper":**

- Нажмите **"Create"** или **"OK"**
- Android Studio автоматически создаст `gradlew` и настройки

**3. Если предложения нет:**

- **File → Settings → Build, Execution, Deployment → Gradle**
- В разделе **"Gradle projects"** выберите:
  - ✅ **"Use Gradle from: 'gradle-wrapper.properties' file"**
- Android Studio автоматически скачает Gradle

### Способ 3: Ручная установка Gradle

Если нужен системный Gradle (не рекомендуется для проекта):

#### macOS (через Homebrew):

```bash
brew install gradle
gradle --version
```

#### Linux (Ubuntu/Debian):

```bash
sudo apt update
sudo apt install gradle
gradle --version
```

#### Windows:

1. Скачайте Gradle: https://gradle.org/releases/
2. Распакуйте архив
3. Добавьте в PATH: `C:\path\to\gradle\bin`

## ⚙️ Настройка в Android Studio

После установки Gradle настройте Android Studio:

### 1. Откройте настройки Gradle

**File → Settings** (`Cmd+,` / `Ctrl+Alt+S`)
→ **Build, Execution, Deployment**
→ **Gradle**

### 2. Настройте использование Gradle

**Вариант A: Gradle Wrapper (Рекомендуется) ⭐**

Выберите:

- ✅ **"Use Gradle from: 'gradle-wrapper.properties' file"**

**Вариант B: Системный Gradle**

Выберите:

- ✅ **"Use Gradle from: Specified location"**
- Укажите путь к Gradle (например: `/usr/local/bin/gradle`)

### 3. Настройте Gradle JDK

1. В тех же настройках найдите **"Gradle JDK"**
2. Выберите JDK 11 или выше
3. Если JDK нет, Android Studio предложит скачать

### 4. Сохраните настройки

- Нажмите **"Apply"** или **"OK"**

## 🔄 Синхронизация проекта

После настройки Gradle:

1. **File → Sync Project with Gradle Files**
2. Дождитесь загрузки зависимостей
3. Проверьте, что нет ошибок

## ✅ Проверка установки

### Через Android Studio:

1. **View → Tool Windows → Terminal**
2. Введите:

```bash
./gradlew --version
```

Должен вывестись версия Gradle, например:

```
Gradle 7.5
```

### Через терминал:

```bash
cd /Users/valentinezov/Projects/Tiggo/development/ЯндексДог
./gradlew --version
```

## 🐛 Решение проблем

### Проблема: "gradlew: command not found"

**Решение:**

```bash
chmod +x gradlew
```

### Проблема: "Gradle wrapper not found"

**Решение:** Создайте файлы wrapper (см. Способ 1 выше)

### Проблема: "Could not find or load main class"

**Решение:**

1. Удалите папку `~/.gradle/wrapper/dists/`
2. Перезапустите синхронизацию

### Проблема: "Unsupported class file major version"

**Решение:** Используйте JDK 11 или выше:

- **File → Settings → Build, Execution, Deployment → Build Tools → Gradle**
- **Gradle JDK:** выберите JDK 11+

## 📝 Быстрая установка (скрипт)

Создайте файл `setup_gradle.sh`:

```bash
#!/bin/bash
cd "$(dirname "$0")"

# Создаем папку wrapper
mkdir -p gradle/wrapper

# Создаем gradle-wrapper.properties (если его нет)
if [ ! -f gradle/wrapper/gradle-wrapper.properties ]; then
    cat > gradle/wrapper/gradle-wrapper.properties << EOF
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-7.5-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
EOF
fi

# Скачиваем gradlew
if [ ! -f gradlew ]; then
    curl -L https://raw.githubusercontent.com/gradle/gradle/master/gradle/wrapper/gradlew \
         -o gradlew
    chmod +x gradlew
fi

echo "✅ Gradle Wrapper установлен!"
echo "Запустите: ./gradlew --version"
```

Запустите:

```bash
chmod +x setup_gradle.sh
./setup_gradle.sh
```

## 🎯 Рекомендации

✅ **Используйте Gradle Wrapper** - это лучший вариант для проекта

- Автоматическая установка нужной версии
- Единая версия для всех разработчиков
- Не требует ручной установки

❌ **Не используйте системный Gradle** для проекта

- Разные версии у разных разработчиков
- Проблемы совместимости

## 📚 Дополнительная информация

- [Официальная документация Gradle](https://docs.gradle.org/)
- [Gradle Wrapper документация](https://docs.gradle.org/current/userguide/gradle_wrapper.html)
- См. `ANDROID_STUDIO_SETUP.md` - настройка Android Studio
