/**
 * map_renderer.c - Рендеринг тайлов карты (в стиле TurboDog)
 * 
 * Стиль TurboDog:
 * - Префиксы функций: Tiggo_RenderMap
 * - Венгерская нотация
 * - C код (не C++)
 * - OpenGL ES 3.0
 */

#include "map_renderer.h"
#include "route_renderer.h"
#include "shader_utils.h"
#include "../data/tile_loader.h"
#include "../core/tiggo_engine.h"
#include <GLES3/gl3.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <android/log.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define LOG_TAG "TiggoMapRenderer"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Внутренняя структура для рендеринга карты
typedef struct {
    // Шейдеры
    GLuint nMapShaderProgram;
    GLuint nMapVertexShader;
    GLuint nMapFragmentShader;
    
    // Шейдер для маркера позиции
    GLuint nMarkerShaderProgram;
    
    // Буферы
    GLuint nMapVBO;  // Vertex Buffer Object
    GLuint nMapVAO;  // Vertex Array Object
    GLuint nMapEBO;  // Element Buffer Object
    
    // Загрузчик тайлов
    TileLoader* pTileLoader;
    
    // Флаги
    BOOL bInitialized;
    BOOL bSimplified;  // TRUE для упрощенного режима (Display 1)
    
    // Размеры
    int nWidth;
    int nHeight;
    
    // Позиция камеры
    float fCameraLat;
    float fCameraLon;
    float fCameraZoom;
    float fCameraBearing;
    float fCameraTilt;
} MapRenderer;

// Глобальные переменные
static MapRenderer* g_pMainMapRenderer = NULL;
static MapRenderer* g_pSecondaryMapRenderers = NULL;
static int g_nSecondaryMapRendererCount = 0;
static int g_nMaxSecondaryRenderers = 4;

// Глобальная ссылка на TileLoader для доступа из JNI и tiggo_engine.c
// Убрали static, чтобы переменная была видна из других модулей
TileLoader* g_pGlobalTileLoader = NULL;

// Forward declaration
static void RenderLocationMarker(MapRenderer* pRenderer, float fLat, float fLon, float fBearing);

/**
 * Инициализация шейдеров
 */
static BOOL InitShaders(MapRenderer* pRenderer) {
    if (pRenderer == NULL) {
        return FALSE;
    }
    
    // Вершинный шейдер для тайлов карты
    const char* pVertexShaderSource = 
        "#version 300 es\n"
        "layout (location = 0) in vec2 aPos;\n"
        "layout (location = 1) in vec2 aTexCoord;\n"
        "out vec2 TexCoord;\n"
        "uniform mat4 projection;\n"
        "uniform mat4 view;\n"
        "uniform mat4 model;\n"
        "void main() {\n"
        "    gl_Position = projection * view * model * vec4(aPos, 0.0, 1.0);\n"
        "    TexCoord = aTexCoord;\n"
        "}\n";
    
    // Фрагментный шейдер для тайлов карты
    const char* pFragmentShaderSource = 
        "#version 300 es\n"
        "precision mediump float;\n"
        "in vec2 TexCoord;\n"
        "out vec4 FragColor;\n"
        "uniform sampler2D texture1;\n"
        "void main() {\n"
        "    FragColor = texture(texture1, TexCoord);\n"
        "}\n";
    
    // Создаем шейдерную программу
    pRenderer->nMapShaderProgram = Tiggo_CreateShaderProgram(pVertexShaderSource, pFragmentShaderSource);
    if (pRenderer->nMapShaderProgram == 0) {
        return FALSE;
    }
    
    Tiggo_CheckGLError("InitShaders");
    
    return TRUE;
}

/**
 * Создание рендерера карты
 * ВАЖНО: Шейдеры будут инициализированы позже, когда OpenGL контекст станет активным
 */
