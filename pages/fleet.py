"""
FlightOps Suite — Fleet Intelligence page  (MODULE 5 upgrade)
Additions: CASM columns, best-use-case tags, route-distance filter, 5 summary cards.
"""
import numpy as np
import dash
from dash import html, dcc, dash_table, Input, Output, callback
from physics import AIRCRAFT, isa, best_LD, breguet_fuel, nonfuel_cost_per_asm

dash.register_page(__name__, path="/fleet", name="Fleet")

# ── Palette ───────────────────────────────────────────────────────────────────
BG     = "#030508"
CARD   = "#04080f"
CARD2  = "#060e1a"
BDR    = "#0a1a2a"
BDR2   = "#0d2030"
CYAN   = "#00c8ff"
GOLD   = "#ffd060"
AMBER  = "#ffd060"
GREEN  = "#00d68f"
WHITE  = "#ffffff"
TSOFT  = "#c8d8e8"
TMID   = "#8ab0c8"
TDIM   = "#3a6080"
TMUTED = "#2a4a65"

_RAJ = "'Rajdhani', sans-serif"
_SG  = "'Space Grotesk', sans-serif"

# Distance limit for the route-distance slider
_DIST_MAX = 20000


# ══════════════════════════════════════════════════════════════════════════════
# DATA BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def _type(name: str, ac: dict) -> str:
    """Aircraft category used for filtering and best-use-case logic."""
    if ac["cruise_mach"] >= 1.5:                     return "Supersonic"
    if ac["seats"] == 0:                              return "Freighter"
    if ac["seats"] >= 200 or ac["S"] >= 280:          return "Widebody"
    if ac["seats"] < 100:                             return "Regional"
    return "Narrowbody"


def _is_turboprop(aircraft_name: str) -> bool:
    """True for piston/turboprop aircraft (cruise Mach < 0.60)."""
    return AIRCRAFT[aircraft_name]["cruise_mach"] < 0.60


def _max_range(ac: dict) -> int:
    """Breguet max range (km) at optimum L/D, 95% fuel, zero payload."""
    g   = 9.80665
    W_i = (ac["OEW"] + ac["max_fuel"] * 0.95) * g
    W_f = (ac["OEW"] + ac["max_fuel"] * 0.05) * g
    if W_f <= 0 or W_i <= W_f:
        return 0
    T, _, _ = isa(ac["cruise_alt"])
    V       = ac["cruise_mach"] * np.sqrt(1.4 * 287.05 * T)
    _, ld   = best_LD(ac["CD0"], ac["k"])
    return int(round((V / (ac["TSFC"] * g)) * ld * np.log(W_i / W_f) / 1000))


def _co2pp(ac: dict, dist_km: float) -> float | None:
    """CO2 per passenger (kg) at a given distance, 85% LF, 15,000 kg payload."""
    if ac["seats"] == 0:
        return None
    g    = 9.80665
    W_N  = (ac["OEW"] + 15000 + ac["max_fuel"] * 0.70) * g
    T, _, rho = isa(ac["cruise_alt"])
    V    = ac["cruise_mach"] * np.sqrt(1.4 * 287.05 * T)
    CL   = (2 * W_N) / (rho * V**2 * ac["S"])
    CD   = ac["CD0"] + ac["k"] * CL**2
    fN, _ = breguet_fuel(W_N, dist_km * 1000, ac["TSFC"], CL / CD, V)
    pax  = int(ac["seats"] * 0.85)
    return round(fN / g * 3.16 / pax, 1) if pax > 0 else None


def _casm_at(name: str, ac: dict, dist_km: float) -> float | None:
    """
    CASM in ¢/ASM at a given distance.
    Standard assumptions: fuel_price=$0.75/kg, LF=85%, payload=15,000 kg.
    Uses the same physics as analyze_route() internally.
    Returns None for freighters.
    """
    if ac["seats"] == 0:
        return None
    g    = 9.80665
    W_N  = (ac["OEW"] + 15000 + ac["max_fuel"] * 0.70) * g
    T, _, rho = isa(ac["cruise_alt"])
    V    = ac["cruise_mach"] * np.sqrt(1.4 * 287.05 * T)
    CL   = (2 * W_N) / (rho * V**2 * ac["S"])
    CD   = ac["CD0"] + ac["k"] * CL**2
    ld   = CL / CD
    fN, _ = breguet_fuel(W_N, dist_km * 1000, ac["TSFC"], ld, V)
    fuel_kg   = fN / g
    fuel_cost = fuel_kg * 0.75

    dist_mi = dist_km * 0.621371
    asm     = ac["seats"] * dist_mi
    if asm <= 0:
        return None

    nf_cost    = nonfuel_cost_per_asm(name) * asm
    total_opex = fuel_cost + nf_cost
    return round(total_opex / asm * 100, 2)   # ¢/ASM


