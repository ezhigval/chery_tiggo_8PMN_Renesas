/**
 * PresentationActivity - Activity для второго дисплея (Display 1 - приборная панель)
 * 
 * Отображает упрощенную карту:
 * - Только маршрут (полилиния)
 * - Камеры скорости
 * - Дорожные события
 * - Минимальная детализация карты
 */
package com.tiggo.navigator;

import android.app.Presentation;
import android.content.Context;
import android.os.Bundle;
import android.util.Log;
import android.view.Display;
import android.view.Surface;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.Window;
import android.view.WindowManager;
import com.yandex.mapkit.MapKitFactory;

/**
 * Presentation Activity для второго дисплея (Display 1 - приборная панель)
 * В стиле TurboDog: SecondaryRenderThread
 * 
 * Использует Android Presentation API для вывода на второй дисплей
 */
public class PresentationActivity extends Presentation implements SurfaceHolder.Callback {
    private static final String TAG = "PresentationActivity";
    
    // Surface для рендеринга
    private SurfaceView mSurfaceView;
    private SurfaceHolder mSurfaceHolder;
    private Surface mSurface;
    
    // Поток рендеринга для второго дисплея
    private TiggoSecondaryRenderThread mRenderThread;
    
    // Флаги
    private boolean mInitialized = false;
    private boolean mSurfaceCreated = false;
    private int mWindowIndex = -1;
    
    // Размеры дисплея
    private int mWidth;
    private int mHeight;
    private int mDpi;
    
    public PresentationActivity(Context outerContext, Display display) {
        super(outerContext, display);
        
        // Получаем параметры дисплея
        android.util.DisplayMetrics metrics = new android.util.DisplayMetrics();
        display.getMetrics(metrics);
        
        mWidth = metrics.widthPixels;
        mHeight = metrics.heightPixels;
        mDpi = (int) metrics.density * 160;
        
        Log.d(TAG, "PresentationActivity created: w=" + mWidth + ", h=" + mHeight + ", dpi=" + mDpi);
    }
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        Log.d(TAG, "onCreate()");
        
        // Настраиваем окно Presentation как отдельное плавающее окно
        // Это позволяет отображать его поверх других приложений
        Window window = getWindow();
        if (window != null) {
            WindowManager.LayoutParams params = window.getAttributes();
            
            // Проверяем разрешение на отображение поверх других приложений
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.M) {
                if (android.provider.Settings.canDrawOverlays(getContext())) {
                    // Используем TYPE_APPLICATION_OVERLAY для отдельного плавающего окна
                    params.type = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY;
                    Log.d(TAG, "Using TYPE_APPLICATION_OVERLAY for floating window");
                } else {
                    // Если разрешение не получено, используем стандартный тип
                    params.type = WindowManager.LayoutParams.TYPE_PRIVATE_PRESENTATION;
                    Log.w(TAG, "Overlay permission not granted, using TYPE_PRIVATE_PRESENTATION");
                }
            } else {
                params.type = WindowManager.LayoutParams.TYPE_SYSTEM_ALERT;
            }
            
            // Позиционируем окно (опционально, можно разместить где угодно)
            params.x = 0;
            params.y = 0;
            params.width = mWidth;
            params.height = mHeight;
            
            // Флаги для плавающего окна
            params.flags = WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL |
                          WindowManager.LayoutParams.FLAG_WATCH_OUTSIDE_TOUCH |
                          WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN |
                          WindowManager.LayoutParams.FLAG_HARDWARE_ACCELERATED;
            
            window.setAttributes(params);
            
            // Убираем заголовок и делаем полноэкранным
            window.requestFeature(Window.FEATURE_NO_TITLE);
            window.setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                          WindowManager.LayoutParams.FLAG_FULLSCREEN);
        }
        
        // Создаем SurfaceView для OpenGL рендеринга
        mSurfaceView = new SurfaceView(getContext());
        mSurfaceHolder = mSurfaceView.getHolder();
        mSurfaceHolder.addCallback(this);
        
        setContentView(mSurfaceView);
        
        // Инициализация нативного кода для второго окна (упрощенный режим)
        TiggoJavaToJni.OnCreate(true); // true = упрощенный режим (Display 1)
        
        // Создаем вторичный OpenGL контекст (упрощенный режим)
        mWindowIndex = TiggoJavaToJni.CreateSecondaryGL(mWidth, mHeight, -1, 
                                                         true, // true = упрощенный режим
                                                         mDpi, 0, 0, 0);
        
        if (mWindowIndex < 0) {
            Log.e(TAG, "Failed to create secondary GL context");
            return;
        }
        
        Log.d(TAG, "Secondary GL context created: index=" + mWindowIndex);
        
        mInitialized = true;
    }
    
    @Override
    protected void onStart() {
        super.onStart();
        Log.d(TAG, "onStart()");
    }
    
    @Override
    protected void onStop() {
        super.onStop();
        Log.d(TAG, "onStop()");
        
        // Останавливаем поток рендеринга
        stopRenderThread();
        
        // Presentation не имеет onDestroy(), поэтому очистку делаем в onStop()
        if (mInitialized && mWindowIndex >= 0) {
            // Удаляем второстепенное окно
            TiggoJavaToJni.DeleteSecondaryWndGL(mWindowIndex);
            mWindowIndex = -1;
        }
        
        if (mInitialized) {
            // Завершение нативного кода
            TiggoJavaToJni.OnDestroy();
            mInitialized = false;
        }
    }
    
    // ========== SurfaceHolder.Callback ==========
    
    @Override
    public void surfaceCreated(SurfaceHolder holder) {
        Log.d(TAG, "surfaceCreated()");
        mSurfaceCreated = true;
        mSurface = holder.getSurface();
        
        // Запускаем поток рендеринга для второго дисплея
        if (mInitialized && mRenderThread == null) {
            startRenderThread();
        }
    }
    
    @Override
    public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) {
        Log.d(TAG, "surfaceChanged(): w=" + width + ", h=" + height);
        
        // Обновляем размеры
        mWidth = width;
        mHeight = height;
        
        // Устанавливаем размер второго окна в нативном коде
        if (mInitialized && mWindowIndex >= 0) {
            TiggoJavaToJni.SetSecondaryWndSize(mWindowIndex, width, height, 0, 0, mDpi, true);
        }
    }
    
    @Override
    public void surfaceDestroyed(SurfaceHolder holder) {
        Log.d(TAG, "surfaceDestroyed()");
        mSurfaceCreated = false;
        mSurface = null;
        
        // Останавливаем поток рендеринга
        stopRenderThread();
    }
    
    // ========== Render Thread ==========
    
    /**
     * Запуск потока рендеринга для второго дисплея
     */
    private void startRenderThread() {
        if (mRenderThread != null) {
            return;
        }
        
        // Создаем поток рендеринга для второго дисплея (упрощенный режим)
        mRenderThread = new TiggoSecondaryRenderThread(mWidth, mHeight, true); // true = упрощенный
        mRenderThread.setSurface(mSurface);
        mRenderThread.startRender();
        
        Log.d(TAG, "Secondary render thread started: index=" + mWindowIndex);
    }
    
    /**
     * Остановка потока рендеринга
     */
    private void stopRenderThread() {
        if (mRenderThread != null) {
            mRenderThread.stopRender();
            mRenderThread = null;
            
            Log.d(TAG, "Secondary render thread stopped");
        }
    }
    
    /**
     * Получение индекса окна
     */
    public int getWindowIndex() {
        return mWindowIndex;
    }
}

