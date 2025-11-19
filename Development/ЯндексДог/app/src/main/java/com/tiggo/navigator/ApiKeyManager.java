/**
 * ApiKeyManager - Утилита для загрузки API ключа Yandex MapKit
 * 
 * Загружает API ключ из файла config/api_key.txt
 */
package com.tiggo.navigator;

import android.content.Context;
import android.util.Log;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;

/**
 * Менеджер для загрузки API ключа Yandex MapKit
 */
public class ApiKeyManager {
    private static final String TAG = "ApiKeyManager";
    
    // Путь к файлу с API ключом в assets или resources
    private static final String API_KEY_FILE_PATH = "config/api_key.txt";
    
    // Кешированный API ключ
    private static String sCachedApiKey = null;
    
    /**
     * Загрузка API ключа из файла
     * 
     * @param context контекст приложения
     * @return API ключ или null при ошибке
     */
    public static String loadApiKey(Context context) {
        // Используем кеш, если ключ уже загружен
        if (sCachedApiKey != null) {
            return sCachedApiKey;
        }
        
        try {
            // Пробуем загрузить из assets
            InputStream inputStream = context.getAssets().open(API_KEY_FILE_PATH);
            BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream));
            
            String apiKey = reader.readLine();
            reader.close();
            inputStream.close();
            
            if (apiKey != null && !apiKey.trim().isEmpty()) {
                // Убираем пробелы и переносы строк
                apiKey = apiKey.trim();
                sCachedApiKey = apiKey;
                Log.d(TAG, "API key loaded successfully from assets");
                return apiKey;
            }
        } catch (IOException e) {
            Log.w(TAG, "Failed to load API key from assets: " + e.getMessage());
        }
        
        // Если не получилось загрузить из assets, пробуем из resources
        try {
            // Читаем из raw ресурса (если файл добавлен в res/raw/)
            // int resourceId = context.getResources().getIdentifier("api_key", "raw", context.getPackageName());
            // InputStream inputStream = context.getResources().openRawResource(resourceId);
            // ...
        } catch (Exception e) {
            Log.w(TAG, "Failed to load API key from resources: " + e.getMessage());
        }
        
        // Fallback: используем хардкод (только для разработки!)
        // ⚠️ ВНИМАНИЕ: Не использовать в production!
        Log.w(TAG, "Using hardcoded API key (development only!)");
        sCachedApiKey = "c75cd846-c6de-425a-b974-41917fec5071";
        return sCachedApiKey;
    }
    
    /**
     * Получение API ключа (кешированная версия)
     * 
     * @param context контекст приложения
     * @return API ключ
     */
    public static String getApiKey(Context context) {
        if (sCachedApiKey == null) {
            return loadApiKey(context);
        }
        return sCachedApiKey;
    }
    
    /**
     * Сброс кеша API ключа
     */
    public static void clearCache() {
        sCachedApiKey = null;
    }
}