static MapRenderer* CreateMapRenderer(BOOL bSimplified, int nWidth, int nHeight) {
    MapRenderer* pRenderer = (MapRenderer*)malloc(sizeof(MapRenderer));
    if (pRenderer == NULL) {
        return NULL;
    }
    
    memset(pRenderer, 0, sizeof(MapRenderer));
    pRenderer->bSimplified = bSimplified;
    pRenderer->bInitialized = FALSE; // Помечаем как не инициализированный до создания OpenGL контекста
    pRenderer->nWidth = nWidth;
    pRenderer->nHeight = nHeight;
    
    // Создаем загрузчик тайлов
    int nMaxTiles = bSimplified ? 64 : 256; // Для упрощенного режима меньше тайлов
    pRenderer->pTileLoader = Tiggo_CreateTileLoader(bSimplified, nMaxTiles);
    if (pRenderer->pTileLoader == NULL) {
        free(pRenderer);
        return NULL;
    }
    
    // Сохраняем глобальную ссылку на TileLoader для доступа из JNI
    if (!bSimplified) {
        g_pGlobalTileLoader = pRenderer->pTileLoader;
    }
    
    // ВАЖНО: Инициализация шейдеров отложена до первого рендеринга
    // когда OpenGL контекст уже будет активен (создан в Java коде)
    // Не инициализируем шейдеры здесь, так как OpenGL контекст еще не создан
    
    // ВАЖНО: Буферы тоже отложены до первого рендеринга
    // Не создаем их здесь, так как OpenGL контекст еще не создан
    
    // Помечаем рендерер как созданный, но не инициализированный
    // Полная инициализация произойдет в первом вызове Tiggo_RenderMap()
    
    return pRenderer;
}

/**
 * Уничтожение рендерера карты
 */
static void DestroyMapRenderer(MapRenderer* pRenderer) {
    if (pRenderer == NULL) {
        return;
    }
    
    if (pRenderer->bInitialized) {
        // Уничтожаем загрузчик тайлов
        if (pRenderer->pTileLoader != NULL) {
            Tiggo_DestroyTileLoader(pRenderer->pTileLoader);
        }
        
        // Удаляем буферы
        if (pRenderer->nMapVBO != 0) {
            glDeleteBuffers(1, &pRenderer->nMapVBO);
        }
        if (pRenderer->nMapVAO != 0) {
            glDeleteVertexArrays(1, &pRenderer->nMapVAO);
        }
        if (pRenderer->nMapEBO != 0) {
            glDeleteBuffers(1, &pRenderer->nMapEBO);
        }
        
        // Удаляем шейдеры
        if (pRenderer->nMapShaderProgram != 0) {
            glDeleteProgram(pRenderer->nMapShaderProgram);
        }
        if (pRenderer->nMarkerShaderProgram != 0) {
            glDeleteProgram(pRenderer->nMarkerShaderProgram);
        }
    }
    
    free(pRenderer);
}

/**
 * Рендеринг карты
 * В стиле TurboDog: RenderMap()
 */
