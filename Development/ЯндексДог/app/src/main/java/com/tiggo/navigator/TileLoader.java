/**
 * TileLoader - Загрузка тайлов карты от Yandex MapKit
 * 
 * Этот класс загружает тайлы карты через Yandex MapKit API
 * и передает их в нативный код для рендеринга
 */
package com.tiggo.navigator;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.util.Log;
import com.yandex.mapkit.MapKit;
import com.yandex.mapkit.MapKitFactory;
import com.yandex.mapkit.map.CameraPosition;
// TODO: MapType и TileProvider могут быть недоступны в lite версии
// import com.yandex.mapkit.map.MapType;
// import com.yandex.mapkit.tiles.TileProvider;
// import com.yandex.mapkit.tiles.TileUrlProvider;
// import com.yandex.mapkit.tiles.UrlProvider;
// import com.yandex.mapkit.tiles.UrlProviderType;

import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Загрузчик тайлов карты от Yandex MapKit
 */
public class TileLoader {
    private static final String TAG = "TileLoader";
    
    static {
        System.loadLibrary("tiggo_navigator");
    }
    
    // Пул потоков для асинхронной загрузки тайлов
    private ExecutorService mTileLoaderExecutor;
    
    // TODO: TileProvider недоступен в lite версии
    // private TileProvider mTileProvider;
    
    // Callback для загруженных тайлов
    private TileLoadCallback mCallback;
    
    // Флаги
    private boolean mInitialized = false;
    
    // Native методы
    private native void nativeInit();
    private native void nativeShutdown();
    
    /**
     * Инициализация загрузчика тайлов
     */
    public boolean initialize() {
        if (mInitialized) {
            return true;
        }
        
        try {
            // Создаем пул потоков для загрузки тайлов (до 4 потоков)
            mTileLoaderExecutor = Executors.newFixedThreadPool(4);
            
            // TODO: TileProvider недоступен в lite версии MapKit
            // Используем прямой HTTP загрузку тайлов (реализовано в loadTileDirect)
            // MapKit mapKit = MapKitFactory.getInstance();
            // if (mapKit != null) {
            //     mTileProvider = mapKit.createTileProvider(MapType.VECTOR);
            // }
            
            mInitialized = true;
            
            // Инициализация нативного кода
            nativeInit();
            
            Log.d(TAG, "TileLoader initialized");
            return true;
        } catch (Exception e) {
            Log.e(TAG, "Failed to initialize TileLoader", e);
            return false;
        }
    }
    
    /**
     * Загрузка тайла от Yandex
     * 
     * @param tileX координата X тайла
     * @param tileY координата Y тайла
     * @param zoom уровень масштабирования
     * @param callback callback для передачи загруженного тайла
     */
    public void loadTile(int tileX, int tileY, int zoom, TileLoadCallback callback) {
        if (!mInitialized || callback == null) {
            return;
        }
        
        // Загружаем тайл асинхронно
        mTileLoaderExecutor.execute(new TileLoadTask(tileX, tileY, zoom, callback));
    }
    
    /**
     * Загрузка тайла напрямую через HTTP URL (альтернативный способ)
     * 
     * @param tileX координата X тайла
     * @param tileY координата Y тайла
     * @param zoom уровень масштабирования
     * @param callback callback для передачи загруженного тайла (может быть null, тогда используется mCallback)
     */
    public void loadTileDirect(int tileX, int tileY, int zoom, TileLoadCallback callback) {
        if (!mInitialized) {
            return;
        }
        
        // Используем переданный callback или стандартный
        TileLoadCallback actualCallback = callback != null ? callback : mCallback;
        
        if (actualCallback == null) {
            Log.w(TAG, "No callback set for tile load");
            return;
        }
        
        // Загружаем тайл асинхронно через HTTP
        mTileLoaderExecutor.execute(new TileLoadDirectTask(tileX, tileY, zoom, actualCallback));
    }
    
    /**
     * Установка callback для загруженных тайлов
     */
    public void setCallback(TileLoadCallback callback) {
        this.mCallback = callback;
    }
    
    /**
     * Завершение загрузчика тайлов
     */
    public void shutdown() {
        if (mTileLoaderExecutor != null) {
            mTileLoaderExecutor.shutdown();
            mTileLoaderExecutor = null;
        }
        
        // Завершение нативного кода
        if (mInitialized) {
            nativeShutdown();
        }
        
        mCallback = null;
        mInitialized = false;
        Log.d(TAG, "TileLoader shutdown");
    }
    
