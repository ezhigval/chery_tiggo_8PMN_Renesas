/**
 * font_renderer.c - Реализация рендеринга текста (в стиле TurboDog)
 * 
 * Простой bitmap шрифт для рендеринга цифр и текста
 * Использует встроенный bitmap шрифт (7x9 пикселей для каждой цифры)
 * 
 * Стиль TurboDog:
 * - Префиксы функций: Tiggo_
 * - Венгерская нотация
 * - C код (не C++)
 */

#include "font_renderer.h"
#include "ui_renderer.h"
#include "../core/tiggo_engine.h"
#include "shader_utils.h"
#include <GLES3/gl3.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>

// Встроенный bitmap шрифт (простой 7x9 пикселей для каждой цифры)
// Формат: каждый символ представлен как массив байтов (1 = пиксель, 0 = прозрачный)
// Для простоты используем шрифт размером 7x9 пикселей

#define FONT_CHAR_WIDTH  7
#define FONT_CHAR_HEIGHT 9
#define FONT_SPACING     1

// Всего символов: 10 цифр + 26 больших букв + 26 маленьких букв + некоторые спецсимволы
#define FONT_NUM_DIGITS    10
#define FONT_NUM_UPPERCASE 26
#define FONT_NUM_LOWERCASE 26
#define FONT_NUM_SPECIAL   10  // км, м, ч, мин, и т.д.
#define FONT_TOTAL_CHARS   (FONT_NUM_DIGITS + FONT_NUM_UPPERCASE + FONT_NUM_LOWERCASE + FONT_NUM_SPECIAL)

// Bitmap данных для цифр 0-9 (7x9 пикселей)
// Каждая цифра представлена как массив из 9 байтов
static const unsigned char g_aDigitBitmaps[10][9] = {
    // 0
    {
        0b0111110,  //  ### ###
        0b1000001,  // #     #
        0b1000001,  // #     #
        0b1000001,  // #     #
        0b1000001,  // #     #
        0b1000001,  // #     #
        0b1000001,  // #     #
        0b1000001,  // #     #
        0b0111110   //  ### ###
    },
    // 1
    {
        0b0001000,  //    #
        0b0011000,  //   ##
        0b0001000,  //    #
        0b0001000,  //    #
        0b0001000,  //    #
        0b0001000,  //    #
        0b0001000,  //    #
        0b0001000,  //    #
        0b0011100   //   ###
    },
    // 2
    {
        0b0111110,  //  ### ###
        0b1000001,  // #     #
        0b0000001,  //       #
        0b0000010,  //      #
        0b0000100,  //     #
        0b0001000,  //    #
        0b0010000,  //   #
        0b0100000,  //  #
        0b1111111   // #######
    },
    // 3
    {
        0b0111110,  //  ### ###
        0b1000001,  // #     #
        0b0000001,  //       #
        0b0000001,  //       #
        0b0111110,  //  ### ###
        0b0000001,  //       #
        0b0000001,  //       #
        0b1000001,  // #     #
        0b0111110   //  ### ###
    },
    // 4
    {
        0b0000010,  //      #
        0b0000110,  //     ##
        0b0001010,  //    # #
        0b0010010,  //   #  #
        0b0100010,  //  #   #
        0b1111111,  // #######
        0b0000010,  //      #
        0b0000010,  //      #
        0b0000010   //      #
    },
    // 5
    {
        0b1111111,  // #######
        0b1000000,  // #
        0b1000000,  // #
        0b1111110,  // ###### #
        0b0000001,  //       #
        0b0000001,  //       #
        0b0000001,  //       #
        0b1000001,  // #     #
        0b0111110   //  ### ###
    },
    // 6
    {
        0b0111110,  //  ### ###
        0b1000001,  // #     #
        0b1000000,  // #
        0b1111110,  // ###### #
        0b1000001,  // #     #
        0b1000001,  // #     #
        0b1000001,  // #     #
        0b1000001,  // #     #
        0b0111110   //  ### ###
    },
    // 7
    {
        0b1111111,  // #######
        0b0000001,  //       #
        0b0000010,  //      #
        0b0000100,  //     #
        0b0001000,  //    #
        0b0010000,  //   #
        0b0100000,  //  #
        0b0100000,  //  #
        0b0100000   //  #
    },
    // 8
    {
        0b0111110,  //  ### ###
        0b1000001,  // #     #
        0b1000001,  // #     #
        0b1000001,  // #     #
        0b0111110,  //  ### ###
        0b1000001,  // #     #
        0b1000001,  // #     #
        0b1000001,  // #     #
        0b0111110   //  ### ###
    },
    // 9
    {
        0b0111110,  //  ### ###
        0b1000001,  // #     #
        0b1000001,  // #     #
        0b1000001,  // #     #
        0b0111111,  //  ######
        0b0000001,  //       #
        0b0000001,  //       #
        0b1000001,  // #     #
        0b0111110   //  ### ###
    }
};

