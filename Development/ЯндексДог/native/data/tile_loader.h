/**
 * tile_loader.h - Загрузка тайлов карты (в стиле TurboDog)
 */

#ifndef TILE_LOADER_H
#define TILE_LOADER_H

#include <stdbool.h>
#include <stdint.h>
#include <GLES3/gl3.h>

#ifdef __cplusplus
extern "C" {
#endif

// Boolean тип (если еще не определен)
#ifndef BOOL
typedef int BOOL;
#define TRUE  1
#define FALSE 0
#endif

// Структура тайла карты
typedef struct {
    int nX;          // Координата X тайла
    int nY;          // Координата Y тайла
    int nZoom;       // Уровень масштабирования
    GLuint nTexture; // ID текстуры OpenGL
    BOOL bLoaded;    // TRUE если тайл загружен
    BOOL bVisible;   // TRUE если тайл видим
    BOOL bRequested; // TRUE если запрос тайла уже отправлен
    float fLat;      // Широта центра тайла
    float fLon;      // Долгота центра тайла
    
    // Данные для загрузки текстуры (используются в потоке рендеринга)
    unsigned char* pPendingData; // RGBA данные тайла (NULL если нет ожидающих данных)
    int nPendingWidth;           // Ширина ожидающего тайла
    int nPendingHeight;          // Высота ожидающего тайла
    BOOL bHasPendingData;        // TRUE если есть данные, ожидающие загрузки в текстуру
} MapTile;

// Структура загрузчика тайлов
typedef struct {
    MapTile* pTiles;        // Массив тайлов
    int nTileCount;         // Количество тайлов
    int nMaxTiles;          // Максимальное количество тайлов
    
    // Параметры камеры
    float fCameraLat;       // Широта камеры
    float fCameraLon;       // Долгота камеры
    float fCameraZoom;      // Уровень масштабирования
    int nViewWidth;         // Ширина окна просмотра
    int nViewHeight;        // Высота окна просмотра
    
    // Флаги
    BOOL bInitialized;
    BOOL bSimplified;       // TRUE для упрощенного режима (Display 1)
} TileLoader;

/**
 * Инициализация загрузчика тайлов
 * @param bSimplified TRUE для упрощенного режима (Display 1), FALSE для полноценного (Display 0)
 * @param nMaxTiles максимальное количество тайлов
 * @return указатель на загрузчик тайлов или NULL при ошибке
 */
TileLoader* Tiggo_CreateTileLoader(BOOL bSimplified, int nMaxTiles);

/**
 * Уничтожение загрузчика тайлов
 * @param pLoader указатель на загрузчик тайлов
 */
void Tiggo_DestroyTileLoader(TileLoader* pLoader);

/**
 * Обновление тайлов при изменении камеры
 * @param pLoader указатель на загрузчик тайлов
 * @param fLat широта камеры
 * @param fLon долгота камеры
 * @param fZoom уровень масштабирования
 * @param nWidth ширина окна просмотра
 * @param nHeight высота окна просмотра
 * @return TRUE при успехе, FALSE при ошибке
 */
BOOL Tiggo_UpdateTiles(TileLoader* pLoader, float fLat, float fLon, float fZoom,
                       int nWidth, int nHeight);

/**
 * Загрузка тайла из Yandex MapKit
 * @param pLoader указатель на загрузчик тайлов
 * @param nTileX координата X тайла
 * @param nTileY координата Y тайла
 * @param nZoom уровень масштабирования
 * @return указатель на загруженный тайл или NULL при ошибке
 */
MapTile* Tiggo_LoadTile(TileLoader* pLoader, int nTileX, int nTileY, int nZoom);

/**
 * Загрузка тайла из данных (RGBA)
 * @param pLoader указатель на загрузчик тайлов
 * @param nTileX координата X тайла
 * @param nTileY координата Y тайла
 * @param nZoom уровень масштабирования
 * @param pRgbaData данные пикселей в формате RGBA
 * @param nWidth ширина тайла
 * @param nHeight высота тайла
 * @return указатель на загруженный тайл или NULL при ошибке
 */
MapTile* Tiggo_LoadTileFromData(TileLoader* pLoader, int nTileX, int nTileY, int nZoom,
                                const unsigned char* pRgbaData, int nWidth, int nHeight);

/**
 * Обработка ожидающих тайлов - создание текстур из сохраненных данных
 * Должна вызываться в потоке рендеринга (где активен OpenGL контекст)
 * @param pLoader указатель на загрузчик тайлов
 * @return количество обработанных тайлов
 */
int Tiggo_ProcessPendingTiles(TileLoader* pLoader);

/**
 * Получение тайла по координатам
 * @param pLoader указатель на загрузчик тайлов
 * @param fLat широта
 * @param fLon долгота
 * @param nZoom уровень масштабирования
 * @return указатель на тайл или NULL если не найден
 */
MapTile* Tiggo_GetTileAt(TileLoader* pLoader, float fLat, float fLon, int nZoom);

/**
 * Очистка всех тайлов
 * @param pLoader указатель на загрузчик тайлов
 */
void Tiggo_ClearTiles(TileLoader* pLoader);

/**
 * Конвертация географических координат в координаты тайла
 * @param fLat широта
 * @param fLon долгота
 * @param nZoom уровень масштабирования
 * @param pnTileX выходная координата X тайла
 * @param pnTileY выходная координата Y тайла
 */
void Tiggo_GeoToTile(float fLat, float fLon, int nZoom, int* pnTileX, int* pnTileY);

/**
 * Конвертация координат тайла в географические координаты
 * @param nTileX координата X тайла
 * @param nTileY координата Y тайла
 * @param nZoom уровень масштабирования
 * @param pfLat выходная широта
 * @param pfLon выходная долгота
 */
void Tiggo_TileToGeo(int nTileX, int nTileY, int nZoom, float* pfLat, float* pfLon);

#ifdef __cplusplus
}
#endif

#endif // TILE_LOADER_H