BOOL Tiggo_RenderMap(CTiggoEngine* pEngine, BOOL bSimplified) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return FALSE;
    }
    
    MapRenderer* pRenderer = NULL;
    
    if (bSimplified) {
        // Упрощенный режим (Display 1)
        // TODO: использовать вторичный рендерер
        // Пока используем основной
        pRenderer = g_pMainMapRenderer;
    } else {
        // Полноценный режим (Display 0)
        pRenderer = g_pMainMapRenderer;
    }
    
    if (pRenderer == NULL) {
        return FALSE;
    }
    
    // ВАЖНО: Отложенная инициализация шейдеров и буферов
    // Инициализируем их при первом рендеринге, когда OpenGL контекст уже активен
    if (!pRenderer->bInitialized) {
        // Инициализация шейдеров
        if (!InitShaders(pRenderer)) {
            return FALSE;
        }
        
        // Создаем VBO, VAO, EBO для рендеринга тайлов
        glGenVertexArrays(1, &pRenderer->nMapVAO);
        glGenBuffers(1, &pRenderer->nMapVBO);
        glGenBuffers(1, &pRenderer->nMapEBO);
        
        glBindVertexArray(pRenderer->nMapVAO);
        
        // Инициализируем VBO (пока пустой, заполним при рендеринге)
        glBindBuffer(GL_ARRAY_BUFFER, pRenderer->nMapVBO);
        glBufferData(GL_ARRAY_BUFFER, 0, NULL, GL_DYNAMIC_DRAW);
        
        // Настраиваем атрибуты вершин
        // Позиция (location = 0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(float), (void*)0);
        glEnableVertexAttribArray(0);
        
        // Текстурные координаты (location = 1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(float), (void*)(2 * sizeof(float)));
        glEnableVertexAttribArray(1);
        
        glBindVertexArray(0);
        
        Tiggo_CheckGLError("Tiggo_RenderMap - delayed initialization");
        
        // Помечаем рендерер как инициализированный
        pRenderer->bInitialized = TRUE;
    }
    
    // Обновляем тайлы при изменении камеры
    // Это автоматически создаст заглушки для недостающих тайлов
    // Java код загрузит тайлы через TileLoader и передаст их в нативный код
    if (pRenderer->pTileLoader != NULL) {
        Tiggo_UpdateTiles(pRenderer->pTileLoader, pRenderer->fCameraLat, pRenderer->fCameraLon,
                         pRenderer->fCameraZoom, pRenderer->nWidth, pRenderer->nHeight);
        
        // TODO: Запросить загрузку тайлов через Java TileLoader
        // Это будет реализовано автоматически при обновлении тайлов
        // Java код отслеживает видимые тайлы и загружает недостающие
    }
    
    // Рендеринг тайлов карты
    if (pRenderer->pTileLoader != NULL && pRenderer->pTileLoader->bInitialized) {
        // Активируем шейдерную программу для тайлов
        glUseProgram(pRenderer->nMapShaderProgram);
        
        // Устанавливаем матрицы проекции и вида (orthographic для 2D)
        // Используем простую ортографическую проекцию для нормализованных координат [-1, 1]
        // Идентичная матрица - координаты уже нормализованы
        float fProjection[16] = {
            1.0f, 0.0f, 0.0f, 0.0f,
            0.0f, 1.0f, 0.0f, 0.0f,
            0.0f, 0.0f, -1.0f, 0.0f,
            0.0f, 0.0f, 0.0f, 1.0f
        };
        
        float fView[16] = {
            1.0f, 0.0f, 0.0f, 0.0f,
            0.0f, 1.0f, 0.0f, 0.0f,
            0.0f, 0.0f, 1.0f, 0.0f,
            0.0f, 0.0f, 0.0f, 1.0f
        };
        
        float fModel[16] = {
            1.0f, 0.0f, 0.0f, 0.0f,
            0.0f, 1.0f, 0.0f, 0.0f,
            0.0f, 0.0f, 1.0f, 0.0f,
            0.0f, 0.0f, 0.0f, 1.0f
        };
        
        // Устанавливаем uniform переменные
        GLint nProjectionLoc = glGetUniformLocation(pRenderer->nMapShaderProgram, "projection");
        GLint nViewLoc = glGetUniformLocation(pRenderer->nMapShaderProgram, "view");
        GLint nModelLoc = glGetUniformLocation(pRenderer->nMapShaderProgram, "model");
        
        if (nProjectionLoc >= 0) {
            glUniformMatrix4fv(nProjectionLoc, 1, GL_FALSE, fProjection);
        }
        if (nViewLoc >= 0) {
            glUniformMatrix4fv(nViewLoc, 1, GL_FALSE, fView);
        }
        if (nModelLoc >= 0) {
            glUniformMatrix4fv(nModelLoc, 1, GL_FALSE, fModel);
        }
        
        // Включаем смешивание для прозрачности
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        
        // Привязываем VAO
        glBindVertexArray(pRenderer->nMapVAO);
        
        // Обрабатываем ожидающие тайлы - создаем текстуры из сохраненных данных
        // (это должно быть в потоке рендеринга, где активен OpenGL контекст)
        Tiggo_ProcessPendingTiles(pRenderer->pTileLoader);
        
        // Логирование для отладки (первые 10 кадров)
        static int nRenderCount = 0;
        nRenderCount++;
        if (nRenderCount <= 5) {
            LOGI("RenderMap: tileCount=%d, cameraLat=%.2f, cameraLon=%.2f, zoom=%.1f",
                 pRenderer->pTileLoader->nTileCount,
                 pRenderer->fCameraLat, pRenderer->fCameraLon, pRenderer->fCameraZoom);
        }
        
        // Рендерим все видимые тайлы
        int nRenderedTiles = 0;
        int nLoadedTiles = 0;
        int nVisibleTiles = 0;
        for (int i = 0; i < pRenderer->pTileLoader->nTileCount; i++) {
            MapTile* pTile = &pRenderer->pTileLoader->pTiles[i];
            
            if (pTile->bVisible) {
                nVisibleTiles++;
            }
            if (pTile->bLoaded) {
                nLoadedTiles++;
            }
            
            // Рендерим только загруженные тайлы (пропускаем незагруженные - они прозрачные)
            if (pTile->bVisible && pTile->bLoaded && pTile->nTexture != 0) {
                // Вычисляем экранные координаты тайла
                // Используем прямое вычисление на основе тайловых индексов и зума
                
                // Размер тайла в пикселях (256 пикселей на уровне зума, масштабируется с зумом)
                float fTileSizePixels = 256.0f;
                
                // Конвертируем координаты камеры в тайловые координаты
                int nCameraTileX, nCameraTileY;
                Tiggo_GeoToTile(pRenderer->fCameraLat, pRenderer->fCameraLon, (int)pRenderer->fCameraZoom, 
                               &nCameraTileX, &nCameraTileY);
                
                // Вычисляем дробную часть позиции камеры в тайле
                // Конвертируем географические координаты камеры в точные тайловые координаты
                double dN = pow(2.0, (int)pRenderer->fCameraZoom);
                double dLon = pRenderer->fCameraLon * M_PI / 180.0;
                double dLat = pRenderer->fCameraLat * M_PI / 180.0;
                double dTileX = (dLon + M_PI) / (2.0 * M_PI) * dN;
                double dTileY = (1.0 - log(tan(dLat) + 1.0 / cos(dLat)) / M_PI) / 2.0 * dN;
                
                // Дробная часть позиции камеры в тайле (0.0 - 1.0)
                float fCameraTileFractionX = (float)(dTileX - (double)nCameraTileX);
                float fCameraTileFractionY = (float)(dTileY - (double)nCameraTileY);
                
                // Разница в тайлах между тайлом и камерой
                int nDeltaTileX = pTile->nX - nCameraTileX;
                int nDeltaTileY = pTile->nY - nCameraTileY;
                
                // Позиция тайла на экране в пикселях (центр экрана = камера)
                // Тайл с координатами (nCameraTileX, nCameraTileY) должен быть в центре экрана
                // со смещением на дробную часть
                float fTileX = (float)pRenderer->nWidth / 2.0f - fCameraTileFractionX * fTileSizePixels + nDeltaTileX * fTileSizePixels;
                float fTileY = (float)pRenderer->nHeight / 2.0f - fCameraTileFractionY * fTileSizePixels + nDeltaTileY * fTileSizePixels;
                
                // Конвертируем экранные координаты в нормализованные координаты OpenGL
                // OpenGL координаты: [-1, 1] для X и Y
                // X: левый край = -1, правый край = 1
                // Y: нижний край = -1, верхний край = 1
                float fNormX = (fTileX / (float)pRenderer->nWidth) * 2.0f - 1.0f;
                float fNormY = -((fTileY / (float)pRenderer->nHeight) * 2.0f - 1.0f); // Инвертируем Y (OpenGL Y растет вверх)
                float fNormSizeX = (fTileSizePixels / (float)pRenderer->nWidth) * 2.0f;
                float fNormSizeY = (fTileSizePixels / (float)pRenderer->nHeight) * 2.0f;
                
                // Создаем вершины квада тайла [x, y, u, v] в нормализованных координатах
                // Порядок вершин: против часовой стрелки, начиная с нижнего левого
                // Текстурные координаты: (0,0) - верхний левый в OpenGL, но для правильной ориентации используем (0,1) как верхний левый
                float fVertices[] = {
                    // Позиция (normalized)    // Текстурные координаты (u, v)
                    fNormX, fNormY,             0.0f, 1.0f,  // Нижний левый (текстура: верхний левый)
                    fNormX + fNormSizeX, fNormY,             1.0f, 1.0f,  // Нижний правый (текстура: верхний правый)
                    fNormX + fNormSizeX, fNormY + fNormSizeY, 1.0f, 0.0f,  // Верхний правый (текстура: нижний правый)
                    fNormX, fNormY + fNormSizeY, 0.0f, 0.0f   // Верхний левый (текстура: нижний левый)
                };
                
                // Обновляем VBO с вершинами тайла
                glBindBuffer(GL_ARRAY_BUFFER, pRenderer->nMapVBO);
                glBufferData(GL_ARRAY_BUFFER, sizeof(fVertices), fVertices, GL_DYNAMIC_DRAW);
                
                // Привязываем текстуру тайла
                glActiveTexture(GL_TEXTURE0);
                glBindTexture(GL_TEXTURE_2D, pTile->nTexture);
                GLint nTextureLoc = glGetUniformLocation(pRenderer->nMapShaderProgram, "texture1");
                if (nTextureLoc >= 0) {
                    glUniform1i(nTextureLoc, 0);
                }
                
                // Индексы для рендеринга квада (2 треугольника)
                unsigned int nIndices[] = {
                    0, 1, 2,  // Первый треугольник
                    2, 3, 0   // Второй треугольник
                };
                
                // Обновляем EBO с индексами
                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, pRenderer->nMapEBO);
                glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(nIndices), nIndices, GL_DYNAMIC_DRAW);
                
                // Рендерим тайл
                glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, 0);
                nRenderedTiles++;
                
                // Логирование для первых тайлов (первые 5 кадров)
                if (nRenderCount <= 5 && nRenderedTiles <= 3) {
                    LOGI("Tile: x=%d,y=%d,z=%d, deltaX=%d,deltaY=%d, screenX=%.1f, screenY=%.1f, normX=%.3f, normY=%.3f, normSizeX=%.3f, normSizeY=%.3f",
                         pTile->nX, pTile->nY, pTile->nZoom,
                         nDeltaTileX, nDeltaTileY,
                         fTileX, fTileY,
                         fNormX, fNormY, fNormSizeX, fNormSizeY);
                }
            }
        }
        
        if (nRenderCount <= 10) {
            LOGI("RenderMap: total=%d, visible=%d, loaded=%d, rendered=%d", 
                 pRenderer->pTileLoader->nTileCount, nVisibleTiles, nLoadedTiles, nRenderedTiles);
        }
        
        glBindVertexArray(0);
        glDisable(GL_BLEND);
        
        Tiggo_CheckGLError("RenderMap");
    }
    
    if (bSimplified) {
        // Упрощенный режим: только основные элементы
        // - Базовый фон
        // - Только маршрут (полилиния)
        // - Камеры скорости
        // - Дорожные события
        // Без: POI, детальной карты, зданий
    } else {
        // Полноценный режим: все элементы
        // - Полная карта с тайлами (уже отрендерена выше)
        // - POI и события (TODO)
        // - Детализация карты
        // - Здания и 3D объекты (TODO)
    }
    
    // Рендеринг маршрута поверх карты
    if (pEngine->m_bNavigationActive) {
        Tiggo_RenderRoute(pEngine, bSimplified);
    }
    
    // Рендеринг маркера текущей позиции (синий круг с белой обводкой, как в Яндекс Навигаторе)
    if (pRenderer != NULL && pEngine->m_fCurrentLat != 0.0f && pEngine->m_fCurrentLon != 0.0f) {
        RenderLocationMarker(pRenderer, pEngine->m_fCurrentLat, pEngine->m_fCurrentLon, 
                            pEngine->m_fCurrentBearing);
    }
    
    return TRUE;
}

