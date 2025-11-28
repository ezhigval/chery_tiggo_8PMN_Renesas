## QNX ↔ Android: взаимодействие навигации и системных сервисов

В этой инструкции собрана детальная информация о том, как на головном устройстве организовано взаимодействие **QNX ↔ Android** в части навигации **TurboDog**, десаевских системных сервисов, приборной панели, второго дисплея (HDMI/cluster), а также как сверху на это накладываются темы/скины.

Материал основан на реальном анализе устройства через `adb`, `dumpsys`, `logcat` и извлечённые APK.

## Основные компоненты

- **Навигационное приложение (Android)**: `com.astrob.turbodog`
  - Основное `Activity`: `com.astrob.turbodog/.WelcomeActivity`
  - Навигационный сервис: `com.astrob.turbodog/.TurboDogGpsService`
  - Собственный AIDL/IPC сервис: `NaviAIDLService` (логирует `autoStatus` и другие состояния).
  - GL/рендер‑слой: класс/слой `CTurboDogDlg`, создающий основное и вторичные окна.

- **Map‑сервис Desay (Android)**: `com.desaysv.mapservice`
  - APK: `SVMapService.apk` (в проекте: `apks/com.desaysv.mapservice.apk`)
  - Важные классы (по стектрейсам логов):
    - `com.desaysv.mapservice.manager.SVCarLanManager`
    - `com.desaysv.mapservice.manager.MeterControl`
    - `com.desaysv.mapservice.util.ActivityUtil`
    - `com.desaysv.mapservice.adapter.map.turbodog.TurboDogAdapter`

- **Системный ассистент/аватар и boot‑progress (Android)**: `com.iflytek.avatarService`
  - APK: `IflytekAvatar.apk` (в проекте: `apks/com.iflytek.avatarService.apk`)
  - Сервис: `com.iflytek.avatarService/.SceneEgineService`
  - Рисует:
    - окно `ty=BOOT_PROGRESS` (экран прогресса при загрузке),
    - окно `ty=SYSTEM_OVERLAY` (окно ассистента/аватара).

- **Системный UI (Android)**: `com.android.systemui`
  - Окна шторок/панелей:
    - `NavigationBar` (`ty=NAVIGATION_BAR`)
    - `StatusBar` (`ty=STATUS_BAR`)
    - `SystemUI_smallPanel`, `SystemUI_Container` (`ty=FIRST_DESAYSV_CUSTOM_WINDOW`)

- **Климат (верхняя шторка)**: `com.desaysv.svhvac`
  - Окно `SVAirCondition` (`ty=FIRST_DESAYSV_CUSTOM_WINDOW`).

- **QNX‑сторона**
  - Не видна напрямую через `adb`, но видны её сообщения, приходящие в `SVCarLanManager` (`com.desaysv.mapservice.manager.SVCarLanManager`), которые инициируют действия на Android‑стороне.

## Дисплеи и окна

По `dumpsys window displays`:

- **Основной дисплей**:
  - `Display: mDisplayId=0`
  - Тип: `BUILT_IN`
  - Разрешение: `1920x720`
  - Здесь живут:
    - Launcher, настройки, TurboDog основное окно и т.д.

- **Второй дисплей (HDMI / приборная панель / cluster)**:
  - `Display: mDisplayId=1`
  - Тип: `HDMI`
  - Разрешение: `1920x720`
  - Здесь отображается, в частности, карта TurboDog через `Presentation`‑окно.

### Примеры окон на дисплеях

- Основное окно TurboDog (на `mDisplayId=0`):

  - `ActivityManager`:
    - `START u0 {flg=0x10000000 cmp=com.astrob.turbodog/.WelcomeActivity}`
  - `WindowManager`:
    - `Window{... u0 com.desaysv.vehiclesetting/...}` и др. — обычные приложения.

