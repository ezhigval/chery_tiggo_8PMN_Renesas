/**
 * YandexMapKitBridge - Мост к Yandex MapKit API для получения данных навигации
 * 
 * Этот класс:
 * 1. Получает данные от Yandex MapKit/NaviKit API
 * 2. Передает данные в нативный код через TiggoJavaToJni
 * 3. Использует публичный Yandex MapKit API (не Reflection)
 */
package com.tiggo.navigator;

import android.content.Context;
import android.util.Log;

import com.yandex.mapkit.MapKit;
import com.yandex.mapkit.MapKitFactory;
import com.yandex.mapkit.navigation.Guidance;
import com.yandex.mapkit.navigation.GuidanceListener;
import com.yandex.mapkit.navigation.Navigation;
import com.yandex.mapkit.navigation.guidance.GuidanceStates;
import com.yandex.mapkit.navigation.windshield.Windshield;
import com.yandex.mapkit.navigation.windshield.Manoeuvre;
import com.yandex.mapkit.navigation.driving_route.DrivingRoute;
import com.yandex.mapkit.location.Location;
import com.yandex.mapkit.common.LocalizedValue;
import com.yandex.mapkit.geometry.Point;
import com.yandex.mapkit.geometry.Polyline;

import java.util.List;
import java.util.Timer;
import java.util.TimerTask;

/**
 * Мост к Yandex MapKit API
 * Получает данные от Yandex и передает в нативный код
 */
public class YandexMapKitBridge implements GuidanceListener {
    private static final String TAG = "YandexBridge";
    private static final long DATA_EXTRACTION_INTERVAL_MS = 500; // 500ms
    
    private Context mContext;
    private MapKit mMapKit;
    private Navigation mNavigation;
    private Guidance mGuidance;
    private Windshield mWindshield;
    
    // Таймер для периодического извлечения данных
    private Timer mDataExtractionTimer;
    
    // Кеш данных для минимизации вызовов API
    private volatile long mLastUpdateTime = 0;
    private static final long CACHE_VALIDITY_MS = 300; // Кеш валиден 300ms
    
    /**
     * Инициализация моста
     */
    public boolean initialize(Context context, String apiKey) {
        mContext = context;
        
        try {
            // Инициализация MapKit (должна быть вызвана в Application)
            MapKitFactory.setApiKey(apiKey);
            mMapKit = MapKitFactory.getInstance();
            
            // Получаем Navigation объект
            mNavigation = mMapKit.createNavigation();
            if (mNavigation == null) {
                Log.e(TAG, "Navigation is null - MapKit may not be initialized");
                return false;
            }
            
            // Получаем Guidance объект
            mGuidance = mNavigation.getGuidance();
            if (mGuidance == null) {
                Log.e(TAG, "Guidance is null");
                return false;
            }
            
            // Подписываемся на события Guidance для автоматических обновлений
            mGuidance.addGuidanceListener(this);
            
            // Получаем Windshield для маневров
            mWindshield = mGuidance.getWindshield();
            
            Log.d(TAG, "Yandex MapKit Bridge initialized successfully");
            
            // Запускаем периодическое извлечение данных
            startDataExtraction();
            
            return true;
        } catch (Exception e) {
            Log.e(TAG, "Failed to initialize Yandex MapKit Bridge", e);
            return false;
        }
    }
    
    /**
     * Завершение моста
     */
    public void shutdown() {
        stopDataExtraction();
        
        if (mGuidance != null) {
            try {
                mGuidance.removeGuidanceListener(this);
            } catch (Exception e) {
                Log.e(TAG, "Error removing guidance listener", e);
            }
        }
        
        if (mNavigation != null) {
            try {
                mNavigation.removeAll();
            } catch (Exception e) {
                Log.e(TAG, "Error removing navigation", e);
            }
        }
        
        Log.d(TAG, "Yandex MapKit Bridge shutdown");
    }
    
    /**
     * Запуск периодического извлечения данных
     */
    private void startDataExtraction() {
        if (mDataExtractionTimer != null) {
            mDataExtractionTimer.cancel();
        }
        
        mDataExtractionTimer = new Timer();
        mDataExtractionTimer.scheduleAtFixedRate(new TimerTask() {
            @Override
            public void run() {
                extractAndSendNavigationData();
            }
        }, 0, DATA_EXTRACTION_INTERVAL_MS);
        
        Log.d(TAG, "Data extraction started");
    }
    
