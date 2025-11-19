/**
 * route_renderer.c - Рендеринг маршрута (полилинии) (в стиле TurboDog)
 * 
 * Стиль TurboDog:
 * - Префиксы функций: Tiggo_RenderRoute
 * - Венгерская нотация
 * - C код (не C++)
 * - OpenGL ES 3.0
 */

#include "route_renderer.h"
#include "shader_utils.h"
#include "../core/tiggo_engine.h"
#include <GLES3/gl3.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// Внутренняя структура для рендеринга маршрута
typedef struct {
    // Точки маршрута (в географических координатах)
    double* pdRoutePoints;  // [lat1, lon1, lat2, lon2, ...]
    int nRoutePointCount;
    int nMaxRoutePoints;
    
    // Точки маршрута (в экранных координатах)
    float* pfRouteVertices;  // [x1, y1, x2, y2, ...]
    int nRouteVertexCount;
    int nMaxRouteVertices;
    
    // Буферы OpenGL
    GLuint nRouteVBO;  // Vertex Buffer Object
    GLuint nRouteVAO;  // Vertex Array Object
    
    // Шейдеры
    GLuint nRouteShaderProgram;
    
    // Стиль маршрута
    float fRouteWidth;  // Ширина линии маршрута
    float fRouteColor[4];  // Цвет маршрута [R, G, B, A]
    
    // Параметры камеры для конвертации координат
    float fCameraLat;
    float fCameraLon;
    float fCameraZoom;
    int nViewWidth;
    int nViewHeight;
    
    // Флаги
    BOOL bInitialized;
    BOOL bHasRoute;
    BOOL bNeedUpdate;  // TRUE если нужно обновить экранные координаты
} RouteRenderer;

// Глобальные переменные
static RouteRenderer* g_pRouteRenderer = NULL;

/**
 * Инициализация шейдеров маршрута
 */
static BOOL InitRouteShaders(RouteRenderer* pRenderer) {
    if (pRenderer == NULL) {
        return FALSE;
    }
    
    // Вершинный шейдер для маршрута (полилинии)
    const char* pVertexShaderSource = 
        "#version 300 es\n"
        "layout (location = 0) in vec2 aPos;\n"
        "uniform mat4 projection;\n"
        "uniform mat4 view;\n"
        "void main() {\n"
        "    gl_Position = projection * view * vec4(aPos.x, aPos.y, 0.0, 1.0);\n"
        "}\n";
    
    // Фрагментный шейдер для маршрута
    const char* pFragmentShaderSource = 
        "#version 300 es\n"
        "precision mediump float;\n"
        "out vec4 FragColor;\n"
        "uniform vec4 routeColor;\n"
        "void main() {\n"
        "    FragColor = routeColor;\n"
        "}\n";
    
    // Создаем шейдерную программу
    pRenderer->nRouteShaderProgram = Tiggo_CreateShaderProgram(pVertexShaderSource, pFragmentShaderSource);
    if (pRenderer->nRouteShaderProgram == 0) {
        return FALSE;
    }
    
    Tiggo_CheckGLError("InitRouteShaders");
    
    return TRUE;
}

/**
 * Создание рендерера маршрута
 */
static RouteRenderer* CreateRouteRenderer(void) {
    RouteRenderer* pRenderer = (RouteRenderer*)malloc(sizeof(RouteRenderer));
    if (pRenderer == NULL) {
        return NULL;
    }
    
    memset(pRenderer, 0, sizeof(RouteRenderer));
    
    // Настройки по умолчанию
    pRenderer->fRouteWidth = 5.0f;  // 5 пикселей
    pRenderer->fRouteColor[0] = 0.2f;  // R
    pRenderer->fRouteColor[1] = 0.6f;  // G
    pRenderer->fRouteColor[2] = 1.0f;  // B
    pRenderer->fRouteColor[3] = 1.0f;  // A (непрозрачный)
    
    pRenderer->nMaxRouteVertices = 10000; // Максимум 10000 точек
    
    // Выделяем память для вершин маршрута
    pRenderer->pfRouteVertices = (float*)malloc(sizeof(float) * pRenderer->nMaxRouteVertices * 2);
    if (pRenderer->pfRouteVertices == NULL) {
        free(pRenderer);
        return NULL;
    }
    
    // Инициализация шейдеров
    if (!InitRouteShaders(pRenderer)) {
        free(pRenderer->pfRouteVertices);
        free(pRenderer);
        return NULL;
    }
    
    // Создаем VBO и VAO для рендеринга маршрута
    glGenVertexArrays(1, &pRenderer->nRouteVAO);
    glGenBuffers(1, &pRenderer->nRouteVBO);
    
    glBindVertexArray(pRenderer->nRouteVAO);
    
    // Инициализируем VBO (пока пустой, заполним при обновлении маршрута)
    glBindBuffer(GL_ARRAY_BUFFER, pRenderer->nRouteVBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(float) * pRenderer->nMaxRouteVertices * 2, NULL, GL_DYNAMIC_DRAW);
    
    // Настраиваем атрибут позиции (location = 0)
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);
    
    glBindVertexArray(0);
    
    // Инициализация параметров камеры
    pRenderer->fCameraLat = 0.0f;
    pRenderer->fCameraLon = 0.0f;
    pRenderer->fCameraZoom = 10.0f;
    pRenderer->nViewWidth = 1024;
    pRenderer->nViewHeight = 768;
    
    Tiggo_CheckGLError("CreateRouteRenderer");
    
    pRenderer->bInitialized = TRUE;
    
    return pRenderer;
}

