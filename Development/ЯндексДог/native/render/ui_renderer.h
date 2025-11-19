/**
 * ui_renderer.h - Заголовок рендеринга UI элементов (в стиле TurboDog)
 * 
 * UI рендеринг поверх OpenGL ES для отображения:
 * - Скорости
 * - Указателей маневров
 * - Ограничений скорости
 * - Названий дорог
 * - Других навигационных элементов
 */

#ifndef UI_RENDERER_H
#define UI_RENDERER_H

#include "../core/tiggo_engine.h"

#ifdef __cplusplus
extern "C" {
#endif

// Boolean тип определен в tiggo_engine.h (уже включен выше)

/**
 * Инициализация UI рендерера
 * @param pEngine указатель на движок
 * @param nWidth ширина окна
 * @param nHeight высота окна
 * @return TRUE при успехе, FALSE при ошибке
 */
BOOL Tiggo_InitUIRenderer(CTiggoEngine* pEngine, int nWidth, int nHeight);

/**
 * Уничтожение UI рендерера
 * @param pEngine указатель на движок
 */
void Tiggo_DestroyUIRenderer(CTiggoEngine* pEngine);

/**
 * Рендеринг UI элементов
 * @param pEngine указатель на движок
 * @param bSimplified TRUE для упрощенного UI (Display 1), FALSE для полного (Display 0)
 */
void Tiggo_RenderUI(CTiggoEngine* pEngine, BOOL bSimplified);

/**
 * Обновление размера UI рендерера
 * @param pEngine указатель на движок
 * @param nWidth новая ширина
 * @param nHeight новая высота
 */
void Tiggo_UpdateUISize(CTiggoEngine* pEngine, int nWidth, int nHeight);

// ========== Отдельные функции рендеринга UI элементов ==========

/**
 * Рендеринг скорости
 * @param pEngine указатель на движок
 * @param nSpeed скорость в км/ч
 * @param nX позиция X
 * @param nY позиция Y
 */
void Tiggo_RenderSpeed(CTiggoEngine* pEngine, int nSpeed, int nX, int nY);

/**
 * Рендеринг указателя маневра
 * @param pEngine указатель на движок
 * @param nType тип маневра (0-нет, 1-налево, 2-направо, и т.д.)
 * @param nDistance расстояние до маневра в метрах
 * @param nCenterX центр экрана X
 * @param nCenterY центр экрана Y
 */
void Tiggo_RenderManeuverArrow(CTiggoEngine* pEngine, int nType, int nDistance, 
                               int nCenterX, int nCenterY);

/**
 * Рендеринг ограничения скорости
 * @param pEngine указатель на движок
 * @param nSpeedLimit ограничение скорости в км/ч
 * @param nX позиция X
 * @param nY позиция Y
 */
void Tiggo_RenderSpeedLimit(CTiggoEngine* pEngine, int nSpeedLimit, int nX, int nY);

/**
 * Рендеринг названия дороги
 * @param pEngine указатель на движок
 * @param pcRoadName название дороги
 * @param nX позиция X
 * @param nY позиция Y
 */
void Tiggo_RenderRoadName(CTiggoEngine* pEngine, const char* pcRoadName, int nX, int nY);

/**
 * Рендеринг расстояния до цели
 * @param pEngine указатель на движок
 * @param nDistance расстояние в метрах
 * @param nTime время в секундах
 * @param nX позиция X
 * @param nY позиция Y
 */
void Tiggo_RenderDistanceToDestination(CTiggoEngine* pEngine, int nDistance, int nTime,
                                       int nX, int nY);

#ifdef __cplusplus
}
#endif

#endif // UI_RENDERER_H

