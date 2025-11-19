/**
 * jni_utils.h - Утилиты для JNI (в стиле TurboDog)
 */

#ifndef JNI_UTILS_H
#define JNI_UTILS_H

#include <jni.h>
#include <string.h>
#include <stdlib.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Утилиты для работы со строками JNI
 */

// Конвертация jstring в C строку (вызывающий должен освободить память)
static inline char* JStringToCString(JNIEnv* env, jstring jstr) {
    if (jstr == NULL) {
        return NULL;
    }
    
    const char* pcStr = (*env)->GetStringUTFChars(env, jstr, NULL);
    if (pcStr == NULL) {
        return NULL;
    }
    
    // Копируем строку (вызывающий должен освободить)
    size_t nLen = strlen(pcStr);
    char* pResult = (char*)malloc(nLen + 1);
    if (pResult != NULL) {
        strcpy(pResult, pcStr);
    }
    
    (*env)->ReleaseStringUTFChars(env, jstr, pcStr);
    
    return pResult;
}

// Освобождение C строки
static inline void FreeCString(char* pStr) {
    if (pStr != NULL) {
        free(pStr);
    }
}

// Вызов Java метода из нативного кода
static inline void CallJavaMethod(JNIEnv* env, jclass clazz, const char* methodName,
                                  const char* methodSig, ...) {
    if (env == NULL || clazz == NULL || methodName == NULL || methodSig == NULL) {
        return;
    }
    
    jmethodID method = (*env)->GetStaticMethodID(env, clazz, methodName, methodSig);
    if (method == NULL) {
        return;
    }
    
    // TODO: вызов метода с параметрами через va_list
}

#ifdef __cplusplus
}
#endif

#endif // JNI_UTILS_H