// Bitmap данных для больших букв A-Z (7x9 пикселей)
static const unsigned char g_aUppercaseBitmaps[26][9] = {
    // A
    {0b0011100, 0b0100010, 0b1000001, 0b1000001, 0b1111111, 0b1000001, 0b1000001, 0b1000001, 0b1000001},
    // B
    {0b1111110, 0b1000001, 0b1000001, 0b1000001, 0b1111110, 0b1000001, 0b1000001, 0b1000001, 0b1111110},
    // C
    {0b0111110, 0b1000001, 0b1000000, 0b1000000, 0b1000000, 0b1000000, 0b1000000, 0b1000001, 0b0111110},
    // D
    {0b1111110, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1111110},
    // E
    {0b1111111, 0b1000000, 0b1000000, 0b1000000, 0b1111110, 0b1000000, 0b1000000, 0b1000000, 0b1111111},
    // F
    {0b1111111, 0b1000000, 0b1000000, 0b1000000, 0b1111110, 0b1000000, 0b1000000, 0b1000000, 0b1000000},
    // G
    {0b0111110, 0b1000001, 0b1000000, 0b1000000, 0b1001111, 0b1000001, 0b1000001, 0b1000001, 0b0111110},
    // H
    {0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1111111, 0b1000001, 0b1000001, 0b1000001, 0b1000001},
    // I
    {0b1111111, 0b0011000, 0b0011000, 0b0011000, 0b0011000, 0b0011000, 0b0011000, 0b0011000, 0b1111111},
    // J
    {0b0001111, 0b0000001, 0b0000001, 0b0000001, 0b0000001, 0b0000001, 0b1000001, 0b1000001, 0b0111110},
    // K
    {0b1000001, 0b1000010, 0b1000100, 0b1001000, 0b1110000, 0b1001000, 0b1000100, 0b1000010, 0b1000001},
    // L
    {0b1000000, 0b1000000, 0b1000000, 0b1000000, 0b1000000, 0b1000000, 0b1000000, 0b1000000, 0b1111111},
    // M
    {0b1000001, 0b1100011, 0b1010101, 0b1001001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001},
    // N
    {0b1000001, 0b1100001, 0b1010001, 0b1001001, 0b1000101, 0b1000011, 0b1000001, 0b1000001, 0b1000001},
    // O
    {0b0111110, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b0111110},
    // P
    {0b1111110, 0b1000001, 0b1000001, 0b1000001, 0b1111110, 0b1000000, 0b1000000, 0b1000000, 0b1000000},
    // Q
    {0b0111110, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1001001, 0b1000101, 0b1000011, 0b0111111},
    // R
    {0b1111110, 0b1000001, 0b1000001, 0b1000001, 0b1111110, 0b1000100, 0b1000010, 0b1000001, 0b1000001},
    // S
    {0b0111110, 0b1000001, 0b1000000, 0b1000000, 0b0111110, 0b0000001, 0b0000001, 0b1000001, 0b0111110},
    // T
    {0b1111111, 0b0011000, 0b0011000, 0b0011000, 0b0011000, 0b0011000, 0b0011000, 0b0011000, 0b0011000},
    // U
    {0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b0111110},
    // V
    {0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b0100010, 0b0010100, 0b0001000},
    // W
    {0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1001001, 0b1010101, 0b1100011, 0b1000001},
    // X
    {0b1000001, 0b0100010, 0b0010100, 0b0001000, 0b0001000, 0b0010100, 0b0100010, 0b1000001, 0b1000001},
    // Y
    {0b1000001, 0b1000001, 0b0100010, 0b0010100, 0b0001000, 0b0001000, 0b0001000, 0b0001000, 0b0001000},
    // Z
    {0b1111111, 0b0000001, 0b0000010, 0b0000100, 0b0001000, 0b0010000, 0b0100000, 0b1000000, 0b1111111}
};

