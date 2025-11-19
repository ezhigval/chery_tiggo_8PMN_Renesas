/**
 * tiggo_engine.c - Реализация навигационного движка (в стиле TurboDog)
 * 
 * Стиль кода:
 * - Венгерская нотация (m_, n_, f_, p_, b_)
 * - Префикс Tiggo_ для всех функций
 * - Структуры с префиксом C
 */

#include "tiggo_engine.h"
#include "../render/route_renderer.h"
#include "../render/map_renderer.h"
#include "../data/tile_loader.h"
#include "../jni/jni_navigation_ui.h"
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <pthread.h>
#include <android/log.h>

#define LOG_TAG "TiggoEngine"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Внешняя ссылка на глобальный TileLoader (определена в map_renderer.c)
extern TileLoader* g_pGlobalTileLoader;

// Внутренняя структура (приватные данные)
typedef struct {
    pthread_mutex_t mutex;
    TiggoNavigationCallback pCallback;
    void* pUserData;
} TiggoEngineInternal;

/**
 * Создание движка
 */
CTiggoEngine* Tiggo_CreateEngine(void) {
    CTiggoEngine* pEngine = (CTiggoEngine*)malloc(sizeof(CTiggoEngine));
    if (pEngine == NULL) {
        return NULL;
    }
    
    // Инициализация нулями
    memset(pEngine, 0, sizeof(CTiggoEngine));
    
    // Выделение памяти для внутренних данных
    pEngine->m_pInternal = malloc(sizeof(TiggoEngineInternal));
    if (pEngine->m_pInternal == NULL) {
        free(pEngine);
        return NULL;
    }
    
    TiggoEngineInternal* pInternal = (TiggoEngineInternal*)pEngine->m_pInternal;
    pthread_mutex_init(&pInternal->mutex, NULL);
    pInternal->pCallback = NULL;
    pInternal->pUserData = NULL;
    
    pEngine->m_bInitialized = FALSE;
    pEngine->m_bNavigationActive = FALSE;
    pEngine->m_bMapActivated = FALSE;
    
    // Инициализация данных
    pEngine->m_nSpeedLimitKmh = 0;
    pEngine->m_nNextManeuverDistance = 0;
    pEngine->m_nNextManeuverType = 0;
    pEngine->m_fCurrentLat = 0.0f;
    pEngine->m_fCurrentLon = 0.0f;
    pEngine->m_fCurrentSpeed = 0.0f;
    pEngine->m_fCurrentBearing = 0.0f;
    pEngine->m_pcCurrentRoadName[0] = '\0';
    pEngine->m_nMainDisplayWidth = 1024;
    pEngine->m_nMainDisplayHeight = 768;
    pEngine->m_nSecondaryDisplayWidth = 800;
    pEngine->m_nSecondaryDisplayHeight = 480;
    
    return pEngine;
}

/**
 * Уничтожение движка
 */
void Tiggo_DestroyEngine(CTiggoEngine* pEngine) {
    if (pEngine == NULL) {
        return;
    }
    
    if (pEngine->m_bInitialized) {
        Tiggo_Shutdown(pEngine);
    }
    
    // Освобождение внутренних данных
    if (pEngine->m_pInternal != NULL) {
        TiggoEngineInternal* pInternal = (TiggoEngineInternal*)pEngine->m_pInternal;
        pthread_mutex_destroy(&pInternal->mutex);
        free(pEngine->m_pInternal);
    }
    
    // Освобождение компонентов (если выделялись)
    // TODO: освобождение m_pNavigationState, m_pRouteCalculator и т.д.
    
    free(pEngine);
}

/**
 * Инициализация
 */
BOOL Tiggo_Initialize(CTiggoEngine* pEngine) {
    if (pEngine == NULL) {
        return FALSE;
    }
    
    if (pEngine->m_bInitialized) {
        return TRUE; // Уже инициализирован
    }
    
    // Инициализация компонентов
    // TODO: инициализация navigation state, route calculator и т.д.
    
    pEngine->m_bInitialized = TRUE;
    return TRUE;
}

