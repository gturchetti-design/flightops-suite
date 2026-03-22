import numpy as np
import requests
from physics import AIRCRAFT, isa, best_LD, breguet_fuel, best_cruise_altitude, base_ticket_price

# ============================================================
# AIRPORT COORDINATES
# ============================================================

AIRPORTS = {
    # North America
    "ORD": {"name": "Chicago O'Hare", "lat": 41.9742, "lon": -87.9073},
    "LAX": {"name": "Los Angeles", "lat": 33.9425, "lon": -118.4081},
    "JFK": {"name": "New York JFK", "lat": 40.6413, "lon": -73.7781},
    "SFO": {"name": "San Francisco", "lat": 37.6213, "lon": -122.3790},
    "MIA": {"name": "Miami", "lat": 25.7959, "lon": -80.2870},
    "IAD": {"name": "Washington Dulles", "lat": 38.9531, "lon": -77.4565},
    "YYZ": {"name": "Toronto Pearson", "lat": 43.6777, "lon": -79.6248},
    "YVR": {"name": "Vancouver", "lat": 49.1967, "lon": -123.1815},
    "MEX": {"name": "Mexico City", "lat": 19.4363, "lon": -99.0721},
    "EWR": {"name": "New York Newark", "lat": 40.6895, "lon": -74.1745},
    "BOS": {"name": "Boston", "lat": 42.3656, "lon": -71.0096},
    "SEA": {"name": "Seattle", "lat": 47.4502, "lon": -122.3088},
    "DEN": {"name": "Denver", "lat": 39.8561, "lon": -104.6737},
    "ATL": {"name": "Atlanta", "lat": 33.6407, "lon": -84.4277},
    # Europe
    "LHR": {"name": "London Heathrow", "lat": 51.4700, "lon": -0.4543},
    "CDG": {"name": "Paris Charles de Gaulle", "lat": 49.0097, "lon": 2.5479},
    "MAD": {"name": "Madrid Barajas", "lat": 40.4983, "lon": -3.5676},
    "BCN": {"name": "Barcelona", "lat": 41.2974, "lon": 2.0833},
    "MXP": {"name": "Milan Malpensa", "lat": 45.6306, "lon": 8.7281},
    "FCO": {"name": "Rome Fiumicino", "lat": 41.8003, "lon": 12.2389},
    "AMS": {"name": "Amsterdam Schiphol", "lat": 52.3086, "lon": 4.7639},
    "FRA": {"name": "Frankfurt", "lat": 50.0379, "lon": 8.5622},
    "MUC": {"name": "Munich", "lat": 48.3537, "lon": 11.7750},
    "ZRH": {"name": "Zurich", "lat": 47.4647, "lon": 8.5492},
    "VIE": {"name": "Vienna", "lat": 48.1103, "lon": 16.5697},
    "LIS": {"name": "Lisbon", "lat": 38.7756, "lon": -9.1354},
    "ATH": {"name": "Athens", "lat": 37.9364, "lon": 23.9445},
    "IST": {"name": "Istanbul", "lat": 41.2608, "lon": 28.7418},
    "CPH": {"name": "Copenhagen", "lat": 55.6181, "lon": 12.6560},
    # Asia
    "NRT": {"name": "Tokyo Narita", "lat": 35.7720, "lon": 140.3929},
    "HND": {"name": "Tokyo Haneda", "lat": 35.5494, "lon": 139.7798},
    "PEK": {"name": "Beijing Capital", "lat": 40.0799, "lon": 116.6031},
    "PVG": {"name": "Shanghai Pudong", "lat": 31.1443, "lon": 121.8083},
    "HKG": {"name": "Hong Kong", "lat": 22.3080, "lon": 113.9185},
    "SIN": {"name": "Singapore Changi", "lat": 1.3644, "lon": 103.9915},
    "BKK": {"name": "Bangkok Suvarnabhumi", "lat": 13.6900, "lon": 100.7501},
    "DEL": {"name": "Delhi Indira Gandhi", "lat": 28.5562, "lon": 77.1000},
    "BOM": {"name": "Mumbai", "lat": 19.0896, "lon": 72.8656},
    "ICN": {"name": "Seoul Incheon", "lat": 37.4602, "lon": 126.4407},
    "KUL": {"name": "Kuala Lumpur", "lat": 2.7456, "lon": 101.7099},
    # Middle East & Africa
    "DXB": {"name": "Dubai", "lat": 25.2532, "lon": 55.3657},
    "DOH": {"name": "Doha Hamad", "lat": 25.2609, "lon": 51.6138},
    "AUH": {"name": "Abu Dhabi", "lat": 24.4330, "lon": 54.6511},
    "CAI": {"name": "Cairo", "lat": 30.1219, "lon": 31.4056},
    "JNB": {"name": "Johannesburg", "lat": -26.1392, "lon": 28.2460},
    "NBO": {"name": "Nairobi", "lat": -1.3192, "lon": 36.9275},
    "CMN": {"name": "Casablanca", "lat": 33.3675, "lon": -7.5898},
    # Oceania & South America
    "SYD": {"name": "Sydney", "lat": -33.9461, "lon": 151.1772},
    "MEL": {"name": "Melbourne", "lat": -37.6690, "lon": 144.8410},
    "AKL": {"name": "Auckland", "lat": -37.0082, "lon": 174.7917},
    "GRU": {"name": "Sao Paulo Guarulhos", "lat": -23.4356, "lon": -46.4731},
    "EZE": {"name": "Buenos Aires", "lat": -34.8222, "lon": -58.5358},
    "BOG": {"name": "Bogota", "lat": 4.7016, "lon": -74.1469},
    "LIM": {"name": "Lima", "lat": -12.0219, "lon": -77.1143},
    "SCL": {"name": "Santiago", "lat": -33.3930, "lon": -70.7858},
}