// Bitmap данных для маленьких букв а-я (упрощенный, используем латиницу a-z)
static const unsigned char g_aLowercaseBitmaps[26][9] = {
    // a
    {0b0000000, 0b0000000, 0b0111110, 0b0000001, 0b0111111, 0b1000001, 0b1000001, 0b1000011, 0b0111101},
    // b
    {0b1000000, 0b1000000, 0b1111110, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1111110},
    // c
    {0b0000000, 0b0000000, 0b0111110, 0b1000001, 0b1000000, 0b1000000, 0b1000000, 0b1000001, 0b0111110},
    // d
    {0b0000001, 0b0000001, 0b0111111, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b0111111},
    // e
    {0b0000000, 0b0000000, 0b0111110, 0b1000001, 0b1111111, 0b1000000, 0b1000000, 0b1000001, 0b0111110},
    // f
    {0b0011110, 0b0100000, 0b1111110, 0b0100000, 0b0100000, 0b0100000, 0b0100000, 0b0100000, 0b0100000},
    // g
    {0b0000000, 0b0000000, 0b0111111, 0b1000001, 0b1000001, 0b0111111, 0b0000001, 0b1000001, 0b0111110},
    // h
    {0b1000000, 0b1000000, 0b1111110, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001},
    // i
    {0b0011000, 0b0000000, 0b0011000, 0b0011000, 0b0011000, 0b0011000, 0b0011000, 0b0011000, 0b0011000},
    // j
    {0b0000110, 0b0000000, 0b0000110, 0b0000110, 0b0000110, 0b0000110, 0b1000110, 0b1000110, 0b0111100},
    // k
    {0b1000000, 0b1000000, 0b1000010, 0b1000100, 0b1001000, 0b1110000, 0b1001000, 0b1000100, 0b1000010},
    // l
    {0b0011000, 0b0011000, 0b0011000, 0b0011000, 0b0011000, 0b0011000, 0b0011000, 0b0011000, 0b0011000},
    // m
    {0b0000000, 0b0000000, 0b1110110, 0b1001001, 0b1001001, 0b1001001, 0b1001001, 0b1001001, 0b1001001},
    // n
    {0b0000000, 0b0000000, 0b1111110, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001},
    // o
    {0b0000000, 0b0000000, 0b0111110, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b0111110},
    // p
    {0b0000000, 0b0000000, 0b1111110, 0b1000001, 0b1000001, 0b1111110, 0b1000000, 0b1000000, 0b1000000},
    // q
    {0b0000000, 0b0000000, 0b0111111, 0b1000001, 0b1000001, 0b0111111, 0b0000001, 0b0000001, 0b0000001},
    // r
    {0b0000000, 0b0000000, 0b1111110, 0b1000001, 0b1000000, 0b1000000, 0b1000000, 0b1000000, 0b1000000},
    // s
    {0b0000000, 0b0000000, 0b0111110, 0b1000001, 0b1000000, 0b0111110, 0b0000001, 0b1000001, 0b0111110},
    // t
    {0b0100000, 0b0100000, 0b1111110, 0b0100000, 0b0100000, 0b0100000, 0b0100000, 0b0100000, 0b0011110},
    // u
    {0b0000000, 0b0000000, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b0111111},
    // v
    {0b0000000, 0b0000000, 0b1000001, 0b1000001, 0b1000001, 0b0100010, 0b0010100, 0b0001000, 0b0000000},
    // w
    {0b0000000, 0b0000000, 0b1001001, 0b1001001, 0b1001001, 0b1001001, 0b1001001, 0b0110110, 0b0000000},
    // x
    {0b0000000, 0b0000000, 0b1000001, 0b0100010, 0b0010100, 0b0001000, 0b0010100, 0b0100010, 0b1000001},
    // y
    {0b0000000, 0b0000000, 0b1000001, 0b1000001, 0b1000001, 0b0111111, 0b0000001, 0b1000001, 0b0111110},
    // z
    {0b0000000, 0b0000000, 0b1111111, 0b0000010, 0b0000100, 0b0001000, 0b0010000, 0b0100000, 0b1111111}
};

