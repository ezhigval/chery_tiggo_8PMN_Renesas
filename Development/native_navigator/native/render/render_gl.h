/**
 * render_gl.h - OpenGL ES рендеринг (в стиле TurboDog)
 * 
 * Стиль TurboDog:
 * - Префиксы функций: Tiggo_CreateGL, Tiggo_RenderGL
 * - Венгерская нотация
 * - C код (не C++)
 */

#ifndef RENDER_GL_H
#define RENDER_GL_H

#include <stdbool.h>
#include <stdint.h>
#include "../core/tiggo_engine.h"

#ifdef __cplusplus
extern "C" {
#endif

// Boolean тип
typedef int BOOL;
#define TRUE  1
#define FALSE 0

// ========== OpenGL функции (в стиле TurboDog) ==========

/**
 * Создание основного OpenGL контекста
 * @param pEngine указатель на движок
 * @param bSimplified TRUE для упрощенного режима (Display 1), FALSE для полноценного (Display 0)
 * @param bEnable3D TRUE для 3D режима, FALSE для 2D
 * @return TRUE при успехе, FALSE при ошибке
 */
BOOL Tiggo_CreateGL(CTiggoEngine* pEngine, BOOL bSimplified, BOOL bEnable3D);

/**
 * Создание вторичного OpenGL контекста для второго дисплея
 * @param pEngine указатель на движок
 * @param nWidth ширина окна
 * @param nHeight высота окна
 * @param nIndex индекс окна
 * @param bSimplified TRUE для упрощенного режима (Display 1)
 * @param nDpi DPI дисплея
 * @param nFormat формат
 * @param nFlags флаги
 * @param nAdditionalFlags дополнительные флаги
 * @return индекс созданного окна, -1 при ошибке
 */
int Tiggo_CreateSecondaryGL(CTiggoEngine* pEngine, int nWidth, int nHeight, int nIndex,
                            BOOL bSimplified, int nDpi, int nFormat, int nFlags, int nAdditionalFlags);

/**
 * Рендеринг основного окна (Display 0 - полноценная карта)
 * @param pEngine указатель на движок
 */
void Tiggo_RenderGL(CTiggoEngine* pEngine);

/**
 * Рендеринг второго окна (Display 1 - упрощенная карта)
 * @param pEngine указатель на движок
 * @param nIndex индекс окна
 */
void Tiggo_RenderSecondaryWndGL(CTiggoEngine* pEngine, int nIndex);

/**
 * Уничтожение OpenGL контекста
 * @param pEngine указатель на движок
 */
void Tiggo_DestroyGL(CTiggoEngine* pEngine);

/**
 * Добавление второго окна (Presentation)
 * @param pEngine указатель на движок
 * @param nX координата X
 * @param nY координата Y
 * @param nWidth ширина
 * @param nHeight высота
 * @param nDpi DPI
 * @param bSimplified TRUE для упрощенного режима
 * @param nFormat формат
 * @param nFlags флаги
 * @param nAdditionalFlags дополнительные флаги
 * @param nReserved зарезервировано
 * @return индекс созданного окна, -1 при ошибке
 */
int Tiggo_AddSecondaryWndGL(CTiggoEngine* pEngine, int nX, int nY, int nWidth, int nHeight,
                            int nDpi, BOOL bSimplified, int nFormat, int nFlags,
                            int nAdditionalFlags, int nReserved);

/**
 * Удаление второго окна
 * @param pEngine указатель на движок
 * @param nIndex индекс окна
 */
void Tiggo_DeleteSecondaryWndGL(CTiggoEngine* pEngine, int nIndex);

/**
 * Установка размера второго окна
 * @param pEngine указатель на движок
 * @param nIndex индекс окна
 * @param nWidth ширина
 * @param nHeight высота
 * @param nX координата X
 * @param nY координата Y
 * @param nDpi DPI
 * @param bSimplified TRUE для упрощенного режима
 */
void Tiggo_SetSecondaryWndSize(CTiggoEngine* pEngine, int nIndex, int nWidth, int nHeight,
                               int nX, int nY, int nDpi, BOOL bSimplified);

/**
 * Установка размера основного окна
 * @param pEngine указатель на движок
 * @param nWidth ширина
 * @param nHeight высота
 */
void Tiggo_SetWindowSizeGL(CTiggoEngine* pEngine, int nWidth, int nHeight);

/**
 * Отмена рендеринга
 * @param pEngine указатель на движок
 */
void Tiggo_CancelRenderGL(CTiggoEngine* pEngine);

/**
 * Установка метрик дисплея
 * @param pEngine указатель на движок
 * @param nDpi DPI
 */
void Tiggo_SetDisplayMetricsGL(CTiggoEngine* pEngine, int nDpi);

#ifdef __cplusplus
}
#endif

#endif // RENDER_GL_H

