/**
 * ui_renderer.c - Реализация рендеринга UI элементов (в стиле TurboDog)
 * 
 * Стиль TurboDog:
 * - Префиксы функций: Tiggo_
 * - Венгерская нотация (m_, n_, f_, p_, b_)
 * - C код (не C++)
 * - OpenGL ES 3.0 для рендеринга
 * 
 * Для векторной графики используем прямой OpenGL ES рендеринг
 * (альтернатива NanoVG, более легковесный подход)
 */

#include "ui_renderer.h"
#include "../core/tiggo_engine.h"
#include "shader_utils.h"
#include "font_renderer.h"
#include <GLES3/gl3.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdio.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// Внутренняя структура для UI рендерера
typedef struct {
    // Шейдеры для UI
    GLuint nUITextShaderProgram;      // Шейдер для текста
    GLuint nUIQuadShaderProgram;      // Шейдер для квадов (иконки, фоны)
    GLuint nUILineShaderProgram;      // Шейдер для линий (стрелки)
    
    // VBO/VAO для UI элементов
    GLuint nUITextVAO;                // VAO для текста
    GLuint nUITextVBO;                // VBO для текста
    GLuint nUIQuadVAO;                // VAO для квадов
    GLuint nUIQuadVBO;                // VBO для квадов
    GLuint nUILineVAO;                // VAO для линий
    GLuint nUILineVBO;                // VBO для линий
    
    // Размеры окна
    int nWidth;
    int nHeight;
    
    // Флаги
    BOOL bInitialized;
} UIRenderer;

// Глобальная переменная для UI рендерера
static UIRenderer* g_pUIRenderer = NULL;

// ========== Шейдеры для UI ==========

/**
 * Вершинный шейдер для текста
 */
static const char* g_pUITextVertexShader = 
    "#version 300 es\n"
    "layout (location = 0) in vec2 aPos;\n"
    "layout (location = 1) in vec2 aTexCoord;\n"
    "out vec2 TexCoord;\n"
    "uniform mat4 projection;\n"
    "void main() {\n"
    "    gl_Position = projection * vec4(aPos.x, aPos.y, 0.0, 1.0);\n"
    "    TexCoord = aTexCoord;\n"
    "}\n";

/**
 * Фрагментный шейдер для текста (упрощенный, без текстуры шрифта)
 */
static const char* g_pUITextFragmentShader = 
    "#version 300 es\n"
    "precision mediump float;\n"
    "in vec2 TexCoord;\n"
    "out vec4 FragColor;\n"
    "uniform vec4 textColor;\n"
    "uniform float textAlpha;\n"
    "void main() {\n"
    "    // Упрощенный рендеринг текста (без текстуры шрифта)\n"
    "    // TODO: Добавить текстуру шрифта для реального рендеринга текста\n"
    "    FragColor = vec4(textColor.rgb, textColor.a * textAlpha);\n"
    "}\n";

/**
 * Вершинный шейдер для квадов (иконки, фоны)
 */
static const char* g_pUIQuadVertexShader = 
    "#version 300 es\n"
    "layout (location = 0) in vec2 aPos;\n"
    "out vec2 FragPos;\n"
    "uniform mat4 projection;\n"
    "void main() {\n"
    "    FragPos = aPos;\n"
    "    gl_Position = projection * vec4(aPos.x, aPos.y, 0.0, 1.0);\n"
    "}\n";

/**
 * Фрагментный шейдер для квадов
 */
static const char* g_pUIQuadFragmentShader = 
    "#version 300 es\n"
    "precision mediump float;\n"
    "in vec2 FragPos;\n"
    "out vec4 FragColor;\n"
    "uniform vec4 quadColor;\n"
    "uniform vec2 quadSize;\n"
    "uniform vec2 quadPos;\n"
    "uniform float borderRadius;\n"
    "void main() {\n"
    "    vec2 pos = FragPos - quadPos;\n"
    "    vec2 halfSize = quadSize * 0.5;\n"
    "    vec2 centerPos = abs(pos - halfSize);\n"
    "    \n"
    "    // Простой рендеринг квада с возможностью скругления углов\n"
    "    if (borderRadius > 0.0) {\n"
    "        vec2 corner = halfSize - vec2(borderRadius);\n"
    "        if (centerPos.x > corner.x && centerPos.y > corner.y) {\n"
    "            float dist = length(centerPos - corner);\n"
    "            if (dist > borderRadius) {\n"
    "                discard;\n"
    "            }\n"
    "        }\n"
    "    }\n"
    "    \n"
    "    FragColor = quadColor;\n"
    "}\n";

