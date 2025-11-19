/**
 * tile_loader.c - Реализация загрузки тайлов карты (в стиле TurboDog)
 * 
 * Стиль TurboDog:
 * - Префиксы функций: Tiggo_
 * - Венгерская нотация
 * - C код (не C++)
 */

#include "tile_loader.h"
#include "../jni/jni_tile_loader.h"
#include <GLES3/gl3.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <android/log.h>

#define LOG_TAG "TiggoTileLoader"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/**
 * Конвертация географических координат в координаты тайла (Web Mercator)
 */
void Tiggo_GeoToTile(float fLat, float fLon, int nZoom, int* pnTileX, int* pnTileY) {
    if (pnTileX == NULL || pnTileY == NULL) {
        return;
    }
    
    // Web Mercator projection
    double dLat = fLat * M_PI / 180.0;
    double dLon = fLon * M_PI / 180.0;
    
    double dN = pow(2.0, nZoom);
    
    int nX = (int)((dLon + M_PI) / (2.0 * M_PI) * dN);
    int nY = (int)((1.0 - log(tan(dLat) + 1.0 / cos(dLat)) / M_PI) / 2.0 * dN);
    
    *pnTileX = nX;
    *pnTileY = nY;
}

/**
 * Конвертация координат тайла в географические координаты (Web Mercator)
 */
void Tiggo_TileToGeo(int nTileX, int nTileY, int nZoom, float* pfLat, float* pfLon) {
    if (pfLat == NULL || pfLon == NULL) {
        return;
    }
    
    double dN = pow(2.0, nZoom);
    
    double dLon = (double)nTileX / dN * 2.0 * M_PI - M_PI;
    double dLat = atan(sinh(M_PI * (1.0 - 2.0 * (double)nTileY / dN)));
    
    *pfLon = (float)(dLon * 180.0 / M_PI);
    *pfLat = (float)(dLat * 180.0 / M_PI);
}

/**
 * Создание загрузчика тайлов
 */
TileLoader* Tiggo_CreateTileLoader(BOOL bSimplified, int nMaxTiles) {
    TileLoader* pLoader = (TileLoader*)malloc(sizeof(TileLoader));
    if (pLoader == NULL) {
        return NULL;
    }
    
    memset(pLoader, 0, sizeof(TileLoader));
    pLoader->bSimplified = bSimplified;
    pLoader->nMaxTiles = nMaxTiles > 0 ? nMaxTiles : 256; // По умолчанию 256 тайлов
    
    // Выделяем память для тайлов
    pLoader->pTiles = (MapTile*)malloc(sizeof(MapTile) * pLoader->nMaxTiles);
    if (pLoader->pTiles == NULL) {
        free(pLoader);
        return NULL;
    }
    
    memset(pLoader->pTiles, 0, sizeof(MapTile) * pLoader->nMaxTiles);
    
    // Инициализация параметров камеры
    pLoader->fCameraLat = 0.0f;
    pLoader->fCameraLon = 0.0f;
    pLoader->fCameraZoom = 10.0f;
    pLoader->nViewWidth = 1024;
    pLoader->nViewHeight = 768;
    
    pLoader->bInitialized = TRUE;
    
    return pLoader;
}

/**
 * Уничтожение загрузчика тайлов
 */
void Tiggo_DestroyTileLoader(TileLoader* pLoader) {
    if (pLoader == NULL) {
        return;
    }
    
    if (pLoader->bInitialized) {
        // Очищаем все тайлы
        Tiggo_ClearTiles(pLoader);
        
        // Освобождаем память тайлов
        if (pLoader->pTiles != NULL) {
            free(pLoader->pTiles);
        }
    }
    
    free(pLoader);
}

/**
 * Очистка всех тайлов
 */
void Tiggo_ClearTiles(TileLoader* pLoader) {
    if (pLoader == NULL || pLoader->pTiles == NULL) {
        return;
    }
    
    // Удаляем текстуры OpenGL для всех тайлов
    for (int i = 0; i < pLoader->nTileCount; i++) {
        if (pLoader->pTiles[i].bLoaded && pLoader->pTiles[i].nTexture != 0) {
            glDeleteTextures(1, &pLoader->pTiles[i].nTexture);
            pLoader->pTiles[i].nTexture = 0;
        }
        // Освобождаем ожидающие данные
        if (pLoader->pTiles[i].pPendingData != NULL) {
            free(pLoader->pTiles[i].pPendingData);
            pLoader->pTiles[i].pPendingData = NULL;
        }
        pLoader->pTiles[i].bLoaded = FALSE;
        pLoader->pTiles[i].bVisible = FALSE;
        pLoader->pTiles[i].bRequested = FALSE;
        pLoader->pTiles[i].bHasPendingData = FALSE;
    }
    
    pLoader->nTileCount = 0;
}