    /**
     * Остановка периодического извлечения данных
     */
    private void stopDataExtraction() {
        if (mDataExtractionTimer != null) {
            mDataExtractionTimer.cancel();
            mDataExtractionTimer = null;
        }
        Log.d(TAG, "Data extraction stopped");
    }
    
    /**
     * Основной метод извлечения и отправки данных навигации
     * Использует кеширование для оптимизации производительности
     */
    private void extractAndSendNavigationData() {
        if (mGuidance == null) {
            return;
        }
        
        long currentTime = System.currentTimeMillis();
        
        // Используем кеш, если данные свежие
        if (currentTime - mLastUpdateTime < CACHE_VALIDITY_MS) {
            return;
        }
        
        try {
            // 1. Ограничение скорости
            extractAndSendSpeedLimit();
            
            // 2. Маневры
            extractAndSendManeuver();
            
            // 3. Маршрут
            extractAndSendRoute();
            
            // 4. Текущее местоположение
            extractAndSendLocation();
            
            // 5. Статус маршрута
            extractAndSendRouteStatus();
            
            mLastUpdateTime = currentTime;
            
        } catch (Exception e) {
            Log.e(TAG, "Error extracting navigation data", e);
        }
    }
    
    /**
     * Извлечение и отправка ограничения скорости
     */
    private void extractAndSendSpeedLimit() {
        try {
            LocalizedValue speedLimit = mGuidance.getSpeedLimit();
            if (speedLimit == null) {
                return;
            }
            
            // Получаем значение в м/с и конвертируем в км/ч
            double valueMs = speedLimit.getValue();
            int valueKmh = (int) Math.round(valueMs * 3.6);
            
            // Получаем локализованный текст
            String text = speedLimit.getText();
            
            // Отправляем в нативный код
            TiggoJavaToJni.OnYandexSpeedLimit(valueKmh, text != null ? text : "");
            
        } catch (Exception e) {
            Log.e(TAG, "Error extracting speed limit", e);
        }
    }
    
    /**
     * Извлечение и отправка следующего маневра
     */
    private void extractAndSendManeuver() {
        try {
            if (mWindshield == null) {
                return;
            }
            
            // Получаем список предстоящих маневров
            List<Manoeuvre> manoeuvres = mWindshield.getUpcomingManoeuvres();
            
            if (manoeuvres == null || manoeuvres.isEmpty()) {
                return;
            }
            
            // Берем первый маневр (следующий)
            Manoeuvre manoeuvre = manoeuvres.get(0);
            
            // Извлекаем данные маневра
            String title = manoeuvre.getTitle();
            String subtitle = manoeuvre.getSubtitle();
            
            // Расстояние до маневра
            int distanceMeters = 0;
            int timeSeconds = 0;
            try {
                LocalizedValue distance = manoeuvre.getDistance();
                if (distance != null) {
                    double valueMeters = distance.getValue();
                    distanceMeters = (int) Math.round(valueMeters);
                }
                
                // Время до маневра (если доступно)
                // TODO: получить время до маневра из API
            } catch (Exception e) {
                // Игнорируем ошибки для отдельных полей
            }
            
            // Конвертируем тип маневра в формат TurboDog
            int type = convertManeuverType(title);
            
            // Отправляем в нативный код
            TiggoJavaToJni.OnYandexManeuver(type, distanceMeters, timeSeconds,
                                           title != null ? title : "",
                                           subtitle != null ? subtitle : "");
            
        } catch (Exception e) {
            Log.e(TAG, "Error extracting maneuver", e);
        }
    }
    
    /**
     * Конвертация типа маневра из Yandex формата в TurboDog формат
     */
    private int convertManeuverType(String maneuverTitle) {
        if (maneuverTitle == null) {
            return 0; // STRAIGHT
        }
        
        String lower = maneuverTitle.toLowerCase();
        
        if (lower.contains("налево") || lower.contains("left")) {
            return 1; // LEFT
        } else if (lower.contains("направо") || lower.contains("right")) {
            return 2; // RIGHT
        } else if (lower.contains("разворот") || lower.contains("uturn") || lower.contains("u-turn")) {
            return 3; // UTURN
        }
        
        return 0; // STRAIGHT
    }
    
