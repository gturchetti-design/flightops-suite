"""
FlightOps Suite -Route Viability Score  (MODULE 2)

compute_viability_score(result: dict) -> dict

Takes the full output of route.analyze_route() and returns a scored
assessment suitable for display to airline analysts and consultants.

Scoring (0-100):
  Financial     0-40  -margin, RASM/CASM spread, profit per pax
  Operational   0-25  -fuel headroom, aerodynamic efficiency, break-even LF
  ESG           0-20  -CO2/pax vs IATA distance-band benchmarks
  Market fit    0-15  -aircraft type vs route distance category
"""

from physics import AIRCRAFT

# ── ESG benchmarks (IATA 2023, total CO2 per passenger per flight) ────────────
# These are representative values by haul category, not per-km rates.
# Short-haul flights emit less total CO2 per pax because the route is shorter;
# long-haul emit more per pax in absolute terms despite better airframe efficiency.
_ESG_BENCHMARKS = {
    "short":  {"max_km": 2000,  "kg": 255.0},
    "medium": {"max_km": 5000,  "kg": 195.0},
    "long":   {"max_km": float("inf"), "kg": 150.0},
}

# ── Verdict thresholds ────────────────────────────────────────────────────────
_LAUNCH_THRESHOLD  = 70
_OPTIMIZE_THRESHOLD = 45

# ── Verdict colours (align with app design palette) ───────────────────────────
_COLORS = {
    "LAUNCH":   "#00d68f",
    "OPTIMIZE": "#f5a623",
    "AVOID":    "#f04040",
    "N/A":      "#6a8faf",
}


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _aircraft_category(aircraft_name: str) -> str:
    """Classify aircraft into one of four route-strategy categories."""
    ac = AIRCRAFT[aircraft_name]
    seats = ac["seats"]
    if ac["cruise_mach"] >= 1.5:
        return "supersonic"
    if seats == 0:
        return "freighter"
    if seats < 100:
        return "regional"
    if seats < 200:
        return "narrowbody"
    return "widebody"


def _esg_benchmark(distance_km: float) -> float:
    """Return the appropriate CO2/pax benchmark (kg) for this route distance."""
    for band in ("short", "medium", "long"):
        if distance_km < _ESG_BENCHMARKS[band]["max_km"]:
            return _ESG_BENCHMARKS[band]["kg"]
    return _ESG_BENCHMARKS["long"]["kg"]


def _score_financial(result: dict, passengers: int) -> tuple[int, float, float, float]:
    """
    Returns (score, op_margin, rasm_casm_ratio, op_profit_per_pax).
    Score max: 40.
    """
    op_margin = result.get("op_margin_pct") or 0.0
    rasm      = result.get("rasm_cents")    or 0.0
    casm      = result.get("casm_cents")    or 1.0   # avoid div-by-zero
    op_profit = result.get("op_profit")     or 0.0

    profit_per_pax = op_profit / passengers if passengers > 0 else 0.0

    # Operating margin (0-20)
    if op_margin > 30:
        margin_pts = 20
    elif op_margin >= 15:
        margin_pts = 12
    elif op_margin >= 0:
        margin_pts = 6
    else:
        margin_pts = 0

    # RASM vs CASM spread (0-12)
    ratio = rasm / casm if casm > 0 else 0.0
    if ratio >= 1.50:
        spread_pts = 12
    elif ratio >= 1.20:
        spread_pts = 8
    elif ratio >= 1.00:
        spread_pts = 4
    else:
        spread_pts = 0

    # Operating profit per passenger (0-8)
    if profit_per_pax > 300:
        pax_pts = 8
    elif profit_per_pax >= 150:
        pax_pts = 5
    elif profit_per_pax >= 50:
        pax_pts = 2
    else:
        pax_pts = 0

    score = margin_pts + spread_pts + pax_pts
    return score, op_margin, ratio, profit_per_pax