/**
 * Вершинный шейдер для линий (стрелки маневров)
 */
static const char* g_pUILineVertexShader = 
    "#version 300 es\n"
    "layout (location = 0) in vec2 aPos;\n"
    "uniform mat4 projection;\n"
    "void main() {\n"
    "    gl_Position = projection * vec4(aPos.x, aPos.y, 0.0, 1.0);\n"
    "}\n";

/**
 * Фрагментный шейдер для линий
 */
static const char* g_pUILineFragmentShader = 
    "#version 300 es\n"
    "precision mediump float;\n"
    "out vec4 FragColor;\n"
    "uniform vec4 lineColor;\n"
    "void main() {\n"
    "    FragColor = lineColor;\n"
    "}\n";

/**
 * Инициализация шейдеров UI
 */
static BOOL InitUIShaders(UIRenderer* pRenderer) {
    if (pRenderer == NULL) {
        return FALSE;
    }
    
    // Создаем шейдер для текста
    pRenderer->nUITextShaderProgram = Tiggo_CreateShaderProgram(
        g_pUITextVertexShader, g_pUITextFragmentShader);
    if (pRenderer->nUITextShaderProgram == 0) {
        return FALSE;
    }
    
    // Создаем шейдер для квадов
    pRenderer->nUIQuadShaderProgram = Tiggo_CreateShaderProgram(
        g_pUIQuadVertexShader, g_pUIQuadFragmentShader);
    if (pRenderer->nUIQuadShaderProgram == 0) {
        return FALSE;
    }
    
    // Создаем шейдер для линий
    pRenderer->nUILineShaderProgram = Tiggo_CreateShaderProgram(
        g_pUILineVertexShader, g_pUILineFragmentShader);
    if (pRenderer->nUILineShaderProgram == 0) {
        return FALSE;
    }
    
    Tiggo_CheckGLError("InitUIShaders");
    
    return TRUE;
}

/**
 * Инициализация VBO/VAO для UI
 */
static BOOL InitUIBuffers(UIRenderer* pRenderer) {
    if (pRenderer == NULL) {
        return FALSE;
    }
    
    // VAO/VBO для текста
    glGenVertexArrays(1, &pRenderer->nUITextVAO);
    glGenBuffers(1, &pRenderer->nUITextVBO);
    
    glBindVertexArray(pRenderer->nUITextVAO);
    glBindBuffer(GL_ARRAY_BUFFER, pRenderer->nUITextVBO);
    glBufferData(GL_ARRAY_BUFFER, 0, NULL, GL_DYNAMIC_DRAW);
    
    // Настройка атрибутов (позиция + текстурные координаты)
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(float), (void*)(2 * sizeof(float)));
    glEnableVertexAttribArray(1);
    
    // VAO/VBO для квадов
    glGenVertexArrays(1, &pRenderer->nUIQuadVAO);
    glGenBuffers(1, &pRenderer->nUIQuadVBO);
    
    glBindVertexArray(pRenderer->nUIQuadVAO);
    glBindBuffer(GL_ARRAY_BUFFER, pRenderer->nUIQuadVBO);
    glBufferData(GL_ARRAY_BUFFER, 0, NULL, GL_DYNAMIC_DRAW);
    
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);
    
    // VAO/VBO для линий
    glGenVertexArrays(1, &pRenderer->nUILineVAO);
    glGenBuffers(1, &pRenderer->nUILineVBO);
    
    glBindVertexArray(pRenderer->nUILineVAO);
    glBindBuffer(GL_ARRAY_BUFFER, pRenderer->nUILineVBO);
    glBufferData(GL_ARRAY_BUFFER, 0, NULL, GL_DYNAMIC_DRAW);
    
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);
    
    glBindVertexArray(0);
    
    Tiggo_CheckGLError("InitUIBuffers");
    
    return TRUE;
}