/**
 * Завершение
 */
void Tiggo_Shutdown(CTiggoEngine* pEngine) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return;
    }
    
    // Остановка навигации
    if (pEngine->m_bNavigationActive) {
        Tiggo_StopNavigation(pEngine);
    }
    
    // Освобождение ресурсов
    // TODO: shutdown компонентов
    
    pEngine->m_bInitialized = FALSE;
}

/**
 * Обновление (вызывается каждый кадр)
 */
void Tiggo_Update(CTiggoEngine* pEngine, float fDeltaTime) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return;
    }
    
    // TODO: обновление логики навигации
    
    // Если навигация активна, отправляем данные через callback
    if (pEngine->m_bNavigationActive) {
        TiggoEngineInternal* pInternal = (TiggoEngineInternal*)pEngine->m_pInternal;
        
        if (pInternal->pCallback != NULL) {
            // Отправляем данные в формате TurboDog
            // CODE=201 (TURN-BY-TURN данные)
            pthread_mutex_lock(&pInternal->mutex);
            pInternal->pCallback(pInternal->pUserData, 201, 0, // TODO: реальные данные
                                pEngine->m_nNextManeuverDistance, 0, "");
            pthread_mutex_unlock(&pInternal->mutex);
        }
    }
}

/**
 * Навигация
 */
BOOL Tiggo_StartNavigation(CTiggoEngine* pEngine) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return FALSE;
    }
    
    pEngine->m_bNavigationActive = TRUE;
    
    // Обновляем UI - навигация активна
    extern void Tiggo_SetNavigationActive(BOOL bActive);
    Tiggo_SetNavigationActive(TRUE);
    
    return TRUE;
}

void Tiggo_StopNavigation(CTiggoEngine* pEngine) {
    if (pEngine == NULL) {
        return;
    }
    
    pEngine->m_bNavigationActive = FALSE;
    
    // Обновляем UI - навигация неактивна
    extern void Tiggo_SetNavigationActive(BOOL bActive);
    Tiggo_SetNavigationActive(FALSE);
}

BOOL Tiggo_IsNavigationActive(const CTiggoEngine* pEngine) {
    if (pEngine == NULL) {
        return FALSE;
    }
    return pEngine->m_bNavigationActive;
}

/**
 * Данные от GPS
 */
void Tiggo_OnGpsUpdate(CTiggoEngine* pEngine, double dLatitude, double dLongitude,
                      float fBearing, float fSpeed) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return;
    }
    
    pEngine->m_fCurrentLat = (float)dLatitude;
    pEngine->m_fCurrentLon = (float)dLongitude;
    
    // TODO: обработка GPS данных
}

/**
 * Обновление геопозиции (вызывается из LocationService)
 */
void Tiggo_OnLocationUpdate(CTiggoEngine* pEngine, float fLatitude, float fLongitude,
                            float fSpeed, float fBearing, float fAccuracy) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return;
    }
    
    // Обновляем координаты
    pEngine->m_fCurrentLat = fLatitude;
    pEngine->m_fCurrentLon = fLongitude;
    pEngine->m_fCurrentSpeed = fSpeed;
    pEngine->m_fCurrentBearing = fBearing;
    
    LOGI("Location update: lat=%.6f, lon=%.6f, speed=%.1f km/h, bearing=%.1f°, accuracy=%.1f m",
         fLatitude, fLongitude, fSpeed, fBearing, fAccuracy);
    
    // Обновляем камеру карты (следуем за GPS позицией)
    // Используем зум 15 для навигации (хороший баланс между детализацией и обзором)
    float fZoom = 15.0f;
    float fTilt = 0.0f; // Пока без наклона
    
    // Обновляем камеру через функцию из map_renderer
    // ВАЖНО: всегда обновляем камеру на GPS координаты, чтобы карта следовала за пользователем
    extern void Tiggo_UpdateCamera(CTiggoEngine* pEngine, float fLat, float fLon,
                                   float fZoom, float fBearing, float fTilt);
    Tiggo_UpdateCamera(pEngine, fLatitude, fLongitude, fZoom, fBearing, fTilt);
    
    // Обновляем UI через JNI
    Tiggo_UpdateNavigationUI(fSpeed, fBearing, pEngine->m_nSpeedLimitKmh,
                            pEngine->m_nNextManeuverType, pEngine->m_nNextManeuverDistance,
                            pEngine->m_pcCurrentRoadName);
}

