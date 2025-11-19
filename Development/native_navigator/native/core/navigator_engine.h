#pragma once

#include <memory>
#include <functional>
#include <atomic>
#include <mutex>

#include "navigation_state.h"
#include "route_calculator.h"
#include "gps_processor.h"

namespace tiggo {
namespace navigator {

/**
 * NavigatorEngine - Главный класс навигационного движка
 * 
 * Аналогичен CTurboDogDlg в TurboDog, но использует данные от Yandex
 */
class NavigatorEngine {
public:
    NavigatorEngine();
    ~NavigatorEngine();

    // Инициализация и завершение
    bool Initialize();
    void Shutdown();

    // Навигация
    bool StartNavigation(const Route& route);
    void StopNavigation();
    bool IsNavigationActive() const { return state_.IsNavigationActive(); }
    
    // Обновление (вызывается каждый кадр)
    void Update(float deltaTime);
    
    // Данные от GPS (вызывается при получении GPS данных)
    void OnGpsUpdate(const GpsData& gps);
    
    // Данные от Yandex (вызываются через JNI)
    void OnSpeedLimitReceived(int speedLimitKmh);
    void OnManeuverReceived(const ManeuverData& maneuver);
    void OnRouteReceived(const RouteData& route);
    void OnLocationReceived(const LocationData& location);
    
    // Получение данных
    NavigationState GetState() const { 
        std::lock_guard<std::mutex> lock(state_mutex_);
        return state_;
    }
    
    SpeedLimit GetSpeedLimit() const {
        std::lock_guard<std::mutex> lock(state_mutex_);
        return state_.GetSpeedLimit();
    }
    
    Maneuver GetNextManeuver() const {
        std::lock_guard<std::mutex> lock(state_mutex_);
        return state_.GetNextManeuver();
    }
    
    Location GetCurrentLocation() const {
        std::lock_guard<std::mutex> lock(state_mutex_);
        return state_.GetCurrentLocation();
    }
    
    // Callbacks
    using NavigationStateCallback = std::function<void(const NavigationState&)>;
    void SetStateCallback(NavigationStateCallback callback) {
        state_callback_ = callback;
    }
    
private:
    // Состояние
    NavigationState state_;
    mutable std::mutex state_mutex_;
    
    // Компоненты
    std::unique_ptr<RouteCalculator> route_calculator_;
    std::unique_ptr<GpsProcessor> gps_processor_;
    
    // Callbacks
    NavigationStateCallback state_callback_;
    
    // Флаги
    std::atomic<bool> initialized_{false};
    std::atomic<bool> navigation_active_{false};
    
    // Внутренние методы
    void UpdateNavigationState(float deltaTime);
    void NotifyStateChanged();
};

} // namespace navigator
} // namespace tiggo

