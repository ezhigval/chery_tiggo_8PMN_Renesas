/**
 * shader_utils.h - Утилиты для работы с шейдерами (в стиле TurboDog)
 */

#ifndef SHADER_UTILS_H
#define SHADER_UTILS_H

#include <GLES3/gl3.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Boolean тип - должен быть определен в включающем файле
// Если используется отдельно, нужно включить tiggo_engine.h или определить BOOL
// Boolean тип (если еще не определен, будет определен в tiggo_engine.h)
#ifndef BOOL
typedef int BOOL;
#define TRUE  1
#define FALSE 0
#endif

/**
 * Компиляция шейдера
 * @param nShaderType тип шейдера (GL_VERTEX_SHADER или GL_FRAGMENT_SHADER)
 * @param pcSource исходный код шейдера
 * @return ID скомпилированного шейдера или 0 при ошибке
 */
GLuint Tiggo_CompileShader(GLenum nShaderType, const char* pcSource);

/**
 * Линковка шейдерной программы
 * @param nVertexShader ID вершинного шейдера
 * @param nFragmentShader ID фрагментного шейдера
 * @return ID линкованной программы или 0 при ошибке
 */
GLuint Tiggo_LinkProgram(GLuint nVertexShader, GLuint nFragmentShader);

/**
 * Создание шейдерной программы из исходников
 * @param pcVertexSource исходный код вершинного шейдера
 * @param pcFragmentSource исходный код фрагментного шейдера
 * @return ID созданной программы или 0 при ошибке
 */
GLuint Tiggo_CreateShaderProgram(const char* pcVertexSource, const char* pcFragmentSource);

/**
 * Проверка ошибок OpenGL
 * @param pcOperation название операции для лога
 * @return TRUE если ошибок нет, FALSE если есть ошибка
 */
BOOL Tiggo_CheckGLError(const char* pcOperation);

#ifdef __cplusplus
}
#endif

#endif // SHADER_UTILS_H