// Спецсимволы: к, м, ч, М, К, пробел (индексы: 0-5)
static const unsigned char g_aSpecialBitmaps[10][9] = {
    // к (0) - кириллица к
    {0b1000001, 0b1000001, 0b1000010, 0b1000100, 0b1111000, 0b1000100, 0b1000010, 0b1000001, 0b1000001},
    // м (1) - кириллица м
    {0b1000001, 0b1100011, 0b1010101, 0b1001001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001},
    // ч (2) - кириллица ч
    {0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b0111111, 0b0000001, 0b0000001, 0b0000001, 0b0000001},
    // М (3) - большая М (для км)
    {0b1000001, 0b1100011, 0b1010101, 0b1001001, 0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1000001},
    // К (4) - большая К (для км)
    {0b1000001, 0b1000010, 0b1000100, 0b1001000, 0b1110000, 0b1001000, 0b1000100, 0b1000010, 0b1000001},
    // пробел (5) - пустой символ
    {0b0000000, 0b0000000, 0b0000000, 0b0000000, 0b0000000, 0b0000000, 0b0000000, 0b0000000, 0b0000000},
    // и (6) - кириллица и (для "мин")
    {0b1000001, 0b1000001, 0b1000001, 0b1000011, 0b1000101, 0b1001001, 0b1010001, 0b1100001, 0b1000001},
    // н (7) - кириллица н (для "мин")
    {0b1000001, 0b1000001, 0b1000001, 0b1000001, 0b1111111, 0b1000001, 0b1000001, 0b1000001, 0b1000001},
    // а (8) - кириллица а (для названий)
    {0b0000000, 0b0000000, 0b0111110, 0b0000001, 0b0111111, 0b1000001, 0b1000001, 0b1000011, 0b0111101},
    // я (9) - кириллица я (для названий)
    {0b0111111, 0b1000001, 0b1000001, 0b1000001, 0b0111111, 0b0010001, 0b0100001, 0b1000001, 0b1000001}
};

// Глобальные переменные для шрифта
static GLuint g_nFontTexture = 0;
static GLuint g_nFontVAO = 0;
static GLuint g_nFontVBO = 0;
static GLuint g_nFontShaderProgram = 0;
static BOOL g_bFontInitialized = FALSE;

// Размеры окна для рендеринга шрифта (обновляются из ui_renderer.c)
// Определены здесь, но объявлены в font_renderer.h как extern
int g_nFontWindowWidth = 0;
int g_nFontWindowHeight = 0;

/**
 * Генерация одного символа в текстуру
 */
static void GenerateCharToTexture(unsigned char* pTextureData, int nTextureWidth, 
                                   const unsigned char* pCharBitmap, int nCharIndex) {
    int nOffsetX = nCharIndex * (FONT_CHAR_WIDTH + FONT_SPACING);
    
    for (int y = 0; y < FONT_CHAR_HEIGHT; y++) {
        unsigned char nByte = pCharBitmap[y];
        
        for (int x = 0; x < FONT_CHAR_WIDTH; x++) {
            int nPixelX = nOffsetX + x;
            int nPixelY = y;
            int nIndex = (nPixelY * nTextureWidth + nPixelX) * 4;
            
            // Извлекаем бит (от старшего к младшему)
            unsigned char nBit = (nByte >> (FONT_CHAR_WIDTH - 1 - x)) & 1;
            
            if (nBit) {
                // Белый пиксель
                pTextureData[nIndex + 0] = 255; // R
                pTextureData[nIndex + 1] = 255; // G
                pTextureData[nIndex + 2] = 255; // B
                pTextureData[nIndex + 3] = 255; // A
            } else {
                // Прозрачный пиксель
                pTextureData[nIndex + 0] = 0;
                pTextureData[nIndex + 1] = 0;
                pTextureData[nIndex + 2] = 0;
                pTextureData[nIndex + 3] = 0;
            }
        }
    }
}

/**
 * Создание текстуры шрифта из bitmap данных
 */