def _score_operational(result: dict, aircraft_name: str) -> int:
    """Score max: 25."""
    ac           = AIRCRAFT[aircraft_name]
    fuel_burned  = result["fuel_burned_kg"]
    max_fuel     = ac["max_fuel"]
    fuel_pct     = fuel_burned / max_fuel if max_fuel > 0 else 1.0
    ld_ratio     = result.get("LD_ratio") or 0.0
    belf         = result.get("breakeven_lf")   # may be None

    # Fuel headroom -how much fuel reserve exists (0-10)
    if fuel_pct < 0.70:
        fuel_pts = 10
    elif fuel_pct < 0.85:
        fuel_pts = 6
    elif fuel_pct < 0.95:
        fuel_pts = 2
    else:
        fuel_pts = 0

    # Aerodynamic efficiency -L/D at cruise (0-8)
    if ld_ratio > 18:
        ld_pts = 8
    elif ld_ratio >= 15:
        ld_pts = 5
    elif ld_ratio >= 12:
        ld_pts = 3
    else:
        ld_pts = 1

    # Break-even load factor (0-7)
    if belf is None:
        belf_pts = 0
    elif belf < 50:
        belf_pts = 7
    elif belf < 65:
        belf_pts = 4
    elif belf < 80:
        belf_pts = 2
    else:
        belf_pts = 0

    return fuel_pts + ld_pts + belf_pts


def _score_esg(
    result: dict, passengers: int, distance_km: float
) -> tuple[int, float, float, float]:
    """
    Returns (score, co2_per_pax, benchmark, pct_vs_benchmark).
    pct_vs_benchmark < 0 means better than benchmark.
    Score max: 20.
    """
    co2_kg      = result.get("co2_kg") or 0.0
    co2_per_pax = co2_kg / passengers if passengers > 0 else 0.0
    benchmark   = _esg_benchmark(distance_km)
    pct         = (co2_per_pax - benchmark) / benchmark * 100   # negative = better

    if pct < -20:     # >20% below benchmark
        pts = 20
    elif pct < -10:   # 10–20% below
        pts = 14
    elif pct < 0:     # 0–10% below
        pts = 8
    else:             # above benchmark
        pts = 3

    return pts, round(co2_per_pax, 1), benchmark, round(pct, 1)


def _score_market(aircraft_cat: str, distance_km: float) -> int:
    """Score max: 15."""
    if aircraft_cat == "supersonic":
        return 10

    if aircraft_cat == "narrowbody":
        if distance_km < 3000:
            return 15
        elif distance_km < 5000:
            return 8
        else:
            return 2

    if aircraft_cat == "widebody":
        if distance_km > 5000:
            return 15
        elif distance_km >= 3000:
            return 10
        else:
            return 4

    if aircraft_cat == "regional":
        if distance_km < 1500:
            return 15
        elif distance_km < 3000:
            return 6
        else:
            return 0

    return 0   # freighter or unknown