/**
 * Данные от Yandex: ограничение скорости
 */
void Tiggo_OnYandexSpeedLimit(CTiggoEngine* pEngine, int nSpeedLimitKmh, const char* pcText) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return;
    }
    
    pEngine->m_nSpeedLimitKmh = nSpeedLimitKmh;
    
    // Обновляем UI через JNI
    Tiggo_UpdateNavigationUI(pEngine->m_fCurrentSpeed, pEngine->m_fCurrentBearing,
                            nSpeedLimitKmh, pEngine->m_nNextManeuverType,
                            pEngine->m_nNextManeuverDistance, pEngine->m_pcCurrentRoadName);
}

/**
 * Данные от Yandex: маневр
 */
void Tiggo_OnYandexManeuver(CTiggoEngine* pEngine, int nType, int nDistanceMeters, int nTimeSeconds,
                           const char* pcTitle, const char* pcSubtitle) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return;
    }
    
    pEngine->m_nNextManeuverDistance = nDistanceMeters;
    pEngine->m_nNextManeuverType = nType;
    
    // Используем subtitle (название улицы) для маневра, если доступно
    const char* pcManeuverStreet = (pcSubtitle != NULL && strlen(pcSubtitle) > 0) ? pcSubtitle : 
                                  (pcTitle != NULL && strlen(pcTitle) > 0) ? pcTitle : "";
    
    // Обновляем UI через JNI (передаем название улицы для маневра)
    Tiggo_UpdateNavigationUI(pEngine->m_fCurrentSpeed, pEngine->m_fCurrentBearing,
                            pEngine->m_nSpeedLimitKmh, nType, nDistanceMeters,
                            pcManeuverStreet);
}

/**
 * Данные от Yandex: маршрут
 */
void Tiggo_OnYandexRoute(CTiggoEngine* pEngine, const double* pdRoutePoints, int nPointCount,
                        int nDistanceMeters, int nTimeSeconds) {
    if (pEngine == NULL || !pEngine->m_bInitialized || pdRoutePoints == NULL || nPointCount <= 0) {
        return;
    }
    
    // Передаем точки маршрута в рендерер маршрута
    Tiggo_SetRoutePoints(pEngine, pdRoutePoints, nPointCount);
    
    // Если маршрут получен, можно начать навигацию
    if (nPointCount > 0 && !pEngine->m_bNavigationActive) {
        Tiggo_StartNavigation(pEngine);
    }
    
    // Обновляем информацию о маршруте в UI
    // Вычисляем время прибытия
    time_t nCurrentTime = time(NULL);
    time_t nArrivalTime = nCurrentTime + nTimeSeconds;
    struct tm* pArrivalTm = localtime(&nArrivalTime);
    char pcArrivalTime[6]; // "HH:mm"
    snprintf(pcArrivalTime, sizeof(pcArrivalTime), "%02d:%02d", pArrivalTm->tm_hour, pArrivalTm->tm_min);
    
    // Вызываем JNI для обновления UI (jni_navigation_ui.h уже включен в начале файла)
    Tiggo_UpdateRouteInfo(pcArrivalTime, nTimeSeconds / 60, (float)nDistanceMeters / 1000.0f);
}

/**
 * Данные от Yandex: местоположение
 */
