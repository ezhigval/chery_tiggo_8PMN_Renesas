/**
 * jni_navigation_ui.h - JNI функции для обновления UI навигации
 */

#ifndef JNI_NAVIGATION_UI_H
#define JNI_NAVIGATION_UI_H

#include <jni.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Инициализация JNI для NavigationUI
 */
void Tiggo_InitNavigationUI(JavaVM* pJavaVM);

/**
 * Обновление UI навигации
 */
void Tiggo_UpdateNavigationUI(float fSpeed, float fBearing, int nSpeedLimit,
                              int nManeuverType, int nManeuverDistance,
                              const char* pcRoadName);

void Tiggo_UpdateRouteInfo(const char* pcArrivalTime, int nRemainingTimeMinutes, float fRemainingDistanceKm);

void Tiggo_SetNavigationActive(BOOL bActive);

#ifdef __cplusplus
}
#endif

#endif // JNI_NAVIGATION_UI_H