- Окно TurboDog на втором дисплее (на `mDisplayId=1`):

  - В `dumpsys window windows`:

    - `Window #13 Window{... u0 com.astrob.turbodog}`  
      - `mDisplayId=1`  
      - `package=com.astrob.turbodog`  
      - `ty=PRESENTATION`  
      - `mFrame=[0,0][1920,720]`

  Это `Presentation`‑окно, созданное самим TurboDog для вывода карты на HDMI/cluster.

## Окна ассистента и прогресса загрузки

### Boot‑progress

- Окно:
  - `Window{... u0 com.iflytek.avatarService}`
  - `ty=BOOT_PROGRESS`
  - Владeлец: `com.iflytek.avatarService` (UID 1000, системный).

- Из `dumpsys package com.iflytek.avatarService`:
  - Имеет права:
    - `android.permission.SYSTEM_ALERT_WINDOW`
    - `android.permission.SYSTEM_OVERLAY_WINDOW`
    - `android.permission.INTERNAL_SYSTEM_WINDOW`
    - `android.permission.RECEIVE_BOOT_COMPLETED`

**Поведение:**

- После загрузки устройства:
  - Система посылает `BOOT_COMPLETED`.
  - `com.iflytek.avatarService` поднимает `SceneEgineService` и создаёт окно `BOOT_PROGRESS` через `WindowManager.addView(...)`.
  - Когда система готова, окно удаляется (`WindowManager.removeView(...)`), и становится виден launcher и прочий UI.

### Ассистент / аватар

- Окно:
  - `Window{... u0 com.iflytek.avatarService}`
  - `ty=SYSTEM_OVERLAY`
  - `appop=SYSTEM_ALERT_WINDOW`
  - Размеры порядка `398x350`, в верхнем левом углу.

- Сцена/движок:
  - `com.iflytek.autofly.sceneengine`:
    - Окно `ty=APPLICATION_OVERLAY`, размер `1x1`, используется как невидимый триггер.

**Цепочка:**

- `com.iflytek.autofly.sceneengine` решает по сценарию, что нужно показать/изменить ассистента.
- Отправляет Intent с action `com.iflytek.autofly.AVATARDECISION`.
- Этот action мапится в `SceneEgineService` (`com.iflytek.avatarService/.SceneEgineService`).
- `SceneEgineService` через `WindowManager` создаёт/обновляет окно `SYSTEM_OVERLAY` (аватар) и управляет его видимостью.

## Темы/текстурпаки

На экране настроек (класс `com.desaysv.setting/.ui.activity.SecondSettingActivity`) можно выбрать одну из трёх тем/скинов. При смене темы меняются системные настройки и системные свойства.

### Ключевые настройки и свойства

Сняты слепки до и после смены темы (`theme_debug/*_before.txt` / `*_after.txt`).

**Settings.System:**

- При смене темы:
  - `com.desaysv.setting.temp.theme.mode`: `2 → 1`
  - `com.desaysv.setting.theme.mode.self`: `2 → 1`
  - `com.desaysv.setting.theme.mode`: `2 → 1`

Это числовой идентификатор активной темы (0/1/2).

**Системные свойства (`getprop`):**

- `persist.vpa.theme`:
  - пример: `topic3.skin → topic2.skin`
  - человекочитаемое имя темы (`topicX.skin`).

- `sys.theme.change.state`:
  - появляется/меняется в процессе смены темы (флаг текущего процесса смены темы).

Файлов `*.skin` в явном виде в системе не найдено, поэтому темы, вероятнее всего, представлены как наборы ресурсов внутри системных APK (launcher, настройки, SystemUI и т.д.), а `topicX.skin` — логическое название профиля.

### Интеграция кастомного приложения с темами

Приложение может “подстраиваться” под тему, если:

- Читает настройки:
  - `Settings.System.getInt(contentResolver, "com.desaysv.setting.theme.mode", ...)`
  - либо парсит `persist.vpa.theme` через `getprop` (при наличии подходящих прав).
- Подписывается на изменения:
  - через `ContentObserver` на `Settings.System.getUriFor("com.desaysv.setting.theme.mode")`;
  - либо через broadcast’ы, если OEM их шлёт (для этого нужно анализировать APK `com.desaysv.setting`).