/**
 * Инициализация шейдера для маркера позиции
 */
static BOOL InitMarkerShader(MapRenderer* pRenderer) {
    if (pRenderer->nMarkerShaderProgram != 0) {
        return TRUE; // Уже инициализирован
    }
    
    // Простой вершинный шейдер для маркера
    const char* pVertexShaderSource = 
        "#version 300 es\n"
        "in vec2 aPosition;\n"
        "uniform vec2 uCenter;\n"
        "uniform float uSize;\n"
        "void main() {\n"
        "    vec2 pos = aPosition * uSize + uCenter;\n"
        "    gl_Position = vec4(pos, 0.0, 1.0);\n"
        "}\n";
    
    // Простой фрагментный шейдер для маркера (цветной)
    const char* pFragmentShaderSource = 
        "#version 300 es\n"
        "precision mediump float;\n"
        "uniform vec4 uColor;\n"
        "out vec4 fragColor;\n"
        "void main() {\n"
        "    fragColor = uColor;\n"
        "}\n";
    
    pRenderer->nMarkerShaderProgram = Tiggo_CreateShaderProgram(pVertexShaderSource, pFragmentShaderSource);
    if (pRenderer->nMarkerShaderProgram == 0) {
        LOGE("Failed to create marker shader program");
        return FALSE;
    }
    
    return TRUE;
}

