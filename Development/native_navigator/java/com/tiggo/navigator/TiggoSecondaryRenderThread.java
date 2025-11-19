/**
 * TiggoSecondaryRenderThread - Отдельный поток для рендеринга второго дисплея
 * Аналог SecondaryRenderThread из TurboDog
 * 
 * Стиль TurboDog:
 * - Отдельный поток для рендеринга
 * - EGL для OpenGL контекста
 * - Использование AddSecondaryWndGL для создания окна
 */
package com.tiggo.navigator;

import android.util.Log;
import android.view.Surface;
import javax.microedition.khronos.egl.EGL10;
import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.egl.EGLContext;
import javax.microedition.khronos.egl.EGLDisplay;
import javax.microedition.khronos.egl.EGLSurface;

/**
 * Отдельный поток для рендеринга второго дисплея (Presentation окна)
 * В стиле TurboDog: SecondaryRenderThread
 */
public class TiggoSecondaryRenderThread extends Thread {
    private static final String TAG = "TiggoSecondaryRender";
    
    // Индекс окна
    private int mIndex;
    
    // Surface для рендеринга
    private Surface mSurface;
    
    // Размеры окна
    private int mWidth;
    private int mHeight;
    
    // Флаги
    private volatile boolean mRunning;
    private volatile boolean mSurfaceCreated;
    private volatile boolean mRenderInitialized;
    
    // EGL для OpenGL контекста (как в TurboDog)
    private EGL10 mEgl;
    private EGLDisplay mEglDisplay;
    private EGLConfig mEglConfig;
    private EGLContext mEglContext;
    private EGLSurface mEglSurface;
    
    // Упрощенный режим (Display 1)
    private boolean mSimplified;
    
    public TiggoSecondaryRenderThread(int width, int height, boolean simplified) {
        super("TiggoSecondaryRenderThread");
        this.mWidth = width;
        this.mHeight = height;
        this.mSimplified = simplified;
        this.mRunning = false;
        this.mSurfaceCreated = false;
        this.mRenderInitialized = false;
        this.mIndex = -1;
        
        Log.i(TAG, "TiggoSecondaryRenderThread created: w=" + width + ", h=" + height + 
                   ", simplified=" + simplified);
    }
    
    /**
     * Установка Surface для рендеринга
     */
    public synchronized void setSurface(Surface surface) {
        this.mSurface = surface;
        this.mSurfaceCreated = (surface != null);
        
        if (mSurfaceCreated) {
            // Создаем окно в нативном коде (как TurboDog)
            createNativeWindow();
        } else {
            // Уничтожаем окно в нативном коде
            destroyNativeWindow();
        }
        
        notifyAll();
    }
    
    /**
     * Создание окна в нативном коде (аналог AddSecondaryWndGL в TurboDog)
     */
    private void createNativeWindow() {
        if (mIndex >= 0) {
            // Окно уже создано
            return;
        }
        
        // Создаем окно в нативном коде
        // В стиле TurboDog: AddSecondaryWndGL(0, 0, width, height, dpi, simplified, ...)
        mIndex = TiggoJavaToJni.AddSecondaryWndGL(0, 0, mWidth, mHeight, 160, 
                                                   mSimplified, 0, 0, 0, 0);
        
        if (mIndex >= 0) {
            Log.i(TAG, "TiggoSecondaryRenderThread():AddSecondaryWndGL(0, 0) index=" + mIndex);
            
            // Создаем вторичный GL контекст
            int result = TiggoJavaToJni.CreateSecondaryGL(mWidth, mHeight, mIndex, 
                                                          mSimplified, 160, 0, 0, 0);
            if (result >= 0) {
                mRenderInitialized = true;
                Log.i(TAG, "TiggoSecondaryRenderThread():RenderGL initialized");
            }
        } else {
            Log.e(TAG, "TiggoSecondaryRenderThread():Failed to create native window");
        }
    }
    
    /**
     * Уничтожение окна в нативном коде
     */
    private void destroyNativeWindow() {
        if (mIndex >= 0) {
            // Уничтожаем окно в нативном коде
            TiggoJavaToJni.DeleteSecondaryWndGL(mIndex);
            mIndex = -1;
            mRenderInitialized = false;
            
            Log.i(TAG, "TiggoSecondaryRenderThread():Native window destroyed");
        }
    }
    