static BOOL CreateFontTexture(void) {
    if (g_nFontTexture != 0) {
        glDeleteTextures(1, &g_nFontTexture);
    }
    
    // Создаем текстуру для всех символов
    const int nTextureWidth = FONT_TOTAL_CHARS * (FONT_CHAR_WIDTH + FONT_SPACING);
    const int nTextureHeight = FONT_CHAR_HEIGHT;
    
    // Создаем данные текстуры (RGBA)
    unsigned char* pTextureData = (unsigned char*)malloc(nTextureWidth * nTextureHeight * 4);
    if (pTextureData == NULL) {
        return FALSE;
    }
    
    memset(pTextureData, 0, nTextureWidth * nTextureHeight * 4);
    
    int nCharIndex = 0;
    
    // Генерируем текстуру для цифр 0-9
    for (int nDigit = 0; nDigit < FONT_NUM_DIGITS; nDigit++) {
        GenerateCharToTexture(pTextureData, nTextureWidth, g_aDigitBitmaps[nDigit], nCharIndex);
        nCharIndex++;
    }
    
    // Генерируем текстуру для больших букв A-Z
    for (int nLetter = 0; nLetter < FONT_NUM_UPPERCASE; nLetter++) {
        GenerateCharToTexture(pTextureData, nTextureWidth, g_aUppercaseBitmaps[nLetter], nCharIndex);
        nCharIndex++;
    }
    
    // Генерируем текстуру для маленьких букв a-z
    for (int nLetter = 0; nLetter < FONT_NUM_LOWERCASE; nLetter++) {
        GenerateCharToTexture(pTextureData, nTextureWidth, g_aLowercaseBitmaps[nLetter], nCharIndex);
        nCharIndex++;
    }
    
    // Генерируем текстуру для спецсимволов
    for (int nSpecial = 0; nSpecial < FONT_NUM_SPECIAL; nSpecial++) {
        GenerateCharToTexture(pTextureData, nTextureWidth, g_aSpecialBitmaps[nSpecial], nCharIndex);
        nCharIndex++;
    }
    
    // Создаем OpenGL текстуру
    glGenTextures(1, &g_nFontTexture);
    glBindTexture(GL_TEXTURE_2D, g_nFontTexture);
    
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, nTextureWidth, nTextureHeight, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, pTextureData);
    
    free(pTextureData);
    
    Tiggo_CheckGLError("CreateFontTexture");
    
    return TRUE;
}

/**
 * Инициализация шейдеров для шрифта
 */
static BOOL InitFontShaders(void) {
    const char* pVertexShader = 
        "#version 300 es\n"
        "layout (location = 0) in vec2 aPos;\n"
        "layout (location = 1) in vec2 aTexCoord;\n"
        "out vec2 TexCoord;\n"
        "uniform mat4 projection;\n"
        "void main() {\n"
        "    gl_Position = projection * vec4(aPos.x, aPos.y, 0.0, 1.0);\n"
        "    TexCoord = aTexCoord;\n"
        "}\n";
    
    const char* pFragmentShader = 
        "#version 300 es\n"
        "precision mediump float;\n"
        "in vec2 TexCoord;\n"
        "out vec4 FragColor;\n"
        "uniform sampler2D fontTexture;\n"
        "uniform vec4 textColor;\n"
        "void main() {\n"
        "    vec4 texColor = texture(fontTexture, TexCoord);\n"
        "    FragColor = vec4(textColor.rgb, texColor.a * textColor.a);\n"
        "}\n";
    
    g_nFontShaderProgram = Tiggo_CreateShaderProgram(pVertexShader, pFragmentShader);
    if (g_nFontShaderProgram == 0) {
        return FALSE;
    }
    
    Tiggo_CheckGLError("InitFontShaders");
    
    return TRUE;
}

/**
 * Инициализация VBO/VAO для шрифта
 */
static BOOL InitFontBuffers(void) {
    glGenVertexArrays(1, &g_nFontVAO);
    glGenBuffers(1, &g_nFontVBO);
    
    glBindVertexArray(g_nFontVAO);
    glBindBuffer(GL_ARRAY_BUFFER, g_nFontVBO);
    glBufferData(GL_ARRAY_BUFFER, 0, NULL, GL_DYNAMIC_DRAW);
    
    // Настройка атрибутов
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(float), (void*)(2 * sizeof(float)));
    glEnableVertexAttribArray(1);
    
    glBindVertexArray(0);
    
    Tiggo_CheckGLError("InitFontBuffers");
    
    return TRUE;
}

/**
 * Инициализация рендерера шрифтов
 */
BOOL Tiggo_InitFontRenderer(void) {
    if (g_bFontInitialized) {
        return TRUE;
    }
    
    // Инициализация шейдеров
    if (!InitFontShaders()) {
        return FALSE;
    }
    
    // Инициализация буферов
    if (!InitFontBuffers()) {
        return FALSE;
    }
    
    // Создание текстуры шрифта
    if (!CreateFontTexture()) {
        return FALSE;
    }
    
    g_bFontInitialized = TRUE;
    return TRUE;
}

/**
 * Установка размеров окна для шрифта
 * Вызывается из ui_renderer.c
 */