    /**
     * Извлечение и отправка маршрута
     */
    private void extractAndSendRoute() {
        try {
            DrivingRoute route = mGuidance.getCurrentRoute();
            
            if (route == null) {
                return;
            }
            
            // Получаем геометрию маршрута (полилиния)
            Polyline polyline = route.getGeometry();
            if (polyline == null) {
                return;
            }
            
            // Извлекаем точки маршрута
            List<Point> points = polyline.getPoints();
            if (points == null || points.isEmpty()) {
                return;
            }
            
            // Конвертируем в массив double [lat1, lon1, lat2, lon2, ...]
            double[] routePoints = new double[points.size() * 2];
            for (int i = 0; i < points.size(); i++) {
                Point point = points.get(i);
                routePoints[i * 2] = point.getLatitude();
                routePoints[i * 2 + 1] = point.getLongitude();
            }
            
            // Извлекаем расстояние и время маршрута
            int distanceMeters = 0;
            int timeSeconds = 0;
            
            try {
                LocalizedValue distance = route.getDistance();
                if (distance != null) {
                    double valueMeters = distance.getValue();
                    distanceMeters = (int) Math.round(valueMeters);
                }
                
                LocalizedValue duration = route.getDuration();
                if (duration != null) {
                    double valueSeconds = duration.getValue();
                    timeSeconds = (int) Math.round(valueSeconds);
                }
            } catch (Exception e) {
                // Игнорируем ошибки для отдельных полей
            }
            
            // Отправляем в нативный код
            TiggoJavaToJni.OnYandexRoute(routePoints, distanceMeters, timeSeconds);
            
        } catch (Exception e) {
            Log.e(TAG, "Error extracting route", e);
        }
    }
    
    /**
     * Извлечение и отправка текущего местоположения
     */
    private void extractAndSendLocation() {
        try {
            Location location = mGuidance.getLocation();
            
            if (location == null) {
                return;
            }
            
            // Извлекаем координаты
            Point position = location.getPosition();
            if (position == null) {
                return;
            }
            
            double latitude = position.getLatitude();
            double longitude = position.getLongitude();
            
            // Извлекаем направление движения
            float bearing = location.getBearing();
            
            // Извлекаем скорость
            float speed = location.getSpeed();
            
            // Извлекаем название дороги
            String roadName = mGuidance.getRoadName();
            
            // Отправляем в нативный код
            TiggoJavaToJni.OnYandexLocation(latitude, longitude, bearing, speed,
                                           roadName != null ? roadName : "");
            
        } catch (Exception e) {
            Log.e(TAG, "Error extracting location", e);
        }
    }
    
    /**
     * Извлечение и отправка статуса маршрута
     */
    private void extractAndSendRouteStatus() {
        try {
            // Проверяем, активен ли маршрут
            GuidanceStates currentState = mGuidance.getCurrentState();
            
            boolean isActive = (currentState == GuidanceStates.FOLLOWING_ROUTE ||
                               currentState == GuidanceStates.ROUTE_RECALCULATING);
            
            boolean isRecalculating = (currentState == GuidanceStates.ROUTE_RECALCULATING);
            
            // Отправляем в нативный код
            TiggoJavaToJni.OnYandexRouteStatus(isActive, isRecalculating);
            
        } catch (Exception e) {
            Log.e(TAG, "Error extracting route status", e);
        }
    }
    
    // ========== GuidanceListener implementation ==========
    
    @Override
    public void onGuidanceStateChanged(GuidanceStates state) {
        Log.d(TAG, "Guidance state changed: " + state);
        // Триггерим обновление данных при изменении состояния
        extractAndSendNavigationData();
    }
    
    @Override
    public void onRouteChanged(DrivingRoute route) {
        Log.d(TAG, "Route changed");
        extractAndSendNavigationData();
    }
    
    @Override
    public void onLocationUpdated(Location location) {
        // Обновление происходит часто, не логируем каждый раз
        extractAndSendNavigationData();
    }
}