/**
 * Уничтожение рендерера маршрута
 */
static void DestroyRouteRenderer(RouteRenderer* pRenderer) {
    if (pRenderer == NULL) {
        return;
    }
    
    if (pRenderer->bInitialized) {
        // Удаляем буферы
        if (pRenderer->nRouteVBO != 0) {
            glDeleteBuffers(1, &pRenderer->nRouteVBO);
        }
        if (pRenderer->nRouteVAO != 0) {
            glDeleteVertexArrays(1, &pRenderer->nRouteVAO);
        }
        
        // Удаляем шейдеры
        if (pRenderer->nRouteShaderProgram != 0) {
            glDeleteProgram(pRenderer->nRouteShaderProgram);
        }
    }
    
    // Освобождаем память вершин
    if (pRenderer->pfRouteVertices != NULL) {
        free(pRenderer->pfRouteVertices);
    }
    
    free(pRenderer);
}

/**
 * Конвертация географических координат в экранные координаты
 * Web Mercator проекция с учетом камеры
 */
static void ConvertGeoToScreen(float fLat, float fLon, float fCameraLat, float fCameraLon,
                               float fZoom, int nWidth, int nHeight,
                               float* pfScreenX, float* pfScreenY) {
    if (pfScreenX == NULL || pfScreenY == NULL) {
        return;
    }
    
    // Web Mercator проекция
    double dLat = fLat * M_PI / 180.0;
    double dLon = fLon * M_PI / 180.0;
    
    double dCameraLat = fCameraLat * M_PI / 180.0;
    double dCameraLon = fCameraLon * M_PI / 180.0;
    
    // Конвертируем в метры Web Mercator
    double dEarthRadius = 6378137.0; // Радиус Земли в метрах
    
    double dX = dLon * dEarthRadius;
    double dY = log(tan(M_PI / 4.0 + dLat / 2.0)) * dEarthRadius;
    
    double dCameraX = dCameraLon * dEarthRadius;
    double dCameraY = log(tan(M_PI / 4.0 + dCameraLat / 2.0)) * dEarthRadius;
    
    // Масштаб в зависимости от уровня зума
    double dScale = pow(2.0, fZoom);
    
    // Конвертируем в экранные координаты (центр экрана - позиция камеры)
    double dScreenX = (dX - dCameraX) * dScale + (double)nWidth / 2.0;
    double dScreenY = -(dY - dCameraY) * dScale + (double)nHeight / 2.0;
    
    *pfScreenX = (float)dScreenX;
    *pfScreenY = (float)dScreenY;
}

/**
 * Рендеринг маршрута
 * В стиле TurboDog: RenderRoute()
 */
