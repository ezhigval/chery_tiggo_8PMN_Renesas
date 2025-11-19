/**
 * map_renderer.h - Заголовок рендеринга карты (в стиле TurboDog)
 */

#ifndef MAP_RENDERER_H
#define MAP_RENDERER_H

#include <stdbool.h>
#include <stdint.h>
#include "../core/tiggo_engine.h"
#include "../data/tile_loader.h"

#ifdef __cplusplus
extern "C" {
#endif

// Boolean тип определен в tiggo_engine.h (уже включен выше)
// tile_loader.h тоже определяет BOOL, но это не проблема благодаря include guards

/**
 * Рендеринг карты
 * @param pEngine указатель на движок
 * @param bSimplified TRUE для упрощенного режима (Display 1), FALSE для полноценного (Display 0)
 * @return TRUE при успехе, FALSE при ошибке
 */
BOOL Tiggo_RenderMap(CTiggoEngine* pEngine, BOOL bSimplified);

/**
 * Инициализация рендерера карты
 * @param pEngine указатель на движок
 * @param bSimplified TRUE для упрощенного режима (Display 1), FALSE для полноценного (Display 0)
 * @param nWidth ширина окна
 * @param nHeight высота окна
 * @return TRUE при успехе, FALSE при ошибке
 */
BOOL Tiggo_InitMapRenderer(CTiggoEngine* pEngine, BOOL bSimplified, int nWidth, int nHeight);

/**
 * Обновление камеры
 * @param pEngine указатель на движок
 * @param fLat широта камеры
 * @param fLon долгота камеры
 * @param fZoom уровень масштабирования
 * @param fBearing направление камеры в градусах
 * @param fTilt наклон камеры в градусах
 */
void Tiggo_UpdateCamera(CTiggoEngine* pEngine, float fLat, float fLon, 
                       float fZoom, float fBearing, float fTilt);

/**
 * Обновление размера окна
 * @param pEngine указатель на движок
 * @param bSimplified TRUE для упрощенного режима (Display 1), FALSE для полноценного (Display 0)
 * @param nWidth ширина окна
 * @param nHeight высота окна
 */
void Tiggo_UpdateMapSize(CTiggoEngine* pEngine, BOOL bSimplified, int nWidth, int nHeight);

#ifdef __cplusplus
}
#endif

#endif // MAP_RENDERER_H

