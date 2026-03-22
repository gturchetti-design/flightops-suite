import numpy as np

# ============================================================
# INTERNATIONAL STANDARD ATMOSPHERE (ISA)
# ============================================================

def isa(altitude_m):
    T0 = 288.15
    P0 = 101325.0
    L = 0.0065
    R = 287.05
    g = 9.80665

    if altitude_m <= 11000:
        T = T0 - L * altitude_m
        P = P0 * (T / T0) ** (g / (R * L))
    else:
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
    # ── NARROWBODY ──────────────────────────────────────────
    "Boeing 737-800": {
        "CD0": 0.0265, "k": 0.0375, "S": 125.0,
        "MTOW": 79016, "OEW": 41413, "max_fuel": 26020,
        "TSFC": 1.58e-5, "cruise_mach": 0.785, "cruise_alt": 11000,
        "seats": 162,
    },
    "Boeing 737 MAX 9": {
        "CD0": 0.0248, "k": 0.0365, "S": 125.0,
        "MTOW": 88314, "OEW": 44676, "max_fuel": 25816,
        "TSFC": 1.48e-5, "cruise_mach": 0.785, "cruise_alt": 11900,
        "seats": 178,
    },
    "Boeing 757-200": {
        "CD0": 0.0270, "k": 0.0380, "S": 185.3,
        "MTOW": 115680, "OEW": 57840, "max_fuel": 43400,
        "TSFC": 1.65e-5, "cruise_mach": 0.800, "cruise_alt": 11900,
        "seats": 176,
    },
    "Airbus A220-300": {
        "CD0": 0.0242, "k": 0.0362, "S": 112.3,
        "MTOW": 70900, "OEW": 38800, "max_fuel": 21805,
        "TSFC": 1.45e-5, "cruise_mach": 0.820, "cruise_alt": 12500,
        "seats": 130,
    },
    "Airbus A320neo": {
        "CD0": 0.0250, "k": 0.0370, "S": 122.6,
        "MTOW": 79000, "OEW": 42600, "max_fuel": 26730,
        "TSFC": 1.54e-5, "cruise_mach": 0.780, "cruise_alt": 11900,
        "seats": 150,
    },
    "Airbus A321neo": {
        "CD0": 0.0252, "k": 0.0372, "S": 122.6,
        "MTOW": 97000, "OEW": 50100, "max_fuel": 32940,
        "TSFC": 1.52e-5, "cruise_mach": 0.780, "cruise_alt": 12100,
        "seats": 180,
    },
    "Embraer E195-E2": {
        "CD0": 0.0255, "k": 0.0378, "S": 92.5,
        "MTOW": 61000, "OEW": 33600, "max_fuel": 18800,
        "TSFC": 1.50e-5, "cruise_mach": 0.820, "cruise_alt": 12500,
        "seats": 120,
    },
    "Bombardier CRJ-900": {
        "CD0": 0.0278, "k": 0.0392, "S": 70.6,
        "MTOW": 36514, "OEW": 21319, "max_fuel": 10600,
        "TSFC": 1.72e-5, "cruise_mach": 0.780, "cruise_alt": 11300,
        "seats": 76,
    },
    "ATR 72-600": {
        "CD0": 0.0310, "k": 0.0420, "S": 61.0,
        "MTOW": 23000, "OEW": 13500, "max_fuel": 6370,
        "TSFC": 1.95e-5, "cruise_mach": 0.410, "cruise_alt": 7500,
        "seats": 70,
    },
    # ── WIDEBODY ────────────────────────────────────────────
    "Boeing 767-300ER": {
        "CD0": 0.0258, "k": 0.0368, "S": 283.3,
        "MTOW": 186880, "OEW": 90900, "max_fuel": 91370,
        "TSFC": 1.62e-5, "cruise_mach": 0.800, "cruise_alt": 11900,
        "seats": 218,
    },
    "Boeing 777-300ER": {
        "CD0": 0.0228, "k": 0.0348, "S": 436.8,
        "MTOW": 352400, "OEW": 167800, "max_fuel": 181300,
        "TSFC": 1.50e-5, "cruise_mach": 0.840, "cruise_alt": 12500,
        "seats": 386,
    },
    "Boeing 777X (777-9)": {
        "CD0": 0.0210, "k": 0.0330, "S": 466.8,
        "MTOW": 352400, "OEW": 167800, "max_fuel": 197400,
        "TSFC": 1.38e-5, "cruise_mach": 0.850, "cruise_alt": 13100,
        "seats": 426,
    },
    "Boeing 787-9": {
        "CD0": 0.0210, "k": 0.0340, "S": 325.0,
        "MTOW": 254011, "OEW": 128850, "max_fuel": 126920,
        "TSFC": 1.42e-5, "cruise_mach": 0.850, "cruise_alt": 12500,
        "seats": 296,
    },
    "Boeing 747-8F": {
        "CD0": 0.0245, "k": 0.0355, "S": 541.2,
        "MTOW": 447696, "OEW": 197131, "max_fuel": 226100,
        "TSFC": 1.55e-5, "cruise_mach": 0.855, "cruise_alt": 12500,
        "seats": 0,
    },
    "Airbus A330-900neo": {
        "CD0": 0.0228, "k": 0.0348, "S": 361.6,
        "MTOW": 251000, "OEW": 127500, "max_fuel": 139090,
        "TSFC": 1.44e-5, "cruise_mach": 0.825, "cruise_alt": 12500,
        "seats": 287,
    },
    "Airbus A330-200F": {
        "CD0": 0.0238, "k": 0.0355, "S": 361.6,
        "MTOW": 233000, "OEW": 109300, "max_fuel": 139090,
        "TSFC": 1.58e-5, "cruise_mach": 0.820, "cruise_alt": 11900,
        "seats": 0,
    },
    "Airbus A350-900": {
        "CD0": 0.0200, "k": 0.0320, "S": 442.0,
        "MTOW": 280000, "OEW": 142400, "max_fuel": 158000,
        "TSFC": 1.38e-5, "cruise_mach": 0.850, "cruise_alt": 13100,
        "seats": 369,
    },
    "Airbus A380-800": {
        "CD0": 0.0225, "k": 0.0338, "S": 845.0,
        "MTOW": 575000, "OEW": 276800, "max_fuel": 320000,
        "TSFC": 1.48e-5, "cruise_mach": 0.850, "cruise_alt": 13100,
        "seats": 555,
    },
    # ── SUPERSONIC ──────────────────────────────────────────
    "Concorde": {
        "CD0": 0.0350, "k": 0.0850, "S": 358.6,
        "MTOW": 187700, "OEW": 78700, "max_fuel": 119500,
        "TSFC": 3.20e-5, "cruise_mach": 2.040, "cruise_alt": 18000,
        "seats": 100,
    },
    "Boom Overture": {
        "CD0": 0.0280, "k": 0.0650, "S": 290.0,
        "MTOW": 170000, "OEW": 75000, "max_fuel": 95000,
        "TSFC": 2.40e-5, "cruise_mach": 1.700, "cruise_alt": 18000,
        "seats": 65,
    },
}


