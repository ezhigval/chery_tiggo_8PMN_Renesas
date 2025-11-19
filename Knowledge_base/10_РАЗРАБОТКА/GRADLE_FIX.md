# Исправление проблемы сборки

## Проблема
```
NoSuchMethodError: 'org.gradle.api.artifacts.Dependency org.gradle.api.artifacts.dsl.DependencyHandler.module(java.lang.Object)'
```

Это несовместимость версий Android Gradle Plugin и Gradle.

## Решение

Обновлены версии:
- **Android Gradle Plugin:** 8.3.0 (было 8.1.4)
- **Gradle:** 8.4 (было 8.10.2)

## Что сделано

1. ✅ Обновлен `build.gradle` - AGP 8.3.0
2. ✅ Обновлен `gradle-wrapper.properties` - Gradle 8.4
3. ✅ Очищен кеш

## Следующие шаги

### Вариант 1: Через Android Studio (РЕКОМЕНДУЕТСЯ)
1. Откройте проект в Android Studio
2. Дождитесь синхронизации Gradle
3. Соберите: `Build > Make Project`
4. APK будет в: `app/build/outputs/apk/debug/app-debug.apk`

### Вариант 2: Через командную строку
```bash
cd development/projects/YandexNavigatorDev
./gradlew clean assembleDebug
```

## Совместимость версий

- **AGP 8.3.0** требует **Gradle 8.4+**
- **Gradle 8.4** поддерживает **Java 17-21**
- Для **Java 25** нужен **Gradle 8.10+**, но он несовместим с AGP 8.3.0

**Рекомендация:** Используйте Android Studio, он автоматически настроит правильные версии.