def _best_use_case(name: str, ac: dict, max_range_km: int) -> str:
    """One-line strategic description based on aircraft characteristics."""
    mach  = ac["cruise_mach"]
    seats = ac["seats"]
    is_wb = seats >= 200 or ac["S"] >= 280

    if mach >= 1.5:                           return "Premium supersonic"
    if seats == 0:                            return "Cargo / freight"
    if seats < 100:                           return "Short-haul regional"
    if not is_wb:  # narrowbody
        if max_range_km < 4000:               return "Short-haul domestic"
        elif max_range_km <= 7000:            return "Medium-haul / thin routes"
        else:                                 return "Transatlantic narrowbody"
    else:          # widebody
        if max_range_km < 8000:               return "Medium-haul widebody"
        elif max_range_km <= 14000:           return "Long-haul intercontinental"
        else:                                 return "Ultra long haul / flag routes"


def _build() -> list[dict]:
    rows = []
    for name, ac in AIRCRAFT.items():
        _, ld    = best_LD(ac["CD0"], ac["k"])
        max_r    = _max_range(ac)
        ac_type  = _type(name, ac)
        best_use = _best_use_case(name, ac, max_r)

        # Raw CASM floats (stored as hidden keys for summary-card stats)
        raw_500   = _casm_at(name, ac, 500)
        raw_3000  = _casm_at(name, ac, 3000)
        raw_10000 = _casm_at(name, ac, 10000)

        rows.append({
            # ── Displayed columns ───────────────────────────────────────────
            "Aircraft":         name,
            "Type":             ac_type,
            "Seats":            ac["seats"] if ac["seats"] > 0 else "—",
            "Max Range (km)":   max_r,
            "Cruise Mach":      ac["cruise_mach"],
            "TSFC (x10^-5)":    round(ac["TSFC"] * 1e5, 2),
            "Max L/D":          round(ld, 1),
            "CO2/pax 500km":    _co2pp(ac, 500)   or "—",
            "CO2/pax 3000km":   _co2pp(ac, 3000)  or "—",
            "CO2/pax 10000km":  _co2pp(ac, 10000) or "—",
            # CASM formatted strings (spec: "X.XX¢")
            "CASM 500km":       f"{raw_500:.2f}c"   if raw_500   is not None else "—",
            "CASM 3000km":      f"{raw_3000:.2f}c"  if raw_3000  is not None else "—",
            "CASM 10000km":     f"{raw_10000:.2f}c" if raw_10000 is not None else "—",
            "Best use case":    best_use,
            # ── Hidden raw values (stats computation; not in _COLS) ─────────
            "_casm_500":        raw_500,
            "_casm_3000":       raw_3000,
            "_casm_10000":      raw_10000,
        })
    return rows


_DATA = _build()


# ══════════════════════════════════════════════════════════════════════════════
# PRE-COMPUTED SUMMARY STATS (five cards)
# ══════════════════════════════════════════════════════════════════════════════

# 1. Most efficient — lowest CASM at 3,000 km (all passenger aircraft)
_c3k = [(i, r["_casm_3000"]) for i, r in enumerate(_DATA)
        if r["_casm_3000"] is not None]
_EFF_IDX  = min(_c3k, key=lambda x: x[1])[0] if _c3k else None
_EFF_NAME = _DATA[_EFF_IDX]["Aircraft"]          if _EFF_IDX is not None else "—"
_EFF_VAL  = f"{_DATA[_EFF_IDX]['_casm_3000']:.2f}c" if _EFF_IDX is not None else "—"

