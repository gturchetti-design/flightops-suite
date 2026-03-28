"""
FlightOps Suite — Fleet Intelligence page
"""
import numpy as np
import dash
from dash import html, dcc, dash_table, Input, Output, callback
from physics import AIRCRAFT, isa, best_LD, breguet_fuel

dash.register_page(__name__, path="/fleet", name="Fleet")

# ── Palette ───────────────────────────────────────────────────────────────────
BG     = "#030508"
CARD   = "#04080f"
CARD2  = "#060e1a"
BDR    = "#0a1a2a"
BDR2   = "#0d2030"
CYAN   = "#00c8ff"
GOLD   = "#ffd060"
WHITE  = "#ffffff"
TSOFT  = "#c8d8e8"
TMID   = "#8ab0c8"
TDIM   = "#3a6080"
TMUTED = "#2a4a65"

_RAJ = "'Rajdhani', sans-serif"
_SG  = "'Space Grotesk', sans-serif"


# ── Data builders ─────────────────────────────────────────────────────────────
def _type(name, ac):
    if ac["cruise_mach"] >= 1.5: return "Supersonic"
    if ac["seats"] == 0:         return "Freighter"
    if ac["seats"] >= 200 or ac["S"] >= 280: return "Widebody"
    return "Narrowbody"


def _max_range(ac):
    g   = 9.80665
    W_i = (ac["OEW"] + ac["max_fuel"] * 0.95) * g
    W_f = (ac["OEW"] + ac["max_fuel"] * 0.05) * g
    if W_f <= 0 or W_i <= W_f: return 0
    T, _, _ = isa(ac["cruise_alt"])
    V       = ac["cruise_mach"] * np.sqrt(1.4 * 287.05 * T)
    _, ld   = best_LD(ac["CD0"], ac["k"])
    return int(round((V / (ac["TSFC"] * g)) * ld * np.log(W_i / W_f) / 1000))


def _co2pp(ac, dist_km):
    if ac["seats"] == 0: return None
    g    = 9.80665
    W_N  = (ac["OEW"] + 15000 + ac["max_fuel"] * 0.70) * g
    T, _, rho = isa(ac["cruise_alt"])
    V    = ac["cruise_mach"] * np.sqrt(1.4 * 287.05 * T)
    CL   = (2 * W_N) / (rho * V**2 * ac["S"])
    CD   = ac["CD0"] + ac["k"] * CL**2
    fN, _ = breguet_fuel(W_N, dist_km * 1000, ac["TSFC"], CL/CD, V)
    pax  = int(ac["seats"] * 0.85)
    return round(fN / g * 3.16 / pax, 1) if pax > 0 else None


def _build():
    rows = []
    for name, ac in AIRCRAFT.items():
        _, ld = best_LD(ac["CD0"], ac["k"])
        rows.append({
            "Aircraft":       name,
            "Type":           _type(name, ac),
            "Seats":          ac["seats"] if ac["seats"] > 0 else "—",
            "Max Range (km)": _max_range(ac),
            "Cruise Mach":    ac["cruise_mach"],
            "TSFC (×10⁻⁵)":  round(ac["TSFC"] * 1e5, 2),
            "Max L/D":        round(ld, 1),
            "CO2/pax 500km":  _co2pp(ac, 500)   or "—",
            "CO2/pax 3000km": _co2pp(ac, 3000)  or "—",
            "CO2/pax 10000km":_co2pp(ac, 10000) or "—",
        })
    return rows


_DATA = _build()

_med  = [(i, r["CO2/pax 3000km"]) for i, r in enumerate(_DATA)
         if isinstance(r["CO2/pax 3000km"], float)]
_BEST = min(_med, key=lambda x: x[1])[0] if _med else None

_EFF_NAME  = _DATA[_BEST]["Aircraft"]            if _BEST is not None else "—"
_EFF_CO2   = _DATA[_BEST]["CO2/pax 3000km"]      if _BEST is not None else "—"
_LONG_ROW  = max(_DATA, key=lambda r: r["Max Range (km)"])
_LONG_NAME = _LONG_ROW["Aircraft"]
_LONG_KM   = _LONG_ROW["Max Range (km)"]

_TYPES     = ["All"] + sorted({r["Type"] for r in _DATA})
_RANGE_MAX = max(r["Max Range (km)"] for r in _DATA)
_SEATS_MAX = max((r["Seats"] for r in _DATA if isinstance(r["Seats"], int)), default=600)

_COLS = [
    {"name": c, "id": c,
     "type": "text" if c in ("Aircraft", "Type") else "numeric"}
    for c in _DATA[0]
]


# ── Layout helpers ────────────────────────────────────────────────────────────
def _stat_card(label, value, sub, val_color=CYAN):
    return html.Div([
        html.P(label, style={
            "color":         TDIM,
            "fontSize":      "7px",
            "fontWeight":    "500",
            "letterSpacing": "1.5px",
            "textTransform": "uppercase",
            "fontFamily":    _SG,
            "margin":        "0 0 6px 0",
        }),
        html.P(value, style={
            "color":      val_color,
            "fontSize":   "13px",
            "fontWeight": "700",
            "fontFamily": _SG,
            "margin":     "0 0 3px 0",
            "lineHeight": "1",
        }),
        html.P(sub, style={
            "color":      TMUTED,
            "fontSize":   "7px",
            "fontFamily": _SG,
            "margin":     "0",
        }),
    ], style={
        "flex":            "1",
        "minWidth":        "160px",
        "backgroundColor": CARD,
        "border":          f"1px solid {BDR}",
        "borderRadius":    "4px",
        "padding":         "14px 16px",
    })