    /**
     * Инициализация EGL контекста (как в TurboDog)
     */
    private boolean initEGL() {
        mEgl = (EGL10) EGLContext.getEGL();
        
        // Получаем EGL Display
        mEglDisplay = mEgl.eglGetDisplay(EGL10.EGL_DEFAULT_DISPLAY);
        if (mEglDisplay == EGL10.EGL_NO_DISPLAY) {
            Log.e(TAG, "eglGetDisplay failed");
            return false;
        }
        
        // Инициализируем EGL
        int[] version = new int[2];
        if (!mEgl.eglInitialize(mEglDisplay, version)) {
            Log.e(TAG, "eglInitialize failed");
            return false;
        }
        
        // Выбираем конфигурацию EGL
        int[] configAttribs = {
            EGL10.EGL_RENDERABLE_TYPE, 4, // EGL_OPENGL_ES3_BIT
            EGL10.EGL_SURFACE_TYPE, EGL10.EGL_WINDOW_BIT,
            EGL10.EGL_BLUE_SIZE, 8,
            EGL10.EGL_GREEN_SIZE, 8,
            EGL10.EGL_RED_SIZE, 8,
            EGL10.EGL_ALPHA_SIZE, 8,
            EGL10.EGL_DEPTH_SIZE, 24,
            EGL10.EGL_STENCIL_SIZE, 8,
            EGL10.EGL_NONE
        };
        
        EGLConfig[] configs = new EGLConfig[1];
        int[] numConfigs = new int[1];
        if (!mEgl.eglChooseConfig(mEglDisplay, configAttribs, configs, 1, numConfigs)) {
            Log.e(TAG, "eglChooseConfig failed");
            return false;
        }
        
        if (numConfigs[0] == 0) {
            Log.e(TAG, "No EGL config found");
            return false;
        }
        
        mEglConfig = configs[0];
        
        // Создаем EGL Context
        int[] contextAttribs = {
            0x3098, 3, // EGL_CONTEXT_CLIENT_VERSION, OpenGL ES 3.0
            EGL10.EGL_NONE
        };
        
        mEglContext = mEgl.eglCreateContext(mEglDisplay, mEglConfig, 
                                            EGL10.EGL_NO_CONTEXT, contextAttribs);
        if (mEglContext == EGL10.EGL_NO_CONTEXT) {
            Log.e(TAG, "eglCreateContext failed");
            return false;
        }
        
        return true;
    }
    
    /**
     * Создание EGL Surface (как в TurboDog)
     */
    private boolean createEGLSurface() {
        if (mSurface == null) {
            Log.e(TAG, "Surface is null");
            return false;
        }
        
        Log.i(TAG, "eglCreateSurface");
        
        try {
            // Создаем EGL Surface из Android Surface
            mEglSurface = mEgl.eglCreateWindowSurface(mEglDisplay, mEglConfig, mSurface, null);
            
            if (mEglSurface == null || mEglSurface == EGL10.EGL_NO_SURFACE) {
                Log.e(TAG, "eglSurface create failed");
                return false;
            }
            
            // Активируем контекст
            if (!mEgl.eglMakeCurrent(mEglDisplay, mEglSurface, mEglSurface, mEglContext)) {
                Log.e(TAG, "eglMakeCurrent failed");
                return false;
            }
            
            return true;
        } catch (Exception e) {
            Log.e(TAG, "Error creating EGL surface", e);
            return false;
        }
    }
    
    /**
     * Уничтожение EGL Surface (как в TurboDog)
     */
    private void destroyEGLSurface() {
        if (mEglSurface == null || mEglSurface == EGL10.EGL_NO_SURFACE) {
            return;
        }
        
        Log.i(TAG, "eglDestroySurface");
        
        // Деактивируем контекст
        mEgl.eglMakeCurrent(mEglDisplay, EGL10.EGL_NO_SURFACE, EGL10.EGL_NO_SURFACE, 
                           EGL10.EGL_NO_CONTEXT);
        
        // Уничтожаем Surface
        if (!mEgl.eglDestroySurface(mEglDisplay, mEglSurface)) {
            Log.e(TAG, "eglDestroySurface failed");
        }
        
        mEglSurface = null;
    }
    
