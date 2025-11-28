# Детальный план реализации App Package решения

## 🎯 Цель

Создать пакет приложений и управляющий лаунчер, который:
1. Скрывает системные приложения
2. Подставляет наши модифицированные приложения
3. Обеспечивает полную интеграцию с системой

---

## 📦 Состав пакета

### 1. Custom Launcher
- **Назначение:** Замена стандартного лаунчера
- **Функции:**
  - Скрытие системных приложений
  - Отображение только наших приложений
  - Управление приложениями

### 2. Модифицированный SVMedia
- **Назначение:** Медиа-приложение с поддержкой Яндекс Музыки
- **Изменения:**
  - Добавлен источник "Яндекс Музыка"
  - Автоопределение медиа-приложений
  - Получение метаданных через MediaSession API

### 3. Bridge Service
- **Назначение:** Интеграция Яндекс Навигатора
- **Функции:**
  - Запуск Яндекс Навигатора
  - Перехват событий навигации
  - Преобразование данных
  - Отправка в систему (CAN/QNX)

### 4. Media Bridge
- **Назначение:** Интеграция метаданных медиа
- **Функции:**
  - Получение метаданных от Яндекс Музыки
  - Отправка в SVMeterInteraction
  - Отображение на приборной панели

---

## 🏗️ Архитектура решения

```
┌─────────────────────────────────────────┐
│  Custom Launcher (системный)           │
│  - Скрывает системные приложения        │
│  - Показывает только наши              │
└──────────┬──────────────────────────────┘
           │
           ├──► Модифицированный SVMedia
           │   └──► Яндекс Музыка
           │       └──► Media Bridge
           │           └──► SVMeterInteraction
           │               └──► Приборная панель
           │
           ├──► Bridge Service
           │   └──► Яндекс Навигатор
           │       └──► Перехват событий
           │           └──► Преобразование
           │               └──► SVMeterInteraction
           │                   └──► CAN/QNX
           │
           └──► Другие наши приложения
```

---

## 📋 Пошаговый план реализации

### Этап 1: Подготовка и исследование (3-5 дней)

#### 1.1 Исследование текущей системы

**Задачи:**
- [ ] Изучить текущий лаунчер системы
- [ ] Понять механизм скрытия приложений
- [ ] Исследовать системные разрешения
- [ ] Проверить доступ к системным разделам

**Инструменты:**
```bash
# Получение списка приложений
adb shell pm list packages

# Получение информации о лаунчере
adb shell pm query-activities -a android.intent.action.MAIN -c android.intent.category.HOME

# Проверка разрешений
adb shell dumpsys package | grep permission
```

#### 1.2 Подготовка инструментов

**Задачи:**
- [ ] Настроить ADB
- [ ] Подготовить скрипты установки
- [ ] Создать резервные копии системных приложений
- [ ] Подготовить тестовое окружение

**Скрипты:**
```bash
# backup_system.sh
#!/bin/bash
adb root
adb remount
adb pull /system/app/ ./backup/system_app/
adb pull /system/priv-app/ ./backup/system_priv-app/
```

#### 1.3 Анализ системных приложений

**Задачи:**
- [ ] Декомпилировать SVMedia
- [ ] Декомпилировать SVMapService
- [ ] Изучить протоколы обмена данными
- [ ] Понять механизм вывода на приборную панель

---

### Этап 2: Разработка Custom Launcher (5-7 дней)

#### 2.1 Создание базового лаунчера

**Задачи:**
- [ ] Создать проект Android Studio
- [ ] Реализовать базовый лаунчер
- [ ] Добавить список приложений
- [ ] Реализовать запуск приложений

**Код:**
```java
public class CustomLauncherActivity extends Activity {
    private RecyclerView appList;
    private AppListAdapter adapter;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_launcher);
        
        appList = findViewById(R.id.app_list);
        adapter = new AppListAdapter(getInstalledApps());
        appList.setAdapter(adapter);
    }
    
    private List<AppInfo> getInstalledApps() {
        // Получение списка приложений
        // Фильтрация системных приложений
    }
}
```

#### 2.2 Скрытие системных приложений

**Задачи:**
- [ ] Реализовать фильтрацию системных приложений
- [ ] Скрыть системные приложения из списка
- [ ] Обработать попытки запуска системных приложений

**Код:**
```java
private List<AppInfo> filterSystemApps(List<AppInfo> apps) {
    String[] systemPackages = {
        "com.desaysv.mediaapp",
        "com.desaysv.mapservice",
        // ... другие
    };
    
    return apps.stream()
        .filter(app -> !Arrays.asList(systemPackages).contains(app.packageName))
        .collect(Collectors.toList());
}
```

#### 2.3 Установка как системного лаунчера

**Задачи:**
- [ ] Добавить Intent Filter для HOME
- [ ] Установить как системное приложение
- [ ] Настроить как лаунчер по умолчанию