def _build_explanation(
    verdict: str,
    fin: int, ops: int, esg: int, mkt: int,
    op_margin: float,
    rasm_casm_ratio: float,
    profit_per_pax: float,
    co2_pct: float,
    belf: float | None,
    aircraft_cat: str,
    distance_km: float,
) -> str:
    """
    Generate a single plain-English sentence that explains the verdict by
    referencing the dominant strength and the most limiting weakness.
    """
    # Normalised score ratios to find weakest/strongest dimension
    ratios = {
        "financial":    fin / 40,
        "operational":  ops / 25,
        "ESG":          esg / 20,
        "market fit":   mkt / 15,
    }
    ranked = sorted(ratios.items(), key=lambda x: x[1])
    weakest   = ranked[0][0]
    strongest = ranked[-1][0]

    belf_str   = f"{belf:.0f}%" if belf is not None else "unknown"
    margin_str = f"{op_margin:.0f}%"
    ratio_str  = f"{rasm_casm_ratio:.1f}x"

    if verdict == "LAUNCH":
        if esg == 3:   # long-haul ESG hit -the only significant drag
            return (
                f"Strong financial ({margin_str} margin, {ratio_str} RASM/CASM) and "
                f"operational efficiency confirm this as a launch-ready route; "
                f"CO2 per passenger sits above the long-haul IATA benchmark "
                f"({co2_pct:+.0f}%), which is typical for intercontinental operations."
            )
        if aircraft_cat == "supersonic":
            return (
                f"Niche supersonic market with {margin_str} operating margin -"
                f"viable for premium positioning but dependent on consistent high-yield demand."
            )
        if mkt <= 4:   # good economics but aircraft-distance mismatch
            return (
                f"Strong unit economics ({margin_str} margin, {belf_str} break-even LF) "
                f"but the aircraft is over-specified for this route distance; "
                f"a smaller, better-matched type would improve CASM and schedule flexibility."
            )
        return (
            f"Excellent economics ({margin_str} margin, {ratio_str} RASM/CASM, "
            f"{belf_str} break-even load factor) and strong aircraft-route alignment "
            f"make this a high-confidence launch decision with limited downside risk."
        )

    if verdict == "OPTIMIZE":
        if weakest == "ESG":
            return (
                f"Solid {strongest} performance ({margin_str} margin) but CO2 per passenger "
                f"is {co2_pct:+.0f}% versus benchmark - aSAF blend or more efficient "
                f"aircraft would meaningfully improve ESG positioning."
            )
        if weakest == "financial":
            return (
                f"Aircraft-route fit scores well but thin margins ({margin_str}) "
                f"and a {belf_str} break-even load factor leave limited buffer against "
                f"demand shocks -pricing or cost structure optimisation is needed."
            )
        if weakest == "market fit":
            return (
                f"Core economics are sound but the aircraft type is sub-optimal for this "
                f"distance category; reassigning to a better-matched fleet type would "
                f"improve unit costs and push this route into launch territory."
            )
        return (
            f"Mixed viability profile -{strongest} is the standout strength but "
            f"{weakest} is a drag; targeted adjustments could unlock full profitability "
            f"within a single schedule cycle."
        )

    # AVOID
    if weakest == "financial" or fin < 15:
        return (
            f"Insufficient operating economics -${profit_per_pax:.0f}/pax operating "
            f"profit and {margin_str} margin make this route financially untenable "
            f"under current assumptions."
        )
    if weakest == "operational" or ops < 10:
        return (
            f"Structural operational mismatch -the aircraft’s fuel requirements "
            f"and aerodynamic profile are poorly suited to this route distance, "
            f"signalling high range or efficiency risk."
        )
    if weakest == "market fit" or mkt <= 4:
        return (
            f"Aircraft type is fundamentally mismatched to this route distance -"
            f"unit economics and passenger experience would both suffer; "
            f"a different aircraft category is required."
        )
    return (
        f"Low scores across multiple dimensions ({weakest} is the weakest at "
        f"{ratios[weakest]:.0%} of maximum) -this route does not meet "
        f"minimum viability thresholds under current parameters."
    )


# ============================================================
# PUBLIC API
# ============================================================