/**
 * Рендеринг маркера текущей позиции (синий круг с белой обводкой, как в Яндекс Навигаторе)
 */
static void RenderLocationMarker(MapRenderer* pRenderer, float fLat, float fLon, float fBearing) {
    if (pRenderer == NULL || !pRenderer->bInitialized) {
        return;
    }
    
    // Инициализируем шейдер маркера, если еще не инициализирован
    if (pRenderer->nMarkerShaderProgram == 0) {
        if (!InitMarkerShader(pRenderer)) {
            return; // Не удалось создать шейдер
        }
    }
    
    // Конвертируем географические координаты в экранные координаты
    int nCameraTileX, nCameraTileY;
    Tiggo_GeoToTile(pRenderer->fCameraLat, pRenderer->fCameraLon, (int)pRenderer->fCameraZoom, 
                   &nCameraTileX, &nCameraTileY);
    
    // Вычисляем дробную часть позиции камеры в тайле
    double dN = pow(2.0, (int)pRenderer->fCameraZoom);
    double dLon = pRenderer->fCameraLon * M_PI / 180.0;
    double dLat = pRenderer->fCameraLat * M_PI / 180.0;
    double dCameraTileX = (dLon + M_PI) / (2.0 * M_PI) * dN;
    double dCameraTileY = (1.0 - log(tan(dLat) + 1.0 / cos(dLat)) / M_PI) / 2.0 * dN;
    float fCameraTileFractionX = (float)(dCameraTileX - (double)nCameraTileX);
    float fCameraTileFractionY = (float)(dCameraTileY - (double)nCameraTileY);
    
    // Вычисляем позицию маркера в тайловых координатах
    double dMarkerLon = fLon * M_PI / 180.0;
    double dMarkerLat = fLat * M_PI / 180.0;
    double dMarkerTileX = (dMarkerLon + M_PI) / (2.0 * M_PI) * dN;
    double dMarkerTileY = (1.0 - log(tan(dMarkerLat) + 1.0 / cos(dMarkerLat)) / M_PI) / 2.0 * dN;
    
    // Разница в тайлах между маркером и камерой
    float fDeltaTileX = (float)(dMarkerTileX - dCameraTileX);
    float fDeltaTileY = (float)(dMarkerTileY - dCameraTileY);
    
    // Размер тайла в пикселях
    float fTileSizePixels = 256.0f;
    
    // Позиция маркера на экране в пикселях (используем ту же логику, что и для тайлов)
    float fMarkerX = (float)pRenderer->nWidth / 2.0f - fCameraTileFractionX * fTileSizePixels + fDeltaTileX * fTileSizePixels;
    float fMarkerY = (float)pRenderer->nHeight / 2.0f - fCameraTileFractionY * fTileSizePixels + fDeltaTileY * fTileSizePixels;
    
    // Конвертируем в нормализованные координаты OpenGL (та же логика, что и для тайлов)
    float fNormX = (fMarkerX / (float)pRenderer->nWidth) * 2.0f - 1.0f;
    float fNormY = -((fMarkerY / (float)pRenderer->nHeight) * 2.0f - 1.0f);
    
    // Логирование для отладки (только первые несколько раз)
    static int nMarkerLogCount = 0;
    if (nMarkerLogCount < 3) {
        LOGI("Marker: GPS lat=%.6f,lon=%.6f, Camera lat=%.6f,lon=%.6f, Screen x=%.1f,y=%.1f, Norm x=%.3f,y=%.3f",
             fLat, fLon, pRenderer->fCameraLat, pRenderer->fCameraLon, fMarkerX, fMarkerY, fNormX, fNormY);
        nMarkerLogCount++;
    }
    
    // Размер маркера в нормализованных координатах (примерно 12 пикселей - уменьшили)
    // Формула: размер в пикселях / высота экрана * 2 (для нормализации в [-1, 1])
    float fMarkerSize = 12.0f / (float)pRenderer->nHeight * 2.0f;
    float fOuterSize = 14.0f / (float)pRenderer->nHeight * 2.0f; // Белая обводка (тонкая)
    
    // Включаем смешивание
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    
    // Используем шейдер маркера
    glUseProgram(pRenderer->nMarkerShaderProgram);
    
    // Создаем круг из треугольников через TRIANGLE_FAN
    // TRIANGLE_FAN требует: первая точка - центр, остальные - точки на окружности
    const int nSegments = 16; // Уменьшили количество сегментов для производительности
    float fVertices[(nSegments + 2) * 2]; // +2: центр + замыкание
    
    // Центр круга (в локальных координатах, будет умножен на uSize в шейдере)
    fVertices[0] = 0.0f;
    fVertices[1] = 0.0f;
    
    // Вершины на окружности (единичный круг)
    for (int i = 0; i <= nSegments; i++) {
        float fAngle = (float)i / (float)nSegments * 2.0f * (float)M_PI;
        fVertices[(i + 1) * 2] = cosf(fAngle);
        fVertices[(i + 1) * 2 + 1] = sinf(fAngle);
    }
    
    // Устанавливаем uniform переменные
    GLint nCenterLoc = glGetUniformLocation(pRenderer->nMarkerShaderProgram, "uCenter");
    GLint nSizeLoc = glGetUniformLocation(pRenderer->nMarkerShaderProgram, "uSize");
    GLint nColorLoc = glGetUniformLocation(pRenderer->nMarkerShaderProgram, "uColor");
    
    if (nCenterLoc >= 0) {
        glUniform2f(nCenterLoc, fNormX, fNormY);
    }
    
    // Рисуем белый внешний круг (обводка)
    if (nSizeLoc >= 0) {
        glUniform1f(nSizeLoc, fOuterSize);
    }
    if (nColorLoc >= 0) {
        glUniform4f(nColorLoc, 1.0f, 1.0f, 1.0f, 1.0f); // Белый
    }
    
    // Создаем VBO для круга
    GLuint nMarkerVBO;
    glGenBuffers(1, &nMarkerVBO);
    glBindBuffer(GL_ARRAY_BUFFER, nMarkerVBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(fVertices), fVertices, GL_STATIC_DRAW);
    
    // Настраиваем атрибуты
    GLint nPositionLoc = glGetAttribLocation(pRenderer->nMarkerShaderProgram, "aPosition");
    if (nPositionLoc >= 0) {
        glEnableVertexAttribArray(nPositionLoc);
        glVertexAttribPointer(nPositionLoc, 2, GL_FLOAT, GL_FALSE, 0, 0);
    }
    
    // Рисуем желтую стрелку вверх (как в Яндекс Навигаторе)
    // Внешний белый круг (обводка)
    glDrawArrays(GL_TRIANGLE_FAN, 0, nSegments + 2);
    
    // Внутренний желтый круг
    if (nSizeLoc >= 0) {
        glUniform1f(nSizeLoc, fMarkerSize);
    }
    if (nColorLoc >= 0) {
        glUniform4f(nColorLoc, 1.0f, 0.84f, 0.0f, 1.0f); // Желтый цвет (#FFD700)
    }
    glDrawArrays(GL_TRIANGLE_FAN, 0, nSegments + 2);
    
    // Рисуем стрелку вверх поверх желтого круга
    // Создаем треугольник стрелки
    float fArrowVertices[3 * 2]; // 3 вершины для треугольника
    float fArrowSize = fMarkerSize * 0.6f; // Размер стрелки
    
    // Вершины треугольника стрелки вверх (в локальных координатах единичного круга)
    fArrowVertices[0] = 0.0f; // Верхняя точка
    fArrowVertices[1] = 0.6f;
    fArrowVertices[2] = -0.36f; // Левая нижняя
    fArrowVertices[3] = -0.18f;
    fArrowVertices[4] = 0.36f; // Правая нижняя
    fArrowVertices[5] = -0.18f;
    
    // Создаем VBO для стрелки
    GLuint nArrowVBO;
    glGenBuffers(1, &nArrowVBO);
    glBindBuffer(GL_ARRAY_BUFFER, nArrowVBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(fArrowVertices), fArrowVertices, GL_STATIC_DRAW);
    
    // Устанавливаем размер стрелки (используем тот же размер, что и для круга)
    if (nSizeLoc >= 0) {
        glUniform1f(nSizeLoc, fMarkerSize);
    }
    if (nColorLoc >= 0) {
        glUniform4f(nColorLoc, 1.0f, 1.0f, 1.0f, 1.0f); // Белая стрелка
    }
    
    // Рисуем стрелку
    if (nPositionLoc >= 0) {
        glVertexAttribPointer(nPositionLoc, 2, GL_FLOAT, GL_FALSE, 0, 0);
    }
    glDrawArrays(GL_TRIANGLES, 0, 3);
    
    // Очистка стрелки
    glBindBuffer(GL_ARRAY_BUFFER, 0);
    glDeleteBuffers(1, &nArrowVBO);
    
    // Очистка
    if (nPositionLoc >= 0) {
        glDisableVertexAttribArray(nPositionLoc);
    }
    glBindBuffer(GL_ARRAY_BUFFER, 0);
    glDeleteBuffers(1, &nMarkerVBO);
    
    // Восстанавливаем состояние
    glDisable(GL_BLEND);
    glUseProgram(0);
}