/**
 * Поиск тайла в массиве
 */
static MapTile* FindTile(TileLoader* pLoader, int nTileX, int nTileY, int nZoom) {
    if (pLoader == NULL || pLoader->pTiles == NULL) {
        return NULL;
    }
    
    for (int i = 0; i < pLoader->nTileCount; i++) {
        if (pLoader->pTiles[i].nX == nTileX &&
            pLoader->pTiles[i].nY == nTileY &&
            pLoader->pTiles[i].nZoom == nZoom) {
            return &pLoader->pTiles[i];
        }
    }
    
    return NULL;
}

/**
 * Добавление нового тайла
 */
static MapTile* AddTile(TileLoader* pLoader, int nTileX, int nTileY, int nZoom) {
    if (pLoader == NULL || pLoader->pTiles == NULL) {
        return NULL;
    }
    
    // Проверяем, есть ли место
    if (pLoader->nTileCount >= pLoader->nMaxTiles) {
        // Удаляем самый старый тайл (FIFO)
        MapTile* pOldestTile = &pLoader->pTiles[0];
        if (pOldestTile->bLoaded && pOldestTile->nTexture != 0) {
            glDeleteTextures(1, &pOldestTile->nTexture);
        }
        // Освобождаем ожидающие данные
        if (pOldestTile->pPendingData != NULL) {
            free(pOldestTile->pPendingData);
            pOldestTile->pPendingData = NULL;
        }
        
        // Сдвигаем массив
        memmove(&pLoader->pTiles[0], &pLoader->pTiles[1],
                sizeof(MapTile) * (pLoader->nTileCount - 1));
        pLoader->nTileCount--;
    }
    
    // Добавляем новый тайл
    MapTile* pTile = &pLoader->pTiles[pLoader->nTileCount];
    memset(pTile, 0, sizeof(MapTile));
    
    pTile->nX = nTileX;
    pTile->nY = nTileY;
    pTile->nZoom = nZoom;
    pTile->bRequested = FALSE; // Инициализируем флаг запроса
    
    // Вычисляем географические координаты центра тайла
    Tiggo_TileToGeo(nTileX, nTileY, nZoom, &pTile->fLat, &pTile->fLon);
    
    pLoader->nTileCount++;
    
    return pTile;
}

/**
 * Загрузка тайла из Yandex MapKit
 * Вызывает Java код для загрузки тайла через HTTP
 */
MapTile* Tiggo_LoadTile(TileLoader* pLoader, int nTileX, int nTileY, int nZoom) {
    if (pLoader == NULL || !pLoader->bInitialized) {
        return NULL;
    }
    
    // Проверяем, есть ли уже такой тайл
    MapTile* pTile = FindTile(pLoader, nTileX, nTileY, nZoom);
    if (pTile != NULL && pTile->bLoaded) {
        return pTile; // Тайл уже загружен
    }
    
    // Если тайл уже запрошен, не делаем повторный запрос
    if (pTile != NULL && pTile->bRequested) {
        return pTile; // Тайл уже запрошен, ждем загрузки
    }
    
    // Добавляем новый тайл, если его нет
    if (pTile == NULL) {
        pTile = AddTile(pLoader, nTileX, nTileY, nZoom);
        if (pTile == NULL) {
            return NULL;
        }
    }
    
    // Создаем временную текстуру (будет заменена при загрузке реального тайла)
    if (pTile->nTexture == 0) {
        GLuint nTexture = 0;
        glGenTextures(1, &nTexture);
        glBindTexture(GL_TEXTURE_2D, nTexture);
        
        // Параметры текстуры
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        
        // Создаем пустую прозрачную текстуру (1x1, полностью прозрачная)
        unsigned char pTransparentData[4] = {0, 0, 0, 0};
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 1, 1, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, pTransparentData);
        
        pTile->nTexture = nTexture;
    }
    
    pTile->bLoaded = FALSE; // Помечаем как не загруженный, пока Java не загрузит
    pTile->bVisible = TRUE;
    pTile->bRequested = TRUE; // Помечаем, что запрос отправлен
    
    // Запрашиваем загрузку тайла через Java/JNI
    Tiggo_RequestTileLoad(nTileX, nTileY, nZoom);
    
    return pTile;
}

