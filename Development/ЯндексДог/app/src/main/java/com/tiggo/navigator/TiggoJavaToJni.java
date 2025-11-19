/**
 * TiggoJavaToJni - JNI слой для вызова нативного кода (аналог JavaToJni из TurboDog)
 * 
 * Стиль TurboDog:
 * - Native методы для вызова нативного кода
 * - Префиксы функций как в TurboDog
 * - JSON протокол для обмена данными
 */
package com.tiggo.navigator;

import android.content.res.AssetManager;

public class TiggoJavaToJni {
    static {
        System.loadLibrary("tiggo_navigator");
    }

    // ========== OpenGL функции (в стиле TurboDog) ==========
    
    /**
     * Создание основного OpenGL контекста
     * @param simplified TRUE для упрощенного режима (Display 1), FALSE для полноценного (Display 0)
     * @param enable3D TRUE для 3D режима, FALSE для 2D
     * @return 0 при успехе, -1 при ошибке
     */
    public static native int CreateGL(boolean simplified, boolean enable3D);

    /**
     * Создание вторичного OpenGL контекста для второго дисплея
     * @param width ширина окна
     * @param height высота окна
     * @param index индекс окна
     * @param simplified TRUE для упрощенного режима (Display 1)
     * @param dpi DPI дисплея
     * @param format формат
     * @param flags флаги
     * @param additionalFlags дополнительные флаги
     * @return индекс созданного окна, -1 при ошибке
     */
    public static native int CreateSecondaryGL(int width, int height, int index, 
                                               boolean simplified, int dpi, int format, 
                                               int flags, int additionalFlags);

    /**
     * Рендеринг основного окна (Display 0)
     */
    public static native void RenderGL();

    /**
     * Рендеринг второго окна (Display 1 - Presentation)
     * @param index индекс окна
     */
    public static native void RenderSecondaryWndGL(int index);

    /**
     * Уничтожение OpenGL контекста
     */
    public static native void DestroyGL();

    /**
     * Добавление второго окна (Presentation)
     * @param x координата X
     * @param y координата Y
     * @param width ширина
     * @param height высота
     * @param dpi DPI
     * @param simplified TRUE для упрощенного режима
     * @param format формат
     * @param flags флаги
     * @param additionalFlags дополнительные флаги
     * @param reserved зарезервировано
     * @return индекс созданного окна, -1 при ошибке
     */
    public static native int AddSecondaryWndGL(int x, int y, int width, int height, 
                                               int dpi, boolean simplified, int format,
                                               int flags, int additionalFlags, int reserved);

    /**
     * Удаление второго окна
     * @param index индекс окна
     */
    public static native void DeleteSecondaryWndGL(int index);

    /**
     * Установка размера второго окна
     * @param index индекс окна
     * @param width ширина
     * @param height высота
     * @param x координата X
     * @param y координата Y
     * @param dpi DPI
     * @param simplified TRUE для упрощенного режима
     */
    public static native void SetSecondaryWndSize(int index, int width, int height, 
                                                  int x, int y, int dpi, boolean simplified);

    /**
     * Установка размера основного окна
     * @param width ширина
     * @param height высота
     */
    public static native void SetWindowSizeGL(int width, int height);

    /**
     * Отмена рендеринга
     */
    public static native void CancelRenderGL();

    /**
     * Установка метрик дисплея
     * @param dpi DPI
     */
    public static native void SetDisplayMetricsGL(int dpi);

    // ========== Lifecycle функции (в стиле TurboDog) ==========

    /**
     * Инициализация при создании Activity
     * @param simplified TRUE для упрощенного режима
     */
    public static native void OnCreate(boolean simplified);

    /**
     * Завершение при уничтожении Activity
     */
    public static native void OnDestroy();

    /**
     * Инициализация движка
     * @param width ширина экрана
     * @param height высота экрана
     * @return TRUE при успехе, FALSE при ошибке
     */
    public static native boolean OnInit(int width, int height);

    /**
     * Приостановка Activity
     */
    public static native void OnPause();

    /**
     * Возобновление Activity
     */
    public static native void OnResume();

    /**
     * Финализация
     */
    public static native void Finalized();

    /**
     * Установка фона приложения
     * @param inBackground TRUE если приложение в фоне
     */
    public static native void SetAppInBackground(boolean inBackground);

    // ========== GPS/IMU функции (в стиле TurboDog) ==========

    /**
     * Обновление GPS координат
     * @param latitude широта
     * @param longitude долгота
     * @param speed скорость в км/ч
     * @param bearing курс в градусах (0-360)
     * @param accuracy точность в метрах
     */
    public static native void OnLocationUpdate(float latitude, float longitude, 
                                               float speed, float bearing, float accuracy);

    /**
     * Отправка GPS данных в NMEA формате
     * @param nmeaData NMEA данные
     * @param length длина данных
     */
    public static native void AstrobGPSPostNMEA(byte[] nmeaData, int length);

