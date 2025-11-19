/**
 * MainActivity - Главная Activity для основного дисплея (Display 0)
 * 
 * Отображает полноценную карту со всеми деталями:
 * - Полная карта с тайлами
 * - POI и события
 * - Детализация карты
 * - Все элементы интерфейса
 */
package com.tiggo.navigator;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.util.Log;
import android.view.MotionEvent;
import android.view.ScaleGestureDetector;
import android.view.Surface;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import com.yandex.mapkit.MapKitFactory;

/**
 * Главная Activity для основного дисплея (Display 0)
 * В стиле TurboDog: WelcomeActivity
 */
public class MainActivity extends Activity implements SurfaceHolder.Callback {
    private static final String TAG = "MainActivity";
    
    // Surface для рендеринга
    private SurfaceView mSurfaceView;
    private SurfaceHolder mSurfaceHolder;
    private Surface mSurface;
    
    // Навигационные компоненты
    private YandexMapKitBridge mYandexBridge;
    private TiggoRenderThread mRenderThread;
    private NavigationUI mNavigationUI;
    
    // Жесты для карты
    private ScaleGestureDetector mScaleDetector;
    private float mLastTouchX = 0;
    private float mLastTouchY = 0;
    private boolean mIsDragging = false;
    
    // Параметры камеры
    private float mCameraLat = 59.804538f;  // Санкт-Петербург (текущее местоположение)
    private float mCameraLon = 30.162479f;
    private float mCameraZoom = 13.0f;
    private float mCameraBearing = 0.0f;
    private float mCameraTilt = 0.0f;
    
    // Константы для расчета перемещения
    private static final float DEGREES_PER_PIXEL = 0.0001f;  // Грубая аппроксимация
    private static final float MIN_ZOOM = 5.0f;
    private static final float MAX_ZOOM = 19.0f;
    
    // Флаги
    private boolean mInitialized = false;
    private boolean mSurfaceCreated = false;
    
    private static final int PERMISSION_REQUEST_LOCATION = 1001;
    private static final int PERMISSION_REQUEST_OVERLAY = 1002;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        Log.d(TAG, "onCreate()");
        
        // Запрашиваем разрешения на геопозицию
        requestLocationPermissions();
        
        // Запрашиваем разрешение на отображение поверх других приложений
        requestOverlayPermission();
        
