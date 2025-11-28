# Исправление ошибок компиляции

## Проблема

Компилятор пытается скомпилировать декомпилированные файлы из TurboDog:

```
turbodog_analysis/decompiled/sources/androidx/core/widget/b.java
```

Эти файлы содержат синтаксические ошибки из-за особенностей декомпиляции.

## Решение

### 1. Исключить папку из компиляции

**Обновлен `.gitignore`** - добавлены исключения:

```
turbodog_analysis/extracted/
turbodog_analysis/decompiled/
turbodog_analysis/**/*.java
turbodog_analysis/**/*.smali
turbodog_analysis/**/*.class
```

### 2. Если используете Android Studio

**Вариант A: Исключить папку в настройках IDE**

1. Откройте Android Studio
2. File → Settings (Preferences на Mac)
3. Build, Execution, Deployment → Compiler
4. Добавьте в "Excludes":
   ```
   turbodog_analysis/**
   ```

**Вариант B: Удалить папку из проекта**

1. File → Project Structure
2. Modules → выберите модуль
3. Sources → исключите папку `turbodog_analysis`

### 3. Если используете командную строку

**Создайте `build.gradle` с исключениями:**

```gradle
android {
    sourceSets {
        main {
            java {
                exclude 'turbodog_analysis/**'
            }
        }
    }
}
```

### 4. Временное решение (если ничего не помогает)

Переместите папку `turbodog_analysis` за пределы проекта:

```bash
cd /Users/valentinezov/Projects/Tiggo/development/ЯндексДог
mv turbodog_analysis ../turbodog_analysis_backup
```

### 5. Проверка

После изменений проверьте, что файлы не компилируются:

```bash
# Проверка, что файлы не в sourceSet
find . -name "*.java" -path "*/turbodog_analysis/*" | head -5
```

## Рекомендация

**Папка `turbodog_analysis/` используется только для анализа кода TurboDog.**

Она не должна участвовать в сборке проекта ЯндексДог. Лучше всего:

- Исключить её из IDE
- Или переместить за пределы проекта
- Или добавить в `.idea/modules.xml` исключения

## Статус

✅ `.gitignore` обновлен
⏳ Нужно исключить папку в IDE настройках (если используется Android Studio)
⏳ Нужно создать `build.gradle` (если компилируете через Gradle)
