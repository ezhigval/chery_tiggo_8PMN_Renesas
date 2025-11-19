/**
 * jni_navigation_ui.c - JNI функции для обновления UI навигации
 * 
 * Вызывает Java методы для обновления NavigationUI
 */

#include <jni.h>
#include <android/log.h>
#include <string.h>

// Для BOOL типа
#ifndef BOOL
typedef int BOOL;
#endif

#define LOG_TAG "TiggoJNI"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Глобальные ссылки на Java класс и методы
static jclass g_pTiggoJniToJavaClass = NULL;
static jmethodID g_pJniCallUpdateNavigationUIMethod = NULL;
static jmethodID g_pJniCallUpdateRouteInfoMethod = NULL;
static JavaVM* g_pJavaVM = NULL;

/**
 * Инициализация JNI для NavigationUI
 */
void Tiggo_InitNavigationUI(JavaVM* pJavaVM) {
    g_pJavaVM = pJavaVM;
    
    // Класс и метод будут инициализированы при первом вызове
}

/**
 * Обновление UI навигации
 */
void Tiggo_UpdateNavigationUI(float fSpeed, float fBearing, int nSpeedLimit,
                              int nManeuverType, int nManeuverDistance,
                              const char* pcRoadName) {
    if (g_pJavaVM == NULL) {
        return;
    }
    
    // Получаем JNIEnv для текущего потока
    JNIEnv* env = NULL;
    int nAttachResult = (*g_pJavaVM)->GetEnv(g_pJavaVM, (void**)&env, JNI_VERSION_1_6);
    
    if (nAttachResult == JNI_EDETACHED) {
        nAttachResult = (*g_pJavaVM)->AttachCurrentThread(g_pJavaVM, &env, NULL);
        if (nAttachResult != JNI_OK || env == NULL) {
            LOGE("Failed to attach thread to JVM for NavigationUI update");
            return;
        }
    } else if (nAttachResult != JNI_OK || env == NULL) {
        LOGE("Failed to get JNIEnv for NavigationUI update");
        return;
    }
    
    // Инициализируем класс и метод при первом вызове
    if (g_pTiggoJniToJavaClass == NULL || g_pJniCallUpdateNavigationUIMethod == NULL) {
        jclass tiggoJniToJavaClass = (*env)->FindClass(env, "com/tiggo/navigator/TiggoJniToJava");
        if (tiggoJniToJavaClass != NULL) {
            g_pTiggoJniToJavaClass = (*env)->NewGlobalRef(env, tiggoJniToJavaClass);
            g_pJniCallUpdateNavigationUIMethod = (*env)->GetStaticMethodID(env, tiggoJniToJavaClass,
                "jniCallUpdateNavigationUI", "(FFIIILjava/lang/String;)V");
            if (g_pJniCallUpdateNavigationUIMethod == NULL) {
                LOGE("Failed to find jniCallUpdateNavigationUI method");
            }
            (*env)->DeleteLocalRef(env, tiggoJniToJavaClass);
        } else {
            LOGE("Failed to find TiggoJniToJava class for NavigationUI");
        }
    }
    
    if (g_pTiggoJniToJavaClass == NULL || g_pJniCallUpdateNavigationUIMethod == NULL) {
        return;
    }
    
    // Создаем Java строку для названия дороги
    jstring jRoadName = NULL;
    if (pcRoadName != NULL && strlen(pcRoadName) > 0) {
        jRoadName = (*env)->NewStringUTF(env, pcRoadName);
    } else {
        jRoadName = (*env)->NewStringUTF(env, "");
    }
    
    // Вызываем статический метод
    (*env)->CallStaticVoidMethod(env, g_pTiggoJniToJavaClass, g_pJniCallUpdateNavigationUIMethod,
                                 (jfloat)fSpeed, (jfloat)fBearing, (jint)nSpeedLimit,
                                 (jint)nManeuverType, (jint)nManeuverDistance, jRoadName);
    
    // Проверяем исключения
    if ((*env)->ExceptionCheck(env)) {
        LOGE("Exception occurred while calling jniCallUpdateNavigationUI");
        (*env)->ExceptionDescribe(env);
        (*env)->ExceptionClear(env);
    }
    
    // Освобождаем строку
    if (jRoadName != NULL) {
        (*env)->DeleteLocalRef(env, jRoadName);
    }
}

/**
 * Обновление информации о маршруте
 */