    /**
     * Уничтожение EGL (как в TurboDog)
     */
    private void destroyEGL() {
        Log.i(TAG, "eglDestroy");
        
        destroyEGLSurface();
        
        // Уничтожаем Context
        if (mEglContext != null) {
            mEgl.eglDestroyContext(mEglDisplay, mEglContext);
            mEglContext = null;
        }
        
        // Завершаем EGL
        if (mEglDisplay != null) {
            mEgl.eglTerminate(mEglDisplay);
            mEglDisplay = null;
        }
    }
    
    /**
     * Запуск потока рендеринга
     */
    public void startRender() {
        if (mRunning) {
            return;
        }
        
        mRunning = true;
        start();
        
        Log.i(TAG, "TiggoSecondaryRenderThread started");
    }
    
    /**
     * Остановка потока рендеринга
     */
    public void stopRender() {
        mRunning = false;
        
        // Уведомляем поток о необходимости остановки
        synchronized (this) {
            notifyAll();
        }
        
        try {
            join(1000); // Ждем максимум 1 секунду
        } catch (InterruptedException e) {
            Log.e(TAG, "Error stopping render thread", e);
        }
        
        Log.i(TAG, "TiggoSecondaryRenderThread stopped");
    }
    
    /**
     * Основной цикл рендеринга (как в TurboDog)
     */
    @Override
    public void run() {
        Log.i(TAG, "TiggoSecondaryRenderThread run() started");
        
        // Инициализация EGL
        if (!initEGL()) {
            Log.e(TAG, "Failed to initialize EGL");
            return;
        }
        
        // Ждем создания Surface
        synchronized (this) {
            while (!mSurfaceCreated && mRunning) {
                try {
                    wait();
                } catch (InterruptedException e) {
                    Log.e(TAG, "Interrupted while waiting for surface", e);
                    return;
                }
            }
        }
        
        if (!mRunning) {
            destroyEGL();
            return;
        }
        
        // Создаем EGL Surface
        if (!createEGLSurface()) {
            Log.e(TAG, "Failed to create EGL surface");
            destroyEGL();
            return;
        }
        
        Log.i(TAG, "TiggoSecondaryRenderThread():RenderGL initialized");
        
        // Основной цикл рендеринга
        while (mRunning) {
            synchronized (this) {
                if (!mSurfaceCreated) {
                    // Surface уничтожен, ждем нового
                    try {
                        wait();
                    } catch (InterruptedException e) {
                        break;
                    }
                    continue;
                }
            }
            
            // Рендеринг второго окна (упрощенная карта)
            if (mRenderInitialized && mIndex >= 0) {
                TiggoJavaToJni.RenderSecondaryWndGL(mIndex);
            }
            
            // Swap buffers
            if (mEglSurface != null && mEglSurface != EGL10.EGL_NO_SURFACE) {
                mEgl.eglSwapBuffers(mEglDisplay, mEglSurface);
            }
            
            // Оптимизация: обновляем реже, чем основной дисплей
            // Display 0: 60 FPS
            // Display 1: 30 FPS (реже для экономии ресурсов)
            try {
                Thread.sleep(33); // ~30 FPS
            } catch (InterruptedException e) {
                break;
            }
        }
        
        // Очистка
        destroyEGL();
        destroyNativeWindow();
        
        Log.i(TAG, "TiggoSecondaryRenderThread run() finished");
    }
    
    /**
     * Установка размера окна (как в TurboDog)
     */
    public void setSize(int width, int height, int x, int y, int dpi) {
        synchronized (this) {
            this.mWidth = width;
            this.mHeight = height;
            
            if (mIndex >= 0) {
                TiggoJavaToJni.SetSecondaryWndSize(mIndex, width, height, x, y, dpi, mSimplified);
            }
        }
    }
    
    /**
     * Получение индекса окна
     */
    public int getIndex() {
        return mIndex;
    }
    
    /**
     * Проверка, активен ли рендеринг
     */
    public boolean isRenderInitialized() {
        return mRenderInitialized;
    }
}