/**
 * Создание матрицы ортографической проекции для UI
 */
static void CreateOrthoMatrix(float* pMatrix, float fLeft, float fRight, 
                              float fBottom, float fTop, float fNear, float fFar) {
    if (pMatrix == NULL) {
        return;
    }
    
    memset(pMatrix, 0, sizeof(float) * 16);
    
    pMatrix[0] = 2.0f / (fRight - fLeft);
    pMatrix[5] = 2.0f / (fTop - fBottom);
    pMatrix[10] = -2.0f / (fFar - fNear);
    pMatrix[12] = -(fRight + fLeft) / (fRight - fLeft);
    pMatrix[13] = -(fTop + fBottom) / (fTop - fBottom);
    pMatrix[14] = -(fFar + fNear) / (fFar - fNear);
    pMatrix[15] = 1.0f;
}

// ========== Публичные функции ==========

/**
 * Инициализация UI рендерера
 */
BOOL Tiggo_InitUIRenderer(CTiggoEngine* pEngine, int nWidth, int nHeight) {
    if (pEngine == NULL || nWidth <= 0 || nHeight <= 0) {
        return FALSE;
    }
    
    // Если уже инициализирован, переинициализируем
    if (g_pUIRenderer != NULL) {
        Tiggo_DestroyUIRenderer(pEngine);
    }
    
    // Выделяем память
    g_pUIRenderer = (UIRenderer*)malloc(sizeof(UIRenderer));
    if (g_pUIRenderer == NULL) {
        return FALSE;
    }
    
    memset(g_pUIRenderer, 0, sizeof(UIRenderer));
    g_pUIRenderer->nWidth = nWidth;
    g_pUIRenderer->nHeight = nHeight;
    
    // Инициализация шейдеров
    if (!InitUIShaders(g_pUIRenderer)) {
        free(g_pUIRenderer);
        g_pUIRenderer = NULL;
        return FALSE;
    }
    
    // Инициализация буферов
    if (!InitUIBuffers(g_pUIRenderer)) {
        free(g_pUIRenderer);
        g_pUIRenderer = NULL;
        return FALSE;
    }
    
    // Инициализация рендерера шрифтов
    if (!Tiggo_InitFontRenderer()) {
        // Шрифт не критичен, продолжаем
    }
    
    g_pUIRenderer->bInitialized = TRUE;
    
    return TRUE;
}

/**
 * Уничтожение UI рендерера
 */
void Tiggo_DestroyUIRenderer(CTiggoEngine* pEngine) {
    if (g_pUIRenderer == NULL) {
        return;
    }
    
    // Уничтожаем рендерер шрифтов
    Tiggo_DestroyFontRenderer();
    
    // Удаляем шейдеры
    if (g_pUIRenderer->nUITextShaderProgram != 0) {
        glDeleteProgram(g_pUIRenderer->nUITextShaderProgram);
    }
    if (g_pUIRenderer->nUIQuadShaderProgram != 0) {
        glDeleteProgram(g_pUIRenderer->nUIQuadShaderProgram);
    }
    if (g_pUIRenderer->nUILineShaderProgram != 0) {
        glDeleteProgram(g_pUIRenderer->nUILineShaderProgram);
    }
    
    // Удаляем буферы
    if (g_pUIRenderer->nUITextVAO != 0) {
        glDeleteVertexArrays(1, &g_pUIRenderer->nUITextVAO);
    }
    if (g_pUIRenderer->nUITextVBO != 0) {
        glDeleteBuffers(1, &g_pUIRenderer->nUITextVBO);
    }
    if (g_pUIRenderer->nUIQuadVAO != 0) {
        glDeleteVertexArrays(1, &g_pUIRenderer->nUIQuadVAO);
    }
    if (g_pUIRenderer->nUIQuadVBO != 0) {
        glDeleteBuffers(1, &g_pUIRenderer->nUIQuadVBO);
    }
    if (g_pUIRenderer->nUILineVAO != 0) {
        glDeleteVertexArrays(1, &g_pUIRenderer->nUILineVAO);
    }
    if (g_pUIRenderer->nUILineVBO != 0) {
        glDeleteBuffers(1, &g_pUIRenderer->nUILineVBO);
    }
    
    free(g_pUIRenderer);
    g_pUIRenderer = NULL;
}