void Tiggo_FontSetWindowSize(int nWidth, int nHeight) {
    g_nFontWindowWidth = nWidth;
    g_nFontWindowHeight = nHeight;
}

/**
 * Уничтожение рендерера шрифтов
 */
void Tiggo_DestroyFontRenderer(void) {
    if (!g_bFontInitialized) {
        return;
    }
    
    if (g_nFontTexture != 0) {
        glDeleteTextures(1, &g_nFontTexture);
        g_nFontTexture = 0;
    }
    
    if (g_nFontVAO != 0) {
        glDeleteVertexArrays(1, &g_nFontVAO);
        g_nFontVAO = 0;
    }
    
    if (g_nFontVBO != 0) {
        glDeleteBuffers(1, &g_nFontVBO);
        g_nFontVBO = 0;
    }
    
    if (g_nFontShaderProgram != 0) {
        glDeleteProgram(g_nFontShaderProgram);
        g_nFontShaderProgram = 0;
    }
    
    g_bFontInitialized = FALSE;
}

/**
 * Рендеринг одного символа по индексу в текстуре
 */
static void RenderCharByIndex(int nCharIndex, int nX, int nY, int nSize,
                               float fR, float fG, float fB, float fA) {
    if (!g_bFontInitialized || nCharIndex < 0 || nCharIndex >= FONT_TOTAL_CHARS) {
        return;
    }
    
    // Получаем размеры окна
    int nWidth = g_nFontWindowWidth;
    int nHeight = g_nFontWindowHeight;
    
    // Конвертируем координаты в нормализованные
    float fNormX = ((float)nX / (float)nWidth) * 2.0f - 1.0f;
    float fNormY = 1.0f - ((float)nY / (float)nHeight) * 2.0f;
    float fNormWidth = ((float)nSize * FONT_CHAR_WIDTH / (float)FONT_CHAR_HEIGHT) / (float)nWidth * 2.0f;
    float fNormHeight = ((float)nSize) / (float)nHeight * 2.0f;
    
    // Вычисляем текстурные координаты для символа
    float fCharWidth = (float)(FONT_CHAR_WIDTH + FONT_SPACING);
    float fTexCoordX = (float)nCharIndex * fCharWidth / (float)(FONT_TOTAL_CHARS * (FONT_CHAR_WIDTH + FONT_SPACING));
    float fTexCoordWidth = (float)FONT_CHAR_WIDTH / (float)(FONT_TOTAL_CHARS * (FONT_CHAR_WIDTH + FONT_SPACING));
    
    // Вершины квада [x, y, u, v]
    float fVertices[] = {
        // Нижний левый
        fNormX, fNormY, fTexCoordX, 1.0f,
        // Нижний правый
        fNormX + fNormWidth, fNormY, fTexCoordX + fTexCoordWidth, 1.0f,
        // Верхний правый
        fNormX + fNormWidth, fNormY + fNormHeight, fTexCoordX + fTexCoordWidth, 0.0f,
        // Нижний левый (для второго треугольника)
        fNormX, fNormY, fTexCoordX, 1.0f,
        // Верхний правый
        fNormX + fNormWidth, fNormY + fNormHeight, fTexCoordX + fTexCoordWidth, 0.0f,
        // Верхний левый
        fNormX, fNormY + fNormHeight, fTexCoordX, 0.0f
    };
    
    // Активируем шейдер
    glUseProgram(g_nFontShaderProgram);
    
    // Устанавливаем матрицу проекции (ортографическая)
    float fProjection[16] = {
        1.0f, 0.0f, 0.0f, 0.0f,
        0.0f, 1.0f, 0.0f, 0.0f,
        0.0f, 0.0f, 1.0f, 0.0f,
        0.0f, 0.0f, 0.0f, 1.0f
    };
    
    GLint nProjectionLoc = glGetUniformLocation(g_nFontShaderProgram, "projection");
    if (nProjectionLoc >= 0) {
        glUniformMatrix4fv(nProjectionLoc, 1, GL_FALSE, fProjection);
    }
    
    GLint nColorLoc = glGetUniformLocation(g_nFontShaderProgram, "textColor");
    if (nColorLoc >= 0) {
        glUniform4f(nColorLoc, fR, fG, fB, fA);
    }
    
    // Привязываем текстуру шрифта
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, g_nFontTexture);
    GLint nTextureLoc = glGetUniformLocation(g_nFontShaderProgram, "fontTexture");
    if (nTextureLoc >= 0) {
        glUniform1i(nTextureLoc, 0);
    }
    
    // Включаем смешивание
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    
    // Рендерим
    glBindVertexArray(g_nFontVAO);
    glBindBuffer(GL_ARRAY_BUFFER, g_nFontVBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(fVertices), fVertices, GL_DYNAMIC_DRAW);
    
    glDrawArrays(GL_TRIANGLES, 0, 6);
    
    glBindVertexArray(0);
    glDisable(GL_BLEND);
}