def compute_viability_score(result: dict) -> dict:
    """
    Compute a 0-100 route viability score from a full analyze_route() result.

    Parameters
    ----------
    result : dict
        The complete return value of route.analyze_route().

    Returns
    -------
    dict with keys:
        total_score          int  0-100, or None for freighters
        financial_score      int  0-40
        operational_score    int  0-25
        esg_score            int  0-20
        market_score         int  0-15
        verdict              str  "LAUNCH" | "OPTIMIZE" | "AVOID" | "N/A (freighter)"
        verdict_color        str  hex colour
        explanation          str  one plain-English sentence
        co2_per_pax_kg       float | None
        co2_benchmark_kg     float | None
        co2_vs_benchmark_pct float | None  (negative = better than benchmark)
    """
    # ── Freighter guard ───────────────────────────────────────────────────────
    if result.get("is_freighter"):
        return {
            "total_score":          None,
            "financial_score":      None,
            "operational_score":    None,
            "esg_score":            None,
            "market_score":         None,
            "verdict":              "N/A (freighter)",
            "verdict_color":        _COLORS["N/A"],
            "explanation":          (
                "Freighter aircraft -viability scoring applies to passenger "
                "routes only; freighter economics require a cargo-yield model."
            ),
            "co2_per_pax_kg":       None,
            "co2_benchmark_kg":     None,
            "co2_vs_benchmark_pct": None,
        }

    aircraft_name = result["aircraft"]
    distance_km   = result["distance_km"]
    passengers    = result.get("passengers") or 0
    aircraft_cat  = _aircraft_category(aircraft_name)

    # ── Infeasibility guard ───────────────────────────────────────────────────
    # If the Breguet calculation produced a fuel burn exceeding tank capacity,
    # the route is physically impossible. Override the score immediately rather
    # than letting the financial dimension mask an impossible flight.
    ac = AIRCRAFT[aircraft_name]
    if result["fuel_burned_kg"] > ac["max_fuel"] * 0.95:
        _, co2_pax, co2_bm, co2_pct_raw = _score_esg(result, passengers, distance_km)
        return {
            "total_score":          0,
            "financial_score":      0,
            "operational_score":    0,
            "esg_score":            0,
            "market_score":         0,
            "verdict":              "AVOID",
            "verdict_color":        _COLORS["AVOID"],
            "explanation":          (
                f"The {aircraft_name} cannot physically complete this {distance_km:,.0f} km route; "
                f"required fuel exceeds tank capacity by "
                f"{(result['fuel_burned_kg'] / ac['max_fuel'] - 1) * 100:.0f}%. "
                f"Select a longer-range aircraft such as the Boeing 787-9 or Airbus A350-900."
            ),
            "co2_per_pax_kg":       co2_pax,
            "co2_benchmark_kg":     co2_bm,
            "co2_vs_benchmark_pct": co2_pct_raw,
        }

    # ── Sub-scores ────────────────────────────────────────────────────────────
    financial_score, op_margin, rasm_ratio, ppp = _score_financial(result, passengers)
    operational_score                            = _score_operational(result, aircraft_name)
    esg_score, co2_pax, co2_bm, co2_pct         = _score_esg(result, passengers, distance_km)
    market_score                                 = _score_market(aircraft_cat, distance_km)

    total_score = financial_score + operational_score + esg_score + market_score

    # ── Verdict ───────────────────────────────────────────────────────────────
    if total_score >= _LAUNCH_THRESHOLD:
        verdict = "LAUNCH"
    elif total_score >= _OPTIMIZE_THRESHOLD:
        verdict = "OPTIMIZE"
    else:
        verdict = "AVOID"

    # ── Explanation ───────────────────────────────────────────────────────────
    explanation = _build_explanation(
        verdict,
        financial_score, operational_score, esg_score, market_score,
        op_margin, rasm_ratio, ppp, co2_pct,
        result.get("breakeven_lf"),
        aircraft_cat, distance_km,
    )

    return {
        "total_score":          total_score,
        "financial_score":      financial_score,
        "operational_score":    operational_score,
        "esg_score":            esg_score,
        "market_score":         market_score,
        "verdict":              verdict,
        "verdict_color":        _COLORS[verdict],
        "explanation":          explanation,
        "co2_per_pax_kg":       co2_pax,
        "co2_benchmark_kg":     co2_bm,
        "co2_vs_benchmark_pct": co2_pct,
    }


# ============================================================
# QUICK TEST
# ============================================================

if __name__ == "__main__":
    from route import analyze_route

    cases = [
        ("ORD", "LHR", "Boeing 787-9",        "Long-haul widebody benchmark"),
        ("JFK", "ORD", "Boeing 737 MAX 9",     "Short-medium narrowbody"),
        ("BOS", "JFK", "Bombardier CRJ-900",   "Ultra-short regional"),
        ("BOS", "JFK", "Airbus A380-800",      "Widebody on wrong route (mismatch)"),
        ("JFK", "SIN", "Boeing 737-800",       "Narrowbody on ultra-long haul (infeasible)"),
    ]

    for origin, dest, aircraft, label in cases:
        r = analyze_route(origin, dest, aircraft)
        v = compute_viability_score(r)
        print(f"\n{'='*60}")
        print(f"{label}")
        print(f"{origin} -> {dest}  |  {aircraft}")
        print(f"{'='*60}")
        print(f"  TOTAL SCORE   {v['total_score']}  ->  {v['verdict']}")
        print(f"  Financial     {v['financial_score']}/40")
        print(f"  Operational   {v['operational_score']}/25")
        print(f"  ESG           {v['esg_score']}/20  "
              f"(CO2/pax {v['co2_per_pax_kg']}kg vs {v['co2_benchmark_kg']}kg benchmark, "
              f"{v['co2_vs_benchmark_pct']:+.1f}%)")
        print(f"  Market fit    {v['market_score']}/15")
        print(f"  Explanation:  {v['explanation']}")
