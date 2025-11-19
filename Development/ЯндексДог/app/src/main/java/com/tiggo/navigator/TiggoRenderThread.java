/**
 * TiggoRenderThread - Поток рендеринга для основного дисплея (Display 0)
 * 
 * Рендерит полноценную карту:
 * - Полная детализация карты
 * - POI и события
 * - Все элементы интерфейса
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
 * Поток рендеринга для основного дисплея (Display 0)
 * В стиле TurboDog: RenderThread
 */
public class TiggoRenderThread extends Thread {
    private static final String TAG = "TiggoRenderThread";
    
    // Surface для рендеринга
    private Surface mSurface;
    
    // Флаги
    private volatile boolean mRunning;
    private volatile boolean mSurfaceValid;
    private boolean mSimplified; // false для полноценного режима
    
    // EGL для OpenGL контекста (как в TurboDog)
    private EGL10 mEgl;
    private EGLDisplay mEglDisplay;
    private EGLConfig mEglConfig;
    private EGLContext mEglContext;
    private EGLSurface mEglSurface;
    
    public TiggoRenderThread(Surface surface, boolean simplified) {
        super("TiggoRenderThread");
        this.mSurface = surface;
        this.mSimplified = simplified;
        this.mRunning = false;
        this.mSurfaceValid = (surface != null);
        
        Log.i(TAG, "TiggoRenderThread created: simplified=" + simplified);
    }
    
    /**
     * Установка Surface для рендеринга
     */
    public synchronized void setSurface(Surface surface) {
        this.mSurface = surface;
        this.mSurfaceValid = (surface != null);
        notifyAll();
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
        
        if (!mSurfaceValid) {
            Log.e(TAG, "Surface is not valid");
            return false;
        }
        
        Log.i(TAG, "eglCreateWindowSurface: surface=" + mSurface + ", display=" + mEglDisplay + ", config=" + mEglConfig);
        
        try {
            // Создаем EGL Surface из Android Surface
            mEglSurface = mEgl.eglCreateWindowSurface(mEglDisplay, mEglConfig, mSurface, null);
            
            if (mEglSurface == null || mEglSurface == EGL10.EGL_NO_SURFACE) {
                int error = mEgl.eglGetError();
                Log.e(TAG, "eglCreateWindowSurface failed: error=0x" + Integer.toHexString(error));
                return false;
            }
            
            Log.i(TAG, "EGL surface created: " + mEglSurface);
            
            // Активируем контекст
            if (!mEgl.eglMakeCurrent(mEglDisplay, mEglSurface, mEglSurface, mEglContext)) {
                int error = mEgl.eglGetError();
                Log.e(TAG, "eglMakeCurrent failed: error=0x" + Integer.toHexString(error));
                return false;
            }
            
            Log.i(TAG, "EGL context made current successfully");
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
        
        Log.i(TAG, "TiggoRenderThread started");
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
        
        Log.i(TAG, "TiggoRenderThread stopped");
    }
    
    /**
     * Основной цикл рендеринга (как в TurboDog)
     */
    @Override
    public void run() {
        Log.i(TAG, "TiggoRenderThread run() started");
        
        // Инициализация EGL
        if (!initEGL()) {
            Log.e(TAG, "Failed to initialize EGL");
            return;
        }
        
        Log.i(TAG, "EGL initialized, waiting for surface: mSurfaceValid=" + mSurfaceValid + ", mSurface=" + mSurface);
        
        // Ждем создания Surface
        synchronized (this) {
            while (!mSurfaceValid && mRunning) {
                try {
                    Log.i(TAG, "Waiting for surface to be valid...");
                    wait(1000); // Таймаут 1 секунда, чтобы не ждать вечно
                    if (!mSurfaceValid) {
                        Log.w(TAG, "Surface still not valid after wait");
                    }
                } catch (InterruptedException e) {
                    Log.e(TAG, "Interrupted while waiting for surface", e);
                    destroyEGL();
                    return;
                }
            }
        }
        
        Log.i(TAG, "Surface check: mRunning=" + mRunning + ", mSurfaceValid=" + mSurfaceValid + ", mSurface=" + mSurface);
        
        if (!mRunning) {
            Log.e(TAG, "Thread stopped before creating EGL surface");
            destroyEGL();
            return;
        }
        
        // Создаем EGL Surface
        Log.i(TAG, "Creating EGL surface...");
        if (!createEGLSurface()) {
            Log.e(TAG, "Failed to create EGL surface");
            destroyEGL();
            return;
        }
        
        Log.i(TAG, "EGL surface created successfully");
        
        Log.i(TAG, "TiggoRenderThread():RenderGL initialized");
        
        // Основной цикл рендеринга (60 FPS для Display 0)
        long lastFrameTime = System.currentTimeMillis();
        long frameTime = 1000 / 60; // 60 FPS
        
        while (mRunning) {
            synchronized (this) {
                if (!mSurfaceValid || mSurface == null) {
                    // Surface уничтожен, ждем нового
                    try {
                        wait();
                    } catch (InterruptedException e) {
                        break;
                    }
                    continue;
                }
            }
            
            // Рендеринг основного окна (полноценная карта)
            TiggoJavaToJni.RenderGL();
            
            // Swap buffers
            if (mEglSurface != null && mEglSurface != EGL10.EGL_NO_SURFACE) {
                mEgl.eglSwapBuffers(mEglDisplay, mEglSurface);
            }
            
            // Поддержка 60 FPS
            long currentTime = System.currentTimeMillis();
            long elapsed = currentTime - lastFrameTime;
            if (elapsed < frameTime) {
                try {
                    Thread.sleep(frameTime - elapsed);
                } catch (InterruptedException e) {
                    break;
                }
            }
            lastFrameTime = System.currentTimeMillis();
        }
        
        // Очистка
        destroyEGL();
        
        Log.i(TAG, "TiggoRenderThread run() finished");
    }
}

