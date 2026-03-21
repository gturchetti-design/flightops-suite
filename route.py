import numpy as np
import requests
from physics import AIRCRAFT, isa, best_LD, breguet_fuel, best_cruise_altitude

# ============================================================
# AIRPORT COORDINATES
# ============================================================

AIRPORTS = {
    "ORD": {"name": "Chicago O'Hare", "lat": 41.9742, "lon": -87.9073},
    "LAX": {"name": "Los Angeles", "lat": 33.9425, "lon": -118.4081},
    "JFK": {"name": "New York JFK", "lat": 40.6413, "lon": -73.7781},
    "LHR": {"name": "London Heathrow", "lat": 51.4700, "lon": -0.4543},
    "CDG": {"name": "Paris Charles de Gaulle", "lat": 49.0097, "lon": 2.5479},
    "MAD": {"name": "Madrid Barajas", "lat": 40.4983, "lon": -3.5676},
    "MXP": {"name": "Milan Malpensa", "lat": 45.6306, "lon": 8.7281},
    "NRT": {"name": "Tokyo Narita", "lat": 35.7720, "lon": 140.3929},
    "DXB": {"name": "Dubai", "lat": 25.2532, "lon": 55.3657},
    "SYD": {"name": "Sydney", "lat": -33.9461, "lon": 151.1772},
    "GRU": {"name": "Sao Paulo", "lat": -23.4356, "lon": -46.4731},
    "IAD": {"name": "Washington Dulles", "lat": 38.9531, "lon": -77.4565},
    "SFO": {"name": "San Francisco", "lat": 37.6213, "lon": -122.3790},
    "MIA": {"name": "Miami", "lat": 25.7959, "lon": -80.2870},
    "BCN": {"name": "Barcelona", "lat": 41.2974, "lon": 2.0833},
}


# ============================================================
# GREAT CIRCLE DISTANCE
# ============================================================

def great_circle_distance(lat1, lon1, lat2, lon2):
    """
    Returns distance in meters between two coordinates
    using the Haversine formula.
    """
    R = 6371000  # Earth radius in meters
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)

    a = np.sin(dphi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    return R * c


def route_waypoints(lat1, lon1, lat2, lon2, n=50):
    """
    Returns n intermediate points along the great circle route.
    Used for drawing the route on the map.
    """
    waypoints = []
    for i in np.linspace(0, 1, n):
        lat = lat1 + (lat2 - lat1) * i
        lon = lon1 + (lon2 - lon1) * i
        waypoints.append((lat, lon))
    return waypoints


# ============================================================
# WIND DATA (Open-Meteo API)
# ============================================================

def get_wind(lat, lon, altitude_m):
    """
    Fetches real wind speed at a given location and altitude.
    Returns wind speed in m/s.
    """
    pressure_levels = {
        5000: 550, 8000: 400, 11000: 250, 13000: 200
    }
    closest = min(pressure_levels.keys(), key=lambda x: abs(x - altitude_m))
    level = pressure_levels[closest]

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=windspeed_{level}hPa"
        f"&forecast_days=1&timezone=UTC"
    )

    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        wind_kph = data["hourly"][f"windspeed_{level}hPa"][0]
        return wind_kph / 3.6  # Convert to m/s
    except:
        return 0.0  # If API fails, assume no wind


# ============================================================
# FULL ROUTE ANALYSIS
# ============================================================

def analyze_route(origin_code, destination_code, aircraft_name, payload_kg=15000):
    """
    Full route performance analysis.
    Returns a dictionary with all results.
    """
    ac = AIRCRAFT[aircraft_name]
    origin = AIRPORTS[origin_code]
    destination = AIRPORTS[destination_code]

    # Distance
    distance_m = great_circle_distance(
        origin["lat"], origin["lon"],
        destination["lat"], destination["lon"]
    )
    distance_km = distance_m / 1000

    # Weight
    W_kg = ac["OEW"] + payload_kg + ac["max_fuel"] * 0.85
    W_N = W_kg * 9.80665

    # Best cruise altitude
    best_alt, best_ld = best_cruise_altitude(aircraft_name, W_N)

    # Atmosphere at cruise
    T, P, rho = isa(best_alt)
    V = ac["cruise_mach"] * np.sqrt(1.4 * 287.05 * T)

    # Wind at midpoint
    mid_lat = (origin["lat"] + destination["lat"]) / 2
    mid_lon = (origin["lon"] + destination["lon"]) / 2
    wind_ms = get_wind(mid_lat, mid_lon, best_alt)
    V_ground = V + wind_ms  # simplified tailwind assumption

    # Fuel burn
    fuel_burned, W_final = breguet_fuel(W_N, distance_m, ac["TSFC"], best_ld, V)
    fuel_burned_kg = fuel_burned / 9.80665

    # Flight time
    flight_time_hr = distance_m / (V_ground * 3600)

    # Waypoints for map
    waypoints = route_waypoints(
        origin["lat"], origin["lon"],
        destination["lat"], destination["lon"]
    )

    return {
        "origin": origin["name"],
        "destination": destination["name"],
        "aircraft": aircraft_name,
        "distance_km": round(distance_km, 1),
        "cruise_altitude_m": best_alt,
        "cruise_altitude_ft": round(best_alt * 3.28084),
        "cruise_speed_ms": round(V, 1),
        "cruise_speed_kts": round(V * 1.94384),
        "wind_ms": round(wind_ms, 1),
        "LD_ratio": round(best_ld, 2),
        "fuel_burned_kg": round(fuel_burned_kg, 1),
        "fuel_burned_lbs": round(fuel_burned_kg * 2.205),
        "flight_time_hr": round(flight_time_hr, 2),
        "waypoints": waypoints,
    }


# ============================================================
# QUICK TEST
# ============================================================

if __name__ == "__main__":
    print("=== Route Analysis Test: ORD → LHR on Boeing 787-9 ===\n")
    result = analyze_route("ORD", "LHR", "Boeing 787-9")
    for key, value in result.items():
        if key != "waypoints":
            print(f"{key}: {value}")