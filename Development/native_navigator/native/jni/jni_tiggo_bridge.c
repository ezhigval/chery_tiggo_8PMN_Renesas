/**
 * jni_tiggo_bridge.c - JNI слой для TiggoNavigator (в стиле TurboDog)
 * 
 * Стиль TurboDog:
 * - Префиксы функций
 * - Венгерская нотация
 * - C код (не C++)
 */

#include <jni.h>
#include <android/log.h>
#include <string.h>
#include <stdlib.h>

#include "../core/tiggo_engine.h"
#include "../render/render_gl.h"

#define LOG_TAG "TiggoJNI"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Глобальный указатель на движок
static CTiggoEngine* g_pTiggoEngine = NULL;

// ========== OpenGL функции (в стиле TurboDog) ==========

JNIEXPORT jint JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_CreateGL(JNIEnv* env, jclass clazz,
                                                  jboolean simplified, jboolean enable3D) {
    LOGI("CreateGL: simplified=%d, enable3D=%d", simplified, enable3D);
    
    // Создаем движок, если еще не создан
    if (g_pTiggoEngine == NULL) {
        g_pTiggoEngine = Tiggo_CreateEngine();
        if (g_pTiggoEngine == NULL) {
            LOGE("Failed to create TiggoEngine");
            return -1;
        }
        
        if (!Tiggo_Initialize(g_pTiggoEngine)) {
            LOGE("Failed to initialize TiggoEngine");
            Tiggo_DestroyEngine(g_pTiggoEngine);
            g_pTiggoEngine = NULL;
            return -1;
        }
    }
    
    // Создаем OpenGL контекст
    BOOL bSimplified = (simplified == JNI_TRUE);
    BOOL bEnable3D = (enable3D == JNI_TRUE);
    
    if (!Tiggo_CreateGL(g_pTiggoEngine, bSimplified, bEnable3D)) {
        LOGE("Failed to create GL context");
        return -1;
    }
    
    LOGI("GL context created successfully");
    return 0;
}