/**
 * Рендеринг одной цифры
 */
void Tiggo_RenderDigit(int nDigit, int nX, int nY, int nSize,
                       float fR, float fG, float fB, float fA) {
    if (nDigit >= 0 && nDigit <= 9) {
        RenderCharByIndex(nDigit, nX, nY, nSize, fR, fG, fB, fA);
    }
}

/**
 * Получение индекса символа в текстуре
 * Поддержка ASCII и кириллицы (UTF-8)
 */
static int GetCharIndex(const char* pcChar, int* pnBytesUsed) {
    if (pcChar == NULL || pcChar[0] == '\0') {
        if (pnBytesUsed) *pnBytesUsed = 0;
        return -1;
    }
    
    unsigned char c = (unsigned char)pcChar[0];
    int nBytes = 1;
    
    if (c >= '0' && c <= '9') {
        // Цифры 0-9 (индексы 0-9)
        if (pnBytesUsed) *pnBytesUsed = 1;
        return c - '0';
    } else if (c >= 'A' && c <= 'Z') {
        // Большие буквы A-Z (индексы 10-35)
        if (pnBytesUsed) *pnBytesUsed = 1;
        return FONT_NUM_DIGITS + (c - 'A');
    } else if (c >= 'a' && c <= 'z') {
        // Маленькие буквы a-z (индексы 36-61)
        if (pnBytesUsed) *pnBytesUsed = 1;
        return FONT_NUM_DIGITS + FONT_NUM_UPPERCASE + (c - 'a');
    } else if (c == ' ') {
        // Пробел (индекс 67)
        if (pnBytesUsed) *pnBytesUsed = 1;
        return FONT_NUM_DIGITS + FONT_NUM_UPPERCASE + FONT_NUM_LOWERCASE + 5;
    } else if ((c & 0xE0) == 0xC0) {
        // UTF-8 двухбайтовый символ (кириллица)
        if (pcChar[1] == '\0') {
            if (pnBytesUsed) *pnBytesUsed = 1;
            return -1;
        }
        unsigned char c2 = (unsigned char)pcChar[1];
        nBytes = 2;
        
        // Проверяем кириллические символы
        // к (U+043A): 0xD0 0xBA
        // К (U+041A): 0xD0 0x9A
        // м (U+043C): 0xD0 0xBC
        // М (U+041C): 0xD0 0x9C
        // ч (U+0447): 0xD1 0x87
        // Ч (U+0427): 0xD1 0x87
        // и (U+0438): 0xD0 0xB8
        // И (U+0418): 0xD0 0x98
        // н (U+043D): 0xD0 0xBD
        // Н (U+041D): 0xD0 0x9D
        // а (U+0430): 0xD0 0xB0
        // А (U+0410): 0xD0 0x90
        // я (U+044F): 0xD1 0x8F
        // Я (U+042F): 0xD1 0x8F
        
        if (c == 0xD0) {
            if (c2 == 0xBA || c2 == 0x9A) { // к, К
                if (pnBytesUsed) *pnBytesUsed = 2;
                return FONT_NUM_DIGITS + FONT_NUM_UPPERCASE + FONT_NUM_LOWERCASE + 0;
            } else if (c2 == 0xBC || c2 == 0x9C) { // м, М
                if (pnBytesUsed) *pnBytesUsed = 2;
                return FONT_NUM_DIGITS + FONT_NUM_UPPERCASE + FONT_NUM_LOWERCASE + 1;
            } else if (c2 == 0xB8 || c2 == 0x98) { // и, И
                if (pnBytesUsed) *pnBytesUsed = 2;
                return FONT_NUM_DIGITS + FONT_NUM_UPPERCASE + FONT_NUM_LOWERCASE + 6;
            } else if (c2 == 0xBD || c2 == 0x9D) { // н, Н
                if (pnBytesUsed) *pnBytesUsed = 2;
                return FONT_NUM_DIGITS + FONT_NUM_UPPERCASE + FONT_NUM_LOWERCASE + 7;
            } else if (c2 == 0xB0 || c2 == 0x90) { // а, А
                if (pnBytesUsed) *pnBytesUsed = 2;
                return FONT_NUM_DIGITS + FONT_NUM_UPPERCASE + FONT_NUM_LOWERCASE + 8;
            }
        } else if (c == 0xD1) {
            if (c2 == 0x87) { // ч, Ч
                if (pnBytesUsed) *pnBytesUsed = 2;
                return FONT_NUM_DIGITS + FONT_NUM_UPPERCASE + FONT_NUM_LOWERCASE + 2;
            } else if (c2 == 0x8F) { // я, Я
                if (pnBytesUsed) *pnBytesUsed = 2;
                return FONT_NUM_DIGITS + FONT_NUM_UPPERCASE + FONT_NUM_LOWERCASE + 9;
            }
        }
    }
    
    if (pnBytesUsed) *pnBytesUsed = nBytes;
    return -1; // Неизвестный символ
}

