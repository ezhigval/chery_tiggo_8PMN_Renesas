/**
 * route_renderer.h - Заголовок рендеринга маршрута (в стиле TurboDog)
 */

#ifndef ROUTE_RENDERER_H
#define ROUTE_RENDERER_H

#include <stdbool.h>
#include <stdint.h>
#include "../core/tiggo_engine.h"

#ifdef __cplusplus
extern "C" {
#endif

// Boolean тип определен в tiggo_engine.h (уже включен выше)

/**
 * Рендеринг маршрута (полилинии)
 * @param pEngine указатель на движок
 * @param bSimplified TRUE для упрощенного режима (Display 1), FALSE для полноценного (Display 0)
 * @return TRUE при успехе, FALSE при ошибке
 */
BOOL Tiggo_RenderRoute(CTiggoEngine* pEngine, BOOL bSimplified);

/**
 * Установка точек маршрута
 * @param pEngine указатель на движок
 * @param pdRoutePoints массив точек маршрута [lat1, lon1, lat2, lon2, ...]
 * @param nPointCount количество точек
 * @return TRUE при успехе, FALSE при ошибке
 */
BOOL Tiggo_SetRoutePoints(CTiggoEngine* pEngine, const double* pdRoutePoints, int nPointCount);

/**
 * Очистка маршрута
 * @param pEngine указатель на движок
 */
void Tiggo_ClearRoute(CTiggoEngine* pEngine);

#ifdef __cplusplus
}
#endif

#endif // ROUTE_RENDERER_H

