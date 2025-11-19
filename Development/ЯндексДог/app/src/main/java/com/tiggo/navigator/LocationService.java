/**
 * LocationService - Сервис для получения GPS координат (в стиле TurboDog)
 * 
 * Получает геопозицию через LocationManager и передает в native код
 */
package com.tiggo.navigator;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Bundle;
import android.util.Log;
import androidx.core.app.ActivityCompat;

/**
 * Сервис для получения GPS координат
 */
public class LocationService implements LocationListener {
    private static final String TAG = "LocationService";
    
    private static LocationService sInstance = null;
    
    private Context mContext;
    private LocationManager mLocationManager;
    private boolean mEnabled = false;
    
    // Параметры обновления
    private static final long MIN_TIME_MS = 1000; // Минимальное время между обновлениями (1 секунда)
    private static final float MIN_DISTANCE_M = 5.0f; // Минимальное расстояние для обновления (5 метров)
    
    /**
     * Получение экземпляра сервиса
     */
    public static LocationService getInstance() {
        return sInstance;
    }
    
    /**
     * Инициализация сервиса
     */
    public static LocationService initialize(Context context) {
        if (sInstance == null) {
            sInstance = new LocationService(context);
        }
        return sInstance;
    }
    
    /**
     * Конструктор
     */
    private LocationService(Context context) {
        mContext = context.getApplicationContext();
        mLocationManager = (LocationManager) mContext.getSystemService(Context.LOCATION_SERVICE);
    }
    
    /**
     * Запуск получения геопозиции
     */
    public boolean start() {
        if (mEnabled) {
            Log.w(TAG, "LocationService already started");
            return true;
        }
        
        if (mLocationManager == null) {
            Log.e(TAG, "LocationManager is null");
            return false;
        }
        
        // Проверяем разрешения
        if (ActivityCompat.checkSelfPermission(mContext, Manifest.permission.ACCESS_FINE_LOCATION) 
                != PackageManager.PERMISSION_GRANTED &&
            ActivityCompat.checkSelfPermission(mContext, Manifest.permission.ACCESS_COARSE_LOCATION) 
                != PackageManager.PERMISSION_GRANTED) {
            Log.e(TAG, "Location permissions not granted");
            return false;
        }
        
        // Проверяем доступность GPS
        boolean gpsEnabled = mLocationManager.isProviderEnabled(LocationManager.GPS_PROVIDER);
        boolean networkEnabled = mLocationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER);
        
        if (!gpsEnabled && !networkEnabled) {
            Log.e(TAG, "No location providers available");
            return false;
        }
        
        try {
            // Запрашиваем обновления от GPS провайдера (приоритет)
            if (gpsEnabled) {
                mLocationManager.requestLocationUpdates(
                    LocationManager.GPS_PROVIDER,
                    MIN_TIME_MS,
                    MIN_DISTANCE_M,
                    this
                );
                Log.d(TAG, "GPS location updates requested");
            }
            
            // Также запрашиваем от Network провайдера (fallback)
            if (networkEnabled) {
                mLocationManager.requestLocationUpdates(
                    LocationManager.NETWORK_PROVIDER,
                    MIN_TIME_MS,
                    MIN_DISTANCE_M,
                    this
                );
                Log.d(TAG, "Network location updates requested");
            }
            
            // Получаем последнюю известную позицию
            Location lastLocation = null;
            if (gpsEnabled) {
                lastLocation = mLocationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER);
            }
            if (lastLocation == null && networkEnabled) {
                lastLocation = mLocationManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER);
            }
            
            if (lastLocation != null) {
                onLocationChanged(lastLocation);
            }
            
            mEnabled = true;
            Log.d(TAG, "LocationService started successfully");
            return true;
            
        } catch (SecurityException e) {
            Log.e(TAG, "Security exception while requesting location updates", e);
            return false;
        } catch (Exception e) {
            Log.e(TAG, "Error starting LocationService", e);
            return false;
        }
    }
    
    /**
     * Остановка получения геопозиции
     */
    public void stop() {
        if (!mEnabled) {
            return;
        }
        
        if (mLocationManager != null) {
            try {
                mLocationManager.removeUpdates(this);
                Log.d(TAG, "Location updates removed");
            } catch (SecurityException e) {
                Log.e(TAG, "Security exception while removing location updates", e);
            }
        }
        
        mEnabled = false;
        Log.d(TAG, "LocationService stopped");
    }
    
    // ========== LocationListener ==========
    
    @Override
    public void onLocationChanged(Location location) {
        if (location == null) {
            return;
        }
        
        double latitude = location.getLatitude();
        double longitude = location.getLongitude();
        float speed = location.getSpeed() * 3.6f; // Конвертируем м/с в км/ч
        float bearing = location.getBearing();
        float accuracy = location.getAccuracy();
        
        Log.d(TAG, String.format("Location: lat=%.6f, lon=%.6f, speed=%.1f km/h, bearing=%.1f°, accuracy=%.1f m",
            latitude, longitude, speed, bearing, accuracy));
        
        // Передаем координаты в native код
        TiggoJavaToJni.OnLocationUpdate(
            (float)latitude,
            (float)longitude,
            speed,
            bearing,
            accuracy
        );
    }
    
    @Override
    public void onStatusChanged(String provider, int status, Bundle extras) {
        Log.d(TAG, "Location provider status changed: " + provider + ", status=" + status);
    }
    
    @Override
    public void onProviderEnabled(String provider) {
        Log.d(TAG, "Location provider enabled: " + provider);
    }
    
    @Override
    public void onProviderDisabled(String provider) {
        Log.d(TAG, "Location provider disabled: " + provider);
    }
    
    /**
     * Получение текущего состояния
     */
    public boolean isEnabled() {
        return mEnabled;
    }
}