# 2. Lowest CO2/pax at medium haul (3,000 km)
_co2_med = [(i, r["CO2/pax 3000km"]) for i, r in enumerate(_DATA)
            if isinstance(r["CO2/pax 3000km"], float)]
_CO2_IDX  = min(_co2_med, key=lambda x: x[1])[0] if _co2_med else None
_CO2_NAME = _DATA[_CO2_IDX]["Aircraft"]              if _CO2_IDX is not None else "—"
_CO2_VAL  = _DATA[_CO2_IDX]["CO2/pax 3000km"]        if _CO2_IDX is not None else "—"

# 3. Longest range
_LONG_ROW  = max(_DATA, key=lambda r: r["Max Range (km)"])
_LONG_NAME = _LONG_ROW["Aircraft"]
_LONG_KM   = _LONG_ROW["Max Range (km)"]

# 4. Best short haul — lowest CASM at 500 km, narrowbodies + regionals only
_c500_narrow = [(i, r["_casm_500"]) for i, r in enumerate(_DATA)
                if r["_casm_500"] is not None
                and r["Type"] in ("Narrowbody", "Regional")]
_SHORT_IDX  = min(_c500_narrow, key=lambda x: x[1])[0] if _c500_narrow else None
_SHORT_NAME = _DATA[_SHORT_IDX]["Aircraft"]               if _SHORT_IDX is not None else "—"
_SHORT_VAL  = f"{_DATA[_SHORT_IDX]['_casm_500']:.2f}c"   if _SHORT_IDX is not None else "—"

# 5. Best long haul — lowest CASM at 10,000 km, widebodies only
_c10k_wide  = [(i, r["_casm_10000"]) for i, r in enumerate(_DATA)
               if r["_casm_10000"] is not None and r["Type"] == "Widebody"]
_LONG_H_IDX  = min(_c10k_wide, key=lambda x: x[1])[0] if _c10k_wide else None
_LONG_H_NAME = _DATA[_LONG_H_IDX]["Aircraft"]             if _LONG_H_IDX is not None else "—"
_LONG_H_VAL  = f"{_DATA[_LONG_H_IDX]['_casm_10000']:.2f}c" if _LONG_H_IDX is not None else "—"

# ── Highlighted row in table = most efficient by CASM 3000km ─────────────────
_BEST = _EFF_IDX


# ══════════════════════════════════════════════════════════════════════════════
# TABLE CONFIG
# ══════════════════════════════════════════════════════════════════════════════

_TYPES     = ["All"] + sorted({r["Type"] for r in _DATA})
_RANGE_MAX = max(r["Max Range (km)"] for r in _DATA)
_SEATS_MAX = max((r["Seats"] for r in _DATA if isinstance(r["Seats"], int)), default=600)

# Text columns (not numerically sortable)
_TEXT_COLS = {"Aircraft", "Type", "CASM 500km", "CASM 3000km", "CASM 10000km", "Best use case"}

_COLS = [
    {"name": c, "id": c, "type": "text" if c in _TEXT_COLS else "numeric"}
    for c in _DATA[0]
    if not c.startswith("_")     # exclude hidden raw-value keys
]

# CASM column IDs for amber-color styling
_CASM_COLS = ["CASM 500km", "CASM 3000km", "CASM 10000km"]


# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _stat_card(label: str, value: str, sub: str, val_color=CYAN) -> html.Div:
    return html.Div([
        html.P(label, style={
            "color": TDIM, "fontSize": "7px", "fontWeight": "500",
            "letterSpacing": "1.5px", "textTransform": "uppercase",
            "fontFamily": _SG, "margin": "0 0 6px 0",
        }),
        html.P(value, style={
            "color": val_color, "fontSize": "13px", "fontWeight": "700",
            "fontFamily": _SG, "margin": "0 0 3px 0", "lineHeight": "1",
        }),
        html.P(sub, style={
            "color": TMUTED, "fontSize": "7px", "fontFamily": _SG, "margin": "0",
        }),
    ], style={
        "flex": "1", "minWidth": "150px",
        "backgroundColor": CARD, "border": f"1px solid {BDR}",
        "borderRadius": "4px", "padding": "14px 16px",
    })