/**
 * Загрузка тайла из данных (RGBA) - вызывается из JNI
 */
MapTile* Tiggo_LoadTileFromData(TileLoader* pLoader, int nTileX, int nTileY, int nZoom,
                                const unsigned char* pRgbaData, int nWidth, int nHeight) {
    if (pLoader == NULL || !pLoader->bInitialized || 
        pRgbaData == NULL || nWidth <= 0 || nHeight <= 0) {
        LOGE("LoadTileFromData: invalid parameters");
        return NULL;
    }
    
    LOGI("LoadTileFromData: x=%d, y=%d, z=%d, size=%dx%d (saving data for render thread)", 
         nTileX, nTileY, nZoom, nWidth, nHeight);
    
    // Находим или создаем тайл
    MapTile* pTile = FindTile(pLoader, nTileX, nTileY, nZoom);
    if (pTile == NULL) {
        pTile = AddTile(pLoader, nTileX, nTileY, nZoom);
        if (pTile == NULL) {
            LOGE("LoadTileFromData: failed to add tile");
            return NULL;
        }
    }
    
    // Сбрасываем флаг запроса, так как тайл загружен
    pTile->bRequested = FALSE;
    
    // Освобождаем старые ожидающие данные, если они есть
    if (pTile->pPendingData != NULL) {
        free(pTile->pPendingData);
        pTile->pPendingData = NULL;
    }
    
    // Сохраняем данные тайла для загрузки в текстуру в потоке рендеринга
    // (OpenGL контекст доступен только в потоке рендеринга)
    int nDataSize = nWidth * nHeight * 4; // RGBA = 4 байта на пиксель
    pTile->pPendingData = (unsigned char*)malloc(nDataSize);
    if (pTile->pPendingData == NULL) {
        LOGE("LoadTileFromData: failed to allocate memory for tile data");
        return NULL;
    }
    
    memcpy(pTile->pPendingData, pRgbaData, nDataSize);
    pTile->nPendingWidth = nWidth;
    pTile->nPendingHeight = nHeight;
    pTile->bHasPendingData = TRUE;
    
    // НЕ создаем текстуру здесь - это будет сделано в потоке рендеринга
    // НЕ помечаем как загруженный - это будет сделано после создания текстуры
    
    pTile->bVisible = TRUE;
    
    LOGI("LoadTileFromData: data saved, will create texture in render thread");
    
    return pTile;
}

/**
 * Обработка ожидающих тайлов - создание текстур из сохраненных данных
 * Должна вызываться в потоке рендеринга (где активен OpenGL контекст)
 */
int Tiggo_ProcessPendingTiles(TileLoader* pLoader) {
    if (pLoader == NULL || !pLoader->bInitialized) {
        return 0;
    }
    
    int nProcessed = 0;
    
    for (int i = 0; i < pLoader->nTileCount; i++) {
        MapTile* pTile = &pLoader->pTiles[i];
        
        // Проверяем, есть ли данные, ожидающие загрузки в текстуру
        if (pTile->bHasPendingData && pTile->pPendingData != NULL) {
            // Если текстура уже создана, удаляем ее
            if (pTile->nTexture != 0) {
                glDeleteTextures(1, &pTile->nTexture);
                pTile->nTexture = 0;
            }
            
            // Создаем новую текстуру OpenGL
            glGenTextures(1, &pTile->nTexture);
            glBindTexture(GL_TEXTURE_2D, pTile->nTexture);
            
            // Параметры текстуры
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
            
            // Загружаем данные в текстуру
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, pTile->nPendingWidth, pTile->nPendingHeight, 0,
                         GL_RGBA, GL_UNSIGNED_BYTE, pTile->pPendingData);
            
            // Проверяем ошибки
            GLenum glError = glGetError();
            if (glError != GL_NO_ERROR) {
                LOGE("ProcessPendingTiles: OpenGL error for tile x=%d,y=%d: 0x%x", 
                     pTile->nX, pTile->nY, glError);
                // Освобождаем данные и сбрасываем флаг
                free(pTile->pPendingData);
                pTile->pPendingData = NULL;
                pTile->bHasPendingData = FALSE;
                if (pTile->nTexture != 0) {
                    glDeleteTextures(1, &pTile->nTexture);
                    pTile->nTexture = 0;
                }
            } else {
                LOGI("ProcessPendingTiles: texture created for tile x=%d,y=%d, id=%u", 
                     pTile->nX, pTile->nY, pTile->nTexture);
                
                // Освобождаем данные (они теперь в текстуре)
                free(pTile->pPendingData);
                pTile->pPendingData = NULL;
                pTile->bHasPendingData = FALSE;
                
                // Помечаем тайл как загруженный и сбрасываем флаг запроса
                pTile->bLoaded = TRUE;
                pTile->bRequested = FALSE; // Сбрасываем флаг запроса после успешной загрузки
                
                nProcessed++;
            }
        }
    }
    
    if (nProcessed > 0) {
        LOGI("ProcessPendingTiles: processed %d tiles", nProcessed);
    }
    
    return nProcessed;
}