/**
 * Обновление размера UI рендерера
 */
void Tiggo_UpdateUISize(CTiggoEngine* pEngine, int nWidth, int nHeight) {
    if (g_pUIRenderer != NULL) {
        g_pUIRenderer->nWidth = nWidth;
        g_pUIRenderer->nHeight = nHeight;
    }
    
    // Обновляем размеры окна для шрифта
    Tiggo_FontSetWindowSize(nWidth, nHeight);
}

// ========== Функции рендеринга отдельных элементов ==========

/**
 * Рендеринг квада (для фонов иконок)
 */
static void RenderQuad(int nX, int nY, int nWidth, int nHeight, 
                       float fR, float fG, float fB, float fA,
                       float fBorderRadius) {
    if (g_pUIRenderer == NULL || !g_pUIRenderer->bInitialized) {
        return;
    }
    
    // Конвертируем координаты в нормализованные (-1 до 1)
    float fNormX = ((float)nX / (float)g_pUIRenderer->nWidth) * 2.0f - 1.0f;
    float fNormY = 1.0f - ((float)nY / (float)g_pUIRenderer->nHeight) * 2.0f;
    float fNormWidth = ((float)nWidth / (float)g_pUIRenderer->nWidth) * 2.0f;
    float fNormHeight = ((float)nHeight / (float)g_pUIRenderer->nHeight) * 2.0f;
    
    // Вершины квада
    float fVertices[] = {
        fNormX, fNormY,                    // Нижний левый
        fNormX + fNormWidth, fNormY,       // Нижний правый
        fNormX + fNormWidth, fNormY + fNormHeight,  // Верхний правый
        fNormX, fNormY,                    // Нижний левый
        fNormX + fNormWidth, fNormY + fNormHeight,  // Верхний правый
        fNormX, fNormY + fNormHeight       // Верхний левый
    };
    
    glUseProgram(g_pUIRenderer->nUIQuadShaderProgram);
    
    // Устанавливаем матрицу проекции
    float fProjection[16];
    CreateOrthoMatrix(fProjection, -1.0f, 1.0f, -1.0f, 1.0f, -1.0f, 1.0f);
    
    GLint nProjectionLoc = glGetUniformLocation(g_pUIRenderer->nUIQuadShaderProgram, "projection");
    if (nProjectionLoc >= 0) {
        glUniformMatrix4fv(nProjectionLoc, 1, GL_FALSE, fProjection);
    }
    
    GLint nColorLoc = glGetUniformLocation(g_pUIRenderer->nUIQuadShaderProgram, "quadColor");
    if (nColorLoc >= 0) {
        glUniform4f(nColorLoc, fR, fG, fB, fA);
    }
    
    GLint nSizeLoc = glGetUniformLocation(g_pUIRenderer->nUIQuadShaderProgram, "quadSize");
    if (nSizeLoc >= 0) {
        glUniform2f(nSizeLoc, fNormWidth, fNormHeight);
    }
    
    GLint nPosLoc = glGetUniformLocation(g_pUIRenderer->nUIQuadShaderProgram, "quadPos");
    if (nPosLoc >= 0) {
        glUniform2f(nPosLoc, fNormX, fNormY);
    }
    
    GLint nRadiusLoc = glGetUniformLocation(g_pUIRenderer->nUIQuadShaderProgram, "borderRadius");
    if (nRadiusLoc >= 0) {
        float fNormRadius = fBorderRadius / (float)g_pUIRenderer->nHeight * 2.0f;
        glUniform1f(nRadiusLoc, fNormRadius);
    }
    
    // Включаем смешивание для прозрачности
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    
    glBindVertexArray(g_pUIRenderer->nUIQuadVAO);
    glBindBuffer(GL_ARRAY_BUFFER, g_pUIRenderer->nUIQuadVBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(fVertices), fVertices, GL_DYNAMIC_DRAW);
    
    glDrawArrays(GL_TRIANGLES, 0, 6);
    
    glBindVertexArray(0);
    glDisable(GL_BLEND);
}

