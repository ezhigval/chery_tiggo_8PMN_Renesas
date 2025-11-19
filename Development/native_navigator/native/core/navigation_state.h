#pragma once

#include <string>
#include <chrono>

namespace tiggo {
namespace navigator {

/**
 * Типы данных для навигации
 */

struct Point {
    double latitude;
    double longitude;
    
    Point() : latitude(0.0), longitude(0.0) {}
    Point(double lat, double lon) : latitude(lat), longitude(lon) {}
};

struct SpeedLimit {
    int valueKmh;
    std::string text;
    bool valid;
    
    SpeedLimit() : valueKmh(0), valid(false) {}
    SpeedLimit(int kmh, const std::string& txt) 
        : valueKmh(kmh), text(txt), valid(true) {}
};

enum class ManeuverType {
    STRAIGHT = 0,
    LEFT = 1,
    RIGHT = 2,
    UTURN = 3
};

struct Maneuver {
    ManeuverType type;
    int distanceMeters;
    int timeSeconds;
    std::string title;
    std::string subtitle;
    bool valid;
    
    Maneuver() : type(ManeuverType::STRAIGHT), distanceMeters(0), 
                 timeSeconds(0), valid(false) {}
};

struct Location {
    Point position;
    float bearing;
    float speed;
    std::string roadName;
    bool valid;
    
    Location() : bearing(0.0f), speed(0.0f), valid(false) {}
};

struct Route {
    std::vector<Point> points;
    int totalDistanceMeters;
    int totalTimeSeconds;
    bool valid;
    
    Route() : totalDistanceMeters(0), totalTimeSeconds(0), valid(false) {}
};

/**
 * NavigationState - Состояние навигации
 * 
 * Thread-safe класс для хранения состояния навигации
 */
class NavigationState {
public:
    NavigationState();
    
    // Проверка состояния
    bool IsNavigationActive() const { return navigation_active_; }
    
    // Получение данных
    SpeedLimit GetSpeedLimit() const { return speed_limit_; }
    Maneuver GetNextManeuver() const { return next_maneuver_; }
    Location GetCurrentLocation() const { return current_location_; }
    Route GetCurrentRoute() const { return current_route_; }
    
    // Обновление данных (thread-safe)
    void SetNavigationActive(bool active) { navigation_active_ = active; }
    void SetSpeedLimit(const SpeedLimit& limit) { speed_limit_ = limit; }
    void SetNextManeuver(const Maneuver& maneuver) { next_maneuver_ = maneuver; }
    void SetCurrentLocation(const Location& location) { current_location_ = location; }
    void SetCurrentRoute(const Route& route) { current_route_ = route; }
    
    // Метрики
    int GetRemainingDistance() const { return remaining_distance_; }
    int GetRemainingTime() const { return remaining_time_; }
    void SetRemainingDistance(int meters) { remaining_distance_ = meters; }
    void SetRemainingTime(int seconds) { remaining_time_ = seconds; }
    
private:
    // Состояние навигации
    std::atomic<bool> navigation_active_{false};
    
    // Данные
    SpeedLimit speed_limit_;
    Maneuver next_maneuver_;
    Location current_location_;
    Route current_route_;
    
    // Метрики
    std::atomic<int> remaining_distance_{0};
    std::atomic<int> remaining_time_{0};
    
    // Для thread-safety (используется в NavigatorEngine)
    mutable std::mutex mutex_;
};

} // namespace navigator
} // namespace tiggo