/**
 * Инициализация рендерера карты
 */
BOOL Tiggo_InitMapRenderer(CTiggoEngine* pEngine, BOOL bSimplified, int nWidth, int nHeight) {
    if (pEngine == NULL || !pEngine->m_bInitialized) {
        return FALSE;
    }
    
    if (bSimplified) {
        // Инициализация вторичного рендерера (Display 1)
        // Для упрощенного режима используем основной рендерер, но в упрощенном режиме
        if (g_pMainMapRenderer == NULL) {
            g_pMainMapRenderer = CreateMapRenderer(TRUE, nWidth, nHeight); // TRUE = упрощенный
            if (g_pMainMapRenderer == NULL) {
                return FALSE;
            }
            
            // Устанавливаем начальные координаты камеры (Санкт-Петербург)
            g_pMainMapRenderer->fCameraLat = 59.804538f;  // Широта Санкт-Петербурга
            g_pMainMapRenderer->fCameraLon = 30.162479f;  // Долгота Санкт-Петербурга
            g_pMainMapRenderer->fCameraZoom = 13.0f;    // Уровень zoom
            g_pMainMapRenderer->fCameraBearing = 0.0f;
            g_pMainMapRenderer->fCameraTilt = 0.0f;
        } else {
            // Обновляем размеры существующего рендерера
            g_pMainMapRenderer->nWidth = nWidth;
            g_pMainMapRenderer->nHeight = nHeight;
        }
    } else {
        // Инициализация основного рендерера (Display 0)
        if (g_pMainMapRenderer != NULL) {
            DestroyMapRenderer(g_pMainMapRenderer);
        }
        
        g_pMainMapRenderer = CreateMapRenderer(FALSE, nWidth, nHeight);
        if (g_pMainMapRenderer == NULL) {
            return FALSE;
        }
        
        // Устанавливаем начальные координаты камеры (Санкт-Петербург)
        // Это нужно для отображения карты при запуске
        g_pMainMapRenderer->fCameraLat = 59.804538f;  // Широта Санкт-Петербурга
        g_pMainMapRenderer->fCameraLon = 30.162479f;  // Долгота Санкт-Петербурга
        g_pMainMapRenderer->fCameraZoom = 13.0f;    // Уровень zoom (13 = город)
        g_pMainMapRenderer->fCameraBearing = 0.0f;  // Направление (север)
        g_pMainMapRenderer->fCameraTilt = 0.0f;     // Наклон (2D)
    }
    
    return TRUE;
}