def _lbl(text: str) -> html.P:
    return html.P(text, style={
        "color": TDIM, "fontSize": "7px", "letterSpacing": "1.5px",
        "textTransform": "uppercase", "fontFamily": _SG, "margin": "0 0 4px 0",
    })


# ══════════════════════════════════════════════════════════════════════════════
# PAGE LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

layout = html.Div(
    [html.Div([

        # ── Header ───────────────────────────────────────────────────────────
        html.H1("FLEET INTELLIGENCE", style={
            "fontFamily": _RAJ, "fontWeight": "700", "fontSize": "22px",
            "letterSpacing": "3px", "color": CYAN, "margin": "0 0 4px 0",
        }),
        html.P("Aircraft performance & efficiency — full fleet", style={
            "color": TMUTED, "fontSize": "8px", "letterSpacing": "2px",
            "textTransform": "uppercase", "fontFamily": _SG, "margin": "0 0 18px 0",
        }),

        # ── Five summary cards ────────────────────────────────────────────────
        html.Div([
            _stat_card("Most Efficient",
                       _EFF_NAME, f"CASM {_EFF_VAL} · medium haul (3,000 km)", CYAN),
            _stat_card("Lowest CO2/pax",
                       f"{_CO2_VAL} kg" if isinstance(_CO2_VAL, float) else "—",
                       f"{_CO2_NAME} · medium haul", CYAN),
            _stat_card("Longest Range",
                       f"{_LONG_KM:,} km", _LONG_NAME, GOLD),
            _stat_card("Best Short Haul",
                       _SHORT_NAME, f"CASM {_SHORT_VAL} · 500 km", AMBER),
            _stat_card("Best Long Haul",
                       _LONG_H_NAME, f"CASM {_LONG_H_VAL} · 10,000 km", CYAN),
        ], style={
            "display": "flex", "gap": "8px", "flexWrap": "wrap", "marginBottom": "14px",
        }),

        # ── Filter row ────────────────────────────────────────────────────────
        html.Div([
            # Type dropdown
            html.Div([
                _lbl("Type"),
                dcc.Dropdown(id="fl-type",
                    options=[{"label": t, "value": t} for t in _TYPES],
                    value="All", clearable=False,
                    style={"backgroundColor": CARD2, "color": "#000",
                           "border": f"1px solid {BDR2}", "fontSize": "8px"}),
            ], style={"flex": "1", "minWidth": "140px"}),

            # Min range slider
            html.Div([
                _lbl("Min Range (km)"),
                dcc.Slider(id="fl-range", min=0, max=_RANGE_MAX, step=500, value=0,
                    marks={0: "0", _RANGE_MAX: f"{_RANGE_MAX:,}"},
                    tooltip={"placement": "bottom", "always_visible": True}),
            ], style={"flex": "2", "minWidth": "200px"}),

            # Min seats slider
            html.Div([
                _lbl("Min Seats"),
                dcc.Slider(id="fl-seats", min=0, max=_SEATS_MAX, step=20, value=0,
                    marks={0: "0", _SEATS_MAX: str(_SEATS_MAX)},
                    tooltip={"placement": "bottom", "always_visible": True}),
            ], style={"flex": "2", "minWidth": "200px"}),

            # Target route distance slider  (Addition 3)
            html.Div([
                _lbl("Target Route Distance (km)"),
                dcc.Slider(id="fl-dist", min=0, max=_DIST_MAX, step=500, value=0,
                    marks={0: "Any", 5000: "5k", 10000: "10k", _DIST_MAX: "20k"},
                    tooltip={"placement": "bottom", "always_visible": True}),
            ], style={"flex": "2", "minWidth": "200px"}),

        ], style={
            "display": "flex", "gap": "20px", "flexWrap": "wrap",
            "alignItems": "flex-end", "backgroundColor": CARD,
            "border": f"1px solid {BDR}", "borderRadius": "4px",
            "padding": "16px 20px", "marginBottom": "14px",
        }),

        # ── Legend ────────────────────────────────────────────────────────────
        html.P(
            "Highlighted row = most efficient aircraft (lowest CASM · 3,000 km)  "
            "·  CO2/pax in kg per passenger  "
            "·  CASM in US cents per available seat mile",
            style={"color": TMUTED, "fontSize": "7px", "fontFamily": _SG,
                   "marginBottom": "8px", "letterSpacing": "0.5px"},
        ),

        # ── DataTable ─────────────────────────────────────────────────────────
        html.Div(
            dash_table.DataTable(
                id="fl-table",
                columns=_COLS,
                data=_DATA,
                sort_action="native",
                filter_action="none",
                page_action="none",
                style_table={"overflowX": "auto"},
                style_header={
                    "backgroundColor": CARD2,
                    "color":           TDIM,
                    "fontWeight":      "500",
                    "borderBottom":    f"1px solid {BDR}",
                    "textTransform":   "uppercase",
                    "letterSpacing":   "1px",
                    "fontSize":        "7px",
                    "padding":         "8px 10px",
                    "whiteSpace":      "nowrap",
                    "fontFamily":      _SG,
                },
                style_data={
                    "backgroundColor": CARD,
                    "color":           TMID,
                    "borderBottom":    f"1px solid {BDR}",
                    "fontSize":        "9px",
                    "padding":         "7px 10px",
                    "fontFamily":      _SG,
                },
                style_data_conditional=[
                    # Alternating rows
                    {"if": {"row_index": "odd"}, "backgroundColor": BG},
                    # Hover / active
                    {"if": {"state": "active"}, "backgroundColor": CARD2,
                     "color": WHITE, "border": f"1px solid {BDR2}"},
                    # CASM columns in amber
                    *[{"if": {"column_id": col}, "color": AMBER}
                      for col in _CASM_COLS],
                    # Best efficiency row — cyan highlight; Aircraft cell bold white
                    *(
                        [
                            {"if": {"row_index": _BEST, "column_id": "Aircraft"},
                             "color": WHITE, "fontWeight": "700"},
                            {"if": {"row_index": _BEST},
                             "color": CYAN},
                        ]
                        if _BEST is not None else []
                    ),
                ],
                style_cell={
                    "fontFamily": _SG, "textAlign": "left",
                    "border": f"1px solid {BDR}", "minWidth": "70px",
                    "whiteSpace": "nowrap",
                },
                style_cell_conditional=[
                    {"if": {"column_id": "Aircraft"},      "minWidth": "160px"},
                    {"if": {"column_id": "Best use case"}, "minWidth": "200px"},
                    *[{"if": {"column_id": c}, "minWidth": "90px"} for c in _CASM_COLS],
                ],
            ),
            style={"border": f"1px solid {BDR}", "borderRadius": "4px", "overflow": "hidden"},
        ),

    ], style={"maxWidth": "1400px", "margin": "0 auto",
              "padding": "36px 28px 60px", "boxSizing": "border-box"})],
    style={"backgroundColor": BG, "minHeight": "calc(100vh - 42px)"},
)