    /**
     * Отправка IMU данных
     * @param imuData IMU данные
     * @param length длина данных
     * @param timestamp временная метка
     */
    public static native void AstrobDRPostIMU(byte[] imuData, int length, double timestamp);

    // ========== Протокол обмена данными (JSON, как в TurboDog) ==========

    /**
     * Отправка протокольного запроса в нативный код (JSON)
     * @param jsonRequest JSON строка с запросом
     * @return TRUE при успехе, FALSE при ошибке
     */
    public static native boolean OnProtocolRequest(String jsonRequest);

    // ========== Данные от Yandex MapKit (НОВОЕ) ==========

    /**
     * Ограничение скорости от Yandex
     * @param speedLimitKmh ограничение скорости в км/ч
     * @param text текстовое представление ("60 km/h")
     */
    public static native void OnYandexSpeedLimit(int speedLimitKmh, String text);

    /**
     * Маневр от Yandex
     * @param type тип маневра (0=STRAIGHT, 1=LEFT, 2=RIGHT, 3=UTURN)
     * @param distanceMeters расстояние до маневра в метрах
     * @param timeSeconds время до маневра в секундах
     * @param title заголовок маневра ("Поверните налево")
     * @param subtitle подзаголовок маневра ("на улицу Ленина")
     */
    public static native void OnYandexManeuver(int type, int distanceMeters, int timeSeconds,
                                               String title, String subtitle);

    /**
     * Маршрут от Yandex
     * @param routePoints массив точек маршрута [lat1, lon1, lat2, lon2, ...]
     * @param distanceMeters расстояние маршрута в метрах
     * @param timeSeconds время маршрута в секундах
     */
    public static native void OnYandexRoute(double[] routePoints, int distanceMeters, int timeSeconds);

    /**
     * Местоположение от Yandex
     * @param latitude широта
     * @param longitude долгота
     * @param bearing направление движения в градусах
     * @param speed скорость в м/с
     * @param roadName название дороги
     */
    public static native void OnYandexLocation(double latitude, double longitude, 
                                               float bearing, float speed, String roadName);

    /**
     * Статус маршрута от Yandex
     * @param isActive TRUE если маршрут активен
     * @param isRecalculating TRUE если маршрут пересчитывается
     */
    public static native void OnYandexRouteStatus(boolean isActive, boolean isRecalculating);

    // ========== Asset Manager (в стиле TurboDog) ==========

    /**
     * Создание Asset Manager
     * @param assetManager Asset Manager из Android
     */
    public static native void CreateAssetManager(AssetManager assetManager);

    /**
     * Уничтожение Asset Manager
     */
    public static native void DestroyAssetManager();

    // ========== Утилиты (в стиле TurboDog) ==========

    /**
     * Установка системной директории
     * @param dir путь к системной директории
     */
    public static native void SetSystemDir(String dir);

    /**
     * Установка USB директории
     * @param dir путь к USB директории
     */
    public static native void SetUsbDir(String dir);

    /**
     * Установка статуса сети
     * @param status статус сети
     * @param type тип сети
     */
    public static native void SetNetStatus(int status, int type);

    /**
     * Изменение языка
     * @param languageId ID языка
     */
    public static native void ChangeLanguage(int languageId);

    /**
     * Получение версии карты
     * @return версия карты
     */
    public static native String GetMapVersion();

    /**
     * Получение единиц измерения
     * @return 0 = метры, 1 = мили
     */
    public static native int GetMeasureUnit();

    /**
     * Обновление камеры карты (для перемещения и масштабирования)
     * @param latitude широта камеры
     * @param longitude долгота камеры
     * @param zoom уровень масштабирования
     * @param bearing направление камеры в градусах (0-360)
     * @param tilt наклон камеры в градусах (0-90)
     */
    public static native void UpdateCamera(float latitude, float longitude, 
                                          float zoom, float bearing, float tilt);

    /**
     * Получение текущей широты GPS
     * @return широта или 0.0f если координаты еще не получены
     */
    public static native float GetCurrentLatitude();

    /**
     * Получение текущей долготы GPS
     * @return долгота или 0.0f если координаты еще не получены
     */
    public static native float GetCurrentLongitude();

    /**
     * Проверка, активирована ли карта
     * @return TRUE если карта активирована
     */
    public static native boolean IsMapActivated();

    /**
     * Запись лога
     * @param message сообщение для лога
     */
    public static native void WriteLog(String message);
    
    // ========== Загрузка тайлов от Yandex (НОВОЕ) ==========
    
    /**
     * Передача загруженного тайла в нативный код
     * Вызывается из TileLoader после загрузки тайла
     * 
     * @param tileX координата X тайла
     * @param tileY координата Y тайла
     * @param zoom уровень масштабирования
     * @param bitmap Bitmap изображение тайла
     * @return TRUE при успехе, FALSE при ошибке
     */
    public static native boolean OnYandexTileLoaded(int tileX, int tileY, int zoom, android.graphics.Bitmap bitmap);
}

