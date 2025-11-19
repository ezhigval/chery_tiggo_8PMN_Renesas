/**
 * tiggo_engine.h - Главный класс навигационного движка (в стиле TurboDog)
 * 
 * Стиль кода TurboDog:
 * - Префикс C для структур
 * - Префикс Tiggo_ для функций
 * - Hungarian notation для переменных
 * - Указатели через p префикс
 */

#ifndef TIGGO_ENGINE_H
#define TIGGO_ENGINE_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Boolean тип (как в TurboDog)
typedef int BOOL;
#define TRUE  1
#define FALSE 0

// Основная структура движка (в стиле CTurboDogDlg)
typedef struct CTiggoEngine {
    // Состояние
    BOOL m_bInitialized;
    BOOL m_bNavigationActive;
    BOOL m_bMapActivated;
    
    // Данные навигации
    int m_nSpeedLimitKmh;
    int m_nNextManeuverDistance;
    int m_nNextManeuverType;      // Тип маневра (0-нет, 1-налево, 2-направо, и т.д.)
    float m_fCurrentLat;
    float m_fCurrentLon;
    float m_fCurrentSpeed;        // Текущая скорость в км/ч
    float m_fCurrentBearing;      // Текущий курс в градусах
    
    // Название дороги
    char m_pcCurrentRoadName[256];
    
    // Размеры экрана
    int m_nMainDisplayWidth;
    int m_nMainDisplayHeight;
    int m_nSecondaryDisplayWidth;
    int m_nSecondaryDisplayHeight;
    
    // Указатели на компоненты (p префикс)
    void* m_pNavigationState;
    void* m_pRouteCalculator;
    void* m_pGpsProcessor;
    
    // Указатель на данные рендеринга (для OpenGL ES)
    void* m_pRenderData;
    
    // Callback для отправки данных в Java (broadcast)
    void* m_pNavigationCallback;
    void* m_pCallbackUserData;
    
    // Дополнительные данные (например, для Yandex MapKit)
    void* m_pYandexBridge;
    
    // Внутренние данные
    void* m_pInternal;
} CTiggoEngine;

/**
 * Инициализация и завершение
 * Стиль: Tiggo_FunctionName (как TurboDog_CreateGL)
 */
BOOL Tiggo_Initialize(CTiggoEngine* pEngine);
void Tiggo_Shutdown(CTiggoEngine* pEngine);

/**
 * Создание/уничтожение движка
 */
CTiggoEngine* Tiggo_CreateEngine(void);
void Tiggo_DestroyEngine(CTiggoEngine* pEngine);

/**
 * Обновление (вызывается каждый кадр)
 */
void Tiggo_Update(CTiggoEngine* pEngine, float fDeltaTime);

/**
 * Навигация
 */
BOOL Tiggo_StartNavigation(CTiggoEngine* pEngine);
void Tiggo_StopNavigation(CTiggoEngine* pEngine);
BOOL Tiggo_IsNavigationActive(const CTiggoEngine* pEngine);

/**
 * Данные от GPS (вызывается при получении GPS данных)
 */
void Tiggo_OnGpsUpdate(CTiggoEngine* pEngine, double dLatitude, double dLongitude, 
                       float fBearing, float fSpeed);

/**
 * Обновление геопозиции (вызывается из LocationService)
 * @param pEngine указатель на движок
 * @param fLatitude широта
 * @param fLongitude долгота
 * @param fSpeed скорость в км/ч
 * @param fBearing курс в градусах (0-360)
 * @param fAccuracy точность в метрах
 */
void Tiggo_OnLocationUpdate(CTiggoEngine* pEngine, float fLatitude, float fLongitude,
                            float fSpeed, float fBearing, float fAccuracy);

/**
 * Данные от Yandex (вызываются через JNI)
 */
void Tiggo_OnYandexSpeedLimit(CTiggoEngine* pEngine, int nSpeedLimitKmh, const char* pcText);
void Tiggo_OnYandexManeuver(CTiggoEngine* pEngine, int nType, int nDistanceMeters, int nTimeSeconds,
                           const char* pcTitle, const char* pcSubtitle);
void Tiggo_OnYandexRoute(CTiggoEngine* pEngine, const double* pdRoutePoints, int nPointCount,
                        int nDistanceMeters, int nTimeSeconds);
void Tiggo_OnYandexLocation(CTiggoEngine* pEngine, double dLatitude, double dLongitude,
                           float fBearing, float fSpeed, const char* pcRoadName);
void Tiggo_OnYandexRouteStatus(CTiggoEngine* pEngine, BOOL bActive, BOOL bRecalculating);

/**
 * Загрузка тайла от Yandex
 * @param pEngine указатель на движок
 * @param nTileX координата X тайла
 * @param nTileY координата Y тайла
 * @param nZoom уровень масштабирования
 * @param pRgbaData данные пикселей в формате RGBA
 * @param nWidth ширина тайла
 * @param nHeight высота тайла
 */
void Tiggo_OnYandexTileLoaded(CTiggoEngine* pEngine, int nTileX, int nTileY, int nZoom,
                              const unsigned char* pRgbaData, int nWidth, int nHeight);

/**
 * GPS/IMU данные (в стиле TurboDog)
 */
void Tiggo_AstrobGPSPostNMEA(CTiggoEngine* pEngine, const unsigned char* pData, int nLength);
void Tiggo_AstrobDRPostIMU(CTiggoEngine* pEngine, const unsigned char* pData, int nLength, double dTimestamp);

/**
 * Протокол обмена данными (JSON, как в TurboDog)
 */
BOOL Tiggo_OnProtocolRequest(CTiggoEngine* pEngine, const char* pcJsonRequest);

/**
 * Получение данных
 */
int Tiggo_GetSpeedLimit(const CTiggoEngine* pEngine);
int Tiggo_GetNextManeuverDistance(const CTiggoEngine* pEngine);
float Tiggo_GetCurrentLatitude(const CTiggoEngine* pEngine);
float Tiggo_GetCurrentLongitude(const CTiggoEngine* pEngine);

/**
 * Callback для уведомлений (для отправки broadcast через JNI)
 */
typedef void (*TiggoNavigationCallback)(void* pUserData, int nCode, int nType,
                                       int nDistance, int nTime, const char* pcRoad);

void Tiggo_SetNavigationCallback(CTiggoEngine* pEngine, TiggoNavigationCallback pCallback, 
                                 void* pUserData);

/**
 * Lifecycle функции (в стиле TurboDog)
 */
BOOL Tiggo_OnInit(CTiggoEngine* pEngine, int nWidth, int nHeight);
void Tiggo_OnPause(CTiggoEngine* pEngine);
void Tiggo_OnResume(CTiggoEngine* pEngine);
void Tiggo_SetAppInBackground(CTiggoEngine* pEngine, BOOL bInBackground);

/**
 * Утилиты (в стиле TurboDog)
 */
void Tiggo_SetSystemDir(CTiggoEngine* pEngine, const char* pcDir);
void Tiggo_SetUsbDir(CTiggoEngine* pEngine, const char* pcDir);
void Tiggo_SetNetStatus(CTiggoEngine* pEngine, int nStatus, int nType);
void Tiggo_ChangeLanguage(CTiggoEngine* pEngine, int nLanguageId);
int Tiggo_GetMeasureUnit(const CTiggoEngine* pEngine);
BOOL Tiggo_IsMapActivated(const CTiggoEngine* pEngine);

#ifdef __cplusplus
}
#endif

#endif // TIGGO_ENGINE_H