JNIEXPORT jint JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_CreateSecondaryGL(JNIEnv* env, jclass clazz,
                                                           jint width, jint height, jint index,
                                                           jboolean simplified, jint dpi,
                                                           jint format, jint flags, jint additionalFlags) {
    LOGI("CreateSecondaryGL: w=%d, h=%d, index=%d, simplified=%d", width, height, index, simplified);
    
    if (g_pTiggoEngine == NULL) {
        LOGE("TiggoEngine not initialized");
        return -1;
    }
    
    BOOL bSimplified = (simplified == JNI_TRUE);
    
    int nIndex = Tiggo_CreateSecondaryGL(g_pTiggoEngine, width, height, index, bSimplified,
                                        dpi, format, flags, additionalFlags);
    
    if (nIndex < 0) {
        LOGE("Failed to create secondary GL context");
        return -1;
    }
    
    LOGI("Secondary GL context created: index=%d", nIndex);
    return nIndex;
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_RenderGL(JNIEnv* env, jclass clazz) {
    if (g_pTiggoEngine == NULL) {
        return;
    }
    
    Tiggo_RenderGL(g_pTiggoEngine);
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_RenderSecondaryWndGL(JNIEnv* env, jclass clazz, jint index) {
    if (g_pTiggoEngine == NULL) {
        return;
    }
    
    Tiggo_RenderSecondaryWndGL(g_pTiggoEngine, index);
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_DestroyGL(JNIEnv* env, jclass clazz) {
    LOGI("DestroyGL");
    
    if (g_pTiggoEngine != NULL) {
        Tiggo_DestroyGL(g_pTiggoEngine);
    }
}

JNIEXPORT jint JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_AddSecondaryWndGL(JNIEnv* env, jclass clazz,
                                                           jint x, jint y, jint width, jint height,
                                                           jint dpi, jboolean simplified,
                                                           jint format, jint flags, jint additionalFlags,
                                                           jint reserved) {
    LOGI("AddSecondaryWndGL: x=%d, y=%d, w=%d, h=%d, simplified=%d", x, y, width, height, simplified);
    
    if (g_pTiggoEngine == NULL) {
        LOGE("TiggoEngine not initialized");
        return -1;
    }
    
    BOOL bSimplified = (simplified == JNI_TRUE);
    
    int nIndex = Tiggo_AddSecondaryWndGL(g_pTiggoEngine, x, y, width, height, dpi, bSimplified,
                                         format, flags, additionalFlags, reserved);
    
    if (nIndex < 0) {
        LOGE("Failed to add secondary window");
        return -1;
    }
    
    LOGI("Secondary window added: index=%d", nIndex);
    return nIndex;
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_DeleteSecondaryWndGL(JNIEnv* env, jclass clazz, jint index) {
    LOGI("DeleteSecondaryWndGL: index=%d", index);
    
    if (g_pTiggoEngine != NULL) {
        Tiggo_DeleteSecondaryWndGL(g_pTiggoEngine, index);
    }
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_SetSecondaryWndSize(JNIEnv* env, jclass clazz,
                                                             jint index, jint width, jint height,
                                                             jint x, jint y, jint dpi, jboolean simplified) {
    if (g_pTiggoEngine != NULL) {
        BOOL bSimplified = (simplified == JNI_TRUE);
        Tiggo_SetSecondaryWndSize(g_pTiggoEngine, index, width, height, x, y, dpi, bSimplified);
    }
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_SetWindowSizeGL(JNIEnv* env, jclass clazz,
                                                         jint width, jint height) {
    if (g_pTiggoEngine != NULL) {
        Tiggo_SetWindowSizeGL(g_pTiggoEngine, width, height);
    }
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_CancelRenderGL(JNIEnv* env, jclass clazz) {
    if (g_pTiggoEngine != NULL) {
        Tiggo_CancelRenderGL(g_pTiggoEngine);
    }
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_SetDisplayMetricsGL(JNIEnv* env, jclass clazz, jint dpi) {
    if (g_pTiggoEngine != NULL) {
        Tiggo_SetDisplayMetricsGL(g_pTiggoEngine, dpi);
    }
}

// ========== Lifecycle функции ==========

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_OnCreate(JNIEnv* env, jclass clazz, jboolean simplified) {
    LOGI("OnCreate: simplified=%d", simplified);
    
    if (g_pTiggoEngine == NULL) {
        g_pTiggoEngine = Tiggo_CreateEngine();
        if (g_pTiggoEngine != NULL) {
            Tiggo_Initialize(g_pTiggoEngine);
        }
    }
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_OnDestroy(JNIEnv* env, jclass clazz) {
    LOGI("OnDestroy");
    
    if (g_pTiggoEngine != NULL) {
        Tiggo_Shutdown(g_pTiggoEngine);
        Tiggo_DestroyEngine(g_pTiggoEngine);
        g_pTiggoEngine = NULL;
    }
}

JNIEXPORT jboolean JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_OnInit(JNIEnv* env, jclass clazz, jint width, jint height) {
    LOGI("OnInit: w=%d, h=%d", width, height);
    
    if (g_pTiggoEngine == NULL) {
        return JNI_FALSE;
    }
    
    return Tiggo_OnInit(g_pTiggoEngine, width, height) ? JNI_TRUE : JNI_FALSE;
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_OnPause(JNIEnv* env, jclass clazz) {
    if (g_pTiggoEngine != NULL) {
        Tiggo_OnPause(g_pTiggoEngine);
    }
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_OnResume(JNIEnv* env, jclass clazz) {
    if (g_pTiggoEngine != NULL) {
        Tiggo_OnResume(g_pTiggoEngine);
    }
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_Finalized(JNIEnv* env, jclass clazz) {
    LOGI("Finalized");
    
    if (g_pTiggoEngine != NULL) {
        Tiggo_Shutdown(g_pTiggoEngine);
        Tiggo_DestroyEngine(g_pTiggoEngine);
        g_pTiggoEngine = NULL;
    }
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_SetAppInBackground(JNIEnv* env, jclass clazz, jboolean inBackground) {
    if (g_pTiggoEngine != NULL) {
        BOOL bInBackground = (inBackground == JNI_TRUE);
        Tiggo_SetAppInBackground(g_pTiggoEngine, bInBackground);
    }
}

// ========== GPS/IMU функции ==========

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_AstrobGPSPostNMEA(JNIEnv* env, jclass clazz,
                                                           jbyteArray nmeaData, jint length) {
    if (g_pTiggoEngine == NULL || nmeaData == NULL) {
        return;
    }
    
    jbyte* pData = (*env)->GetByteArrayElements(env, nmeaData, NULL);
    if (pData != NULL) {
        Tiggo_AstrobGPSPostNMEA(g_pTiggoEngine, (const unsigned char*)pData, length);
        (*env)->ReleaseByteArrayElements(env, nmeaData, pData, JNI_ABORT);
    }
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_AstrobDRPostIMU(JNIEnv* env, jclass clazz,
                                                         jbyteArray imuData, jint length, jdouble timestamp) {
    if (g_pTiggoEngine == NULL || imuData == NULL) {
        return;
    }
    
    jbyte* pData = (*env)->GetByteArrayElements(env, imuData, NULL);
    if (pData != NULL) {
        Tiggo_AstrobDRPostIMU(g_pTiggoEngine, (const unsigned char*)pData, length, timestamp);
        (*env)->ReleaseByteArrayElements(env, imuData, pData, JNI_ABORT);
    }
}

// ========== Протокол обмена данными (JSON) ==========

JNIEXPORT jboolean JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_OnProtocolRequest(JNIEnv* env, jclass clazz, jstring jsonRequest) {
    if (g_pTiggoEngine == NULL || jsonRequest == NULL) {
        return JNI_FALSE;
    }
    
    const char* pcJson = (*env)->GetStringUTFChars(env, jsonRequest, NULL);
    if (pcJson == NULL) {
        return JNI_FALSE;
    }
    
    BOOL bResult = Tiggo_OnProtocolRequest(g_pTiggoEngine, pcJson);
    
    (*env)->ReleaseStringUTFChars(env, jsonRequest, pcJson);
    
    return bResult ? JNI_TRUE : JNI_FALSE;
}

// ========== Данные от Yandex MapKit (НОВОЕ) ==========

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_OnYandexSpeedLimit(JNIEnv* env, jclass clazz,
                                                            jint speedLimitKmh, jstring text) {
    if (g_pTiggoEngine == NULL) {
        return;
    }
    
    const char* pcText = NULL;
    if (text != NULL) {
        pcText = (*env)->GetStringUTFChars(env, text, NULL);
    }
    
    Tiggo_OnYandexSpeedLimit(g_pTiggoEngine, speedLimitKmh, pcText);
    
    if (pcText != NULL) {
        (*env)->ReleaseStringUTFChars(env, text, pcText);
    }
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_OnYandexManeuver(JNIEnv* env, jclass clazz,
                                                          jint type, jint distanceMeters, jint timeSeconds,
                                                          jstring title, jstring subtitle) {
    if (g_pTiggoEngine == NULL) {
        return;
    }
    
    const char* pcTitle = NULL;
    const char* pcSubtitle = NULL;
    
    if (title != NULL) {
        pcTitle = (*env)->GetStringUTFChars(env, title, NULL);
    }
    if (subtitle != NULL) {
        pcSubtitle = (*env)->GetStringUTFChars(env, subtitle, NULL);
    }
    
    Tiggo_OnYandexManeuver(g_pTiggoEngine, type, distanceMeters, timeSeconds, pcTitle, pcSubtitle);
    
    if (pcTitle != NULL) {
        (*env)->ReleaseStringUTFChars(env, title, pcTitle);
    }
    if (pcSubtitle != NULL) {
        (*env)->ReleaseStringUTFChars(env, subtitle, pcSubtitle);
    }
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_OnYandexRoute(JNIEnv* env, jclass clazz,
                                                       jdoubleArray routePoints, jint distanceMeters, jint timeSeconds) {
    if (g_pTiggoEngine == NULL || routePoints == NULL) {
        return;
    }
    
    jsize nLength = (*env)->GetArrayLength(env, routePoints);
    jdouble* pdPoints = (*env)->GetDoubleArrayElements(env, routePoints, NULL);
    
    if (pdPoints != NULL) {
        Tiggo_OnYandexRoute(g_pTiggoEngine, pdPoints, nLength, distanceMeters, timeSeconds);
        (*env)->ReleaseDoubleArrayElements(env, routePoints, pdPoints, JNI_ABORT);
    }
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_OnYandexLocation(JNIEnv* env, jclass clazz,
                                                          jdouble latitude, jdouble longitude,
                                                          jfloat bearing, jfloat speed, jstring roadName) {
    if (g_pTiggoEngine == NULL) {
        return;
    }
    
    const char* pcRoadName = NULL;
    if (roadName != NULL) {
        pcRoadName = (*env)->GetStringUTFChars(env, roadName, NULL);
    }
    
    Tiggo_OnYandexLocation(g_pTiggoEngine, latitude, longitude, bearing, speed, pcRoadName);
    
    if (pcRoadName != NULL) {
        (*env)->ReleaseStringUTFChars(env, roadName, pcRoadName);
    }
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_OnYandexRouteStatus(JNIEnv* env, jclass clazz,
                                                             jboolean isActive, jboolean isRecalculating) {
    if (g_pTiggoEngine != NULL) {
        BOOL bActive = (isActive == JNI_TRUE);
        BOOL bRecalculating = (isRecalculating == JNI_TRUE);
        Tiggo_OnYandexRouteStatus(g_pTiggoEngine, bActive, bRecalculating);
    }
}

// ========== Утилиты ==========

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_SetSystemDir(JNIEnv* env, jclass clazz, jstring dir) {
    if (g_pTiggoEngine != NULL && dir != NULL) {
        const char* pcDir = (*env)->GetStringUTFChars(env, dir, NULL);
        if (pcDir != NULL) {
            Tiggo_SetSystemDir(g_pTiggoEngine, pcDir);
            (*env)->ReleaseStringUTFChars(env, dir, pcDir);
        }
    }
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_SetUsbDir(JNIEnv* env, jclass clazz, jstring dir) {
    if (g_pTiggoEngine != NULL && dir != NULL) {
        const char* pcDir = (*env)->GetStringUTFChars(env, dir, NULL);
        if (pcDir != NULL) {
            Tiggo_SetUsbDir(g_pTiggoEngine, pcDir);
            (*env)->ReleaseStringUTFChars(env, dir, pcDir);
        }
    }
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_SetNetStatus(JNIEnv* env, jclass clazz, jint status, jint type) {
    if (g_pTiggoEngine != NULL) {
        Tiggo_SetNetStatus(g_pTiggoEngine, status, type);
    }
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_ChangeLanguage(JNIEnv* env, jclass clazz, jint languageId) {
    if (g_pTiggoEngine != NULL) {
        Tiggo_ChangeLanguage(g_pTiggoEngine, languageId);
    }
}

JNIEXPORT jstring JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_GetMapVersion(JNIEnv* env, jclass clazz) {
    // TODO: реализовать получение версии карты
    return (*env)->NewStringUTF(env, "Tiggo Navigator v1.0.0");
}

JNIEXPORT jint JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_GetMeasureUnit(JNIEnv* env, jclass clazz) {
    if (g_pTiggoEngine != NULL) {
        return Tiggo_GetMeasureUnit(g_pTiggoEngine);
    }
    return 0; // 0 = метры
}

JNIEXPORT jboolean JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_IsMapActivated(JNIEnv* env, jclass clazz) {
    if (g_pTiggoEngine != NULL) {
        return Tiggo_IsMapActivated(g_pTiggoEngine) ? JNI_TRUE : JNI_FALSE;
    }
    return JNI_FALSE;
}

JNIEXPORT void JNICALL
Java_com_tiggo_navigator_TiggoJavaToJni_WriteLog(JNIEnv* env, jclass clazz, jstring message) {
    if (message != NULL) {
        const char* pcMsg = (*env)->GetStringUTFChars(env, message, NULL);
        if (pcMsg != NULL) {
            LOGI("%s", pcMsg);
            (*env)->ReleaseStringUTFChars(env, message, pcMsg);
        }
    }
}

