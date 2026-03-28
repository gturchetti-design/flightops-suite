"""
FlightOps Suite — Route Analyzer page
"""
import numpy as np
import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.graph_objects as go
import folium

from route import analyze_route, AIRPORTS
from physics import AIRCRAFT, isa, breguet_fuel

dash.register_page(__name__, path="/analyzer", name="Route Analyzer")

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
AMBER  = "#ffd060"
RED    = "#f04040"

_RAJ = "'Rajdhani', sans-serif"
_SG  = "'Space Grotesk', sans-serif"

# ── Helpers ───────────────────────────────────────────────────────────────────
def _lbl(text):
    return html.P(text, style={
        "color":         TDIM,
        "fontSize":      "7px",
        "fontWeight":    "500",
        "letterSpacing": "1.5px",
        "textTransform": "uppercase",
        "fontFamily":    _SG,
        "margin":        "0 0 4px 0",
    })


def _sec(text):
    return html.P(text, style={
        "color":         TDIM,
        "fontSize":      "7px",
        "letterSpacing": "2.5px",
        "textTransform": "uppercase",
        "fontFamily":    _SG,
        "margin":        "0 0 8px 0",
        "borderBottom":  f"1px solid {BDR}",
        "paddingBottom": "5px",
    })


def _card(label, value, color=WHITE):
    return html.Div([
        html.P(label, style={
            "color":         TDIM,
            "fontSize":      "6px",
            "fontWeight":    "500",
            "letterSpacing": "1.5px",
            "textTransform": "uppercase",
            "fontFamily":    _SG,
            "margin":        "0 0 5px 0",
        }),
        html.P(value, style={
            "color":      color,
            "fontSize":   "13px",
            "fontWeight": "700",
            "fontFamily": _SG,
            "margin":     "0",
            "lineHeight": "1",
        }),
    ], style={
        "backgroundColor": CARD,
        "border":          f"1px solid {BDR}",
        "borderRadius":    "4px",
        "padding":         "10px 12px",
        "flex":            "1",
        "minWidth":        "100px",
    })


_DD = {
    "backgroundColor": CARD2,
    "color":           "#000",
    "border":          f"1px solid {BDR2}",
    "fontSize":        "8px",
    "borderRadius":    "3px",
}

