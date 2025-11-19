# ✅ Быстрая проверка статуса

## 📱 Проверка установки приложения

```bash
adb shell pm list packages | grep tiggo
```

## 🚀 Запуск приложения

```bash
# Главная Activity (Display 0)
adb shell am start -n com.tiggo.navigator/.MainActivity

# Presentation Activity (Display 1)
adb shell am start -n com.tiggo.navigator/.PresentationActivity
```

## 📊 Просмотр логов

```bash
# Фильтрованные логи
./view_logs.sh

# Или вручную
adb logcat | grep -E "tiggo|Tiggo|Navigator|Error|Exception"
```

## 📱 Второй дисплей

```bash
# Запуск скрипта
./start_second_display.sh
```

## 🔍 Проверка процессов

```bash
adb shell ps | grep -i "tiggo\|navigator"
```

## 📦 Проверка APK

```bash
ls -lh app/build/outputs/apk/debug/app-debug.apk
```

