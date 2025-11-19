#include <jni.h>
#include <android/log.h>
#include <memory>

#include "navigator_engine.h"
#include "jni_utils.h"

#define LOG_TAG "TiggoNavigator"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

using namespace tiggo::navigator;

// Глобальный указатель на NavigatorEngine
static std::unique_ptr<NavigatorEngine> g_navigator_engine = nullptr;

extern "C" {

/**
 * Инициализация навигационного движка
 */
JNIEXPORT jboolean JNICALL
Java_com_tiggo_navigator_NavigationService_nativeInitNavigator(JNIEnv* env, jobject thiz) {
    LOGI("Initializing native navigator engine");
    
    try {
        g_navigator_engine = std::make_unique<NavigatorEngine>();
        
        if (!g_navigator_engine->Initialize()) {
            LOGE("Failed to initialize navigator engine");
            g_navigator_engine.reset();
            return JNI_FALSE;
        }
        
        LOGI("Navigator engine initialized successfully");
        return JNI_TRUE;
    } catch (const std::exception& e) {
        LOGE("Exception in nativeInitNavigator: %s", e.what());
        return JNI_FALSE;
    }
}

/**
 * Завершение навигационного движка
 */
JNIEXPORT void JNICALL
Java_com_tiggo_navigator_NavigationService_nativeShutdownNavigator(JNIEnv* env, jobject thiz) {
    LOGI("Shutting down native navigator engine");
    
    if (g_navigator_engine) {
        g_navigator_engine->Shutdown();
        g_navigator_engine.reset();
    }
}

/**
 * Обновление навигационного движка (вызывается каждый кадр)
 */
JNIEXPORT void JNICALL
Java_com_tiggo_navigator_NavigationService_nativeUpdateNavigator(JNIEnv* env, jobject thiz, jfloat deltaTime) {
    if (g_navigator_engine) {
        g_navigator_engine->Update(deltaTime);
    }
}

/**
 * Обновление GPS данных
 */
JNIEXPORT void JNICALL
Java_com_tiggo_navigator_NavigationService_nativeOnGpsUpdate(JNIEnv* env, jobject thiz,
                                                              jdouble latitude, jdouble longitude,
                                                              jfloat bearing, jfloat speed) {
    if (!g_navigator_engine) return;
    
    GpsData gps;
    gps.position.latitude = latitude;
    gps.position.longitude = longitude;
    gps.bearing = bearing;
    gps.speed = speed;
    
    g_navigator_engine->OnGpsUpdate(gps);
}

/**
 * Получение данных от Yandex: ограничение скорости
 */
JNIEXPORT void JNICALL
Java_com_tiggo_navigator_YandexMapKitBridge_nativeOnSpeedLimitReceived(JNIEnv* env, jobject thiz,
                                                                        jint speedLimitKmh, jstring text) {
    if (!g_navigator_engine) return;
    
    std::string textStr = JNIUtils::JStringToString(env, text);
    g_navigator_engine->OnSpeedLimitReceived(speedLimitKmh);
}

/**
 * Получение данных от Yandex: маневр
 */
JNIEXPORT void JNICALL
Java_com_tiggo_navigator_YandexMapKitBridge_nativeOnManeuverReceived(JNIEnv* env, jobject thiz,
                                                                      jint type, jint distanceMeters,
                                                                      jstring title, jstring subtitle) {
    if (!g_navigator_engine) return;
    
    ManeuverData maneuver;
    maneuver.type = static_cast<ManeuverType>(type);
    maneuver.distanceMeters = distanceMeters;
    maneuver.title = JNIUtils::JStringToString(env, title);
    maneuver.subtitle = JNIUtils::JStringToString(env, subtitle);
    
    g_navigator_engine->OnManeuverReceived(maneuver);
}

/**
 * Получение данных от Yandex: маршрут
 */
JNIEXPORT void JNICALL
Java_com_tiggo_navigator_YandexMapKitBridge_nativeOnRouteReceived(JNIEnv* env, jobject thiz,
                                                                   jdoubleArray routePoints,
                                                                   jint distanceMeters, jint timeSeconds) {
    if (!g_navigator_engine) return;
    
    RouteData route;
    
    // Конвертируем массив точек
    jsize length = env->GetArrayLength(routePoints);
    jdouble* points = env->GetDoubleArrayElements(routePoints, nullptr);
    
    for (jsize i = 0; i < length; i += 2) {
        Point point;
        point.latitude = points[i];
        point.longitude = points[i + 1];
        route.points.push_back(point);
    }
    
    env->ReleaseDoubleArrayElements(routePoints, points, JNI_ABORT);
    
    route.totalDistanceMeters = distanceMeters;
    route.totalTimeSeconds = timeSeconds;
    
    g_navigator_engine->OnRouteReceived(route);
}

/**
 * Получение данных от Yandex: местоположение
 */
JNIEXPORT void JNICALL
Java_com_tiggo_navigator_YandexMapKitBridge_nativeOnLocationReceived(JNIEnv* env, jobject thiz,
                                                                      jdouble latitude, jdouble longitude,
                                                                      jfloat bearing, jstring roadName) {
    if (!g_navigator_engine) return;
    
    LocationData location;
    location.position.latitude = latitude;
    location.position.longitude = longitude;
    location.bearing = bearing;
    location.roadName = JNIUtils::JStringToString(env, roadName);
    
    g_navigator_engine->OnLocationReceived(location);
}

} // extern "C"

