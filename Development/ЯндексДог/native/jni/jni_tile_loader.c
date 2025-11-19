/**
 * jni_tile_loader.c - JNI функции для запроса загрузки тайлов (в стиле TurboDog)
 * 
 * Этот файл содержит JNI функции для взаимодействия с Java TileLoader
 */

#include <jni.h>
#include <android/log.h>

#define LOG_TAG "TiggoJNI"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Глобальная ссылка на Java TileLoader объект
static jobject g_pJavaTileLoader = NULL;
static JavaVM* g_pJavaVM = NULL;

// Глобальные ссылки на Java класс и метод для вызова TiggoJniToJava.jniCallRequestTile()
static jclass g_pTiggoJniToJavaClass = NULL;
static jmethodID g_pJniCallRequestTileMethod = NULL;

/**
 * Инициализация JNI для загрузчика тайлов
 * Вызывается при создании Java TileLoader
 */
JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TileLoader_nativeInit(JNIEnv* env, jobject thiz) {
    LOGI("TileLoader nativeInit");
    
    // Сохраняем ссылку на Java объект
    g_pJavaTileLoader = (*env)->NewGlobalRef(env, thiz);
    
    // Сохраняем JavaVM для использования в других потоках
    (*env)->GetJavaVM(env, &g_pJavaVM);
    
    // Инициализируем класс и метод для вызова TiggoJniToJava.jniCallRequestTile()
    jclass tiggoJniToJavaClass = (*env)->FindClass(env, "com/tiggo/navigator/TiggoJniToJava");
    if (tiggoJniToJavaClass != NULL) {
        g_pTiggoJniToJavaClass = (*env)->NewGlobalRef(env, tiggoJniToJavaClass);
        g_pJniCallRequestTileMethod = (*env)->GetStaticMethodID(env, tiggoJniToJavaClass,
                                                                 "jniCallRequestTile", "(III)V");
        if (g_pJniCallRequestTileMethod == NULL) {
            LOGE("Failed to find jniCallRequestTile method");
        } else {
            LOGI("jniCallRequestTile method found");
        }
        (*env)->DeleteLocalRef(env, tiggoJniToJavaClass);
    } else {
        LOGE("Failed to find TiggoJniToJava class");
    }
}

/**
 * Запрос загрузки тайла от Java TileLoader
 * Вызывается из нативного кода для запроса загрузки тайла
 */
JNIEXPORT void JNICALL
Tiggo_RequestTileLoad(int nTileX, int nTileY, int nZoom) {
    if (g_pJavaVM == NULL) {
        LOGE("JavaVM is NULL");
        return;
    }
    
    // Проверяем, инициализированы ли класс и метод
    if (g_pTiggoJniToJavaClass == NULL || g_pJniCallRequestTileMethod == NULL) {
        LOGE("TiggoJniToJava class or method not initialized");
        return;
    }
    
    // Получаем JNIEnv для текущего потока
    JNIEnv* env = NULL;
    int nAttachResult = (*g_pJavaVM)->GetEnv(g_pJavaVM, (void**)&env, JNI_VERSION_1_6);
    
    if (nAttachResult == JNI_EDETACHED) {
        // Текущий поток не прикреплен к JVM, прикрепляем его
        nAttachResult = (*g_pJavaVM)->AttachCurrentThread(g_pJavaVM, &env, NULL);
        if (nAttachResult != JNI_OK || env == NULL) {
            LOGE("Failed to attach thread to JVM");
            return;
        }
    } else if (nAttachResult != JNI_OK || env == NULL) {
        LOGE("Failed to get JNIEnv");
        return;
    }
    
    // Вызываем статический метод TiggoJniToJava.jniCallRequestTile()
    (*env)->CallStaticVoidMethod(env, g_pTiggoJniToJavaClass, g_pJniCallRequestTileMethod,
                                 (jint)nTileX, (jint)nTileY, (jint)nZoom);
    
    // Проверяем исключения
    if ((*env)->ExceptionCheck(env)) {
        LOGE("Exception occurred while calling jniCallRequestTile");
        (*env)->ExceptionDescribe(env);
        (*env)->ExceptionClear(env);
        return;
    }
    
    LOGI("Requested tile load: x=%d, y=%d, z=%d", nTileX, nTileY, nZoom);
}

/**
 * Завершение JNI для загрузчика тайлов
 */
JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TileLoader_nativeShutdown(JNIEnv* env, jobject thiz) {
    LOGI("TileLoader nativeShutdown");
    
    if (g_pJavaTileLoader != NULL) {
        (*env)->DeleteGlobalRef(env, g_pJavaTileLoader);
        g_pJavaTileLoader = NULL;
    }
    
    // Освобождаем ссылки на TiggoJniToJava
    if (g_pTiggoJniToJavaClass != NULL) {
        (*env)->DeleteGlobalRef(env, g_pTiggoJniToJavaClass);
        g_pTiggoJniToJavaClass = NULL;
    }
    
    g_pJniCallRequestTileMethod = NULL;
}

