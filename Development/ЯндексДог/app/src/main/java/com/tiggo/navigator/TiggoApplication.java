/**
 * TiggoApplication - Application класс для инициализации Yandex MapKit
 * 
 * Согласно документации Yandex MapKit, инициализация должна происходить
 * в Application.onCreate() перед setContentView() в Activity
 */
package com.tiggo.navigator;

import android.app.Application;
import android.util.Log;
import com.yandex.mapkit.MapKitFactory;

/**
 * Application класс для навигатора Tiggo
 * В стиле TurboDog: TurboDogApplication
 */
public class TiggoApplication extends Application {
    private static final String TAG = "TiggoApplication";
    
    @Override
    public void onCreate() {
        super.onCreate();
        
        Log.d(TAG, "TiggoApplication onCreate()");
        
        // Инициализация Yandex MapKit
        // API ключ будет загружен из AndroidManifest.xml (meta-data)
        // или из файла через ApiKeyManager
        String apiKey = ApiKeyManager.getApiKey(this);
        
        if (apiKey != null && !apiKey.isEmpty()) {
            // Инициализируем MapKit с API ключом
            MapKitFactory.setApiKey(apiKey);
            // Инициализируем MapKitFactory (создает singleton)
            MapKitFactory.initialize(this);
            Log.d(TAG, "MapKit initialized with API key");
        } else {
            Log.e(TAG, "Failed to initialize MapKit: API key is null or empty");
        }
        
        // После setApiKey() и initialize() MapKitFactory.getInstance() можно вызывать из любого места
    }
    
    @Override
    public void onTerminate() {
        super.onTerminate();
        Log.d(TAG, "TiggoApplication onTerminate()");
    }
}

