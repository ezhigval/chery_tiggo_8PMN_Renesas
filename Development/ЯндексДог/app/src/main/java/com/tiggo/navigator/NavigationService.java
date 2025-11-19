/**
 * NavigationService - Сервис для управления навигацией
 * 
 * Управляет:
 * - Инициализацией Yandex MapKit Bridge
 * - Созданием Presentation окна для второго дисплея
 * - Связью между компонентами
 */
package com.tiggo.navigator;

import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.hardware.display.DisplayManager;
import android.os.IBinder;
import android.util.Log;
import android.view.Display;
import com.yandex.mapkit.MapKitFactory;

/**
 * Сервис навигации
 * Управляет инициализацией и связью между компонентами
 */
public class NavigationService extends Service {
    private static final String TAG = "NavigationService";
    
    // Компоненты
    private YandexMapKitBridge mYandexBridge;
    private PresentationActivity mPresentation;
    private Display[] mDisplays;
    
    // Флаги
    private boolean mInitialized = false;
    
    @Override
    public void onCreate() {
        super.onCreate();
        Log.d(TAG, "onCreate()");
        
        // Инициализация Yandex MapKit Bridge
        mYandexBridge = new YandexMapKitBridge();
        if (!mYandexBridge.initialize(this, null)) {
            Log.e(TAG, "Failed to initialize Yandex MapKit Bridge");
            return;
        }
        
        // Устанавливаем контекст для обратного JNI
        TiggoJniToJava.setContext(this);
        
        // Находим второй дисплей (Display 1 - приборная панель)
        // В TurboDog используется displays[1] - второй элемент массива
        DisplayManager displayManager = (DisplayManager) getSystemService(Context.DISPLAY_SERVICE);
        if (displayManager != null) {
            mDisplays = displayManager.getDisplays();
            
            Log.d(TAG, "Found " + mDisplays.length + " displays");
            for (Display d : mDisplays) {
                Log.d(TAG, "Display: id=" + d.getDisplayId() + ", name=" + d.getName());
            }
            
            // Используем displays[1] как в TurboDog (второй дисплей)
            if (mDisplays != null && mDisplays.length > 1) {
                Display secondaryDisplay = mDisplays[1]; // Второй элемент массива (как в TurboDog)
                Log.d(TAG, "Using secondary display: id=" + secondaryDisplay.getDisplayId() + ", name=" + secondaryDisplay.getName());
                
                // Создаем Presentation окно для второго дисплея
                createPresentation(secondaryDisplay);
            } else {
                Log.w(TAG, "Secondary display not found (only " + (mDisplays != null ? mDisplays.length : 0) + " displays)");
            }
        }
        
        mInitialized = true;
        Log.d(TAG, "NavigationService initialized");
    }
    
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.d(TAG, "onStartCommand()");
        return START_STICKY; // Перезапускается после завершения
    }
    
    @Override
    public void onDestroy() {
        super.onDestroy();
        Log.d(TAG, "onDestroy()");
        
        // Закрываем Presentation окно
        if (mPresentation != null) {
            mPresentation.dismiss();
            mPresentation = null;
        }
        
        // Завершение Yandex Bridge
        if (mYandexBridge != null) {
            mYandexBridge.shutdown();
            mYandexBridge = null;
        }
        
        mInitialized = false;
    }
    
    @Override
    public IBinder onBind(Intent intent) {
        return null; // Не используется
    }
    
    /**
     * Создание Presentation окна для второго дисплея
     */
    private void createPresentation(Display display) {
        if (mPresentation != null) {
            Log.w(TAG, "Presentation already exists, skipping creation");
            return;
        }
        
        try {
            Log.d(TAG, "Creating Presentation for display: id=" + display.getDisplayId() + ", name=" + display.getName());
            mPresentation = new PresentationActivity(this, display);
            
            // Устанавливаем setCancelable(false) как в TurboDog - чтобы нельзя было закрыть
            mPresentation.setCancelable(false);
            
            // Показываем Presentation
            mPresentation.show();
            
            Log.d(TAG, "Presentation window created and shown for display: " + display.getDisplayId());
        } catch (Exception e) {
            Log.e(TAG, "Failed to create presentation window", e);
            e.printStackTrace();
            mPresentation = null;
        }
    }
    
    /**
     * Получение Yandex Bridge
     */
    public YandexMapKitBridge getYandexBridge() {
        return mYandexBridge;
    }
    
    /**
     * Получение Presentation окна
     */
    public PresentationActivity getPresentation() {
        return mPresentation;
    }
    
    /**
     * Проверка, инициализирован ли сервис
     */
    public boolean isInitialized() {
        return mInitialized;
    }
}

