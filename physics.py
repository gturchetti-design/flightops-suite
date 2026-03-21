import numpy as np

# ============================================================
# INTERNATIONAL STANDARD ATMOSPHERE (ISA)
# ============================================================

def isa(altitude_m):
    """
    Returns temperature (K), pressure (Pa), and density (kg/m³)
    for a given altitude in meters.
    """
    T0 = 288.15      # Sea level temperature (K)
    P0 = 101325.0    # Sea level pressure (Pa)
    rho0 = 1.225     # Sea level density (kg/m³)
    L = 0.0065       # Lapse rate (K/m)
    R = 287.05       # Gas constant for air
    g = 9.80665      # Gravity (m/s²)

    if altitude_m <= 11000:  # Troposphere
        T = T0 - L * altitude_m
        P = P0 * (T / T0) ** (g / (R * L))
    else:  # Stratosphere (up to 20,000m)
        T11 = T0 - L * 11000
        P11 = P0 * (T11 / T0) ** (g / (R * L))
        T = T11
        P = P11 * np.exp(-g * (altitude_m - 11000) / (R * T11))

    rho = P / (R * T)
    return T, P, rho


# ============================================================
# AIRCRAFT PARAMETERS
# ============================================================

AIRCRAFT = {
    "Boeing 737-800": {
        "CD0": 0.0265,
        "k": 0.0375,
        "S": 125.0,       # Wing area (m²)
        "MTOW": 79016,    # Max takeoff weight (kg)
        "OEW": 41413,     # Operating empty weight (kg)
        "max_fuel": 26020,# Max fuel (kg)
        "TSFC": 1.58e-5,  # kg/(N·s)
        "cruise_mach": 0.785,
        "cruise_alt": 11000,  # meters
    },
    "Boeing 787-9": {
        "CD0": 0.0210,
        "k": 0.0340,
        "S": 325.0,
        "MTOW": 254011,
        "OEW": 128850,
        "max_fuel": 126920,
        "TSFC": 1.42e-5,
        "cruise_mach": 0.850,
        "cruise_alt": 12500,
    },
    "Airbus A320neo": {
        "CD0": 0.0250,
        "k": 0.0370,
        "S": 122.6,
        "MTOW": 79000,
        "OEW": 42600,
        "max_fuel": 26730,
        "TSFC": 1.54e-5,
        "cruise_mach": 0.780,
        "cruise_alt": 11900,
    },
    "Airbus A350-900": {
        "CD0": 0.0200,
        "k": 0.0320,
        "S": 442.0,
        "MTOW": 280000,
        "OEW": 142400,
        "max_fuel": 158000,
        "TSFC": 1.38e-5,
        "cruise_mach": 0.850,
        "cruise_alt": 13100,
    },
}


# ============================================================
# AERODYNAMICS
# ============================================================

def lift_coefficient(W, rho, V, S):
    """CL = 2W / (rho * V² * S)"""
    return (2 * W) / (rho * V**2 * S)

def drag_coefficient(CL, CD0, k):
    """CD = CD0 + k * CL²"""
    return CD0 + k * CL**2

def lift_to_drag(CL, CD):
    return CL / CD

def best_LD(CD0, k):
    """Maximum L/D and the CL at which it occurs"""
    CL_best = np.sqrt(CD0 / k)
    LD_max = 1 / (2 * np.sqrt(CD0 * k))
    return CL_best, LD_max


# ============================================================
# BREGUET RANGE & FUEL BURN
# ============================================================

def breguet_fuel(W_initial, range_m, TSFC, LD, V):
    """
    Estimates fuel burned over a given range using the Breguet equation.
    Returns fuel burned in kg.
    """
    g = 9.80665
    W_final = W_initial * np.exp(-TSFC * g * range_m / (V * LD))
    fuel_burned = W_initial - W_final
    return fuel_burned, W_final


# ============================================================
# CRUISE ALTITUDE OPTIMIZER
# ============================================================

def best_cruise_altitude(aircraft_name, W, step=500):
    """
    Finds the altitude that maximizes L/D for a given aircraft and weight.
    Returns best altitude (m) and the L/D at that altitude.
    """
    ac = AIRCRAFT[aircraft_name]
    altitudes = np.arange(5000, 14000, step)
    best_alt = 0
    best_ld = 0

    for alt in altitudes:
        T, P, rho = isa(alt)
        V = ac["cruise_mach"] * np.sqrt(1.4 * 287.05 * T)
        CL = lift_coefficient(W, rho, V, ac["S"])
        CD = drag_coefficient(CL, ac["CD0"], ac["k"])
        ld = lift_to_drag(CL, CD)
        if ld > best_ld:
            best_ld = ld
            best_alt = alt

    return best_alt, best_ld


# ============================================================
# QUICK TEST
# ============================================================

if __name__ == "__main__":
    print("=== ISA Test ===")
    for alt in [0, 5000, 11000, 13000]:
        T, P, rho = isa(alt)
        print(f"Alt: {alt}m | T: {T:.1f}K | P: {P:.0f}Pa | rho: {rho:.4f} kg/m³")

    print("\n=== Best L/D per Aircraft ===")
    for name, ac in AIRCRAFT.items():
        CL_best, LD_max = best_LD(ac["CD0"], ac["k"])
        print(f"{name}: Max L/D = {LD_max:.2f} at CL = {CL_best:.4f}")

    print("\n=== Cruise Altitude Optimizer ===")
    for name, ac in AIRCRAFT.items():
        W = ac["MTOW"] * 9.80665 * 0.85
        best_alt, best_ld = best_cruise_altitude(name, W)
        print(f"{name}: Best alt = {best_alt}m | L/D = {best_ld:.2f}")