void Tiggo_OnYandexLocation(CTiggoEngine* pEngine, double dLatitude, double dLongitude,
                           float fBearing, float fSpeed, const char* pcRoadName) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return;
    }
    
    pEngine->m_fCurrentLat = (float)dLatitude;
    pEngine->m_fCurrentLon = (float)dLongitude;
    pEngine->m_fCurrentBearing = fBearing;
    pEngine->m_fCurrentSpeed = fSpeed;
    
    // Обновляем UI через JNI
    Tiggo_UpdateNavigationUI(fSpeed, fBearing, pEngine->m_nSpeedLimitKmh,
                            pEngine->m_nNextManeuverType, pEngine->m_nNextManeuverDistance,
                            pEngine->m_pcCurrentRoadName);
    
    // Сохраняем название дороги
    if (pcRoadName != NULL) {
        strncpy(pEngine->m_pcCurrentRoadName, pcRoadName, sizeof(pEngine->m_pcCurrentRoadName) - 1);
        pEngine->m_pcCurrentRoadName[sizeof(pEngine->m_pcCurrentRoadName) - 1] = '\0';
    } else {
        pEngine->m_pcCurrentRoadName[0] = '\0';
    }
    
    // TODO: обработка местоположения
}

/**
 * Данные от Yandex: статус маршрута
 */
void Tiggo_OnYandexRouteStatus(CTiggoEngine* pEngine, BOOL bActive, BOOL bRecalculating) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return;
    }
    
    if (bActive) {
        if (!pEngine->m_bNavigationActive) {
            Tiggo_StartNavigation(pEngine);
        }
    } else {
        if (pEngine->m_bNavigationActive) {
            Tiggo_StopNavigation(pEngine);
        }
    }
    
    // TODO: обработка статуса маршрута
}

/**
 * GPS данные в NMEA формате (в стиле TurboDog)
 */
void Tiggo_AstrobGPSPostNMEA(CTiggoEngine* pEngine, const unsigned char* pData, int nLength) {
    if (pEngine == NULL || !pEngine->m_bInitialized || pData == NULL || nLength <= 0) {
        return;
    }
    
    // TODO: парсинг NMEA данных
    // Обновление местоположения
}

/**
 * IMU данные (в стиле TurboDog)
 */
void Tiggo_AstrobDRPostIMU(CTiggoEngine* pEngine, const unsigned char* pData, int nLength, double dTimestamp) {
    if (pEngine == NULL || !pEngine->m_bInitialized || pData == NULL || nLength <= 0) {
        return;
    }
    
    // TODO: обработка IMU данных
    // Dead reckoning для точности навигации
}

/**
 * Протокол обмена данными (JSON, как в TurboDog)
 */
BOOL Tiggo_OnProtocolRequest(CTiggoEngine* pEngine, const char* pcJsonRequest) {
    if (pEngine == NULL || !pEngine->m_bInitialized || pcJsonRequest == NULL) {
        return FALSE;
    }
    
    // TODO: парсинг JSON запроса
    // Обработка различных типов запросов
    // Формат: {"request": {"id": 25, "response": 1, "data": {...}}}
    
    return TRUE;
}

/**
 * Lifecycle функции (в стиле TurboDog)
 */
BOOL Tiggo_OnInit(CTiggoEngine* pEngine, int nWidth, int nHeight) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return FALSE;
    }
    
    // Сохраняем размеры экрана
    pEngine->m_nMainDisplayWidth = nWidth;
    pEngine->m_nMainDisplayHeight = nHeight;
    
    // TODO: инициализация с размером окна
    return TRUE;
}

void Tiggo_OnPause(CTiggoEngine* pEngine) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return;
    }
    
    // TODO: приостановка рендеринга
}

void Tiggo_OnResume(CTiggoEngine* pEngine) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return;
    }
    
    // TODO: возобновление рендеринга
}