        // Полноэкранный режим
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                           WindowManager.LayoutParams.FLAG_FULLSCREEN);
        
        // Создаем контейнер для OpenGL и UI
        android.widget.FrameLayout container = new android.widget.FrameLayout(this);
        
        // Создаем SurfaceView для OpenGL рендеринга
        mSurfaceView = new SurfaceView(this);
        mSurfaceHolder = mSurfaceView.getHolder();
        mSurfaceHolder.addCallback(this);
        container.addView(mSurfaceView);
        
        // Создаем NavigationUI поверх OpenGL
        mNavigationUI = new NavigationUI(this);
        android.widget.FrameLayout.LayoutParams uiParams = 
            new android.widget.FrameLayout.LayoutParams(
                android.widget.FrameLayout.LayoutParams.MATCH_PARENT,
                android.widget.FrameLayout.LayoutParams.MATCH_PARENT);
        container.addView(mNavigationUI, uiParams);
        
        // Инициализируем обработчик жестов масштабирования
        mScaleDetector = new ScaleGestureDetector(this, new ScaleGestureDetector.SimpleOnScaleGestureListener() {
            @Override
            public boolean onScale(ScaleGestureDetector detector) {
                float scaleFactor = detector.getScaleFactor();
                mCameraZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, mCameraZoom / scaleFactor));
                updateCamera();
                return true;
            }
        });
        
        // Устанавливаем обработчик касаний для SurfaceView
        mSurfaceView.setOnTouchListener(new View.OnTouchListener() {
            @Override
            public boolean onTouch(View v, MotionEvent event) {
                mScaleDetector.onTouchEvent(event);
                
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        mLastTouchX = event.getX();
                        mLastTouchY = event.getY();
                        mIsDragging = true;
                        return true;
                        
                    case MotionEvent.ACTION_MOVE:
                        if (mIsDragging && !mScaleDetector.isInProgress()) {
                            float deltaX = event.getX() - mLastTouchX;
                            float deltaY = event.getY() - mLastTouchY;
                            
                            // Инвертируем направление: если палец тянет вниз, карта должна двигаться вниз
                            // (то есть latDelta должен быть отрицательным, когда deltaY положительный)
                            // Рассчитываем смещение в градусах (зависит от зума)
                            // Формула: количество пикселей на экране = 256 * 2^(zoom - 20) на 1 градус
                            double metersPerPixel = 156543.03392 * Math.cos(Math.toRadians(mCameraLat)) / Math.pow(2, mCameraZoom);
                            float latDelta = (float)(deltaY * metersPerPixel / 111320.0);  // Инвертировано: убрали минус перед deltaY
                            float lonDelta = (float)(-deltaX * metersPerPixel / (111320.0 * Math.cos(Math.toRadians(mCameraLat))));  // Инвертировано: добавляем минус перед deltaX для инверсии справа налево
                            
                            mCameraLat += latDelta;
                            mCameraLon += lonDelta;
                            
                            // Ограничиваем координаты
                            mCameraLat = Math.max(-85.0f, Math.min(85.0f, mCameraLat));
                            if (mCameraLon > 180.0f) mCameraLon -= 360.0f;
                            if (mCameraLon < -180.0f) mCameraLon += 360.0f;
                            
                            updateCamera();
                            
                            mLastTouchX = event.getX();
                            mLastTouchY = event.getY();
                        }
                        return true;
                        
                    case MotionEvent.ACTION_UP:
                    case MotionEvent.ACTION_CANCEL:
                        mIsDragging = false;
                        return true;
                }
                
                return false;
            }
        });
        
        setContentView(container);
        
        // Инициализируем Yandex MapKit Bridge
        // MapKit уже инициализирован в Application.onCreate()
        mYandexBridge = new YandexMapKitBridge();
        if (!mYandexBridge.initialize(this, null)) {
            Log.e(TAG, "Failed to initialize Yandex MapKit Bridge");
            finish();
            return;
        }
        
        // Инициализируем LocationService для получения GPS координат
        LocationService locationService = LocationService.initialize(this);
        locationService.start();
        
        // Запускаем NavigationService для приборной панели
        try {
            Intent serviceIntent = new Intent(this, NavigationService.class);
            startService(serviceIntent);
            Log.d(TAG, "NavigationService started");
        } catch (Exception e) {
            Log.e(TAG, "Failed to start NavigationService", e);
        }
        
        // Устанавливаем контекст для обратного JNI
        TiggoJniToJava.setContext(this);
        TiggoJniToJava.setNavigationUI(mNavigationUI);
        
        // Инициализация нативного кода (в стиле TurboDog)
        TiggoJavaToJni.OnCreate(false); // false = полноценный режим (Display 0)
        
        // Инициализация движка с размером экрана
        int width = getWindowManager().getDefaultDisplay().getWidth();
        int height = getWindowManager().getDefaultDisplay().getHeight();
        
        if (!TiggoJavaToJni.OnInit(width, height)) {
            Log.e(TAG, "Failed to initialize native engine");
            finish();
            return;
        }
        
        // ВАЖНО: CreateGL() вызывается в surfaceCreated(), когда Surface уже готов
        // Не вызываем здесь, чтобы не закрывать Activity при ошибке
        
        mInitialized = true;
        Log.d(TAG, "MainActivity initialized successfully (waiting for Surface)");
    }
    
    @Override
    protected void onResume() {
        super.onResume();
        Log.d(TAG, "onResume()");
        
        if (mInitialized) {
            TiggoJavaToJni.OnResume();
            
            // Возобновляем получение геопозиции
            LocationService locationService = LocationService.getInstance();
            if (locationService != null && !locationService.isEnabled()) {
                locationService.start();
            }
            
            // Запускаем поток рендеринга
            if (mSurfaceCreated && mRenderThread == null) {
                startRenderThread();
            }
        }
    }
    
    @Override
    protected void onPause() {
        super.onPause();
        Log.d(TAG, "onPause()");
        
        // Останавливаем поток рендеринга
        stopRenderThread();
        
        // Останавливаем получение геопозиции для экономии батареи
        LocationService locationService = LocationService.getInstance();
        if (locationService != null) {
            locationService.stop();
        }
        
        if (mInitialized) {
            TiggoJavaToJni.OnPause();
        }
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        Log.d(TAG, "onDestroy()");
        
        // Останавливаем поток рендеринга
        stopRenderThread();
        
        if (mInitialized) {
            // Уничтожаем OpenGL контекст
            TiggoJavaToJni.DestroyGL();
            
            // Завершение нативного кода
            TiggoJavaToJni.OnDestroy();
        }
        
        // Завершение Yandex Bridge
        if (mYandexBridge != null) {
            mYandexBridge.shutdown();
            mYandexBridge = null;
        }
    }
    
    // ========== SurfaceHolder.Callback ==========
    
    @Override
    public void surfaceCreated(SurfaceHolder holder) {
        Log.d(TAG, "surfaceCreated()");
        mSurfaceCreated = true;
        mSurface = holder.getSurface();
        
        // Создаем OpenGL контекст после создания Surface (полноценный режим)
        if (mInitialized) {
            int result = TiggoJavaToJni.CreateGL(false, true); // false = не упрощенный, true = 3D
            if (result != 0) {
                Log.e(TAG, "Failed to create GL context: " + result);
                // Не закрываем Activity, просто логируем ошибку
                // Render thread все равно запустится и попытается создать EGL контекст
            } else {
                Log.d(TAG, "GL context created successfully");
            }
        }
        
        // Запускаем поток рендеринга, если Activity активна
        if (mInitialized && mRenderThread == null) {
            startRenderThread();
        }
    }
    
    @Override
    public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) {
        Log.d(TAG, "surfaceChanged(): w=" + width + ", h=" + height);
        
        // Устанавливаем размер окна в нативном коде
        if (mInitialized) {
            TiggoJavaToJni.SetWindowSizeGL(width, height);
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
     * Запуск потока рендеринга
     */
    private void startRenderThread() {
        if (mRenderThread != null) {
            Log.w(TAG, "Render thread already exists");
            return;
        }
        
        if (mSurface == null) {
            Log.e(TAG, "Cannot start render thread: Surface is null");
            return;
        }
        
        Log.d(TAG, "Starting render thread with surface: " + mSurface);
        mRenderThread = new TiggoRenderThread(mSurface, false); // false = полноценный режим
        mRenderThread.startRender(); // Используем startRender() вместо start()
        
        Log.d(TAG, "Render thread started");
    }
    
    /**
     * Остановка потока рендеринга
     */
    private void stopRenderThread() {
        if (mRenderThread != null) {
            mRenderThread.stopRender();
            try {
                mRenderThread.join(1000); // Ждем максимум 1 секунду
            } catch (InterruptedException e) {
                Log.e(TAG, "Error stopping render thread", e);
            }
            mRenderThread = null;
            
            Log.d(TAG, "Render thread stopped");
        }
    }
    
    // ========== Camera ==========
    
    /**
     * Обновление камеры карты
     */
    private void updateCamera() {
        if (mInitialized) {
            TiggoJavaToJni.UpdateCamera(mCameraLat, mCameraLon, mCameraZoom, mCameraBearing, mCameraTilt);
        }
    }
    
    /**
     * Установка камеры на указанные координаты
     */
    private void setCamera(float lat, float lon, float zoom) {
        mCameraLat = lat;
        mCameraLon = lon;
        mCameraZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, zoom));
        updateCamera();
    }
    
    // ========== Permissions ==========
    
    /**
     * Запрос разрешений на геопозицию
     */
    private void requestLocationPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) 
                    != PackageManager.PERMISSION_GRANTED ||
                ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) 
                    != PackageManager.PERMISSION_GRANTED) {
                
                ActivityCompat.requestPermissions(this,
                    new String[]{
                        Manifest.permission.ACCESS_FINE_LOCATION,
                        Manifest.permission.ACCESS_COARSE_LOCATION
                    },
                    PERMISSION_REQUEST_LOCATION);
            }
        }
    }
    
    /**
     * Запрос разрешения на отображение поверх других приложений
     * Для создания отдельного плавающего окна Presentation
     */
    private void requestOverlayPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (!Settings.canDrawOverlays(this)) {
                Log.d(TAG, "Requesting overlay permission");
                Intent intent = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:" + getPackageName()));
                startActivityForResult(intent, PERMISSION_REQUEST_OVERLAY);
            } else {
                Log.d(TAG, "Overlay permission already granted");
            }
        }
    }
    
    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        
        if (requestCode == PERMISSION_REQUEST_OVERLAY) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                if (Settings.canDrawOverlays(this)) {
                    Log.d(TAG, "Overlay permission granted");
                } else {
                    Log.w(TAG, "Overlay permission denied");
                }
            }
        }
    }
    
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        
        if (requestCode == PERMISSION_REQUEST_LOCATION) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Log.d(TAG, "Location permission granted");
                // Запускаем LocationService, если разрешение получено
                LocationService locationService = LocationService.getInstance();
                if (locationService != null && !locationService.isEnabled()) {
                    locationService.start();
                }
            } else {
                Log.w(TAG, "Location permission denied");
            }
        }
    }
}

