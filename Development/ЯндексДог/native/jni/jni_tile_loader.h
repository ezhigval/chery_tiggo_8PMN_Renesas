/**
 * jni_tile_loader.h - JNI функции для запроса загрузки тайлов
 */

#ifndef JNI_TILE_LOADER_H
#define JNI_TILE_LOADER_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Запрос загрузки тайла от Java TileLoader
 * Вызывается из нативного кода для запроса загрузки тайла
 * @param nTileX координата X тайла
 * @param nTileY координата Y тайла
 * @param nZoom уровень масштабирования
 */
void Tiggo_RequestTileLoad(int nTileX, int nTileY, int nZoom);

#ifdef __cplusplus
}
#endif

#endif // JNI_TILE_LOADER_H