/**
 * Рендеринг числа
 */
int Tiggo_RenderNumber(int nNumber, int nX, int nY, int nSize,
                       float fR, float fG, float fB, float fA) {
    if (!g_bFontInitialized) {
        return 0;
    }
    
    char szBuffer[32];
    snprintf(szBuffer, sizeof(szBuffer), "%d", nNumber);
    
    int nCurrentX = nX;
    int nDigitWidth = (nSize * FONT_CHAR_WIDTH) / FONT_CHAR_HEIGHT + 2; // +2 для пробела
    
    for (int i = 0; szBuffer[i] != '\0'; i++) {
        char c = szBuffer[i];
        if (c >= '0' && c <= '9') {
            int nDigit = c - '0';
            Tiggo_RenderDigit(nDigit, nCurrentX, nY, nSize, fR, fG, fB, fA);
            nCurrentX += nDigitWidth;
        }
    }
    
    return nCurrentX - nX; // Возвращаем ширину
}

/**
 * Рендеринг текстовой строки (ASCII + кириллица UTF-8)
 */
int Tiggo_RenderText(const char* pcText, int nX, int nY, int nSize,
                     float fR, float fG, float fB, float fA) {
    if (!g_bFontInitialized || pcText == NULL) {
        return 0;
    }
    
    int nCurrentX = nX;
    int nCharWidth = (nSize * FONT_CHAR_WIDTH) / FONT_CHAR_HEIGHT + 2;
    
    for (int i = 0; pcText[i] != '\0'; ) {
        int nBytesUsed = 0;
        int nCharIndex = GetCharIndex(&pcText[i], &nBytesUsed);
        
        if (nCharIndex >= 0) {
            RenderCharByIndex(nCharIndex, nCurrentX, nY, nSize, fR, fG, fB, fA);
            nCurrentX += nCharWidth;
            i += nBytesUsed;
        } else if (pcText[i] == ' ') {
            // Пробел
            nCurrentX += nCharWidth / 2;
            i++;
        } else {
            // Неизвестный символ - пропускаем байты
            if (nBytesUsed > 0) {
                i += nBytesUsed;
            } else {
                i++; // Пропускаем один байт
            }
        }
    }
    
    return nCurrentX - nX;
}

/**
 * Получение ширины текста
 */
int Tiggo_GetTextWidth(const char* pcText, int nSize) {
    if (pcText == NULL) {
        return 0;
    }
    
    int nCharWidth = (nSize * FONT_CHAR_WIDTH) / FONT_CHAR_HEIGHT + 2;
    int nWidth = 0;
    
    for (int i = 0; pcText[i] != '\0'; ) {
        int nBytesUsed = 0;
        int nCharIndex = GetCharIndex(&pcText[i], &nBytesUsed);
        
        if (nCharIndex >= 0) {
            nWidth += nCharWidth;
            i += nBytesUsed;
        } else if (pcText[i] == ' ') {
            nWidth += nCharWidth / 2;
            i++;
        } else {
            // Неизвестный символ - пропускаем
            if (nBytesUsed > 0) {
                i += nBytesUsed;
            } else {
                i++;
            }
        }
    }
    
    return nWidth;
}

/**
 * Получение ширины цифры
 */
int Tiggo_GetDigitWidth(int nDigit, int nSize) {
    if (nDigit < 0 || nDigit > 9) {
        return 0;
    }
    
    return (nSize * FONT_CHAR_WIDTH) / FONT_CHAR_HEIGHT + 2;
}

