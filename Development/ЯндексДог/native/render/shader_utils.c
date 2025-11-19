/**
 * shader_utils.c - Реализация утилит для работы с шейдерами (в стиле TurboDog)
 * 
 * Стиль TurboDog:
 * - Префиксы функций: Tiggo_
 * - Венгерская нотация
 * - C код (не C++)
 */

#include "shader_utils.h"
#include <GLES3/gl3.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <stdarg.h>

// Логирование (можно заменить на реальное логирование)
static void LogError(const char* pcFormat, ...) {
    // TODO: реализовать реальное логирование через Android log
    va_list args;
    va_start(args, pcFormat);
    fprintf(stderr, "Shader Error: ");
    vfprintf(stderr, pcFormat, args);
    fprintf(stderr, "\n");
    va_end(args);
}

/**
 * Компиляция шейдера
 */
GLuint Tiggo_CompileShader(GLenum nShaderType, const char* pcSource) {
    if (pcSource == NULL) {
        LogError("Shader source is NULL");
        return 0;
    }
    
    // Создаем шейдер
    GLuint nShader = glCreateShader(nShaderType);
    if (nShader == 0) {
        LogError("Failed to create shader");
        return 0;
    }
    
    // Загружаем исходный код
    glShaderSource(nShader, 1, &pcSource, NULL);
    
    // Компилируем шейдер
    glCompileShader(nShader);
    
    // Проверяем статус компиляции
    GLint nCompileStatus = 0;
    glGetShaderiv(nShader, GL_COMPILE_STATUS, &nCompileStatus);
    
    if (nCompileStatus == GL_FALSE) {
        // Получаем информацию об ошибке
        GLint nInfoLogLength = 0;
        glGetShaderiv(nShader, GL_INFO_LOG_LENGTH, &nInfoLogLength);
        
        if (nInfoLogLength > 0) {
            char* pcInfoLog = (char*)malloc(nInfoLogLength);
            if (pcInfoLog != NULL) {
                glGetShaderInfoLog(nShader, nInfoLogLength, NULL, pcInfoLog);
                LogError("Shader compilation failed: %s", pcInfoLog);
                free(pcInfoLog);
            }
        }
        
        glDeleteShader(nShader);
        return 0;
    }
    
    return nShader;
}

/**
 * Линковка шейдерной программы
 */
GLuint Tiggo_LinkProgram(GLuint nVertexShader, GLuint nFragmentShader) {
    if (nVertexShader == 0 || nFragmentShader == 0) {
        LogError("Invalid shader IDs for linking");
        return 0;
    }
    
    // Создаем программу
    GLuint nProgram = glCreateProgram();
    if (nProgram == 0) {
        LogError("Failed to create shader program");
        return 0;
    }
    
    // Прикрепляем шейдеры
    glAttachShader(nProgram, nVertexShader);
    glAttachShader(nProgram, nFragmentShader);
    
    // Линкуем программу
    glLinkProgram(nProgram);
    
    // Проверяем статус линковки
    GLint nLinkStatus = 0;
    glGetProgramiv(nProgram, GL_LINK_STATUS, &nLinkStatus);
    
    if (nLinkStatus == GL_FALSE) {
        // Получаем информацию об ошибке
        GLint nInfoLogLength = 0;
        glGetProgramiv(nProgram, GL_INFO_LOG_LENGTH, &nInfoLogLength);
        
        if (nInfoLogLength > 0) {
            char* pcInfoLog = (char*)malloc(nInfoLogLength);
            if (pcInfoLog != NULL) {
                glGetProgramInfoLog(nProgram, nInfoLogLength, NULL, pcInfoLog);
                LogError("Shader linking failed: %s", pcInfoLog);
                free(pcInfoLog);
            }
        }
        
        glDeleteProgram(nProgram);
        return 0;
    }
    
    // Открепляем шейдеры (они больше не нужны в программе)
    glDetachShader(nProgram, nVertexShader);
    glDetachShader(nProgram, nFragmentShader);
    
    return nProgram;
}

/**
 * Создание шейдерной программы из исходников
 */
GLuint Tiggo_CreateShaderProgram(const char* pcVertexSource, const char* pcFragmentSource) {
    if (pcVertexSource == NULL || pcFragmentSource == NULL) {
        LogError("Shader source is NULL");
        return 0;
    }
    
    // Компилируем вершинный шейдер
    GLuint nVertexShader = Tiggo_CompileShader(GL_VERTEX_SHADER, pcVertexSource);
    if (nVertexShader == 0) {
        LogError("Failed to compile vertex shader");
        return 0;
    }
    
    // Компилируем фрагментный шейдер
    GLuint nFragmentShader = Tiggo_CompileShader(GL_FRAGMENT_SHADER, pcFragmentSource);
    if (nFragmentShader == 0) {
        LogError("Failed to compile fragment shader");
        glDeleteShader(nVertexShader);
        return 0;
    }
    
    // Линкуем программу
    GLuint nProgram = Tiggo_LinkProgram(nVertexShader, nFragmentShader);
    
    // Удаляем шейдеры (они уже прикреплены к программе)
    glDeleteShader(nVertexShader);
    glDeleteShader(nFragmentShader);
    
    return nProgram;
}

/**
 * Проверка ошибок OpenGL
 */
BOOL Tiggo_CheckGLError(const char* pcOperation) {
    GLenum nError = glGetError();
    
    if (nError != GL_NO_ERROR) {
        const char* pcErrorString = NULL;
        
        switch (nError) {
            case GL_INVALID_ENUM:
                pcErrorString = "GL_INVALID_ENUM";
                break;
            case GL_INVALID_VALUE:
                pcErrorString = "GL_INVALID_VALUE";
                break;
            case GL_INVALID_OPERATION:
                pcErrorString = "GL_INVALID_OPERATION";
                break;
            case GL_OUT_OF_MEMORY:
                pcErrorString = "GL_OUT_OF_MEMORY";
                break;
            default:
                pcErrorString = "Unknown error";
                break;
        }
        
        LogError("OpenGL error in %s: %s (0x%x)", pcOperation ? pcOperation : "operation", 
                 pcErrorString, nError);
        return FALSE;
    }
    
    return TRUE;
}