def _lbl(text):
    return html.P(text, style={
        "color":         TDIM,
        "fontSize":      "7px",
        "letterSpacing": "1.5px",
        "textTransform": "uppercase",
        "fontFamily":    _SG,
        "margin":        "0 0 4px 0",
    })


# ── Page layout ───────────────────────────────────────────────────────────────
layout = html.Div(
    [html.Div([

        # Header
        html.H1("FLEET INTELLIGENCE", style={
            "fontFamily":    _RAJ,
            "fontWeight":    "700",
            "fontSize":      "22px",
            "letterSpacing": "3px",
            "color":         CYAN,
            "margin":        "0 0 4px 0",
        }),
        html.P("Aircraft performance & efficiency — full fleet", style={
            "color":         TMUTED,
            "fontSize":      "8px",
            "letterSpacing": "2px",
            "textTransform": "uppercase",
            "fontFamily":    _SG,
            "margin":        "0 0 18px 0",
        }),

        # Summary cards
        html.Div([
            _stat_card("Most Efficient",  _EFF_NAME,        "lowest CO₂/pax · 3,000 km",  CYAN),
            _stat_card("Lowest CO₂/pax",  f"{_EFF_CO2} kg" if isinstance(_EFF_CO2, float) else "—",
                       "kg CO₂ per passenger · medium haul", CYAN),
            _stat_card("Longest Range",   f"{_LONG_KM:,} km", _LONG_NAME, GOLD),
        ], style={
            "display":      "flex",
            "gap":          "8px",
            "flexWrap":     "wrap",
            "marginBottom": "14px",
        }),

        # Filters
        html.Div([
            html.Div([
                _lbl("Type"),
                dcc.Dropdown(id="fl-type",
                    options=[{"label": t, "value": t} for t in _TYPES],
                    value="All", clearable=False,
                    style={"backgroundColor": CARD2, "color": "#000",
                           "border": f"1px solid {BDR2}", "fontSize": "8px"}),
            ], style={"flex": "1", "minWidth": "140px"}),

            html.Div([
                _lbl("Min Range (km)"),
                dcc.Slider(id="fl-range", min=0, max=_RANGE_MAX, step=500, value=0,
                    marks={0: "0", _RANGE_MAX: f"{_RANGE_MAX:,}"},
                    tooltip={"placement": "bottom", "always_visible": True}),
            ], style={"flex": "2", "minWidth": "200px"}),

            html.Div([
                _lbl("Min Seats"),
                dcc.Slider(id="fl-seats", min=0, max=_SEATS_MAX, step=20, value=0,
                    marks={0: "0", _SEATS_MAX: str(_SEATS_MAX)},
                    tooltip={"placement": "bottom", "always_visible": True}),
            ], style={"flex": "2", "minWidth": "200px"}),
        ], style={
            "display":         "flex",
            "gap":             "20px",
            "flexWrap":        "wrap",
            "alignItems":      "flex-end",
            "backgroundColor": CARD,
            "border":          f"1px solid {BDR}",
            "borderRadius":    "4px",
            "padding":         "16px 20px",
            "marginBottom":    "14px",
        }),

        # Legend
        html.P(
            "Highlighted row = most efficient aircraft (lowest CO₂/pax medium haul)  ·  "
            "CO₂/pax in kg per passenger",
            style={"color": TMUTED, "fontSize": "7px", "fontFamily": _SG,
                   "marginBottom": "8px", "letterSpacing": "0.5px"},
        ),

        # Table
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
                    {"if": {"row_index": "odd"},
                     "backgroundColor": BG},
                    # Active/hover
                    {"if": {"state": "active"},
                     "backgroundColor": CARD2,
                     "color":           WHITE,
                     "border":          f"1px solid {BDR2}"},
                    # Best efficiency row
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
                    "fontFamily":  _SG,
                    "textAlign":   "left",
                    "border":      f"1px solid {BDR}",
                    "minWidth":    "70px",
                    "whiteSpace":  "nowrap",
                },
                style_cell_conditional=[
                    {"if": {"column_id": "Aircraft"}, "minWidth": "160px"},
                ],
            ),
            style={"border": f"1px solid {BDR}", "borderRadius": "4px", "overflow": "hidden"},
        ),

    ], style={"maxWidth": "1200px", "margin": "0 auto",
              "padding": "36px 28px 60px", "boxSizing": "border-box"})],
    style={"backgroundColor": BG, "minHeight": "calc(100vh - 42px)"},
)


@callback(
    Output("fl-table", "data"),
    Input("fl-type",  "value"),
    Input("fl-range", "value"),
    Input("fl-seats", "value"),
)
def _filter(ac_type, min_range, min_seats):
    rows = _DATA
    if ac_type and ac_type != "All":
        rows = [r for r in rows if r["Type"] == ac_type]
    if min_range:
        rows = [r for r in rows if r["Max Range (km)"] >= min_range]
    if min_seats:
        rows = [r for r in rows if isinstance(r["Seats"], int) and r["Seats"] >= min_seats]
    return rows