/**
 * Рендеринг скорости
 */
void Tiggo_RenderSpeed(CTiggoEngine* pEngine, int nSpeed, int nX, int nY) {
    if (g_pUIRenderer == NULL || !g_pUIRenderer->bInitialized || pEngine == NULL) {
        return;
    }
    
    // Рендерим фон для скорости (округленный прямоугольник)
    int nBgWidth = 120;
    int nBgHeight = 60;
    RenderQuad(nX, nY, nBgWidth, nBgHeight, 0.0f, 0.0f, 0.0f, 0.7f, 8.0f);
    
    // Рендерим текст скорости (белый цвет, большой размер)
    int nTextX = nX + 20;
    int nTextY = nY + 15;
    int nTextSize = 36;
    Tiggo_RenderNumber(nSpeed, nTextX, nTextY, nTextSize, 1.0f, 1.0f, 1.0f, 1.0f);
}

/**
 * Рендеринг указателя маневра
 */
void Tiggo_RenderManeuverArrow(CTiggoEngine* pEngine, int nType, int nDistance,
                               int nCenterX, int nCenterY) {
    if (g_pUIRenderer == NULL || !g_pUIRenderer->bInitialized || pEngine == NULL) {
        return;
    }
    
    if (nType == 0) {
        return; // Нет маневра
    }
    
    glUseProgram(g_pUIRenderer->nUILineShaderProgram);
    
    // Устанавливаем матрицу проекции
    float fProjection[16];
    CreateOrthoMatrix(fProjection, -1.0f, 1.0f, -1.0f, 1.0f, -1.0f, 1.0f);
    
    GLint nProjectionLoc = glGetUniformLocation(g_pUIRenderer->nUILineShaderProgram, "projection");
    if (nProjectionLoc >= 0) {
        glUniformMatrix4fv(nProjectionLoc, 1, GL_FALSE, fProjection);
    }
    
    GLint nColorLoc = glGetUniformLocation(g_pUIRenderer->nUILineShaderProgram, "lineColor");
    if (nColorLoc >= 0) {
        glUniform4f(nColorLoc, 1.0f, 1.0f, 1.0f, 1.0f); // Белый цвет
    }
    
    // Конвертируем координаты
    float fCenterX = ((float)nCenterX / (float)g_pUIRenderer->nWidth) * 2.0f - 1.0f;
    float fCenterY = 1.0f - ((float)nCenterY / (float)g_pUIRenderer->nHeight) * 2.0f;
    
    // Рисуем простую стрелку в зависимости от типа
    float fArrowSize = 0.1f; // Размер стрелки в нормализованных координатах
    float fVertices[6]; // 3 точки для треугольника
    
    switch (nType) {
        case 1: // Налево
            fVertices[0] = fCenterX + fArrowSize; fVertices[1] = fCenterY;
            fVertices[2] = fCenterX; fVertices[3] = fCenterY - fArrowSize;
            fVertices[4] = fCenterX; fVertices[5] = fCenterY + fArrowSize;
            break;
        case 2: // Направо
            fVertices[0] = fCenterX - fArrowSize; fVertices[1] = fCenterY;
            fVertices[2] = fCenterX; fVertices[3] = fCenterY - fArrowSize;
            fVertices[4] = fCenterX; fVertices[5] = fCenterY + fArrowSize;
            break;
        case 3: // Прямо
        default:
            fVertices[0] = fCenterX; fVertices[1] = fCenterY + fArrowSize;
            fVertices[2] = fCenterX - fArrowSize; fVertices[3] = fCenterY;
            fVertices[4] = fCenterX + fArrowSize; fVertices[5] = fCenterY;
            break;
    }
    
    // Включаем смешивание
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    
    glBindVertexArray(g_pUIRenderer->nUILineVAO);
    glBindBuffer(GL_ARRAY_BUFFER, g_pUIRenderer->nUILineVBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(fVertices), fVertices, GL_DYNAMIC_DRAW);
    
    glLineWidth(4.0f);
    glDrawArrays(GL_TRIANGLES, 0, 3);
    
    glBindVertexArray(0);
    glDisable(GL_BLEND);
    
    // Рендерим расстояние под стрелкой
    if (nDistance > 0) {
        int nDistanceY = nCenterY + 40;
        int nDistanceSize = 20;
        
        if (nDistance >= 1000) {
            // Километры (рендерим число + "км")
            int nKm = nDistance / 1000;
            char szDistance[32];
            snprintf(szDistance, sizeof(szDistance), "%d км", nKm);
            int nTextWidth = Tiggo_GetTextWidth(szDistance, nDistanceSize);
            int nTextX = nCenterX - nTextWidth / 2;
            Tiggo_RenderText(szDistance, nTextX, nDistanceY, nDistanceSize, 1.0f, 1.0f, 1.0f, 1.0f);
        } else {
            // Метры
            char szDistance[32];
            snprintf(szDistance, sizeof(szDistance), "%d м", nDistance);
            int nTextWidth = Tiggo_GetTextWidth(szDistance, nDistanceSize);
            int nTextX = nCenterX - nTextWidth / 2;
            Tiggo_RenderText(szDistance, nTextX, nDistanceY, nDistanceSize, 1.0f, 1.0f, 1.0f, 1.0f);
        }
    }
}