    /**
     * Callback для загруженного тайла
     */
    public interface TileLoadCallback {
        /**
         * Вызывается при успешной загрузке тайла
         * 
         * @param tileX координата X тайла
         * @param tileY координата Y тайла
         * @param zoom уровень масштабирования
         * @param bitmap загруженное изображение тайла
         */
        void onTileLoaded(int tileX, int tileY, int zoom, Bitmap bitmap);
        
        /**
         * Вызывается при ошибке загрузки тайла
         * 
         * @param tileX координата X тайла
         * @param tileY координата Y тайла
         * @param zoom уровень масштабирования
         * @param error ошибка загрузки
         */
        void onTileLoadError(int tileX, int tileY, int zoom, Exception error);
    }
    
    /**
     * Задача загрузки тайла через Tile Provider
     */
    private class TileLoadTask implements Runnable {
        private final int mTileX;
        private final int mTileY;
        private final int mZoom;
        private final TileLoadCallback mCallback;
        
        public TileLoadTask(int tileX, int tileY, int zoom, TileLoadCallback callback) {
            this.mTileX = tileX;
            this.mTileY = tileY;
            this.mZoom = zoom;
            this.mCallback = callback;
        }
        
        @Override
        public void run() {
            try {
                // TODO: TileProvider недоступен в lite версии, используем прямой HTTP загрузку
                    loadTileDirect(mTileX, mTileY, mZoom, mCallback);
            } catch (Exception e) {
                Log.e(TAG, "Error loading tile", e);
                if (mCallback != null) {
                    mCallback.onTileLoadError(mTileX, mTileY, mZoom, e);
                }
            }
        }
    }
    
    /**
     * Задача прямой загрузки тайла через HTTP
     */
    private class TileLoadDirectTask implements Runnable {
        private final int mTileX;
        private final int mTileY;
        private final int mZoom;
        private final TileLoadCallback mCallback;
        
        public TileLoadDirectTask(int tileX, int tileY, int zoom, TileLoadCallback callback) {
            this.mTileX = tileX;
            this.mTileY = tileY;
            this.mZoom = zoom;
            this.mCallback = callback;
        }
        
        @Override
        public void run() {
            InputStream inputStream = null;
            HttpURLConnection connection = null;
            
            try {
                // Формируем URL тайла Yandex Maps
                // Формат: https://core-renderer-tiles.maps.yandex.net/tiles?l=map&x={x}&y={y}&z={z}
                String tileUrl = String.format(
                    "https://core-renderer-tiles.maps.yandex.net/tiles?l=map&x=%d&y=%d&z=%d",
                    mTileX, mTileY, mZoom
                );
                
                Log.d(TAG, "Loading tile: " + tileUrl);
                
                // Открываем HTTP соединение
                URL url = new URL(tileUrl);
                connection = (HttpURLConnection) url.openConnection();
                connection.setConnectTimeout(5000); // 5 секунд таймаут
                connection.setReadTimeout(5000);
                connection.setRequestMethod("GET");
                
                // Загружаем изображение
                inputStream = connection.getInputStream();
                Bitmap bitmap = BitmapFactory.decodeStream(inputStream);
                
                if (bitmap != null) {
                    Log.d(TAG, "Tile loaded successfully: x=" + mTileX + ", y=" + mTileY + ", z=" + mZoom + 
                               ", size=" + bitmap.getWidth() + "x" + bitmap.getHeight());
                    
                    // Вызываем callback с загруженным тайлом
                    if (mCallback != null) {
                        mCallback.onTileLoaded(mTileX, mTileY, mZoom, bitmap);
                    }
                } else {
                    throw new IOException("Failed to decode tile bitmap");
                }
                
            } catch (Exception e) {
                Log.e(TAG, "Error loading tile from URL", e);
                
                if (mCallback != null) {
                    mCallback.onTileLoadError(mTileX, mTileY, mZoom, e);
                }
            } finally {
                // Закрываем соединение
                if (inputStream != null) {
                    try {
                        inputStream.close();
                    } catch (IOException e) {
                        // Игнорируем
                    }
                }
                if (connection != null) {
                    connection.disconnect();
                }
            }
        }
    }
}