# ============================================================
# AERODYNAMICS
# ============================================================

def lift_coefficient(W, rho, V, S):
    return (2 * W) / (rho * V**2 * S)

def drag_coefficient(CL, CD0, k):
    return CD0 + k * CL**2

def lift_to_drag(CL, CD):
    return CL / CD

def best_LD(CD0, k):
    CL_best = np.sqrt(CD0 / k)
    LD_max = 1 / (2 * np.sqrt(CD0 * k))
    return CL_best, LD_max


# ============================================================
# BREGUET RANGE & FUEL BURN
# ============================================================

def breguet_fuel(W_initial, range_m, TSFC, LD, V):
    g = 9.80665
    W_final = W_initial * np.exp(-TSFC * g * range_m / (V * LD))
    fuel_burned = W_initial - W_final
    return fuel_burned, W_final


# ============================================================
# TICKET PRICE MODEL (price per km based on route distance)
# ============================================================

def base_ticket_price(distance_km):
    if distance_km < 500:
        return distance_km * 0.25
    elif distance_km < 2000:
        return distance_km * 0.18
    elif distance_km < 5000:
        return distance_km * 0.12
    elif distance_km < 10000:
        return distance_km * 0.09
    else:
        return distance_km * 0.07


# ============================================================
# CRUISE ALTITUDE OPTIMIZER
# ============================================================

def best_cruise_altitude(aircraft_name, W, step=500):
    ac = AIRCRAFT[aircraft_name]
    max_alt = 20000 if ac["cruise_alt"] > 14000 else 14000
    altitudes = np.arange(5000, max_alt, step)
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
    print("=== Best L/D per Aircraft ===")
    for name, ac in AIRCRAFT.items():
        CL_best, LD_max = best_LD(ac["CD0"], ac["k"])
        print(f"{name}: Max L/D = {LD_max:.2f} | Seats = {ac['seats']}")