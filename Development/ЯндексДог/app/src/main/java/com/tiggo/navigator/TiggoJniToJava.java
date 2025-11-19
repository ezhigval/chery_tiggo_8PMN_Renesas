/**
 * TiggoJniToJava - Обратный JNI слой (вызовы из нативного кода в Java)
 * Аналог JniToJava из TurboDog
 * 
 * Эти методы вызываются из нативного кода для отправки данных в Java
 */
package com.tiggo.navigator;

import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * Обратный JNI слой - вызовы из нативного C кода в Java
 * 
 * Стиль TurboDog:
 * - jniCall префикс для всех методов
 * - Отправка broadcast в формате TurboDog
 */
public class TiggoJniToJava {
    private static final String TAG = "TiggoJniToJava";
    private static Context sContext;
    
    // Статическая ссылка на NavigationUI для обновления
    private static NavigationUI sNavigationUI = null;
    
    /**
     * Установка контекста приложения (вызывается из Activity)
     */
    public static void setContext(Context context) {
        sContext = context.getApplicationContext();
    }
    
    /**
     * Установка NavigationUI для обновления (вызывается из Activity)
     */
    public static void setNavigationUI(NavigationUI ui) {
        sNavigationUI = ui;
    }
    
    /**
     * Обновление данных навигации из нативного кода
     * @param speed скорость в км/ч (не используется в новом UI)
     * @param bearing курс в градусах (не используется в новом UI)
     * @param speedLimit ограничение скорости в км/ч (не используется в новом UI)
     * @param maneuverType тип маневра (0=нет, 1=налево, 2=направо, 3=разворот, 4=прямо)
     * @param maneuverDistance расстояние до маневра в метрах
     * @param roadName название улицы для маневра
     */
    public static void jniCallUpdateNavigationUI(float speed, float bearing, int speedLimit,
                                                  int maneuverType, int maneuverDistance,
                                                  String roadName) {
        if (sNavigationUI != null) {
            // Обновляем маневр (новый интерфейс)
            // Если есть маневр, автоматически устанавливаем навигацию как активную
            sNavigationUI.updateNextManeuver(maneuverType, maneuverDistance, roadName);
        }
    }
    
    /**
     * Установка состояния навигации
     * @param active TRUE если навигация активна (следование маршруту)
     */
    public static void jniCallSetNavigationActive(boolean active) {
        if (sNavigationUI != null) {
            sNavigationUI.setNavigationActive(active);
        }
    }
    
    /**
     * Обновление информации о маршруте
     * @param arrivalTime время прибытия (формат "HH:mm")
     * @param remainingTimeMinutes оставшееся время в минутах
     * @param remainingDistanceKm оставшееся расстояние в км
     */
    public static void jniCallUpdateRouteInfo(String arrivalTime, int remainingTimeMinutes, float remainingDistanceKm) {
        if (sNavigationUI != null) {
            sNavigationUI.updateRouteInfo(arrivalTime, remainingTimeMinutes, remainingDistanceKm);
        }
    }
    
    /**
     * Отправка навигационных данных из нативного кода
     * Аналог jniCallOnNaviDispatch в TurboDog
     * 
     * Формат JSON (как в TurboDog):
     * {
     *   "result": {
     *     "msgType": 1,
     *     "id": 124,
     *     "data": {
     *       "turnType": 1,
     *       "turnDis": 500.0,
     *       "turnTime": 30,
     *       "leftDis": 5000.0,
     *       "leftTime": 300,
     *       "curName": "Ленинградский проспект",
     *       "nextName": "Тверская улица",
     *       "roadCls": 1,
     *       "speed": 60
     *     }
     *   }
     * }
     */
    public static void jniCallOnNavigationData(String json) {
        if (sContext == null) {
            Log.w(TAG, "Context not set, cannot send broadcast");
            return;
        }
        
        try {
            // Парсим JSON для извлечения данных
            org.json.JSONObject root = new org.json.JSONObject(json);
            org.json.JSONObject result = root.getJSONObject("result");
            
            if (result.getInt("msgType") != 1) {
                return;
            }
            
            int id = result.getInt("id");
            
            // ID 124 = навигационные данные (TURN-BY-TURN)
            if (id == 124 && result.has("data")) {
                org.json.JSONObject data = result.getJSONObject("data");
                
                // Извлекаем данные
                int turnType = data.getInt("turnType");
                int turnDist = (int) data.getDouble("turnDis");
                int turnTime = (int) data.getDouble("turnTime");
                int remainDist = (int) data.getDouble("leftDis");
                int remainTime = data.getInt("leftTime");
                String curRoad = data.getString("curName");
                String nextRoad = data.getString("nextName");
                
                // Отправляем broadcast в формате TurboDog
                sendNavigationBroadcast(turnType, turnDist, turnTime, remainDist, remainTime, curRoad, nextRoad);
            }
            // Другие ID можно обработать аналогично
            
        } catch (Exception e) {
            Log.e(TAG, "Error parsing navigation data JSON", e);
        }
    }
    
