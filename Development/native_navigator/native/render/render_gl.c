/**
 * render_gl.c - Реализация OpenGL ES рендеринга (в стиле TurboDog)
 * 
 * Стиль TurboDog:
 * - Префиксы функций
 * - Венгерская нотация
 * - C код (не C++)
 * - Аппаратное ускорение через OpenGL ES
 */

#include "render_gl.h"
#include <GLES3/gl3.h>
#include <EGL/egl.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>

// Внутренняя структура для OpenGL контекста
typedef struct {
    EGLDisplay eglDisplay;
    EGLConfig eglConfig;
    EGLContext eglContext;
    EGLSurface eglSurface;
    
    // Размеры окна
    int nWidth;
    int nHeight;
    
    // Флаги
    BOOL bInitialized;
    BOOL bSimplified;  // TRUE для упрощенного режима (Display 1)
    BOOL bEnable3D;
    
    // Mutex для синхронизации
    pthread_mutex_t mutex;
} GLContext;

// Внутренняя структура для второго окна
typedef struct {
    int nIndex;
    GLContext* pGLContext;
    BOOL bActive;
    
    // Размеры окна
    int nX;
    int nY;
    int nWidth;
    int nHeight;
    int nDpi;
    BOOL bSimplified;
} SecondaryWindow;

// Глобальные переменные (как в TurboDog)
static GLContext* g_pMainGLContext = NULL;
static SecondaryWindow* g_pSecondaryWindows = NULL;
static int g_nSecondaryWindowCount = 0;
static int g_nMaxSecondaryWindows = 4; // Максимум 4 окна (как в TurboDog)

/**
 * Инициализация EGL контекста
 */
static BOOL InitEGLContext(GLContext* pCtx, EGLNativeWindowType window, BOOL bSimplified) {
    if (pCtx == NULL) {
        return FALSE;
    }
    
    // Получаем EGL Display
    pCtx->eglDisplay = eglGetDisplay(EGL_DEFAULT_DISPLAY);
    if (pCtx->eglDisplay == EGL_NO_DISPLAY) {
        return FALSE;
    }
    
    // Инициализируем EGL
    EGLint nMajor, nMinor;
    if (!eglInitialize(pCtx->eglDisplay, &nMajor, &nMinor)) {
        return FALSE;
    }
    
    // Выбираем конфигурацию EGL
    const EGLint attribs[] = {
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES3_BIT,
        EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
        EGL_BLUE_SIZE, 8,
        EGL_GREEN_SIZE, 8,
        EGL_RED_SIZE, 8,
        EGL_ALPHA_SIZE, 8,
        EGL_DEPTH_SIZE, 24,
        EGL_STENCIL_SIZE, 8,
        EGL_NONE
    };
    
    EGLint nConfigCount;
    EGLConfig configs[1];
    if (!eglChooseConfig(pCtx->eglDisplay, attribs, configs, 1, &nConfigCount)) {
        return FALSE;
    }
    
    if (nConfigCount == 0) {
        return FALSE;
    }
    
    pCtx->eglConfig = configs[0];
    
    // Создаем EGL Context
    const EGLint contextAttribs[] = {
        EGL_CONTEXT_CLIENT_VERSION, 3, // OpenGL ES 3.0
        EGL_NONE
    };
    
    pCtx->eglContext = eglCreateContext(pCtx->eglDisplay, pCtx->eglConfig,
                                        EGL_NO_CONTEXT, contextAttribs);
    if (pCtx->eglContext == EGL_NO_CONTEXT) {
        return FALSE;
    }
    
    // Создаем EGL Surface (если окно указано)
    if (window != NULL) {
        pCtx->eglSurface = eglCreateWindowSurface(pCtx->eglDisplay, pCtx->eglConfig,
                                                  window, NULL);
        if (pCtx->eglSurface == EGL_NO_SURFACE) {
            eglDestroyContext(pCtx->eglDisplay, pCtx->eglContext);
            return FALSE;
        }
        
        // Сделать контекст текущим
        if (!eglMakeCurrent(pCtx->eglDisplay, pCtx->eglSurface, pCtx->eglSurface,
                           pCtx->eglContext)) {
            eglDestroySurface(pCtx->eglDisplay, pCtx->eglSurface);
            eglDestroyContext(pCtx->eglDisplay, pCtx->eglContext);
            return FALSE;
        }
    }
    
    pCtx->bInitialized = TRUE;
    return TRUE;
}

/**
 * Уничтожение EGL контекста
 */