BOOL Tiggo_RenderRoute(CTiggoEngine* pEngine, BOOL bSimplified) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return FALSE;
    }
    
    if (g_pRouteRenderer == NULL || !g_pRouteRenderer->bInitialized) {
        // Инициализируем рендерер маршрута при первом вызове
        g_pRouteRenderer = CreateRouteRenderer();
        if (g_pRouteRenderer == NULL) {
            return FALSE;
        }
    }
    
    if (!g_pRouteRenderer->bHasRoute || g_pRouteRenderer->nRoutePointCount < 2) {
        return TRUE; // Нет маршрута для рендеринга
    }
    
    // Обновляем экранные координаты при изменении камеры
    if (g_pRouteRenderer->bNeedUpdate || 
        g_pRouteRenderer->fCameraLat != pEngine->m_fCurrentLat ||
        g_pRouteRenderer->fCameraLon != pEngine->m_fCurrentLon ||
        g_pRouteRenderer->fCameraZoom != (pEngine->m_fCurrentLat > 0 ? 10.0f : 10.0f)) {
        // Получаем параметры камеры из движка
        // TODO: добавить методы получения камеры из CTiggoEngine
        g_pRouteRenderer->fCameraLat = pEngine->m_fCurrentLat;
        g_pRouteRenderer->fCameraLon = pEngine->m_fCurrentLon;
        g_pRouteRenderer->fCameraZoom = 10.0f; // TODO: получить из камеры
        g_pRouteRenderer->nViewWidth = 1024;   // TODO: получить из рендерера
        g_pRouteRenderer->nViewHeight = 768;   // TODO: получить из рендерера
        
        // Конвертируем географические координаты в экранные
        if (g_pRouteRenderer->pfRouteVertices == NULL ||
            g_pRouteRenderer->nMaxRouteVertices < g_pRouteRenderer->nRoutePointCount * 2) {
            // Перевыделяем память
            if (g_pRouteRenderer->pfRouteVertices != NULL) {
                free(g_pRouteRenderer->pfRouteVertices);
            }
            g_pRouteRenderer->nMaxRouteVertices = g_pRouteRenderer->nRoutePointCount * 2;
            g_pRouteRenderer->pfRouteVertices = (float*)malloc(sizeof(float) * 
                                                               g_pRouteRenderer->nMaxRouteVertices);
            if (g_pRouteRenderer->pfRouteVertices == NULL) {
                return FALSE;
            }
        }
        
        // Конвертируем все точки маршрута
        for (int i = 0; i < g_pRouteRenderer->nRoutePointCount; i++) {
            float fLat = (float)g_pRouteRenderer->pdRoutePoints[i * 2];
            float fLon = (float)g_pRouteRenderer->pdRoutePoints[i * 2 + 1];
            
            float fScreenX, fScreenY;
            ConvertGeoToScreen(fLat, fLon, g_pRouteRenderer->fCameraLat, 
                             g_pRouteRenderer->fCameraLon, g_pRouteRenderer->fCameraZoom,
                             g_pRouteRenderer->nViewWidth, g_pRouteRenderer->nViewHeight,
                             &fScreenX, &fScreenY);
            
            g_pRouteRenderer->pfRouteVertices[i * 2] = fScreenX;
            g_pRouteRenderer->pfRouteVertices[i * 2 + 1] = fScreenY;
        }
        
        g_pRouteRenderer->nRouteVertexCount = g_pRouteRenderer->nRoutePointCount;
        g_pRouteRenderer->bNeedUpdate = FALSE;
        
        // Обновляем VBO с новыми вершинами
        glBindBuffer(GL_ARRAY_BUFFER, g_pRouteRenderer->nRouteVBO);
        glBufferData(GL_ARRAY_BUFFER, sizeof(float) * g_pRouteRenderer->nRouteVertexCount * 2,
                     g_pRouteRenderer->pfRouteVertices, GL_DYNAMIC_DRAW);
        glBindBuffer(GL_ARRAY_BUFFER, 0);
    }
    
    // Рендеринг полилинии маршрута
    if (bSimplified) {
        // Упрощенный режим (Display 1): только маршрут (полилиния)
        // - Только полилиния маршрута
        // - Без дополнительных элементов
    } else {
        // Полноценный режим (Display 0): маршрут с деталями
        // - Полилиния маршрута
        // - Направления движения (TODO)
        // - Временные метки (TODO)
    }
    
    // Активируем шейдерную программу для маршрута
    glUseProgram(g_pRouteRenderer->nRouteShaderProgram);
    
    // Устанавливаем матрицы проекции и вида (orthographic для 2D)
    // TODO: использовать те же матрицы, что и для карты
    float fAspect = (float)g_pRouteRenderer->nViewWidth / (float)g_pRouteRenderer->nViewHeight;
    float fOrthoWidth = 2.0f * fAspect;
    float fOrthoHeight = 2.0f;
    
    float fProjection[16] = {
        2.0f / fOrthoWidth, 0.0f, 0.0f, 0.0f,
        0.0f, 2.0f / fOrthoHeight, 0.0f, 0.0f,
        0.0f, 0.0f, -1.0f, 0.0f,
        0.0f, 0.0f, 0.0f, 1.0f
    };
    
    float fView[16] = {
        1.0f, 0.0f, 0.0f, 0.0f,
        0.0f, 1.0f, 0.0f, 0.0f,
        0.0f, 0.0f, 1.0f, 0.0f,
        0.0f, 0.0f, 0.0f, 1.0f
    };
    
    // Устанавливаем uniform переменные
    GLint nProjectionLoc = glGetUniformLocation(g_pRouteRenderer->nRouteShaderProgram, "projection");
    GLint nViewLoc = glGetUniformLocation(g_pRouteRenderer->nRouteShaderProgram, "view");
    GLint nColorLoc = glGetUniformLocation(g_pRouteRenderer->nRouteShaderProgram, "routeColor");
    
    if (nProjectionLoc >= 0) {
        glUniformMatrix4fv(nProjectionLoc, 1, GL_FALSE, fProjection);
    }
    if (nViewLoc >= 0) {
        glUniformMatrix4fv(nViewLoc, 1, GL_FALSE, fView);
    }
    if (nColorLoc >= 0) {
        glUniform4fv(nColorLoc, 1, g_pRouteRenderer->fRouteColor);
    }
    
    // Установка параметров рендеринга
    glLineWidth(g_pRouteRenderer->fRouteWidth);
    
    // Привязываем VAO и рендерим маршрут
    glBindVertexArray(g_pRouteRenderer->nRouteVAO);
    
    // Рендерим полилинию маршрута
    glDrawArrays(GL_LINE_STRIP, 0, g_pRouteRenderer->nRouteVertexCount);
    
    glBindVertexArray(0);
    
    Tiggo_CheckGLError("RenderRoute");
    
    return TRUE;
}