/**
 * Получение тайла по географическим координатам
 */
MapTile* Tiggo_GetTileAt(TileLoader* pLoader, float fLat, float fLon, int nZoom) {
    if (pLoader == NULL || !pLoader->bInitialized) {
        return NULL;
    }
    
    // Конвертируем географические координаты в координаты тайла
    int nTileX, nTileY;
    Tiggo_GeoToTile(fLat, fLon, nZoom, &nTileX, &nTileY);
    
    // Ищем тайл
    return FindTile(pLoader, nTileX, nTileY, nZoom);
}

// Глобальная ссылка на Java TileLoader для запроса загрузки тайлов
// TODO: реализовать вызов Java метода для загрузки тайла через JNI

/**
 * Обновление тайлов при изменении камеры
 */
BOOL Tiggo_UpdateTiles(TileLoader* pLoader, float fLat, float fLon, float fZoom,
                       int nWidth, int nHeight) {
    if (pLoader == NULL || !pLoader->bInitialized) {
        return FALSE;
    }
    
    // Обновляем параметры камеры
    pLoader->fCameraLat = fLat;
    pLoader->fCameraLon = fLon;
    pLoader->fCameraZoom = fZoom;
    pLoader->nViewWidth = nWidth;
    pLoader->nViewHeight = nHeight;
    
    // Вычисляем уровень масштабирования для тайлов
    int nTileZoom = (int)fZoom;
    if (nTileZoom < 1) nTileZoom = 1;
    if (nTileZoom > 18) nTileZoom = 18;
    
    // Конвертируем позицию камеры в координаты тайла
    int nCenterTileX, nCenterTileY;
    Tiggo_GeoToTile(fLat, fLon, nTileZoom, &nCenterTileX, &nCenterTileY);
    
    // Вычисляем количество тайлов для отображения
    // Обычно нужно загрузить тайлы в радиусе 1-2 тайла от центра
    int nTileRadius = 2; // Радиус в тайлах
    if (pLoader->bSimplified) {
        nTileRadius = 1; // Для упрощенного режима меньше тайлов
    }
    
    // Помечаем все тайлы как невидимые
    for (int i = 0; i < pLoader->nTileCount; i++) {
        pLoader->pTiles[i].bVisible = FALSE;
    }
    
    // Загружаем тайлы вокруг камеры
    for (int dy = -nTileRadius; dy <= nTileRadius; dy++) {
        for (int dx = -nTileRadius; dx <= nTileRadius; dx++) {
            int nTileX = nCenterTileX + dx;
            int nTileY = nCenterTileY + dy;
            
            // Проверяем, есть ли уже такой тайл
            MapTile* pTile = FindTile(pLoader, nTileX, nTileY, nTileZoom);
            
            if (pTile == NULL) {
                // Создаем новый тайл (заглушка, будет загружен Java кодом)
                pTile = AddTile(pLoader, nTileX, nTileY, nTileZoom);
            }
            
            if (pTile != NULL) {
                pTile->bVisible = TRUE;
                
                // Если тайл еще не загружен и не запрошен, запрашиваем его загрузку
                if ((!pTile->bLoaded || pTile->nTexture == 0) && !pTile->bRequested) {
                    // Загружаем тайл через Java/JNI
                    Tiggo_LoadTile(pLoader, nTileX, nTileY, nTileZoom);
                }
            }
        }
    }
    
    // Удаляем невидимые тайлы, которые не используются
    // TODO: Оптимизация - удаление невидимых тайлов при нехватке памяти
    
    return TRUE;
}