/**
 * Обновление камеры
 */
void Tiggo_UpdateCamera(CTiggoEngine* pEngine, float fLat, float fLon, 
                       float fZoom, float fBearing, float fTilt) {
    if (pEngine == NULL || g_pMainMapRenderer == NULL) {
        return;
    }
    
    g_pMainMapRenderer->fCameraLat = fLat;
    g_pMainMapRenderer->fCameraLon = fLon;
    g_pMainMapRenderer->fCameraZoom = fZoom;
    g_pMainMapRenderer->fCameraBearing = fBearing;
    g_pMainMapRenderer->fCameraTilt = fTilt;
    
    // Обновляем тайлы при изменении камеры
    if (g_pMainMapRenderer->pTileLoader != NULL) {
        Tiggo_UpdateTiles(g_pMainMapRenderer->pTileLoader, fLat, fLon, fZoom,
                         g_pMainMapRenderer->nWidth, g_pMainMapRenderer->nHeight);
    }
    
    // TODO: обновление матриц проекции и вида
}

/**
 * Обновление размера окна
 */
void Tiggo_UpdateMapSize(CTiggoEngine* pEngine, BOOL bSimplified, int nWidth, int nHeight) {
    if (pEngine == NULL) {
        return;
    }
    
    MapRenderer* pRenderer = bSimplified ? NULL : g_pMainMapRenderer;
    if (pRenderer == NULL) {
        return;
    }
    
    pRenderer->nWidth = nWidth;
    pRenderer->nHeight = nHeight;
    
    // TODO: обновление viewport и проекции
}