/**
 * Установка точек маршрута
 */
BOOL Tiggo_SetRoutePoints(CTiggoEngine* pEngine, const double* pdRoutePoints, int nPointCount) {
    if (pEngine == NULL || !pEngine->m_bInitialized || 
        pdRoutePoints == NULL || nPointCount <= 0) {
        return FALSE;
    }
    
    if (g_pRouteRenderer == NULL || !g_pRouteRenderer->bInitialized) {
        g_pRouteRenderer = CreateRouteRenderer();
        if (g_pRouteRenderer == NULL) {
            return FALSE;
        }
    }
    
    // Проверяем, что у нас достаточно памяти
    if (nPointCount > g_pRouteRenderer->nMaxRouteVertices) {
        // Перевыделяем память
        free(g_pRouteRenderer->pfRouteVertices);
        g_pRouteRenderer->nMaxRouteVertices = nPointCount * 2;
        g_pRouteRenderer->pfRouteVertices = (float*)malloc(sizeof(float) * 
                                                           g_pRouteRenderer->nMaxRouteVertices * 2);
        if (g_pRouteRenderer->pfRouteVertices == NULL) {
            return FALSE;
        }
    }
    
    // Сохраняем географические координаты
    if (g_pRouteRenderer->pdRoutePoints == NULL ||
        g_pRouteRenderer->nMaxRoutePoints < nPointCount) {
        // Перевыделяем память
        if (g_pRouteRenderer->pdRoutePoints != NULL) {
            free(g_pRouteRenderer->pdRoutePoints);
        }
        g_pRouteRenderer->nMaxRoutePoints = nPointCount;
        g_pRouteRenderer->pdRoutePoints = (double*)malloc(sizeof(double) * nPointCount * 2);
        if (g_pRouteRenderer->pdRoutePoints == NULL) {
            return FALSE;
        }
        memset(g_pRouteRenderer->pdRoutePoints, 0, sizeof(double) * nPointCount * 2);
    }
    
    // Копируем географические координаты
    for (int i = 0; i < nPointCount * 2; i++) {
        g_pRouteRenderer->pdRoutePoints[i] = pdRoutePoints[i];
    }
    
    g_pRouteRenderer->nRoutePointCount = nPointCount;
    g_pRouteRenderer->bHasRoute = TRUE;
    g_pRouteRenderer->bNeedUpdate = TRUE; // Нужно обновить экранные координаты
    
    // TODO: обновить VBO с новыми вершинами при следующем рендеринге
    
    return TRUE;
}

/**
 * Очистка маршрута
 */
void Tiggo_ClearRoute(CTiggoEngine* pEngine) {
    if (g_pRouteRenderer != NULL) {
        g_pRouteRenderer->nRoutePointCount = 0;
        g_pRouteRenderer->nRouteVertexCount = 0;
        g_pRouteRenderer->bHasRoute = FALSE;
        g_pRouteRenderer->bNeedUpdate = FALSE;
        
        // Очищаем VBO
        if (g_pRouteRenderer->nRouteVBO != 0) {
            glBindBuffer(GL_ARRAY_BUFFER, g_pRouteRenderer->nRouteVBO);
            glBufferData(GL_ARRAY_BUFFER, 0, NULL, GL_DYNAMIC_DRAW);
            glBindBuffer(GL_ARRAY_BUFFER, 0);
        }
        
        // Освобождаем память географических координат (опционально)
        // Можно оставить для быстрого восстановления маршрута
    }
}