static void DestroyEGLContext(GLContext* pCtx) {
    if (pCtx == NULL || !pCtx->bInitialized) {
        return;
    }
    
    // Деактивируем контекст
    if (pCtx->eglDisplay != EGL_NO_DISPLAY) {
        eglMakeCurrent(pCtx->eglDisplay, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
        
        // Уничтожаем Surface
        if (pCtx->eglSurface != EGL_NO_SURFACE) {
            eglDestroySurface(pCtx->eglDisplay, pCtx->eglSurface);
            pCtx->eglSurface = EGL_NO_SURFACE;
        }
        
        // Уничтожаем Context
        if (pCtx->eglContext != EGL_NO_CONTEXT) {
            eglDestroyContext(pCtx->eglDisplay, pCtx->eglContext);
            pCtx->eglContext = EGL_NO_CONTEXT;
        }
        
        // Завершаем EGL
        eglTerminate(pCtx->eglDisplay);
        pCtx->eglDisplay = EGL_NO_DISPLAY;
    }
    
    pCtx->bInitialized = FALSE;
}

/**
 * Создание основного OpenGL контекста
 * В стиле TurboDog: CreateGL(boolean, boolean)
 */
BOOL Tiggo_CreateGL(CTiggoEngine* pEngine, BOOL bSimplified, BOOL bEnable3D) {
    if (pEngine == NULL) {
        return FALSE;
    }
    
    // Если контекст уже создан, уничтожаем его
    if (g_pMainGLContext != NULL) {
        Tiggo_DestroyGL(pEngine);
    }
    
    // Выделяем память для контекста
    g_pMainGLContext = (GLContext*)malloc(sizeof(GLContext));
    if (g_pMainGLContext == NULL) {
        return FALSE;
    }
    
    // Инициализация нулями
    memset(g_pMainGLContext, 0, sizeof(GLContext));
    g_pMainGLContext->bSimplified = bSimplified;
    g_pMainGLContext->bEnable3D = bEnable3D;
    pthread_mutex_init(&g_pMainGLContext->mutex, NULL);
    
    // Инициализация EGL контекста
    // TODO: получить EGLNativeWindowType из Android
    // Пока создаем без окна, окно будет создано позже
    
    // Инициализация OpenGL
    // TODO: настройка OpenGL для рендеринга карты
    
    return TRUE;
}

/**
 * Создание вторичного OpenGL контекста
 * В стиле TurboDog: CreateSecondaryGL(...)
 */
int Tiggo_CreateSecondaryGL(CTiggoEngine* pEngine, int nWidth, int nHeight, int nIndex,
                            BOOL bSimplified, int nDpi, int nFormat, int nFlags, int nAdditionalFlags) {
    if (pEngine == NULL) {
        return -1;
    }
    
    // Выделяем память для массива окон (если еще не выделена)
    if (g_pSecondaryWindows == NULL) {
        g_pSecondaryWindows = (SecondaryWindow*)malloc(sizeof(SecondaryWindow) * g_nMaxSecondaryWindows);
        if (g_pSecondaryWindows == NULL) {
            return -1;
        }
        memset(g_pSecondaryWindows, 0, sizeof(SecondaryWindow) * g_nMaxSecondaryWindows);
    }
    
    // Находим свободное место или используем указанный индекс
    int nActualIndex = -1;
    if (nIndex >= 0 && nIndex < g_nMaxSecondaryWindows) {
        if (!g_pSecondaryWindows[nIndex].bActive) {
            nActualIndex = nIndex;
        }
    } else {
        // Ищем свободное место
        for (int i = 0; i < g_nMaxSecondaryWindows; i++) {
            if (!g_pSecondaryWindows[i].bActive) {
                nActualIndex = i;
                break;
            }
        }
    }
    
    if (nActualIndex < 0) {
        return -1; // Нет свободного места
    }
    
    SecondaryWindow* pWindow = &g_pSecondaryWindows[nActualIndex];
    
    // Инициализация окна
    pWindow->nIndex = nActualIndex;
    pWindow->nWidth = nWidth;
    pWindow->nHeight = nHeight;
    pWindow->nDpi = nDpi;
    pWindow->bSimplified = bSimplified;
    pWindow->bActive = TRUE;
    
    // Выделяем память для GL контекста
    pWindow->pGLContext = (GLContext*)malloc(sizeof(GLContext));
    if (pWindow->pGLContext == NULL) {
        pWindow->bActive = FALSE;
        return -1;
    }
    
    memset(pWindow->pGLContext, 0, sizeof(GLContext));
    pWindow->pGLContext->nWidth = nWidth;
    pWindow->pGLContext->nHeight = nHeight;
    pWindow->pGLContext->bSimplified = bSimplified;
    pthread_mutex_init(&pWindow->pGLContext->mutex, NULL);
    
    // Инициализация EGL контекста
    // TODO: получить EGLNativeWindowType из Android Presentation
    // Пока создаем без окна, окно будет создано позже
    
    // Увеличиваем счетчик окон
    if (nActualIndex >= g_nSecondaryWindowCount) {
        g_nSecondaryWindowCount = nActualIndex + 1;
    }
    
    return nActualIndex;
}

/**
 * Рендеринг основного окна (Display 0 - полноценная карта)
 * В стиле TurboDog: RenderGL()
 */
void Tiggo_RenderGL(CTiggoEngine* pEngine) {
    if (pEngine == NULL || g_pMainGLContext == NULL || !g_pMainGLContext->bInitialized) {
        return;
    }
    
    pthread_mutex_lock(&g_pMainGLContext->mutex);
    
    // Активируем контекст
    if (g_pMainGLContext->eglDisplay != EGL_NO_DISPLAY &&
        g_pMainGLContext->eglSurface != EGL_NO_SURFACE &&
        g_pMainGLContext->eglContext != EGL_NO_CONTEXT) {
        
        eglMakeCurrent(g_pMainGLContext->eglDisplay, g_pMainGLContext->eglSurface,
                      g_pMainGLContext->eglSurface, g_pMainGLContext->eglContext);
        
        // Рендеринг полноценной карты (Display 0)
        // TODO: реализовать рендеринг карты со всеми деталями
        // - Тайлы карты
        // - POI и события
        // - Полная детализация
        
        // Очистка экрана
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
        glClearColor(0.2f, 0.3f, 0.3f, 1.0f); // Темно-синий фон
        
        // TODO: рендеринг карты
        
        // Swap buffers
        eglSwapBuffers(g_pMainGLContext->eglDisplay, g_pMainGLContext->eglSurface);
    }
    
    pthread_mutex_unlock(&g_pMainGLContext->mutex);
}

/**
 * Рендеринг второго окна (Display 1 - упрощенная карта)
 * В стиле TurboDog: RenderSecondaryWndGL(int)
 */
void Tiggo_RenderSecondaryWndGL(CTiggoEngine* pEngine, int nIndex) {
    if (pEngine == NULL || g_pSecondaryWindows == NULL) {
        return;
    }
    
    if (nIndex < 0 || nIndex >= g_nMaxSecondaryWindows) {
        return;
    }
    
    SecondaryWindow* pWindow = &g_pSecondaryWindows[nIndex];
    if (!pWindow->bActive || pWindow->pGLContext == NULL) {
        return;
    }
    
    GLContext* pCtx = pWindow->pGLContext;
    
    pthread_mutex_lock(&pCtx->mutex);
    
    // Активируем контекст
    if (pCtx->eglDisplay != EGL_NO_DISPLAY &&
        pCtx->eglSurface != EGL_NO_SURFACE &&
        pCtx->eglContext != EGL_NO_CONTEXT) {
        
        eglMakeCurrent(pCtx->eglDisplay, pCtx->eglSurface, pCtx->eglSurface, pCtx->eglContext);
        
        // Рендеринг упрощенной карты (Display 1)
        // Только: маршрут (полилиния), камеры, события
        // Без: POI, детальной карты, зданий
        
        // Очистка экрана
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
        glClearColor(0.1f, 0.1f, 0.1f, 1.0f); // Темный фон
        
        // TODO: рендеринг упрощенной карты
        // - Только маршрут (полилиния)
        // - Камеры скорости
        // - Дорожные события
        // - Минимальная детализация карты
        
        // Swap buffers
        eglSwapBuffers(pCtx->eglDisplay, pCtx->eglSurface);
    }
    
    pthread_mutex_unlock(&pCtx->mutex);
}

/**
 * Уничтожение OpenGL контекста
 * В стиле TurboDog: DestroyGL()
 */
void Tiggo_DestroyGL(CTiggoEngine* pEngine) {
    if (g_pMainGLContext != NULL) {
        DestroyEGLContext(g_pMainGLContext);
        pthread_mutex_destroy(&g_pMainGLContext->mutex);
        free(g_pMainGLContext);
        g_pMainGLContext = NULL;
    }
    
    // Уничтожаем второстепенные окна
    if (g_pSecondaryWindows != NULL) {
        for (int i = 0; i < g_nMaxSecondaryWindows; i++) {
            if (g_pSecondaryWindows[i].bActive && g_pSecondaryWindows[i].pGLContext != NULL) {
                DestroyEGLContext(g_pSecondaryWindows[i].pGLContext);
                pthread_mutex_destroy(&g_pSecondaryWindows[i].pGLContext->mutex);
                free(g_pSecondaryWindows[i].pGLContext);
                g_pSecondaryWindows[i].pGLContext = NULL;
                g_pSecondaryWindows[i].bActive = FALSE;
            }
        }
        
        free(g_pSecondaryWindows);
        g_pSecondaryWindows = NULL;
        g_nSecondaryWindowCount = 0;
    }
}

/**
 * Добавление второго окна
 * В стиле TurboDog: AddSecondaryWndGL(...)
 */
int Tiggo_AddSecondaryWndGL(CTiggoEngine* pEngine, int nX, int nY, int nWidth, int nHeight,
                            int nDpi, BOOL bSimplified, int nFormat, int nFlags,
                            int nAdditionalFlags, int nReserved) {
    // Используем CreateSecondaryGL
    return Tiggo_CreateSecondaryGL(pEngine, nWidth, nHeight, -1, bSimplified, nDpi, nFormat, nFlags, nAdditionalFlags);
}

/**
 * Удаление второго окна
 * В стиле TurboDog: DeleteSecondaryWndGL(int)
 */
void Tiggo_DeleteSecondaryWndGL(CTiggoEngine* pEngine, int nIndex) {
    if (g_pSecondaryWindows == NULL) {
        return;
    }
    
    if (nIndex < 0 || nIndex >= g_nMaxSecondaryWindows) {
        return;
    }
    
    SecondaryWindow* pWindow = &g_pSecondaryWindows[nIndex];
    if (!pWindow->bActive) {
        return;
    }
    
    // Уничтожаем GL контекст
    if (pWindow->pGLContext != NULL) {
        DestroyEGLContext(pWindow->pGLContext);
        pthread_mutex_destroy(&pWindow->pGLContext->mutex);
        free(pWindow->pGLContext);
        pWindow->pGLContext = NULL;
    }
    
    pWindow->bActive = FALSE;
}

/**
 * Установка размера второго окна
 * В стиле TurboDog: SetSecondaryWndSize(...)
 */
void Tiggo_SetSecondaryWndSize(CTiggoEngine* pEngine, int nIndex, int nWidth, int nHeight,
                               int nX, int nY, int nDpi, BOOL bSimplified) {
    if (g_pSecondaryWindows == NULL) {
        return;
    }
    
    if (nIndex < 0 || nIndex >= g_nMaxSecondaryWindows) {
        return;
    }
    
    SecondaryWindow* pWindow = &g_pSecondaryWindows[nIndex];
    if (!pWindow->bActive) {
        return;
    }
    
    pWindow->nX = nX;
    pWindow->nY = nY;
    pWindow->nWidth = nWidth;
    pWindow->nHeight = nHeight;
    pWindow->nDpi = nDpi;
    pWindow->bSimplified = bSimplified;
    
    if (pWindow->pGLContext != NULL) {
        pWindow->pGLContext->nWidth = nWidth;
        pWindow->pGLContext->nHeight = nHeight;
        pWindow->pGLContext->bSimplified = bSimplified;
    }
}

/**
 * Установка размера основного окна
 * В стиле TurboDog: SetWindowSizeGL(int, int)
 */
void Tiggo_SetWindowSizeGL(CTiggoEngine* pEngine, int nWidth, int nHeight) {
    if (g_pMainGLContext != NULL) {
        g_pMainGLContext->nWidth = nWidth;
        g_pMainGLContext->nHeight = nHeight;
        
        // TODO: обновление viewport и проекции
    }
}

/**
 * Отмена рендеринга
 * В стиле TurboDog: CancelRenderGL()
 */
void Tiggo_CancelRenderGL(CTiggoEngine* pEngine) {
    // TODO: отмена текущего рендеринга
}

/**
 * Установка метрик дисплея
 * В стиле TurboDog: SetDisplayMetricsGL(int)
 */
void Tiggo_SetDisplayMetricsGL(CTiggoEngine* pEngine, int nDpi) {
    // TODO: установка DPI для масштабирования
}

