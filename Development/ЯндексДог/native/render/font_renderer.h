/**
 * font_renderer.h - Заголовок рендеринга текста (в стиле TurboDog)
 * 
 * Простой bitmap шрифт для рендеринга цифр и текста
 * в стиле TurboDog (легковесный подход)
 */

#ifndef FONT_RENDERER_H
#define FONT_RENDERER_H

#include "../core/tiggo_engine.h"
#include <GLES3/gl3.h>

#ifdef __cplusplus
extern "C" {
#endif

// Boolean тип определен в tiggo_engine.h (уже включен выше)

/**
 * Инициализация рендерера шрифтов
 * @return TRUE при успехе, FALSE при ошибке
 */
BOOL Tiggo_InitFontRenderer(void);

/**
 * Уничтожение рендерера шрифтов
 */
void Tiggo_DestroyFontRenderer(void);

/**
 * Рендеринг одной цифры (0-9)
 * @param nDigit цифра (0-9)
 * @param nX позиция X на экране
 * @param nY позиция Y на экране
 * @param nSize размер цифры в пикселях
 * @param fR красный компонент цвета (0.0-1.0)
 * @param fG зеленый компонент цвета (0.0-1.0)
 * @param fB синий компонент цвета (0.0-1.0)
 * @param fA альфа компонент цвета (0.0-1.0)
 */
void Tiggo_RenderDigit(int nDigit, int nX, int nY, int nSize, 
                       float fR, float fG, float fB, float fA);

/**
 * Рендеринг числа
 * @param nNumber число для отображения
 * @param nX позиция X на экране
 * @param nY позиция Y на экране
 * @param nSize размер цифр в пикселях
 * @param fR красный компонент цвета
 * @param fG зеленый компонент цвета
 * @param fB синий компонент цвета
 * @param fA альфа компонент цвета
 * @return ширина отрендеренного текста в пикселях
 */
int Tiggo_RenderNumber(int nNumber, int nX, int nY, int nSize,
                       float fR, float fG, float fB, float fA);

/**
 * Рендеринг текстовой строки (ASCII)
 * @param pcText текст для отображения
 * @param nX позиция X на экране
 * @param nY позиция Y на экране
 * @param nSize размер символов в пикселях
 * @param fR красный компонент цвета
 * @param fG зеленый компонент цвета
 * @param fB синий компонент цвета
 * @param fA альфа компонент цвета
 * @return ширина отрендеренного текста в пикселях
 */
int Tiggo_RenderText(const char* pcText, int nX, int nY, int nSize,
                     float fR, float fG, float fB, float fA);

/**
 * Получение ширины текста без рендеринга
 * @param pcText текст
 * @param nSize размер символов
 * @return ширина текста в пикселях
 */
int Tiggo_GetTextWidth(const char* pcText, int nSize);

/**
 * Получение ширины цифры без рендеринга
 * @param nDigit цифра (0-9)
 * @param nSize размер цифры
 * @return ширина цифры в пикселях
 */
int Tiggo_GetDigitWidth(int nDigit, int nSize);

/**
 * Установка размеров окна для шрифта
 * Вызывается из ui_renderer.c при обновлении размера
 * @param nWidth ширина окна
 * @param nHeight высота окна
 */
void Tiggo_FontSetWindowSize(int nWidth, int nHeight);

// Внешние переменные для размеров окна (доступны из ui_renderer.c)
extern int g_nFontWindowWidth;
extern int g_nFontWindowHeight;

#ifdef __cplusplus
}
#endif

#endif // FONT_RENDERER_H