void Tiggo_SetAppInBackground(CTiggoEngine* pEngine, BOOL bInBackground) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return;
    }
    
    // TODO: управление состоянием приложения
}

/**
 * Утилиты (в стиле TurboDog)
 */
void Tiggo_SetSystemDir(CTiggoEngine* pEngine, const char* pcDir) {
    if (pEngine == NULL || pcDir == NULL) {
        return;
    }
    
    // TODO: установка системной директории
}

void Tiggo_SetUsbDir(CTiggoEngine* pEngine, const char* pcDir) {
    if (pEngine == NULL || pcDir == NULL) {
        return;
    }
    
    // TODO: установка USB директории
}

void Tiggo_SetNetStatus(CTiggoEngine* pEngine, int nStatus, int nType) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return;
    }
    
    // TODO: установка статуса сети
}

void Tiggo_ChangeLanguage(CTiggoEngine* pEngine, int nLanguageId) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return;
    }
    
    // TODO: смена языка
}

int Tiggo_GetMeasureUnit(const CTiggoEngine* pEngine) {
    if (pEngine == NULL) {
        return 0; // 0 = метры
    }
    
    // TODO: получение единиц измерения
    return 0; // 0 = метры, 1 = мили
}

BOOL Tiggo_IsMapActivated(const CTiggoEngine* pEngine) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return FALSE;
    }
    
    return TRUE; // TODO: проверка активации карты
}

/**
 * Загрузка тайла от Yandex
 */
void Tiggo_OnYandexTileLoaded(CTiggoEngine* pEngine, int nTileX, int nTileY, int nZoom,
                              const unsigned char* pRgbaData, int nWidth, int nHeight) {
    if (pEngine == NULL || !pEngine->m_bInitialized || 
        pRgbaData == NULL || nWidth <= 0 || nHeight <= 0) {
        LOGE("OnYandexTileLoaded: invalid parameters");
        return;
    }
    
    LOGI("OnYandexTileLoaded: x=%d, y=%d, z=%d, size=%dx%d", nTileX, nTileY, nZoom, nWidth, nHeight);
    
    // Получаем глобальный TileLoader из map_renderer
    if (g_pGlobalTileLoader != NULL) {
        // Загружаем тайл из данных
        Tiggo_LoadTileFromData(g_pGlobalTileLoader, nTileX, nTileY, nZoom,
                               pRgbaData, nWidth, nHeight);
    } else {
        LOGE("OnYandexTileLoaded: g_pGlobalTileLoader is NULL");
    }
}

/**
 * Получение данных
 */
int Tiggo_GetSpeedLimit(const CTiggoEngine* pEngine) {
    if (pEngine == NULL) {
        return 0;
    }
    return pEngine->m_nSpeedLimitKmh;
}

int Tiggo_GetNextManeuverDistance(const CTiggoEngine* pEngine) {
    if (pEngine == NULL) {
        return 0;
    }
    return pEngine->m_nNextManeuverDistance;
}

float Tiggo_GetCurrentLatitude(const CTiggoEngine* pEngine) {
    if (pEngine == NULL) {
        return 0.0f;
    }
    return pEngine->m_fCurrentLat;
}

float Tiggo_GetCurrentLongitude(const CTiggoEngine* pEngine) {
    if (pEngine == NULL) {
        return 0.0f;
    }
    return pEngine->m_fCurrentLon;
}

/**
 * Callback для уведомлений
 */
void Tiggo_SetNavigationCallback(CTiggoEngine* pEngine, TiggoNavigationCallback pCallback,
                                void* pUserData) {
    if (pEngine == NULL || pEngine->m_pInternal == NULL) {
        return;
    }
    
    TiggoEngineInternal* pInternal = (TiggoEngineInternal*)pEngine->m_pInternal;
    pthread_mutex_lock(&pInternal->mutex);
    pInternal->pCallback = pCallback;
    pInternal->pUserData = pUserData;
    pthread_mutex_unlock(&pInternal->mutex);
}