**AndroidManifest.xml:**
```xml
<activity
    android:name=".CustomLauncherActivity"
    android:launchMode="singleTask"
    android:theme="@android:style/Theme.NoTitleBar">
    <intent-filter>
        <action android:name="android.intent.action.MAIN" />
        <category android:name="android.intent.category.HOME" />
        <category android:name="android.intent.category.DEFAULT" />
    </intent-filter>
</activity>
```

---

### Этап 3: Модификация SVMedia (7-10 дней)

#### 3.1 Декомпиляция и анализ

**Задачи:**
- [ ] Декомпилировать SVMedia.apk
- [ ] Изучить код выбора источника
- [ ] Найти где обрабатываются метаданные
- [ ] Понять формат отправки в SVMeterInteraction

**Инструменты:**
```bash
# Декомпиляция
jadx -d SVMedia_sources SVMedia.apk
```

#### 3.2 Добавление источника "Яндекс Музыка"

**Задачи:**
- [ ] Модифицировать UI выбора источника
- [ ] Добавить обработчик для Яндекс Музыки
- [ ] Реализовать запуск Яндекс Музыки

**Код:**
```java
// В MediaMainActivity
private void onSourceSelected(int sourceId) {
    switch (sourceId) {
        case R.id.source_yandex_music:
            launchYandexMusic();
            startMetadataListener();
            break;
        // ... другие источники
    }
}

private void launchYandexMusic() {
    Intent intent = new Intent();
    intent.setComponent(new ComponentName(
        "ru.yandex.music",
        "ru.yandex.music.ui.MainActivity"
    ));
    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
    startActivity(intent);
}
```

#### 3.3 Реализация получения метаданных

**Задачи:**
- [ ] Реализовать MediaSession API listener
- [ ] Получать метаданные от Яндекс Музыки
- [ ] Обрабатывать изменения метаданных

**Код:**
```java
public class YandexMusicMetadataListener {
    private MediaController mediaController;
    
    public void startListening() {
        MediaSessionManager sessionManager = 
            (MediaSessionManager) context.getSystemService(Context.MEDIA_SESSION_SERVICE);
        
        List<MediaController> controllers = sessionManager.getActiveSessions(
            new ComponentName(context, MediaButtonReceiver.class)
        );
        
        for (MediaController controller : controllers) {
            if ("ru.yandex.music".equals(controller.getPackageName())) {
                mediaController = controller;
                mediaController.registerCallback(callback);
                break;
            }
        }
    }
    
    private MediaController.Callback callback = new MediaController.Callback() {
        @Override
        public void onMetadataChanged(MediaMetadata metadata) {
            String artist = metadata.getString(MediaMetadata.METADATA_KEY_ARTIST);
            String title = metadata.getString(MediaMetadata.METADATA_KEY_TITLE);
            String album = metadata.getString(MediaMetadata.METADATA_KEY_ALBUM);
            
            sendToMeterInteraction(artist, title, album);
        }
    };
}
```

#### 3.4 Интеграция с системой

**Задачи:**
- [ ] Отправка метаданных в SVMeterInteraction
- [ ] Использование существующего Broadcast Intent
- [ ] Тестирование отображения на приборной панели

**Код:**
```java
private void sendToMeterInteraction(String artist, String title, String album) {
    Intent intent = new Intent("com.desaysv.mediaservice.TRACK_UPDATE");
    intent.putExtra("artist", artist);
    intent.putExtra("title", title);
    intent.putExtra("album", album);
    intent.putExtra("source", "yandex_music");
    sendBroadcast(intent);
}
```

---

### Этап 4: Разработка Bridge Service (7-10 дней)

#### 4.1 Создание проекта

**Задачи:**
- [ ] Создать проект Android Studio
- [ ] Настроить разрешения
- [ ] Реализовать базовую структуру

**Разрешения:**
```xml
<uses-permission android:name="android.permission.QUERY_ALL_PACKAGES"/>
<uses-permission android:name="android.permission.REORDER_TASKS"/>
<uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW"/>
```

#### 4.2 Запуск Яндекс Навигатора

**Задачи:**
- [ ] Реализовать запуск Яндекс Навигатора (из NS.apk)
- [ ] Переключение на передний план
- [ ] Обработка ошибок

#### 4.3 Перехват событий

**Задачи:**
- [ ] Исследовать события Яндекс Навигатора
- [ ] Реализовать Broadcast Receiver
- [ ] Или использовать Accessibility Service

#### 4.4 Преобразование данных

**Задачи:**
- [ ] Изучить формат данных TurboDog
- [ ] Реализовать адаптер данных
- [ ] Преобразование событий навигации

#### 4.5 Интеграция с системой

**Задачи:**
- [ ] Отправка в SVMeterInteraction
- [ ] Отправка в CAN-шину
- [ ] Отправка в QNX (если нужно)

---

### Этап 5: Разработка Media Bridge (5-7 дней)

#### 5.1 Создание проекта

