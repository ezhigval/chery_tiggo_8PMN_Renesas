# Инженерные и сервисные режимы - G6SH/T18FL3

**Дата:** 2025-11-27
**Цель:** Найти все инженерные и сервисные режимы для полного контроля системы

---

## 🎯 НАЙДЕННЫЕ ИНЖЕНЕРНЫЕ РЕЖИМЫ

### 1. Android Engineering Mode (`com.android.engmode`)

**Статус:** ✅ Найден, установлен и **УСПЕШНО ЗАПУЩЕН**

**Путь к APK:**
- `/product/app/SVEngMode/SVEngMode.apk` (это и есть com.android.engmode!)

**Broadcast Actions:**
- `com.android.engmode.EXIT_CARPLAY` - выход из CarPlay
- `com.android.engmode.OPEN` - открытие инженерного режима (не работает как broadcast)

**Разрешения (ключевые):**
- `android.permission.REBOOT` - перезагрузка системы
- `android.permission.MASTER_CLEAR` - сброс к заводским настройкам
- `android.permission.WRITE_SECURE_SETTINGS` - запись защищенных настроек
- `android.permission.RECOVERY` - доступ к recovery
- `android.permission.REAL_GET_TASKS` - получение списка задач
- `android.car.permission.CAR_VENDOR_EXTENSION` - расширения для автомобиля

**Активация:**
```bash
# ✅ Успешный запуск через Activity
adb shell am start -n com.android.engmode/.MainActivity
```

**Результат:** Приложение успешно запущено и отображается на экране устройства!

**Извлечено:** `Knowledge_base/11_QNX/extracted_apk/SVEngMode.apk` (4.0 MB)

---

### 2. Desay SV Engineering Mode (`SVEngMode.apk`)

**Статус:** ✅ Найден и извлечен

**Путь к APK:**
- `/product/app/SVEngMode/SVEngMode.apk`

**Важно:** Это тот же APK, что и `com.android.engmode`! Один APK, два названия.

**Извлечено:** `Knowledge_base/11_QNX/extracted_apk/SVEngMode.apk` (4.0 MB)

**Примечание:** Требуется декомпиляция для анализа всех доступных функций

---

### 3. Desay SV Engineering Broadcast

**Broadcast Actions:**
- `com.desaysv.engineering.START` - ✅ Работает (broadcast отправлен успешно)
- `com.desaysv.engineering.ENABLE` - ✅ Работает (broadcast отправлен успешно)
- `com.desaysv.factory.ENABLE` - ✅ Работает (broadcast отправлен успешно)
- `com.desaysv.diag.ENABLE` - ✅ Работает (broadcast отправлен успешно)

**Активация:**
```bash
adb shell am broadcast -a com.desaysv.engineering.START
adb shell am broadcast -a com.desaysv.engineering.ENABLE
adb shell am broadcast -a com.desaysv.factory.ENABLE
adb shell am broadcast -a com.desaysv.diag.ENABLE
```

**Примечание:** Broadcast отправляются успешно, но обработчики не найдены (возможно, требуют установленного APK)

---

## 🔧 СИСТЕМНЫЕ СВОЙСТВА ДЛЯ ОТЛАДКИ

### Активные свойства отладки:

```bash
# Инженерный режим
persist.sys.eng=1                    # ✅ Установлен
persist.sys.dev=1                    # ✅ Установлен

# Desay SV отладка
persist.sv.debug.adb_enable=1        # ✅ ADB включен
persist.sv.debug_logcat=1            # ✅ Logcat включен
persist.sv.debug_service=1           # ✅ Debug сервис включен

# Системные флаги
ro.debuggable=0                      # ❌ Нельзя изменить (read-only)
ro.secure=1                          # ❌ Нельзя изменить (read-only)
ro.build.type=user                    # Production build
ro.build.tags=dev-keys                # Dev keys (хорошо для отладки)
```

### Установка свойств:

```bash
# Успешно установлены
adb shell setprop persist.sys.eng 1
adb shell setprop persist.sys.dev 1

# Не удалось установить (read-only)
adb shell setprop ro.debuggable 1    # ❌ Failed
adb shell setprop ro.secure 0         # ❌ Failed
```

---

## 🛠️ СЕРВИСЫ ОТЛАДКИ

### 1. svdebug Service

**Статус:** ✅ Запущен

**Путь:** `/vendor/bin/svdebugservice`

**Активация:**
```bash
# Автоматически запускается при:
persist.sv.debug_service=1
```

**Init script:**
```bash
service svdebug /vendor/bin/svdebugservice init
on property:persist.sv.debug_service=1
    start svdebug
```

### 2. svresetfactory Service

**Статус:** ✅ Найден

**Путь:** `/vendor/bin/svresetfactory`

**Активация:**
```bash
# Запускается при:
sys.sv.svresetfactory_service=1
```

**Init script:**
```bash
service svresetfactory /vendor/bin/svresetfactory 2
on property:sys.sv.svresetfactory_service=1
    start svresetfactory
```

---

## 📱 НАЙДЕННЫЕ ПРИЛОЖЕНИЯ

### Инженерные/Тестовые:

1. **com.android.engmode** - Android Engineering Mode
2. **SVEngMode.apk** - Desay SV Engineering Mode
3. **com.desaysv.vehicle.test** - Тестовое приложение (найдено в settings: `car_reserved_2=com.desaysv.vehicle.test/.Test`)

### Сервисные:

1. **com.desaysv.logmanager** - Менеджер логов
2. **com.desaysv.service.link** - Сервис связи (TestLinkDeviceService)
3. **com.desaysv.ftpserver** - FTP сервер

---

## 🔐 РАЗРЕШЕНИЯ И ДОСТУП

### Текущий пользователь:

```bash
uid=2000(shell) gid=2000(shell)
```

### SELinux:

```bash
SELinux: permissive                    # ✅ Permissive режим (хорошо!)
```

### Root доступ:

```bash
su                                      # ❌ Не найден
```

**Примечание:** Нет прямого root доступа, но SELinux в permissive режиме позволяет многое

---

## 🎛️ НАСТРОЙКИ СИСТЕМЫ

### Settings (Global):

```bash
car_reserved_2=com.desaysv.vehicle.test/.Test
device_name=G6SH-r8a7795
device_provisioned=1
```

### Settings (System):

```bash
sys.vehicle.state.engine=1
```

### Settings (Secure):

```bash
android.car.BLUETOOTH_AUTOCONNECT_MUSIC_DEVICES=F4:39:A6:81:FD:C3
android.car.BLUETOOTH_AUTOCONNECT_PHONE_DEVICES=F4:39:A6:81:FD:C3,74:42:18:D1:5E:B9
```

---

## 🔍 ПОИСК СКРЫТЫХ РЕЖИМОВ

### Broadcast Actions для тестирования:

```bash
# Engineering
adb shell am broadcast -a com.desaysv.engineering.START
adb shell am broadcast -a com.desaysv.engineering.ENABLE

# Factory
adb shell am broadcast -a com.desaysv.factory.ENABLE
adb shell am broadcast -a com.desaysv.factory.START

# Diagnostic
adb shell am broadcast -a com.desaysv.diag.ENABLE
adb shell am broadcast -a com.desaysv.diag.START

# Test
adb shell am broadcast -a com.desaysv.test.ENABLE
adb shell am broadcast -a com.desaysv.test.START
```

### Intent Actions:

```bash
# Попытки через Intent
adb shell am start -a android.intent.action.VIEW -d "desaysv://engineering"
adb shell am start -a android.intent.action.VIEW -d "desaysv://factory"
adb shell am start -a android.intent.action.VIEW -d "desaysv://diag"
```

---

## 📋 КОМАНДЫ ДЛЯ АКТИВАЦИИ

### Быстрая активация всех режимов:

```bash
#!/bin/bash

# Установка свойств
adb shell setprop persist.sys.eng 1
adb shell setprop persist.sys.dev 1
adb shell setprop persist.sv.debug_service 1

# Broadcast actions
adb shell am broadcast -a com.desaysv.engineering.START
adb shell am broadcast -a com.desaysv.engineering.ENABLE
adb shell am broadcast -a com.desaysv.factory.ENABLE
adb shell am broadcast -a com.desaysv.diag.ENABLE

# Попытка запуска инженерных приложений
adb shell am start -n com.android.engmode/.MainActivity
```

---

## 🎯 РЕКОМЕНДАЦИИ

### Для получения максимального доступа:

1. **Извлечь и декомпилировать APK:**
   - `SVEngMode.apk`
   - `EngMode.apk` (com.android.engmode)
   - Найти все доступные Activity, Service, Receiver

2. **Изучить init scripts:**
   - `/vendor/etc/init/*.rc`
   - Найти все скрытые сервисы и команды

3. **Анализ системных свойств:**
   - Найти все свойства, начинающиеся с `persist.sys.*`, `persist.sv.*`
   - Попытаться установить их для активации режимов

4. **Поиск скрытых команд:**
   - Изучить `/system/bin`, `/vendor/bin`
   - Найти исполняемые файлы для отладки

5. **Анализ разрешений:**
   - Изучить `/system/etc/permissions/*.xml`
   - Найти специальные разрешения Desay SV

---

## 📝 СЛЕДУЮЩИЕ ШАГИ

1. ✅ Извлечь `SVEngMode.apk` (com.android.engmode)
2. ✅ Создать скрипт для активации всех режимов (`activate_all_modes.sh`)
3. ✅ Успешно запустить инженерный режим
4. ⏳ Декомпилировать APK (JADX) для анализа всех функций
5. ⏳ Найти все Activity, Service, Receiver в APK
6. ⏳ Проанализировать init scripts для скрытых сервисов
7. ⏳ Найти способы изменения read-only свойств
8. ⏳ Изучить все доступные функции инженерного режима

---

## 🚀 БЫСТРЫЙ СТАРТ

### Активация всех режимов:

```bash
cd Knowledge_base/11_QNX
./activate_all_modes.sh
```

### Запуск инженерного режима:

```bash
adb shell am start -n com.android.engmode/.MainActivity
```

### Проверка статуса:

```bash
adb shell getprop | grep -iE 'persist.sys.eng|persist.sys.dev|persist.sv.debug'
```

---

**Статус:** ✅ Инженерный режим найден, извлечен и успешно запущен! Требуется декомпиляция для полного анализа функций.