# ══════════════════════════════════════════════════════════════════════════════
# FILTER CALLBACK
# ══════════════════════════════════════════════════════════════════════════════

@callback(
    Output("fl-table", "data"),
    Input("fl-type",  "value"),
    Input("fl-range", "value"),
    Input("fl-seats", "value"),
    Input("fl-dist",  "value"),
)
def _filter(ac_type: str, min_range: int, min_seats: int, target_dist: int):
    rows = _DATA

    # Type filter
    if ac_type and ac_type != "All":
        rows = [r for r in rows if r["Type"] == ac_type]

    # Minimum range filter
    if min_range:
        rows = [r for r in rows if r["Max Range (km)"] >= min_range]

    # Minimum seats filter
    if min_seats:
        rows = [r for r in rows
                if isinstance(r["Seats"], int) and r["Seats"] >= min_seats]

    # Target route distance filter (Addition 3)
    if target_dist and target_dist > 0:
        keep = []
        for r in rows:
            # Aircraft must have enough range for the route
            if r["Max Range (km)"] < target_dist:
                continue
            # Type-based exclusions for inappropriate aircraft-distance combos
            typ  = r["Type"]
            name = r["Aircraft"]
            if target_dist > 2000 and typ == "Regional":
                continue
            if target_dist > 7000 and typ == "Narrowbody":
                continue
            if target_dist > 1500 and _is_turboprop(name):
                continue
            keep.append(r)
        rows = keep

    return rows