/**
 * Рендеринг ограничения скорости
 */
void Tiggo_RenderSpeedLimit(CTiggoEngine* pEngine, int nSpeedLimit, int nX, int nY) {
    if (g_pUIRenderer == NULL || !g_pUIRenderer->bInitialized || pEngine == NULL) {
        return;
    }
    
    // Рендерим фон (красный круг)
    int nSize = 60;
    RenderQuad(nX, nY, nSize, nSize, 1.0f, 0.0f, 0.0f, 0.9f, (float)nSize / 2.0f);
    
    // Рендерим белый внутренний круг
    int nInnerSize = nSize - 10;
    RenderQuad(nX + 5, nY + 5, nInnerSize, nInnerSize, 1.0f, 1.0f, 1.0f, 1.0f, (float)nInnerSize / 2.0f);
    
    // Рендерим текст ограничения скорости (красный, средний размер)
    int nTextSize = 24;
    int nTextX = nX + nSize / 2 - Tiggo_GetDigitWidth(nSpeedLimit % 10, nTextSize) / 2;
    int nTextY = nY + nSize / 2 - nTextSize / 2;
    Tiggo_RenderNumber(nSpeedLimit, nTextX, nTextY, nTextSize, 1.0f, 0.0f, 0.0f, 1.0f);
}

/**
 * Рендеринг названия дороги
 */
void Tiggo_RenderRoadName(CTiggoEngine* pEngine, const char* pcRoadName, int nX, int nY) {
    if (g_pUIRenderer == NULL || !g_pUIRenderer->bInitialized || 
        pEngine == NULL || pcRoadName == NULL || strlen(pcRoadName) == 0) {
        return;
    }
    
    // Вычисляем ширину текста
    int nTextSize = 20;
    int nTextWidth = Tiggo_GetTextWidth(pcRoadName, nTextSize);
    
    // Рендерим полупрозрачный фон (по ширине текста)
    int nWidth = nTextWidth + 20;
    if (nWidth < 200) nWidth = 200; // Минимальная ширина
    int nHeight = 40;
    RenderQuad(nX, nY, nWidth, nHeight, 0.0f, 0.0f, 0.0f, 0.6f, 4.0f);
    
    // Рендерим текст названия дороги (белый, средний размер)
    int nTextX = nX + 10;
    int nTextY = nY + 10;
    Tiggo_RenderText(pcRoadName, nTextX, nTextY, nTextSize, 1.0f, 1.0f, 1.0f, 1.0f);
}

