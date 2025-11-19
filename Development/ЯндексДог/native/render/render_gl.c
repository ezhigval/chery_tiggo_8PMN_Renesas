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
#include "map_renderer.h"
#include "route_renderer.h"
#include "ui_renderer.h"
#include <GLES3/gl3.h>
#include <EGL/egl.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <android/log.h>

#define LOG_TAG "TiggoRenderGL"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

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
 * 
 * ВАЖНО: EGL контекст создается в Java коде (TiggoRenderThread),
 * нативный код только инициализирует рендереры
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
    
    // ВАЖНО: EGL контекст будет создан в Java коде (TiggoRenderThread)
    // Не создаем его здесь, так как Surface еще не создан
    // Устанавливаем флаги, что контекст "готов" к использованию
    // (но EGL поля будут NULL, их использовать не будем)
    
    // Получаем размеры окна из движка
    int nWidth = pEngine->m_nMainDisplayWidth;
    int nHeight = pEngine->m_nMainDisplayHeight;
    
    // Если размеры не установлены, используем значения по умолчанию
    if (nWidth <= 0 || nHeight <= 0) {
        nWidth = 1024;
        nHeight = 768;
    }
    
    g_pMainGLContext->nWidth = nWidth;
    g_pMainGLContext->nHeight = nHeight;
    
    // Инициализируем рендереры
    if (!Tiggo_InitMapRenderer(pEngine, bSimplified, nWidth, nHeight)) {
        pthread_mutex_destroy(&g_pMainGLContext->mutex);
        free(g_pMainGLContext);
        g_pMainGLContext = NULL;
        return FALSE;
    }
    
    // Инициализация UI рендерера
    if (!Tiggo_InitUIRenderer(pEngine, nWidth, nHeight)) {
        // UI рендерер не критичен, продолжаем даже если не инициализировался
    }
    
    // Помечаем контекст как инициализированный
    // (EGL контекст будет создан позже в Java коде)
    g_pMainGLContext->bInitialized = TRUE;
    
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
    
    // Инициализируем рендерер карты для упрощенного режима (Display 1)
    if (bSimplified && pEngine != NULL) {
        if (!Tiggo_InitMapRenderer(pEngine, TRUE, nWidth, nHeight)) {
            LOGE("Failed to init map renderer for secondary display");
            // Не возвращаем ошибку, так как окно уже создано
        }
    }
    
    return nActualIndex;
}

/**
 * Рендеринг основного окна (Display 0 - полноценная карта)
 * В стиле TurboDog: RenderGL()
 * 
 * ВАЖНО: EGL контекст уже активен (создан в Java коде TiggoRenderThread),
 * нативный код просто использует его
 */
void Tiggo_RenderGL(CTiggoEngine* pEngine) {
    if (pEngine == NULL || g_pMainGLContext == NULL || !g_pMainGLContext->bInitialized) {
        return;
    }
    
    pthread_mutex_lock(&g_pMainGLContext->mutex);
    
    // ВАЖНО: EGL контекст уже активен (создан и сделан текущим в Java коде)
    // Не нужно вызывать eglMakeCurrent() или eglSwapBuffers() -
    // это делается в Java коде (TiggoRenderThread)
    
    // Проверяем, что OpenGL контекст доступен
    // (EGL контекст уже создан в Java коде)
    
    // Рендеринг полноценной карты (Display 0)
    // Очистка экрана
    glClearColor(0.2f, 0.3f, 0.3f, 1.0f); // Темно-синий фон (нормальный цвет)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    
    // Логирование для отладки (первые 10 кадров)
    static int nFrameCount = 0;
    nFrameCount++;
    if (nFrameCount <= 10) {
        LOGI("RenderGL: frame=%d", nFrameCount);
    }
    
    // Рендеринг карты (полноценный режим)
    // - Тайлы карты
    // - POI и события (TODO)
    // - Полная детализация
    BOOL bMapRendered = Tiggo_RenderMap(pEngine, FALSE);
    
    // Рендеринг UI поверх карты (Display 0 - полный UI)
    Tiggo_RenderUI(pEngine, FALSE);
    
    // ВАЖНО: eglSwapBuffers() вызывается в Java коде (TiggoRenderThread)
    // Не вызываем его здесь
    
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
    
    // ВАЖНО: EGL контекст уже активен (создан и сделан текущим в Java коде TiggoSecondaryRenderThread)
    // Не нужно вызывать eglMakeCurrent() или eglSwapBuffers() -
    // это делается в Java коде (TiggoSecondaryRenderThread)
    
    // Рендеринг упрощенной карты (Display 1)
    // Очистка экрана
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    glClearColor(0.1f, 0.1f, 0.1f, 1.0f); // Темный фон
    
    // Рендеринг упрощенной карты
    // Только: маршрут (полилиния), камеры, события
    // Без: POI, детальной карты, зданий
    // - Только маршрут (полилиния)
    // - Камеры скорости (TODO)
    // - Дорожные события (TODO)
    // - Минимальная детализация карты
    
    Tiggo_RenderMap(pEngine, TRUE);
    
    // Рендеринг упрощенного UI (Display 1)
    Tiggo_RenderUI(pEngine, TRUE);
    
    // ВАЖНО: eglSwapBuffers() вызывается в Java коде (TiggoSecondaryRenderThread)
    // Не вызываем его здесь
}

/**
 * Уничтожение OpenGL контекста
 * В стиле TurboDog: DestroyGL()
 * 
 * ВАЖНО: EGL контекст уничтожается в Java коде (TiggoRenderThread),
 * нативный код только очищает ресурсы
 */
void Tiggo_DestroyGL(CTiggoEngine* pEngine) {
    // Уничтожаем UI рендерер
    Tiggo_DestroyUIRenderer(pEngine);
    
    if (g_pMainGLContext != NULL) {
        // ВАЖНО: EGL контекст уничтожается в Java коде (TiggoRenderThread)
        // Не уничтожаем его здесь, так как он не был создан в нативном коде
        // DestroyEGLContext(g_pMainGLContext); // Закомментировано - EGL в Java
        
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
        
        // Обновляем размер рендерера карты
        Tiggo_UpdateMapSize(pEngine, g_pMainGLContext->bSimplified, nWidth, nHeight);
        
        // Обновляем размер UI рендерера
        Tiggo_UpdateUISize(pEngine, nWidth, nHeight);
        
        // Обновляем viewport
        glViewport(0, 0, nWidth, nHeight);
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
    // TODO: установка DPI для масштабирования тайлов и UI элементов
    // Можно использовать для масштабирования размеров тайлов и UI
}