# ── Layout ────────────────────────────────────────────────────────────────────
layout = html.Div(
    style={"display": "flex", "minHeight": "calc(100vh - 42px)", "backgroundColor": BG},
    children=[

        # ── SIDEBAR ──────────────────────────────────────────────────────────
        html.Div(style={
            "width":           "200px",
            "minWidth":        "200px",
            "backgroundColor": CARD,
            "borderRight":     f"1px solid {BDR}",
            "padding":         "20px 14px",
            "display":         "flex",
            "flexDirection":   "column",
            "gap":             "10px",
            "overflowY":       "auto",
        }, children=[

            html.P("PARAMETERS", style={
                "fontFamily":    _RAJ,
                "fontWeight":    "700",
                "fontSize":      "13px",
                "letterSpacing": "3px",
                "color":         GOLD,
                "margin":        "0 0 4px 0",
            }),
            html.Div(style={"height": "1px", "backgroundColor": BDR, "margin": "0 0 4px 0"}),

            _lbl("Origin"),
            dcc.Dropdown(id="az-origin",
                options=[{"label": f"{k} — {v['name']}", "value": k} for k, v in AIRPORTS.items()],
                value="ORD", style=_DD),

            _lbl("Destination"),
            dcc.Dropdown(id="az-destination",
                options=[{"label": f"{k} — {v['name']}", "value": k} for k, v in AIRPORTS.items()],
                value="LHR", style=_DD),

            _lbl("Aircraft"),
            dcc.Dropdown(id="az-aircraft",
                options=[{"label": k, "value": k} for k in AIRCRAFT],
                value="Boeing 787-9", style=_DD),

            _lbl("Compare Aircraft"),
            dcc.Dropdown(id="az-aircraft2",
                options=[{"label": "None", "value": "none"}]
                         + [{"label": k, "value": k} for k in AIRCRAFT],
                value="none", style=_DD),

            html.Div(style={"height": "1px", "backgroundColor": BDR, "margin": "2px 0"}),

            _lbl("Payload (kg)"),
            dcc.Slider(id="az-payload", min=5000, max=50000, step=1000, value=15000,
                marks={5000: "5k", 50000: "50k"},
                tooltip={"placement": "bottom", "always_visible": True}),

            _lbl("Fuel Price ($/kg)"),
            dcc.Slider(id="az-fuel-price", min=0.30, max=1.50, step=0.05, value=0.75,
                marks={0.30: "0.30", 1.50: "1.50"},
                tooltip={"placement": "bottom", "always_visible": True}),

            _lbl("Load Factor (%)"),
            dcc.Slider(id="az-load-factor", min=50, max=100, step=5, value=85,
                marks={50: "50", 100: "100"},
                tooltip={"placement": "bottom", "always_visible": True}),

            _lbl("Ticket Multiplier"),
            dcc.Slider(id="az-ticket-mult", min=0.5, max=2.0, step=0.1, value=1.0,
                marks={0.5: "0.5x", 2.0: "2x"},
                tooltip={"placement": "bottom", "always_visible": True}),

            html.Div(style={"height": "1px", "backgroundColor": BDR, "margin": "2px 0"}),

            html.Button("ANALYZE ROUTE", id="az-btn", n_clicks=0, style={
                "backgroundColor": CYAN,
                "color":           BG,
                "border":          "none",
                "borderRadius":    "3px",
                "padding":         "10px",
                "fontWeight":      "700",
                "fontSize":        "8px",
                "letterSpacing":   "2px",
                "cursor":          "pointer",
                "width":           "100%",
                "fontFamily":      _SG,
                "textTransform":   "uppercase",
            }),
        ]),

        # ── MAIN ─────────────────────────────────────────────────────────────
        html.Div(id="az-main", style={
            "flex":      "1",
            "padding":   "28px 32px",
            "overflowY": "auto",
        }, children=[
            html.Div(style={
                "backgroundColor": CARD,
                "border":          f"1px solid {BDR}",
                "borderRadius":    "4px",
                "padding":         "48px",
                "textAlign":       "center",
                "marginTop":       "40px",
            }, children=[
                html.H1("ROUTE ANALYZER", style={
                    "fontFamily":    _RAJ,
                    "fontWeight":    "700",
                    "fontSize":      "26px",
                    "letterSpacing": "5px",
                    "color":         CYAN,
                    "margin":        "0 0 10px 0",
                }),
                html.P("Select origin, destination and aircraft — then click Analyze Route",
                    style={"color": TDIM, "fontSize": "9px", "letterSpacing": "2px",
                           "textTransform": "uppercase", "fontFamily": _SG}),
            ]),
        ]),
    ],
)