## TurboDog и второй дисплей

### Создание вторичного окна (Presentation)

При запуске `WelcomeActivity` TurboDog лог показывает:

- Старт Activity:

  - `ActivityManager: START u0 {flg=0x10000000 cmp=com.astrob.turbodog/.WelcomeActivity}`

- Инициализация движка:

  - `CTurboDogDlg OnInitDialog, w=1920, h=720`
  - `Startup In Foreground--CTurboDogDlg::TurboDog_CreateGL`
  - `TurboDog_CreateNVG`

- Создание вторичного окна:

  - `CTurboDogDlg::AddSecondaryWnd w=0, h=0, dpi=0, nWndIdx=3`
  - `SecondaryRenderThread():AddSecondaryWndGL(0, 0) index=3`

По `dumpsys window windows` видно, что результат — окно `ty=PRESENTATION` на `mDisplayId=1`:

- `Window{... u0 com.astrob.turbodog}`
  - `mDisplayId=1`
  - `ty=PRESENTATION`
  - `mFrame=[0,0][1920,720]`

Именно это окно выводит карту на HDMI/приборную панель.

## Взаимодействие QNX ↔ Android при открытии карты

### Сценарий: карта открывается с приборной панели (QNX инициирует)

#### 1. Сообщение от QNX попадает в `SVCarLanManager`

В логах (`logcat_turbodog_qnx.txt`):

- Стек:

  - `com.desaysv.mapservice.manager.SVCarLanManager$1$1.onMessage:75`
  - `com.desaysv.mapservice.manager.MeterControl.displayControl:55`
  - `com.desaysv.mapservice.util.ActivityUtil.sendTurboDogScreenBroadcast:229`

Значит:

- QNX → шина → `SVCarLanManager.onMessage()`.
- Внутри `SVCarLanManager` вызывается `MeterControl.displayControl(...)`.
- `MeterControl` решает, что нужно показать TurboDog.
- `ActivityUtil.sendTurboDogScreenBroadcast(...)` отправляет системный broadcast для включения “экрана TurboDog”.

#### 2. Система запускает TurboDog

Лог:

- `ActivityManager: START u0 {flg=0x10000000 cmp=com.astrob.turbodog/.WelcomeActivity} from uid 1000, pid 2487`

Здесь:

- `from uid 1000` → запуск инициирован системным процессом (как раз `com.desaysv.mapservice`).
- Цель: `com.astrob.turbodog/.WelcomeActivity`.

#### 3. TurboDog создаёт главное и вторичное окна

- Основное окно инициализируется через:

  - `CTurboDogDlg OnInitDialog, w=1920, h=720`
  - `TurboDog_CreateGL`

- Вторичное окно на cluster/HDMI:

  - `CTurboDogDlg::AddSecondaryWnd ...`
  - `SecondaryRenderThread():AddSecondaryWndGL(...)`

И это вторичное окно (`ty=PRESENTATION` на `mDisplayId=1`) попадает на приборку.

## Обмен сообщениями при построении маршрута

### Состояния навигации

При построении маршрута лог `NaviAIDLService` показывает смену `autoStatus`:

- Примеры:
  - `autoStatus:14` → состояние навигации (например, подготовка/расчёт маршрута).
  - `autoStatus:1`
  - `autoStatus:16` → состояние после построения маршрута.

Эти статусы используются для синхронизации состояния движка и внешних компонентов.

### Сообщения TurboDog → MapService → приборка/проекция

Ключевые сообщения:

- `GenericCustomCenter`:

  - `Intent { act=turbodog.navigation.system.message (has extras) } Bundle[{CODE=202, DATA=1}]`

  `CODE=202` с `DATA=1` — это сообщение TurboDog о том, что маршрут построен/активен.

- Далее:

  - `NaviAIDLService: ... "autoStatus":16`
  - `FunctionLayer: FL_ConfigImp::FLSaveSet(): ... SystemSet.dat`

**Обработка на стороне Desay:**