# ============================================================
# GREAT CIRCLE DISTANCE
# ============================================================

def great_circle_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c


def route_waypoints(lat1, lon1, lat2, lon2, n=100):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])

    def to_cart(lat, lon):
        return np.array([np.cos(lat)*np.cos(lon),
                         np.cos(lat)*np.sin(lon),
                         np.sin(lat)])

    p1 = to_cart(lat1, lon1)
    p2 = to_cart(lat2, lon2)
    omega = np.arccos(np.clip(np.dot(p1, p2), -1, 1))

    waypoints = []
    for t in np.linspace(0, 1, n):
        if omega < 1e-10:
            p = p1
        else:
            p = (np.sin((1-t)*omega)*p1 + np.sin(t*omega)*p2) / np.sin(omega)
        lat = np.degrees(np.arcsin(p[2]))
        lon = np.degrees(np.arctan2(p[1], p[0]))
        waypoints.append((lat, lon))

    return waypoints


# ============================================================
# WIND DATA
# ============================================================

def get_wind_along_route(waypoints, altitude_m):
    """
    Samples wind at the route midpoint.
    Returns wind speed in m/s.
    """
    pressure_levels = {5000: 550, 8000: 400, 11000: 250, 13000: 200, 18000: 100}
    closest = min(pressure_levels.keys(), key=lambda x: abs(x - altitude_m))
    level = pressure_levels[closest]

    mid = waypoints[len(waypoints)//2]
    lat, lon = mid

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=windspeed_{level}hPa"
        f"&forecast_days=1&timezone=UTC"
    )
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        wind_kph = data["hourly"][f"windspeed_{level}hPa"][6]
        return round(wind_kph / 3.6, 1)
    except:
        return 0.0


# ============================================================
# CO2 EMISSIONS
# ============================================================

def co2_emissions(fuel_burned_kg):
    co2_kg = fuel_burned_kg * 3.16
    co2_tonnes = co2_kg / 1000
    return round(co2_kg, 1), round(co2_tonnes, 2)


# ============================================================
# PROFITABILITY
# ============================================================

def profitability(aircraft_name, fuel_burned_kg, distance_km,
                  fuel_price_per_kg, ticket_price, load_factor):
    ac = AIRCRAFT[aircraft_name]
    seats = ac["seats"]

    if seats == 0:
        return {
            "seats": 0, "passengers": 0, "revenue": 0,
            "fuel_cost": 0, "profit": 0, "profit_per_pax": 0,
            "is_freighter": True
        }

    passengers = int(seats * load_factor / 100)
    revenue = passengers * ticket_price
    fuel_cost = fuel_burned_kg * fuel_price_per_kg
    profit = revenue - fuel_cost
    profit_per_pax = profit / passengers if passengers > 0 else 0

    return {
        "seats": seats,
        "passengers": passengers,
        "revenue": round(revenue),
        "fuel_cost": round(fuel_cost),
        "profit": round(profit),
        "profit_per_pax": round(profit_per_pax, 2),
        "is_freighter": False
    }


# ============================================================
# FULL ROUTE ANALYSIS
# ============================================================

def analyze_route(origin_code, destination_code, aircraft_name,
                  payload_kg=15000, fuel_price=0.75,
                  load_factor=85, ticket_price_multiplier=1.0):

    ac = AIRCRAFT[aircraft_name]
    origin = AIRPORTS[origin_code]
    destination = AIRPORTS[destination_code]

    distance_m = great_circle_distance(
        origin["lat"], origin["lon"],
        destination["lat"], destination["lon"]
    )
    distance_km = distance_m / 1000

    W_kg = ac["OEW"] + payload_kg + ac["max_fuel"] * 0.85
    W_N = W_kg * 9.80665

    best_alt, best_ld = best_cruise_altitude(aircraft_name, W_N)

    T, P, rho = isa(best_alt)
    V = ac["cruise_mach"] * np.sqrt(1.4 * 287.05 * T)

    waypoints = route_waypoints(
        origin["lat"], origin["lon"],
        destination["lat"], destination["lon"]
    )

    wind_ms = get_wind_along_route(waypoints, best_alt)
    V_ground = V + wind_ms

    fuel_burned, W_final = breguet_fuel(W_N, distance_m, ac["TSFC"], best_ld, V)
    fuel_burned_kg = fuel_burned / 9.80665

    flight_time_hr = distance_m / (V_ground * 3600)

    co2_kg, co2_tonnes = co2_emissions(fuel_burned_kg)

    ticket_price = base_ticket_price(distance_km) * ticket_price_multiplier

    profit_data = profitability(
        aircraft_name, fuel_burned_kg, distance_km,
        fuel_price, ticket_price, load_factor
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
        "wind_ms": wind_ms,
        "LD_ratio": round(best_ld, 2),
        "fuel_burned_kg": round(fuel_burned_kg, 1),
        "fuel_burned_lbs": round(fuel_burned_kg * 2.205),
        "flight_time_hr": round(flight_time_hr, 2),
        "co2_kg": co2_kg,
        "co2_tonnes": co2_tonnes,
        "ticket_price": round(ticket_price),
        **profit_data,
        "waypoints": waypoints,
    }


# ============================================================
# QUICK TEST
# ============================================================

if __name__ == "__main__":
    print("=== Route Analysis: ORD -> LHR on Boeing 787-9 ===\n")
    result = analyze_route("ORD", "LHR", "Boeing 787-9")
    for key, value in result.items():
        if key != "waypoints":
            print(f"{key}: {value}")