# ── Callback ──────────────────────────────────────────────────────────────────
@callback(
    Output("az-main", "children"),
    Input("az-btn", "n_clicks"),
    State("az-origin",      "value"),
    State("az-destination", "value"),
    State("az-aircraft",    "value"),
    State("az-aircraft2",   "value"),
    State("az-payload",     "value"),
    State("az-fuel-price",  "value"),
    State("az-load-factor", "value"),
    State("az-ticket-mult", "value"),
    prevent_initial_call=True,
)
def run_analysis(n, origin, destination, aircraft, aircraft2,
                 payload, fuel_price, load_factor, ticket_mult):

    if not origin or not destination or origin == destination:
        return html.P("Please select different origin and destination.",
                      style={"color": RED, "padding": "20px", "fontFamily": _SG})

    result = analyze_route(origin, destination, aircraft, payload,
                           fuel_price, load_factor, ticket_mult)
    ac = AIRCRAFT[aircraft]

    # ── Feasibility check ────────────────────────────────────────────────────
    if result["fuel_burned_kg"] > ac["max_fuel"] * 0.95:
        # Estimate max range via Breguet at MTOW, 95% fuel, cruise conditions
        g    = 9.80665
        W_i  = ac["MTOW"] * g
        W_f  = (ac["MTOW"] - ac["max_fuel"] * 0.95) * g
        from physics import isa as _isa, best_LD as _best_LD
        T, _, _ = _isa(ac["cruise_alt"])
        V_cr    = ac["cruise_mach"] * (1.4 * 287.05 * T) ** 0.5
        _, ld   = _best_LD(ac["CD0"], ac["k"])
        max_range_km = int((V_cr / (ac["TSFC"] * g)) * ld * __import__("math").log(W_i / W_f) / 1000)

        return html.Div(style={
            "backgroundColor": "#1a0a0a",
            "border":          f"1px solid {RED}",
            "borderRadius":    "4px",
            "padding":         "20px 24px",
            "maxWidth":        "560px",
        }, children=[
            html.Div("⚠", style={
                "color":    RED,
                "fontSize": "20px",
                "margin":   "0 0 10px 0",
            }),
            html.H2("ROUTE NOT FEASIBLE", style={
                "fontFamily":    _RAJ,
                "fontWeight":    "700",
                "fontSize":      "16px",
                "letterSpacing": "2px",
                "color":         RED,
                "margin":        "0 0 12px 0",
            }),
            html.P(
                f"The {aircraft} does not have sufficient fuel capacity to complete this route. "
                f"Maximum range with full fuel load is approximately {max_range_km:,} km, "
                f"but this route requires {result['distance_km']:,} km.",
                style={"color": TMID, "fontSize": "10px", "fontFamily": _SG,
                       "lineHeight": "1.7", "margin": "0 0 10px 0"},
            ),
            html.P(
                "Try a longer-range aircraft such as the Boeing 787-9 or Airbus A350-900 for this route.",
                style={"color": TDIM, "fontSize": "9px", "fontFamily": _SG,
                       "fontStyle": "italic", "margin": "0"},
            ),
        ])

    # Charts
    alts = np.arange(5000, 14000, 500)
    ld_v, fuel_v, co2_v = [], [], []
    W_N = (ac["OEW"] + payload + ac["max_fuel"] * 0.85) * 9.80665
    for alt in alts:
        T, _, rho = isa(alt)
        V   = ac["cruise_mach"] * np.sqrt(1.4 * 287.05 * T)
        CL  = (2 * W_N) / (rho * V**2 * ac["S"])
        CD  = ac["CD0"] + ac["k"] * CL**2
        ld  = CL / CD
        ld_v.append(ld)
        fN, _ = breguet_fuel(W_N, result["distance_km"] * 1000, ac["TSFC"], ld, V)
        fkg = fN / 9.80665
        fuel_v.append(fkg)
        co2_v.append(fkg * 3.16 / 1000)

    _ch = dict(
        paper_bgcolor=CARD, plot_bgcolor=CARD,
        font=dict(color=TDIM, size=10, family=_SG),
        xaxis=dict(gridcolor=BDR, color=TDIM, title_font_color=TDIM),
        yaxis=dict(gridcolor=BDR, color=TDIM, title_font_color=TDIM),
        margin=dict(l=44, r=12, t=32, b=32),
        height=220,
    )
    fig_ld   = go.Figure(go.Scatter(x=alts/1000, y=ld_v,   mode="lines", line=dict(color=CYAN,  width=1.5)))
    fig_fuel = go.Figure(go.Scatter(x=alts/1000, y=fuel_v, mode="lines", line=dict(color=AMBER, width=1.5)))
    fig_co2  = go.Figure(go.Scatter(x=alts/1000, y=co2_v,  mode="lines", line=dict(color=RED,   width=1.5)))
    fig_ld.update_layout(  title=dict(text="L/D vs Altitude",    font=dict(color=TDIM, size=9)), **_ch)
    fig_fuel.update_layout(title=dict(text="Fuel Burn vs Alt",   font=dict(color=TDIM, size=9)), **_ch)
    fig_co2.update_layout( title=dict(text="CO2 vs Altitude",    font=dict(color=TDIM, size=9)), **_ch)

    # Map
    mid_lat = (AIRPORTS[origin]["lat"] + AIRPORTS[destination]["lat"]) / 2
    mid_lon = (AIRPORTS[origin]["lon"] + AIRPORTS[destination]["lon"]) / 2
    m = folium.Map(location=[mid_lat, mid_lon], zoom_start=3, tiles="CartoDB dark_matter")
    folium.PolyLine(result["waypoints"], color=CYAN, weight=2, opacity=0.85).add_to(m)
    for code in [origin, destination]:
        ap = AIRPORTS[code]
        folium.CircleMarker([ap["lat"], ap["lon"]], radius=5,
            color=CYAN, fill=True, fill_color=CYAN, fill_opacity=1.0,
            popup=ap["name"]).add_to(m)
    map_html = m._repr_html_()

    # Risk
    avail        = ac["max_fuel"] * 0.85 - result["fuel_burned_kg"]
    extra200     = result["fuel_burned_kg"] * 200 / result["distance_km"] if result["distance_km"] > 0 else 0
    can_divert   = avail >= extra200
    breakeven_lf = None
    if (not result.get("is_freighter") and result.get("seats", 0) > 0
            and result.get("ticket_price", 0) > 0):
        breakeven_lf = min(
            round((result["fuel_cost"] / (result["seats"] * result["ticket_price"])) * 100, 1),
            100.0
        )
    co2_pax = None
    if not result.get("is_freighter") and result.get("passengers", 0) > 0:
        co2_pax = round(result["co2_kg"] / result["passengers"], 1)

    GREEN = "#00d68f"
    profit_color   = GREEN if result.get("profit",        0) > 0 else RED
    pax_color      = GREEN if result.get("profit_per_pax", 0) > 0 else RED

    # Comparison
    comparison = html.Div()
    if aircraft2 and aircraft2 != "none" and aircraft2 != aircraft:
        r2  = analyze_route(origin, destination, aircraft2, payload, fuel_price, load_factor, ticket_mult)
        pc2 = GREEN if r2.get("profit", 0) > 0 else RED

        def _cmp_col(name, r, pc):
            return html.Div([
                html.P(name, style={"color": WHITE, "fontWeight": "700",
                                    "fontSize": "10px", "fontFamily": _SG, "margin": "0 0 8px 0"}),
                _card("Fuel Burned",   f"{r['fuel_burned_kg']:,} kg",  AMBER),
                _card("Fuel Cost",     f"${r['fuel_cost']:,}",         AMBER),
                _card("Passengers",    str(r['passengers']),           WHITE),
                _card("Revenue",       f"${r['revenue']:,}",           CYAN),
                _card("Profit",        f"${r['profit']:,}",            pc),
                _card("Profit / Pax",  f"${r['profit_per_pax']}",      pc),
                _card("CO2",           f"{r['co2_tonnes']} t",         AMBER),
                _card("L/D",           str(r['LD_ratio']),             WHITE),
            ], style={"flex": "1", "display": "flex", "flexDirection": "column", "gap": "6px"})

        comparison = html.Div([
            _sec("AIRCRAFT COMPARISON"),
            html.Div([_cmp_col(aircraft, result, profit_color),
                      _cmp_col(aircraft2, r2, pc2)],
                     style={"display": "flex", "gap": "12px"}),
        ])

    return html.Div(
        style={"display": "flex", "flexDirection": "column", "gap": "18px"},
        children=[

            # Route title
            html.H2(
                f"{result['origin']}  →  {result['destination']}",
                style={"color": WHITE, "margin": "0", "fontSize": "14px",
                       "fontWeight": "700", "fontFamily": _SG},
            ),

            # Flight performance
            html.Div([
                _sec("FLIGHT PERFORMANCE"),
                html.Div(style={"display": "flex", "gap": "6px", "flexWrap": "wrap"}, children=[
                    _card("Distance",     f"{result['distance_km']:,} km",          WHITE),
                    _card("Cruise Alt",   f"{result['cruise_altitude_ft']:,} ft",   WHITE),
                    _card("Cruise Speed", f"{result['cruise_speed_kts']} kts",      WHITE),
                    _card("Flight Time",  f"{result['flight_time_hr']} hrs",        WHITE),
                    _card("L/D Ratio",    str(result['LD_ratio']),                  WHITE),
                    _card("Wind",         f"{result['wind_ms']} m/s",               WHITE),
                ]),
            ]),

            # Fuel & emissions
            html.Div([
                _sec("FUEL & EMISSIONS"),
                html.Div(style={"display": "flex", "gap": "6px", "flexWrap": "wrap"}, children=[
                    _card("Fuel Burned",   f"{result['fuel_burned_kg']:,} kg",  AMBER),
                    _card("Fuel Cost",     f"${result['fuel_cost']:,}",         AMBER),
                    _card("CO2 Emissions", f"{result['co2_tonnes']} t",         AMBER),
                ]),
            ]),

            # Profitability
            html.Div([
                _sec("ROUTE PROFITABILITY"),
                (
                    html.Div(
                        style={"display": "flex", "gap": "6px", "flexWrap": "wrap"},
                        children=[
                            _card("Ticket Price", f"${result['ticket_price']}",     WHITE),
                            _card("Passengers",   str(result['passengers']),        WHITE),
                            _card("Revenue",      f"${result['revenue']:,}",        CYAN),
                            _card("Profit",       f"${result['profit']:,}",         profit_color),
                            _card("Profit/Pax",   f"${result['profit_per_pax']}",   pax_color),
                        ],
                    )
                    if not result.get("is_freighter")
                    else html.P("Cargo / Freighter — no passenger profitability",
                                style={"color": TDIM, "fontSize": "9px", "fontFamily": _SG})
                ),
            ]),

            # Route risk
            html.Div([
                _sec("ROUTE RISK"),
                html.Div(style={
                    "backgroundColor": CARD,
                    "border":          f"1px solid {BDR}",
                    "borderRadius":    "4px",
                    "padding":         "14px 16px",
                    "display":         "flex",
                    "flexWrap":        "wrap",
                    "gap":             "20px",
                }, children=[
                    # Diversion
                    html.Div([
                        html.P("Diversion +200 km", style={
                            "color": TDIM, "fontSize": "6px", "letterSpacing": "1.5px",
                            "textTransform": "uppercase", "fontFamily": _SG, "margin": "0 0 6px 0",
                        }),
                        html.Div([
                            html.Span(
                                "FUEL OK" if can_divert else "MARGINAL",
                                style={
                                    "border":          f"1px solid {CYAN}" if can_divert else f"1px solid {RED}",
                                    "color":           CYAN if can_divert else RED,
                                    "backgroundColor": "#001a2a" if can_divert else "rgba(240,64,64,0.1)",
                                    "borderRadius":    "3px",
                                    "padding":         "2px 8px",
                                    "fontSize":        "8px",
                                    "fontWeight":      "700",
                                    "letterSpacing":   "1px",
                                    "fontFamily":      _SG,
                                },
                            ),
                            html.Span(f"  {avail:,.0f} kg remaining",
                                      style={"color": TDIM, "fontSize": "8px",
                                             "marginLeft": "8px", "fontFamily": _SG}),
                        ], style={"display": "flex", "alignItems": "center"}),
                    ]),
                    # Break-even
                    html.Div([
                        html.P("Break-Even LF", style={
                            "color": TDIM, "fontSize": "6px", "letterSpacing": "1.5px",
                            "textTransform": "uppercase", "fontFamily": _SG, "margin": "0 0 6px 0",
                        }),
                        (html.Span(f"{breakeven_lf:.1f} %", style={
                            "color":      GREEN if breakeven_lf <= load_factor else RED,
                            "fontSize":   "13px",
                            "fontWeight": "700",
                            "fontFamily": _SG,
                         }) if breakeven_lf is not None
                         else html.Span("N/A", style={"color": TDIM, "fontFamily": _SG})),
                    ]),
                    # CO2/pax
                    html.Div([
                        html.P("CO2 per Passenger", style={
                            "color": TDIM, "fontSize": "6px", "letterSpacing": "1.5px",
                            "textTransform": "uppercase", "fontFamily": _SG, "margin": "0 0 6px 0",
                        }),
                        (html.Span(f"{co2_pax} kg", style={
                            "color":      TMID,
                            "fontSize":   "13px",
                            "fontWeight": "700",
                            "fontFamily": _SG,
                         }) if co2_pax is not None
                         else html.Span("N/A", style={"color": TDIM, "fontFamily": _SG})),
                    ]),
                ]),
            ]),

            # Map
            html.Div([
                _sec("ROUTE MAP"),
                html.Iframe(srcDoc=map_html, style={
                    "width": "100%", "height": "400px",
                    "border": f"1px solid {BDR}", "borderRadius": "4px",
                }),
            ]),

            # Charts
            html.Div([
                _sec("PERFORMANCE VS ALTITUDE"),
                html.Div(
                    style={"display": "flex", "gap": "8px"},
                    children=[
                        html.Div(
                            dcc.Graph(figure=fig, config={"displayModeBar": False}),
                            style={"flex": "1", "backgroundColor": CARD,
                                   "borderRadius": "4px", "border": f"1px solid {BDR}"},
                        )
                        for fig in [fig_ld, fig_fuel, fig_co2]
                    ],
                ),
            ]),

            comparison,
        ],
    )