**Задачи:**
- [ ] Создать проект Android Studio
- [ ] Настроить разрешения
- [ ] Реализовать базовую структуру

#### 5.2 Получение метаданных

**Задачи:**
- [ ] Реализовать MediaSession API listener
- [ ] Получать метаданные от различных приложений
- [ ] Обрабатывать изменения

#### 5.3 Отправка в систему

**Задачи:**
- [ ] Отправка в SVMeterInteraction
- [ ] Использование существующего формата
- [ ] Тестирование отображения

---

### Этап 6: Создание пакета установки (3-5 дней)

#### 6.1 Подготовка APK

**Задачи:**
- [ ] Подписать все APK
- [ ] Проверить совместимость
- [ ] Подготовить документацию

#### 6.2 Создание скрипта установки

**Задачи:**
- [ ] Создать скрипт установки
- [ ] Добавить проверки
- [ ] Добавить откат

**Скрипт:**
```bash
#!/bin/bash
# install_package.sh

echo "Starting installation..."

# 1. Backup
echo "Creating backup..."
./backup_system.sh

# 2. Root access
echo "Getting root access..."
adb root
adb remount

# 3. Install Custom Launcher
echo "Installing Custom Launcher..."
adb push CustomLauncher.apk /system/app/CustomLauncher/
adb shell chmod 644 /system/app/CustomLauncher/CustomLauncher.apk

# 4. Install modified SVMedia
echo "Installing modified SVMedia..."
adb push SVMedia_modified.apk /system/app/SVMedia/
adb shell chmod 644 /system/app/SVMedia/SVMedia_modified.apk

# 5. Install Bridge Service
echo "Installing Bridge Service..."
adb push BridgeService.apk /system/priv-app/BridgeService/
adb shell chmod 644 /system/priv-app/BridgeService/BridgeService.apk

# 6. Install Media Bridge
echo "Installing Media Bridge..."
adb push MediaBridge.apk /system/priv-app/MediaBridge/
adb shell chmod 644 /system/priv-app/MediaBridge/MediaBridge.apk

# 7. Reboot
echo "Rebooting..."
adb reboot

echo "Installation complete!"
```

#### 6.3 Создание скрипта отката

**Задачи:**
- [ ] Создать скрипт отката
- [ ] Восстановить оригинальные приложения
- [ ] Восстановить оригинальный лаунчер

**Скрипт:**
```bash
#!/bin/bash
# rollback.sh

echo "Starting rollback..."

# 1. Root access
adb root
adb remount

# 2. Remove our apps
echo "Removing our apps..."
adb shell rm -rf /system/app/CustomLauncher/
adb shell rm -rf /system/app/SVMedia/
adb shell rm -rf /system/priv-app/BridgeService/
adb shell rm -rf /system/priv-app/MediaBridge/

# 3. Restore original apps
echo "Restoring original apps..."
adb push ./backup/system_app/SVMedia/ /system/app/SVMedia/

# 4. Reboot
echo "Rebooting..."
adb reboot

echo "Rollback complete!"
```

---

### Этап 7: Тестирование (5-7 дней)

#### 7.1 Функциональное тестирование

**Задачи:**
- [ ] Тестирование Custom Launcher
- [ ] Тестирование модифицированного SVMedia
- [ ] Тестирование Bridge Service
- [ ] Тестирование Media Bridge

#### 7.2 Интеграционное тестирование

**Задачи:**
- [ ] Тестирование интеграции с системой
- [ ] Тестирование отображения на приборной панели
- [ ] Тестирование работы с CAN/QNX

#### 7.3 Тестирование стабильности

**Задачи:**
- [ ] Долгосрочное тестирование
- [ ] Тестирование при перезагрузке
- [ ] Тестирование при обновлениях

---

## 🔧 Технические детали

### Разрешения для системных приложений

**Custom Launcher:**
```xml
<uses-permission android:name="android.permission.QUERY_ALL_PACKAGES"/>
<uses-permission android:name="android.permission.SET_PREFERRED_APPLICATIONS"/>
```

**Bridge Service:**
```xml
<uses-permission android:name="android.permission.QUERY_ALL_PACKAGES"/>
<uses-permission android:name="android.permission.REORDER_TASKS"/>
<uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW"/>
```

**Media Bridge:**
```xml
<uses-permission android:name="android.permission.MEDIA_CONTENT_CONTROL"/>
```

### Установка как системное приложение

**Путь установки:**
- `/system/app/` - обычные системные приложения
- `/system/priv-app/` - привилегированные системные приложения

**Права доступа:**
```bash
chmod 644 /system/app/MyApp/MyApp.apk
chown root:root /system/app/MyApp/MyApp.apk
```

---

## 📚 Документация

### Для пользователя:
- Инструкция по установке
- Инструкция по использованию
- Инструкция по откату

### Для разработчика:
- Архитектура решения
- API документация
- Процедуры разработки

---

**Статус:** План готов к реализации  
**Дата:** 2024  
**Версия:** 1.0