- `ActivityUtil.sendBroadcast:188`
- `com.desaysv.mapservice.adapter.map.turbodog.TurboDogAdapter$3.onReceive:512`

То есть:

- `turbodog.navigation.system.message` ловится `TurboDogAdapter` внутри `com.desaysv.mapservice`.
- Через `ActivityUtil.sendBroadcast(...)` это состояние/данные прокидывается дальше — по специфической десаевской шине в компоненты, отвечающие за приборку и HUD.

Параллельно TurboDog запрашивает аудиофокус для голосовых подсказок:

- `MediaFocusControl: requestAudioFocus() ... USAGE_ASSISTANCE_NAVIGATION_GUIDANCE`

## Как смотреть и анализировать этот стек самостоятельно

### 1. Просмотр экранов и окон

- Активное Activity:

```bash
adb shell dumpsys activity activities | grep mResumedActivity
```

- Окна по дисплеям:

```bash
adb shell dumpsys window displays
adb shell dumpsys window windows
```

### 2. Отладка TurboDog и mapservice

- Лог по TurboDog и связанным компонентам:

```bash
adb logcat -v time | grep -i -e astrob -e turbodog -e turbodog.navigation.system.message -e SVCarLanManager -e MeterControl
```

- Проверка процессов:

```bash
adb shell ps -A | grep -i turbodog
adb shell ps -A | grep -i mapservice
```

### 3. Анализ APK (offline)

Уже скачанные APK:

- `apks/com.astrob.turbodog.apk`
- `apks/com.desaysv.mapservice.apk`
- `apks/com.iflytek.avatarService.apk`
- и др. (launcher, settings, themes).

Рекомендуемый инструментарий:

- `jadx-gui` — для просмотра smali/Java‑декompиляции.
- `apktool` — для декомпиляции ресурсов (`res/`), манифеста и стилей.

Искомые классы/пакеты:

- В TurboDog:
  - классы, содержащие:
    - `CTurboDogDlg`
    - `SecondaryRenderThread`
    - `TurboDogGpsService`
    - `NaviAIDLService`
    - обработчики `turbodog.navigation.system.message`

- В Desay mapservice:
  - `com.desaysv.mapservice.manager.SVCarLanManager`
  - `com.desaysv.mapservice.manager.MeterControl`
  - `com.desaysv.mapservice.util.ActivityUtil`
  - `com.desaysv.mapservice.adapter.map.turbodog.TurboDogAdapter`

## Итоговая схема взаимодействия

- **QNX → Android**:
  - QNX шлёт сообщение (например, “показать карту”) → попадает в `SVCarLanManager.onMessage()` → `MeterControl.displayControl()` → `ActivityUtil.sendTurboDogScreenBroadcast()` → системный broadcast → `ActivityManager` запускает `com.astrob.turbodog/.WelcomeActivity`.

- **Android (TurboDog) → второе окно**:
  - `WelcomeActivity` инициализирует рендер → `CTurboDogDlg::AddSecondaryWnd` → `SecondaryRenderThread.AddSecondaryWndGL(...)` → создаётся `Presentation`‑окно на `mDisplayId=1` (карта на приборке/HDMI).

- **TurboDog → Desay mapservice → приборка/проекция при маршруте**:
  - TurboDog отправляет `turbodog.navigation.system.message` (`CODE=202`, `DATA=1`) и другие коды через `GenericCustomCenter`.
  - Эти сообщения ловит `TurboDogAdapter` в `com.desaysv.mapservice`, который через `ActivityUtil.sendBroadcast()` прокидывает состояние/данные дальше в компоненты, рисующие подсказки на приборке и в HUD.

- **Темы/скины**:
  - Меняются через `com.desaysv.setting` (`SecondSettingActivity`), что обновляет:
    - `Settings.System` (`com.desaysv.setting.theme.mode`, и др.),
    - `persist.vpa.theme` (`topicX.skin`).
  - Приложения могут подстраиваться под тему, читая эти значения и реагируя на их изменения.