void Tiggo_UpdateRouteInfo(const char* pcArrivalTime, int nRemainingTimeMinutes, float fRemainingDistanceKm) {
    if (g_pJavaVM == NULL) {
        return;
    }
    
    // Получаем JNIEnv для текущего потока
    JNIEnv* env = NULL;
    int nAttachResult = (*g_pJavaVM)->GetEnv(g_pJavaVM, (void**)&env, JNI_VERSION_1_6);
    
    if (nAttachResult == JNI_EDETACHED) {
        nAttachResult = (*g_pJavaVM)->AttachCurrentThread(g_pJavaVM, &env, NULL);
        if (nAttachResult != JNI_OK || env == NULL) {
            LOGE("Failed to attach thread to JVM for RouteInfo update");
            return;
        }
    } else if (nAttachResult != JNI_OK || env == NULL) {
        LOGE("Failed to get JNIEnv for RouteInfo update");
        return;
    }
    
    // Инициализируем класс и метод при первом вызове
    if (g_pTiggoJniToJavaClass == NULL || g_pJniCallUpdateRouteInfoMethod == NULL) {
        jclass tiggoJniToJavaClass = (*env)->FindClass(env, "com/tiggo/navigator/TiggoJniToJava");
        if (tiggoJniToJavaClass != NULL) {
            if (g_pTiggoJniToJavaClass == NULL) {
                g_pTiggoJniToJavaClass = (*env)->NewGlobalRef(env, tiggoJniToJavaClass);
            }
            g_pJniCallUpdateRouteInfoMethod = (*env)->GetStaticMethodID(env, tiggoJniToJavaClass,
                "jniCallUpdateRouteInfo", "(Ljava/lang/String;IF)V");
            if (g_pJniCallUpdateRouteInfoMethod == NULL) {
                LOGE("Failed to find jniCallUpdateRouteInfo method");
            }
            (*env)->DeleteLocalRef(env, tiggoJniToJavaClass);
        } else {
            LOGE("Failed to find TiggoJniToJava class for RouteInfo");
        }
    }
    
    if (g_pTiggoJniToJavaClass == NULL || g_pJniCallUpdateRouteInfoMethod == NULL) {
        return;
    }
    
    // Создаем Java строку для времени прибытия
    jstring jArrivalTime = NULL;
    if (pcArrivalTime != NULL && strlen(pcArrivalTime) > 0) {
        jArrivalTime = (*env)->NewStringUTF(env, pcArrivalTime);
    } else {
        jArrivalTime = (*env)->NewStringUTF(env, "");
    }
    
    // Вызываем статический метод
    (*env)->CallStaticVoidMethod(env, g_pTiggoJniToJavaClass, g_pJniCallUpdateRouteInfoMethod,
                                 jArrivalTime, (jint)nRemainingTimeMinutes, (jfloat)fRemainingDistanceKm);
    
    // Проверяем исключения
    if ((*env)->ExceptionCheck(env)) {
        LOGE("Exception occurred while calling jniCallUpdateRouteInfo");
        (*env)->ExceptionDescribe(env);
        (*env)->ExceptionClear(env);
    }
    
    // Освобождаем строку
    if (jArrivalTime != NULL) {
        (*env)->DeleteLocalRef(env, jArrivalTime);
    }
}

/**
 * Установка состояния навигации (активна/неактивна)
 */
void Tiggo_SetNavigationActive(BOOL bActive) {
    if (g_pJavaVM == NULL) {
        return;
    }
    
    // Получаем JNIEnv для текущего потока
    JNIEnv* env = NULL;
    int nAttachResult = (*g_pJavaVM)->GetEnv(g_pJavaVM, (void**)&env, JNI_VERSION_1_6);
    
    if (nAttachResult == JNI_EDETACHED) {
        nAttachResult = (*g_pJavaVM)->AttachCurrentThread(g_pJavaVM, &env, NULL);
        if (nAttachResult != JNI_OK || env == NULL) {
            LOGE("Failed to attach thread to JVM for SetNavigationActive");
            return;
        }
    } else if (nAttachResult != JNI_OK || env == NULL) {
        LOGE("Failed to get JNIEnv for SetNavigationActive");
        return;
    }
    
    // Инициализируем класс и метод при первом вызове
    if (g_pTiggoJniToJavaClass == NULL) {
        jclass tiggoJniToJavaClass = (*env)->FindClass(env, "com/tiggo/navigator/TiggoJniToJava");
        if (tiggoJniToJavaClass != NULL) {
            g_pTiggoJniToJavaClass = (*env)->NewGlobalRef(env, tiggoJniToJavaClass);
            (*env)->DeleteLocalRef(env, tiggoJniToJavaClass);
        } else {
            LOGE("Failed to find TiggoJniToJava class for SetNavigationActive");
            return;
        }
    }
    
    if (g_pTiggoJniToJavaClass == NULL) {
        return;
    }
    
    // Находим метод
    jmethodID methodID = (*env)->GetStaticMethodID(env, g_pTiggoJniToJavaClass,
        "jniCallSetNavigationActive", "(Z)V");
    if (methodID == NULL) {
        LOGE("Failed to find jniCallSetNavigationActive method");
        return;
    }
    
    // Вызываем статический метод
    (*env)->CallStaticVoidMethod(env, g_pTiggoJniToJavaClass, methodID, (jboolean)(bActive ? JNI_TRUE : JNI_FALSE));
    
    // Проверяем исключения
    if ((*env)->ExceptionCheck(env)) {
        LOGE("Exception occurred while calling jniCallSetNavigationActive");
        (*env)->ExceptionDescribe(env);
        (*env)->ExceptionClear(env);
    }
}

