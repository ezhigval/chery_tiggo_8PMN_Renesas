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
// TODO: Классы навигации недоступны в maps.mobile:4.19.0-lite
// Для навигации нужна полная версия MapKit или отдельная библиотека навигации
// import com.yandex.mapkit.navigation.Guidance;
// import com.yandex.mapkit.navigation.GuidanceListener;
// import com.yandex.mapkit.navigation.Navigation;
// import com.yandex.mapkit.navigation.guidance.GuidanceStates;
// import com.yandex.mapkit.navigation.windshield.Windshield;
// import com.yandex.mapkit.navigation.windshield.Manoeuvre;
// import com.yandex.mapkit.navigation.driving_route.DrivingRoute;
// import com.yandex.mapkit.location.Location;
// import com.yandex.mapkit.common.LocalizedValue;
import com.yandex.mapkit.geometry.Point;
import com.yandex.mapkit.geometry.Polyline;

import java.util.List;
import java.util.Timer;
import java.util.TimerTask;

/**
 * Мост к Yandex MapKit API
 * Получает данные от Yandex и передает в нативный код
 * ВАЖНО: В lite версии MapKit классы навигации недоступны
 */
public class YandexMapKitBridge /*implements GuidanceListener*/ {
    private static final String TAG = "YandexBridge";
    private static final long DATA_EXTRACTION_INTERVAL_MS = 500; // 500ms
    
    private Context mContext;
    private MapKit mMapKit;
    // TODO: Классы навигации недоступны в lite версии
    // private Navigation mNavigation;
    // private Guidance mGuidance;
    // private Windshield mWindshield;
    
    // Загрузчик тайлов
    private TileLoader mTileLoader;
    
    // Таймер для периодического извлечения данных
    private Timer mDataExtractionTimer;
    
    // Статическая ссылка для доступа из JNI
    private static YandexMapKitBridge sInstance = null;
    
    // Кеш данных для минимизации вызовов API
    private volatile long mLastUpdateTime = 0;
    private static final long CACHE_VALIDITY_MS = 300; // Кеш валиден 300ms
    
    /**
     * Инициализация моста
     * 
     * @param context контекст приложения
     * @param apiKey API ключ Yandex MapKit (если null, будет загружен из файла)
     * @return TRUE при успехе, FALSE при ошибке
     */
    public boolean initialize(Context context, String apiKey) {
        mContext = context;
        
        try {
            // MapKit должен быть инициализирован в Application.onCreate()
            // setApiKey() и initialize() уже вызваны в TiggoApplication
            // Нельзя вызывать setApiKey() после initialize()!
            mMapKit = MapKitFactory.getInstance();
            
            if (mMapKit == null) {
                Log.e(TAG, "MapKit is null - initialization failed in Application");
                return false;
            }
            
            // TODO: Классы навигации недоступны в maps.mobile:4.19.0-lite
            // Для навигации нужна полная версия MapKit
            // mNavigation = mMapKit.createNavigation();
            // mGuidance = mNavigation.getGuidance();
            // mWindshield = mGuidance.getWindshield();
            Log.w(TAG, "Navigation features are not available in lite version of MapKit");
            
            // Инициализируем загрузчик тайлов
            mTileLoader = new TileLoader();
            if (!mTileLoader.initialize()) {
                Log.w(TAG, "Failed to initialize TileLoader");
            } else {
                // Настраиваем callback для загруженных тайлов
                mTileLoader.setCallback(new TileLoader.TileLoadCallback() {
                    @Override
                    public void onTileLoaded(int tileX, int tileY, int zoom, android.graphics.Bitmap bitmap) {
                        if (bitmap != null && !bitmap.isRecycled()) {
                            // Передаем загруженный тайл в нативный код
                            boolean success = TiggoJavaToJni.OnYandexTileLoaded(tileX, tileY, zoom, bitmap);
                            if (!success) {
                                Log.w(TAG, "Failed to send tile to native code: x=" + tileX + ", y=" + tileY + ", z=" + zoom);
                            }
                        }
                    }
                    
                    @Override
                    public void onTileLoadError(int tileX, int tileY, int zoom, Exception error) {
                        Log.e(TAG, "Error loading tile: x=" + tileX + ", y=" + tileY + ", z=" + zoom, error);
                    }
                });
            }
            
            Log.d(TAG, "Yandex MapKit Bridge initialized successfully");
            
            // Сохраняем статическую ссылку для доступа из JNI
            sInstance = this;
            
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
        
        // Завершаем загрузчик тайлов
        if (mTileLoader != null) {
            mTileLoader.shutdown();
            mTileLoader = null;
        }
        
        // Очищаем статическую ссылку
        sInstance = null;
        
        // TODO: Классы навигации недоступны в lite версии
        // if (mGuidance != null) {
        //     mGuidance.removeGuidanceListener(this);
        // }
        // if (mNavigation != null) {
        //     mNavigation.removeAll();
        // }
        
        Log.d(TAG, "Yandex MapKit Bridge shutdown");
    }
    
    /**
     * Получение экземпляра для доступа из JNI
     */
    public static YandexMapKitBridge getInstance() {
        return sInstance;
    }
    
    /**
     * Получение загрузчика тайлов
     */
    public TileLoader getTileLoader() {
        return mTileLoader;
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
        // TODO: Навигация недоступна в lite версии MapKit
        // Для навигации нужна полная версия MapKit или отдельная библиотека навигации
            return;
    }
    
    /**
     * Извлечение и отправка ограничения скорости
     */
    private void extractAndSendSpeedLimit() {
        // TODO: Навигация недоступна в lite версии
        return;
        /*try {
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
        }*/
    }
    
    /**
     * Извлечение и отправка следующего маневра
     */
    private void extractAndSendManeuver() {
        // TODO: Навигация недоступна в lite версии
        return;
        /*try {
            if (mWindshield == null) {
                return;
            }
            
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
        }*/
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
        // TODO: Навигация недоступна в lite версии
        return;
        /*try {
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
        }*/
    }
    
    /**
     * Извлечение и отправка текущего местоположения
     */
    private void extractAndSendLocation() {
        // TODO: Навигация недоступна в lite версии
        return;
        /*try {
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
        }*/
    }
    
    /**
     * Извлечение и отправка статуса маршрута
     */
    private void extractAndSendRouteStatus() {
        // TODO: Навигация недоступна в lite версии
        return;
        /*try {
            GuidanceStates currentState = mGuidance.getCurrentState();
            boolean isActive = (currentState == GuidanceStates.FOLLOWING_ROUTE ||
                               currentState == GuidanceStates.ROUTE_RECALCULATING);
            boolean isRecalculating = (currentState == GuidanceStates.ROUTE_RECALCULATING);
            TiggoJavaToJni.OnYandexRouteStatus(isActive, isRecalculating);
        } catch (Exception e) {
            Log.e(TAG, "Error extracting route status", e);
        }*/
    }
    
    // TODO: GuidanceListener implementation недоступна в lite версии
    // ========== GuidanceListener implementation ==========
    /*
    @Override
    public void onGuidanceStateChanged(GuidanceStates state) {
        Log.d(TAG, "Guidance state changed: " + state);
        extractAndSendNavigationData();
    }
    
    @Override
    public void onRouteChanged(DrivingRoute route) {
        Log.d(TAG, "Route changed");
        extractAndSendNavigationData();
    }
    
    @Override
    public void onLocationUpdated(Location location) {
        extractAndSendNavigationData();
    }
    */
}

