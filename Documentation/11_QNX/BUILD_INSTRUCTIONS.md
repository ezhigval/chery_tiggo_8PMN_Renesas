# Инструкции по сборке APK

## Вариант 1: Android Studio (рекомендуется)

1. Установить Android Studio
2. Открыть проект: `File -> Open -> RemoteTunnel/`
3. Дождаться синхронизации Gradle
4. `Build -> Build Bundle(s) / APK(s) -> Build APK(s)`
5. APK будет в: `app/build/outputs/apk/debug/app-debug.apk`

## Вариант 2: Командная строка (если установлен Android SDK)

```bash
cd RemoteTunnel
./gradlew assembleDebug
# APK: app/build/outputs/apk/debug/app-debug.apk
```

## Вариант 3: Использовать готовый APK

Если у вас уже есть APK, можно установить его напрямую.

## После сборки

```bash
# Установка с root
./Knowledge_base/11_QNX/auto_install_root.sh
```