/**
 * Рендеринг расстояния до цели
 */
void Tiggo_RenderDistanceToDestination(CTiggoEngine* pEngine, int nDistance, int nTime,
                                       int nX, int nY) {
    if (g_pUIRenderer == NULL || !g_pUIRenderer->bInitialized || pEngine == NULL) {
        return;
    }
    
    int nTextSize = 18;
    
    // Рендерим расстояние
    char szDistance[64];
    if (nDistance >= 1000) {
        int nKm = nDistance / 1000;
        snprintf(szDistance, sizeof(szDistance), "%d км", nKm);
    } else {
        snprintf(szDistance, sizeof(szDistance), "%d м", nDistance);
    }
    Tiggo_RenderText(szDistance, nX, nY, nTextSize, 1.0f, 1.0f, 1.0f, 1.0f);
    
    // Рендерим время (под расстоянием)
    int nTimeY = nY + nTextSize + 5;
    int nHours = nTime / 3600;
    int nMinutes = (nTime % 3600) / 60;
    
    char szTime[32];
    if (nHours > 0) {
        snprintf(szTime, sizeof(szTime), "%d ч %d мин", nHours, nMinutes);
    } else {
        snprintf(szTime, sizeof(szTime), "%d мин", nMinutes);
    }
    Tiggo_RenderText(szTime, nX, nTimeY, nTextSize, 1.0f, 1.0f, 1.0f, 1.0f);
}

/**
 * Главная функция рендеринга UI
 */
void Tiggo_RenderUI(CTiggoEngine* pEngine, BOOL bSimplified) {
    if (g_pUIRenderer == NULL || !g_pUIRenderer->bInitialized || pEngine == NULL) {
        return;
    }
    
    if (!bSimplified) {
        // Display 0: Полный UI
        
        // Скорость (справа вверху)
        int nSpeedX = g_pUIRenderer->nWidth - 140;
        int nSpeedY = 20;
        int nSpeed = (int)pEngine->m_fCurrentSpeed;
        if (nSpeed < 0) nSpeed = 0;
        if (nSpeed > 300) nSpeed = 300;
        Tiggo_RenderSpeed(pEngine, nSpeed, nSpeedX, nSpeedY);
        
        // Указатель маневра (центр экрана)
        if (pEngine->m_bNavigationActive && pEngine->m_nNextManeuverDistance > 0) {
            int nCenterX = g_pUIRenderer->nWidth / 2;
            int nCenterY = g_pUIRenderer->nHeight / 2 - 50; // Немного выше центра
            Tiggo_RenderManeuverArrow(pEngine, pEngine->m_nNextManeuverType,
                                     pEngine->m_nNextManeuverDistance, nCenterX, nCenterY);
        }
        
        // Ограничение скорости (слева вверху)
        if (pEngine->m_nSpeedLimitKmh > 0) {
            int nLimitX = 20;
            int nLimitY = 20;
            Tiggo_RenderSpeedLimit(pEngine, pEngine->m_nSpeedLimitKmh, nLimitX, nLimitY);
        }
        
        // Название дороги (внизу)
        if (pEngine->m_pcCurrentRoadName[0] != '\0') {
            int nRoadX = g_pUIRenderer->nWidth / 2 - 200;
            int nRoadY = g_pUIRenderer->nHeight - 60;
            Tiggo_RenderRoadName(pEngine, pEngine->m_pcCurrentRoadName, nRoadX, nRoadY);
        }
        
        // TODO: Расстояние до цели (справа внизу)
        
    } else {
        // Display 1: Упрощенный UI
        
        // Только ограничение скорости (если нужно)
        if (pEngine->m_nSpeedLimitKmh > 0) {
            int nLimitX = 20;
            int nLimitY = 20;
            Tiggo_RenderSpeedLimit(pEngine, pEngine->m_nSpeedLimitKmh, nLimitX, nLimitY);
        }
    }
}