    /**
     * Отправка broadcast сообщения в формате TurboDog
     * Совместимо с com.desaysv.mapservice.TurboDogAdapter
     */
    private static void sendNavigationBroadcast(int turnType, int turnDist, int turnTime,
                                                int remainDist, int remainTime,
                                                String curRoad, String nextRoad) {
        Intent intent = new Intent("turbodog.navigation.system.message");
        
        // Базовые данные (совместимые с TurboDog)
        intent.putExtra("CODE", 201); // TURN-BY-TURN данные
        intent.putExtra("TURN_TYPE", turnType);
        intent.putExtra("TURN_DIST", turnDist);
        intent.putExtra("TURN_TIME", turnTime);
        intent.putExtra("REMAINING_DIST", remainDist);
        intent.putExtra("REMAINING_TIME", remainTime);
        intent.putExtra("CURRENT_ROAD", curRoad != null ? curRoad : "");
        intent.putExtra("NEXT_ROAD", nextRoad != null ? nextRoad : "");
        
        // ARRIVE_TIME в Unix timestamp (секунды)
        long arriveTime = System.currentTimeMillis() / 1000 + remainTime;
        intent.putExtra("ARRIVE_TIME", arriveTime);
        
        sContext.sendBroadcast(intent);
        
        Log.d(TAG, "Navigation broadcast sent: CODE=201, TURN_TYPE=" + turnType + 
                   ", TURN_DIST=" + turnDist + "m");
    }
    
    /**
     * Отправка статуса навигации
     * @param isActive TRUE если навигация активна
     * @param isStarting TRUE если навигация начинается
     */
    public static void jniCallOnNavigationStatus(boolean isActive, boolean isStarting) {
        if (sContext == null) {
            return;
        }
        
        Intent intent = new Intent("turbodog.navigation.system.message");
        
        if (isStarting) {
            intent.putExtra("CODE", 202); // Начало навигации
            intent.putExtra("DATA", 1);
        } else if (!isActive) {
            intent.putExtra("CODE", 203); // Остановка навигации
            intent.putExtra("DATA", 0);
        } else {
            intent.putExtra("CODE", 202); // Навигация активна
            intent.putExtra("DATA", 1);
        }
        
        sContext.sendBroadcast(intent);
        
        Log.d(TAG, "Navigation status broadcast sent: CODE=" + intent.getIntExtra("CODE", 0));
    }
    
    /**
     * Отправка информации о навигации
     * @param turnType тип маневра
     * @param turnDist расстояние до маневра
     * @param remainDist оставшееся расстояние
     * @param remainTime оставшееся время
     * @param curRoad текущая дорога
     * @param roadClass класс дороги
     * @param speed скорость
     */
    public static void jniCallOnNavigationInfo(int turnType, int turnDist, int remainDist,
                                               int remainTime, String curRoad, int roadClass, int speed) {
        if (sContext == null) {
            return;
        }
        
        // Отправляем broadcast (аналогично TurboDog)
        Intent intent = new Intent("turbodog.navigation.system.message");
        intent.putExtra("CODE", 201);
        intent.putExtra("TURN_TYPE", turnType);
        intent.putExtra("TURN_DIST", turnDist);
        intent.putExtra("REMAINING_DIST", remainDist);
        intent.putExtra("REMAINING_TIME", remainTime);
        intent.putExtra("CURRENT_ROAD", curRoad != null ? curRoad : "");
        
        sContext.sendBroadcast(intent);
    }
    
    /**
     * Получение текущего языка
     * @return ID языка
     */
    public static int jniCallGetCurLanguage() {
        // TODO: реализовать получение языка из Android
        return 0; // 0 = русский, 1 = английский и т.д.
    }
    
    /**
     * Получение формата даты
     * @return формат даты
     */
    public static int jniCallGetDateFormat() {
        // TODO: реализовать получение формата даты
        return 0;
    }
    
    /**
     * Получение страны данных карты
     * @return страна
     */
    public static String jniCallGetMapDataCountry() {
        // TODO: реализовать
        return "RU";
    }
    
    /**
     * Получение региона данных карты
     * @return регион
     */
    public static String jniCallGetMapDataRegion() {
        // TODO: реализовать
        return "Russia";
    }
    
    /**
     * Запрос загрузки тайла карты из нативного кода
     * @param tileX координата X тайла
     * @param tileY координата Y тайла
     * @param zoom уровень масштабирования
     */
    public static void jniCallRequestTile(int tileX, int tileY, int zoom) {
        if (sContext == null) {
            Log.w(TAG, "Context not set, cannot request tile");
            return;
        }
        
        try {
            // Получаем YandexMapKitBridge через MainActivity или храним ссылку
            // Временно используем статический метод для получения bridge
            YandexMapKitBridge bridge = YandexMapKitBridge.getInstance();
            if (bridge != null) {
                TileLoader tileLoader = bridge.getTileLoader();
                if (tileLoader != null) {
                    // Запрашиваем загрузку тайла (callback уже настроен в YandexMapKitBridge)
                    tileLoader.loadTileDirect(tileX, tileY, zoom, null);
                    Log.d(TAG, "Tile requested: x=" + tileX + ", y=" + tileY + ", z=" + zoom);
                } else {
                    Log.w(TAG, "TileLoader is null");
                }
            } else {
                Log.w(TAG, "YandexMapKitBridge is null");
            }
        } catch (Exception e) {
            Log.e(TAG, "Error requesting tile", e);
        }
    }
}

