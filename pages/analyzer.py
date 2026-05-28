"""
FlightOps Suite — Route Analyzer page  (MODULE 4 visual redesign)
All physics/route logic unchanged. Results layout fully replaced.
"""
import math
import numpy as np
import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.graph_objects as go
import folium

from route import analyze_route, AIRPORTS
from physics import AIRCRAFT, isa, breguet_fuel
from components.viability import compute_viability_score

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
GREEN  = "#00d68f"

_RAJ = "'Rajdhani', sans-serif"
_SG  = "'Space Grotesk', sans-serif"

# Verdict badge backgrounds (rgba so they work in all browsers)
_BADGE_BG = {
    "#00d68f": "rgba(0,214,143,0.12)",
    "#f5a623": "rgba(245,166,35,0.12)",
    "#f04040": "rgba(240,64,64,0.12)",
    "#6a8faf": "rgba(106,143,175,0.12)",
}

# ── EU ETS airport codes (MODULE 3) ───────────────────────────────────────────
_EU_ETS_AIRPORTS = {
    "MAD", "BCN", "CDG", "FRA", "AMS", "MXP", "FCO",
    "MUC", "ZRH", "VIE", "LIS", "ATH", "CPH",
}
_EU_ETS_EUR_PER_TONNE = 65.0
_EUR_TO_USD = 1.08


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 3 — ESG helpers (unchanged)
# ══════════════════════════════════════════════════════════════════════════════

def _compute_esg_layer(result: dict, origin_code: str, destination_code: str) -> dict:
    passengers   = result.get("passengers") or 0
    co2_kg       = result.get("co2_kg")     or 0.0
    co2_tonnes   = result.get("co2_tonnes") or 0.0
    distance_km  = result.get("distance_km") or 0.0
    is_freighter = result.get("is_freighter", False)

    co2_per_pax = round(co2_kg / passengers, 1) if passengers > 0 and not is_freighter else None

    if distance_km < 2000:
        benchmark  = 255.0
        haul_label = "Short haul  (<2,000 km)"
    elif distance_km < 5000:
        benchmark  = 195.0
        haul_label = "Medium haul  (2,000-5,000 km)"
    else:
        benchmark  = 150.0
        haul_label = "Long haul  (>5,000 km)"

    if co2_per_pax is not None:
        pct = (co2_per_pax - benchmark) / benchmark * 100
        vs_label = (f"{abs(pct):.1f}% below benchmark" if pct < 0
                    else f"{pct:.1f}% above benchmark")
        indicator_color = GREEN if pct < 0 else (RED if pct > 20 else AMBER)
    else:
        pct = None; vs_label = "N/A (freighter)"; indicator_color = TDIM

    saf_co2_per_pax = round(co2_per_pax * 0.92, 1) if co2_per_pax is not None else None
    saf_saving      = round(co2_per_pax - saf_co2_per_pax, 1) if co2_per_pax is not None else None

    is_eu_ets = (origin_code in _EU_ETS_AIRPORTS and destination_code in _EU_ETS_AIRPORTS)
    if is_eu_ets and co2_tonnes:
        eu_ets_cost_usd = round(co2_tonnes * _EU_ETS_EUR_PER_TONNE * _EUR_TO_USD)
        eu_ets_label    = f"EU ETS applies - estimated carbon cost: ${eu_ets_cost_usd:,}"
    else:
        eu_ets_cost_usd = None; eu_ets_label = None

    return {
        "co2_per_pax_kg": co2_per_pax, "co2_benchmark_kg": benchmark,
        "haul_label": haul_label,
        "co2_vs_benchmark_pct": round(pct, 1) if pct is not None else None,
        "co2_vs_benchmark_label": vs_label, "co2_indicator_color": indicator_color,
        "saf_co2_per_pax_kg": saf_co2_per_pax, "saf_saving_kg": saf_saving,
        "is_eu_ets": is_eu_ets, "eu_ets_cost_usd": eu_ets_cost_usd,
        "eu_ets_label": eu_ets_label,
    }


def _esg_panel(esg: dict) -> html.Div:
    co2_val = f"{esg['co2_per_pax_kg']} kg"      if esg["co2_per_pax_kg"]      is not None else "N/A"
    saf_val = f"{esg['saf_co2_per_pax_kg']} kg"  if esg["saf_co2_per_pax_kg"]  is not None else "N/A"
    bm_val  = f"{esg['co2_benchmark_kg']:.0f} kg"

    def _sub(text, color):
        return html.P(text, style={"color": color, "fontSize": "8px",
                                   "fontFamily": _SG, "margin": "3px 0 0 0", "lineHeight": "1.3"})
    def _hdr(text):
        return html.P(text, style={"color": TDIM, "fontSize": "6px", "fontWeight": "500",
                                   "letterSpacing": "1.5px", "textTransform": "uppercase",
                                   "fontFamily": _SG, "margin": "0 0 5px 0"})
    def _val(text):
        return html.P(text, style={"color": WHITE, "fontSize": "13px", "fontWeight": "700",
                                   "fontFamily": _SG, "margin": "0", "lineHeight": "1"})

    cs = {"backgroundColor": CARD, "border": f"1px solid {BDR}", "borderRadius": "4px",
          "padding": "10px 12px", "flex": "1", "minWidth": "130px"}

    cards = html.Div(style={"display": "flex", "gap": "6px", "flexWrap": "wrap"}, children=[
        html.Div([_hdr("CO2 per passenger"), _val(co2_val),
                  _sub(esg["co2_vs_benchmark_label"], esg["co2_indicator_color"])], style=cs),
        html.Div([_hdr("With 10% SAF blend"), _val(saf_val),
                  _sub(f"{esg['saf_saving_kg']} kg CO2 saved / pax"
                       if esg["saf_saving_kg"] is not None else "—", GREEN)], style=cs),
        html.Div([_hdr("Industry benchmark"), _val(bm_val),
                  _sub(esg["haul_label"], TDIM)], style=cs),
    ])

    ets = html.Div()
    if esg.get("is_eu_ets") and esg.get("eu_ets_cost_usd") is not None:
        ets = html.Div([
            html.Span("EU ETS", style={"color": AMBER, "fontSize": "7px", "fontWeight": "700",
                                       "letterSpacing": "2px", "fontFamily": _SG,
                                       "textTransform": "uppercase", "marginRight": "10px",
                                       "flexShrink": "0"}),
            html.Span(esg["eu_ets_label"], style={"color": TSOFT, "fontSize": "9px",
                                                  "fontFamily": _SG}),
        ], style={"backgroundColor": "rgba(255,208,96,0.05)",
                  "border": "1px solid rgba(255,208,96,0.22)",
                  "borderLeft": f"3px solid {AMBER}", "borderRadius": "4px",
                  "padding": "8px 12px", "marginTop": "8px",
                  "display": "flex", "alignItems": "center"})

    return html.Div([cards, ets])


# ══════════════════════════════════════════════════════════════════════════════
# SHARED UI HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _lbl(text):
    return html.P(text, style={"color": TDIM, "fontSize": "7px", "fontWeight": "500",
                               "letterSpacing": "1.5px", "textTransform": "uppercase",
                               "fontFamily": _SG, "margin": "0 0 4px 0"})


def _sec(text):
    return html.P(text, style={"color": TDIM, "fontSize": "7px", "letterSpacing": "2.5px",
                               "textTransform": "uppercase", "fontFamily": _SG,
                               "margin": "0 0 8px 0", "borderBottom": f"1px solid {BDR}",
                               "paddingBottom": "5px"})


def _card(label, value, color=WHITE):
    return html.Div([
        html.P(label, style={"color": TDIM, "fontSize": "6px", "fontWeight": "500",
                             "letterSpacing": "1.5px", "textTransform": "uppercase",
                             "fontFamily": _SG, "margin": "0 0 5px 0"}),
        html.P(value, style={"color": color, "fontSize": "13px", "fontWeight": "700",
                             "fontFamily": _SG, "margin": "0", "lineHeight": "1"}),
    ], style={"backgroundColor": CARD, "border": f"1px solid {BDR}", "borderRadius": "4px",
              "padding": "10px 12px", "flex": "1", "minWidth": "100px"})


_DD = {"backgroundColor": CARD2, "color": "#000", "border": f"1px solid {BDR2}",
       "fontSize": "8px", "borderRadius": "3px"}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 4 — New UI components
# ══════════════════════════════════════════════════════════════════════════════

def _mcard(label: str, value: str, color: str, tooltip: str, sublabel: str) -> html.Div:
    """Metric card with dotted-underline tooltip on label and visible sub-label."""
    return html.Div([
        html.Span(label, title=tooltip, style={
            "color": TDIM, "fontSize": "6px", "fontWeight": "500",
            "letterSpacing": "1.5px", "textTransform": "uppercase", "fontFamily": _SG,
            "borderBottom": f"1px dotted {TDIM}", "cursor": "help",
            "display": "inline-block", "marginBottom": "5px",
        }),
        html.P(value, style={"color": color, "fontSize": "13px", "fontWeight": "700",
                             "fontFamily": _SG, "margin": "0 0 3px 0", "lineHeight": "1"}),
        html.P(sublabel, style={"color": TMUTED, "fontSize": "7px",
                                "fontFamily": _SG, "margin": "0"}),
    ], style={"backgroundColor": CARD, "border": f"1px solid {BDR}", "borderRadius": "4px",
              "padding": "10px 12px", "flex": "1", "minWidth": "110px"})


def _score_bar_row(label: str, score_val: int | None, max_val: int,
                   verdict_color: str) -> html.Div:
    """One labelled progress bar row for the viability card."""
    sv  = score_val or 0
    pct = int(sv / max_val * 100)
    return html.Div([
        html.Div([
            html.Span(label, style={"color": TDIM, "fontSize": "7px", "fontFamily": _SG}),
            html.Span(f"{sv}/{max_val}", style={"color": TSOFT, "fontSize": "7px",
                                                "fontFamily": _SG, "fontWeight": "600"}),
        ], style={"display": "flex", "justifyContent": "space-between", "marginBottom": "3px"}),
        html.Div([
            html.Div(style={"height": "4px", "width": f"{pct}%",
                            "backgroundColor": verdict_color, "borderRadius": "2px"})
        ], style={"height": "4px", "backgroundColor": BDR,
                  "borderRadius": "2px", "overflow": "hidden"}),
    ], style={"marginBottom": "9px"})


def _viability_card(v: dict, aircraft_label: str = None,
                    compact: bool = False) -> html.Div:
    """
    Route viability score card.
    compact=True for side-by-side comparison view (smaller fonts, narrower bars panel).
    aircraft_label: shown above the card in compact mode.
    """
    vc = v["verdict_color"]
    badge_bg = _BADGE_BG.get(vc, "rgba(255,255,255,0.05)")

    # Freighter / N/A
    if v["total_score"] is None:
        return html.Div([
            *(([html.P(aircraft_label, style={"color": WHITE, "fontWeight": "700",
                                              "fontSize": "10px", "fontFamily": _SG,
                                              "margin": "0 0 10px 0"})]
               if aircraft_label else [])),
            html.Div([
                html.P("FREIGHTER", style={"color": vc, "fontSize": "11px",
                                           "fontWeight": "700", "letterSpacing": "3px",
                                           "fontFamily": _RAJ, "margin": "0 0 6px 0"}),
                html.P(v["explanation"], style={"color": TDIM, "fontSize": "9px",
                                               "fontFamily": _SG, "lineHeight": "1.6",
                                               "margin": "0"}),
            ]),
        ], style={"backgroundColor": CARD, "border": f"1px solid {BDR}",
                  "borderLeft": f"3px solid {vc}", "borderRadius": "4px",
                  "padding": "16px 18px"})

    score_px = "34px" if compact else "48px"
    bars_w   = "160px" if compact else "200px"

    bars = html.Div([
        html.P("SCORE BREAKDOWN", style={"color": TDIM, "fontSize": "6px",
                                         "letterSpacing": "2px", "fontFamily": _SG,
                                         "textTransform": "uppercase", "margin": "0 0 10px 0"}),
        _score_bar_row("Financial",   v["financial_score"],   40, vc),
        _score_bar_row("Operational", v["operational_score"], 25, vc),
        _score_bar_row("ESG",         v["esg_score"],         20, vc),
        _score_bar_row("Market Fit",  v["market_score"],      15, vc),
    ], style={"width": bars_w, "flexShrink": "0"})

    inner = html.Div([
        # Left: score number + verdict badge + explanation
        html.Div([
            html.Span(str(v["total_score"]), style={
                "fontFamily": _RAJ, "fontWeight": "700", "fontSize": score_px,
                "color": vc, "lineHeight": "1", "display": "block", "marginBottom": "8px",
            }),
            html.Span(v["verdict"], style={
                "backgroundColor": badge_bg, "color": vc,
                "border": f"1px solid {vc}",
                "borderRadius": "20px", "padding": "2px 10px",
                "fontSize": "8px", "fontWeight": "700", "letterSpacing": "2px",
                "fontFamily": _SG, "display": "inline-block", "marginBottom": "10px",
            }),
            html.P(v["explanation"], style={
                "color": TDIM, "fontSize": "9px", "fontFamily": _SG,
                "lineHeight": "1.6", "margin": "0",
            }),
        ], style={"flex": "1", "paddingRight": "20px"}),
        bars,
    ], style={"display": "flex", "alignItems": "flex-start"})

    return html.Div([
        *(([html.P(aircraft_label, style={"color": WHITE, "fontWeight": "700",
                                          "fontSize": "10px", "fontFamily": _SG,
                                          "margin": "0 0 12px 0"})]
           if aircraft_label else [])),
        inner,
    ], style={"backgroundColor": CARD, "border": f"1px solid {BDR}",
              "borderLeft": f"3px solid {vc}", "borderRadius": "4px",
              "padding": "18px 20px"})


def _hbar_row(label: str, value: float, color: str, max_val: float) -> html.Div:
    """Horizontal bar row for unit economics panel."""
    pct = int(min(value / max_val * 100, 100)) if max_val > 0 else 0
    return html.Div([
        html.Div([
            html.Span(label, style={"color": TMID, "fontSize": "8px", "fontFamily": _SG}),
            html.Span(f"{value:.2f}¢", style={"color": TSOFT, "fontSize": "9px",
                                               "fontWeight": "700", "fontFamily": _SG}),
        ], style={"display": "flex", "justifyContent": "space-between", "marginBottom": "4px"}),
        html.Div([
            html.Div(style={"height": "4px", "width": f"{pct}%",
                            "backgroundColor": color, "borderRadius": "2px"})
        ], style={"height": "4px", "backgroundColor": BDR,
                  "borderRadius": "2px", "overflow": "hidden"}),
    ], style={"marginBottom": "14px"})


def _unit_economics_panel(result: dict) -> html.Div:
    """Left panel of Section 3: pure html.Div bar chart for unit economics."""
    is_free = result.get("is_freighter", False)
    casm      = result.get("casm_cents")      or 0.0
    casm_fuel = result.get("casm_fuel_cents") or 0.0
    rasm      = result.get("rasm_cents")      or 0.0

    inner: list
    if is_free or (casm == 0 and rasm == 0):
        inner = [html.P("Not applicable for freighter aircraft.",
                        style={"color": TDIM, "fontSize": "9px", "fontFamily": _SG})]
    else:
        max_val = max(casm, rasm, casm_fuel, 0.01)
        ratio   = rasm / casm if casm > 0 else 0.0
        ratio_color = GREEN if ratio >= 1.0 else RED

        inner = [
            _hbar_row("Fuel CASM",  casm_fuel, AMBER,   max_val),
            _hbar_row("Total CASM", casm,      "#b87000", max_val),
            _hbar_row("RASM",       rasm,      CYAN,    max_val),
            html.Div([
                html.Span("RASM / CASM ratio", style={"color": TDIM, "fontSize": "7px",
                                                       "fontFamily": _SG}),
                html.Span(f"{ratio:.2f}x", style={"color": ratio_color, "fontSize": "11px",
                                                   "fontWeight": "700", "fontFamily": _SG}),
            ], style={"display": "flex", "justifyContent": "space-between",
                      "alignItems": "baseline", "marginTop": "4px",
                      "paddingTop": "10px", "borderTop": f"1px solid {BDR}"}),
        ]

    return html.Div([
        html.P("UNIT ECONOMICS (¢/ASM)", style={
            "color": TDIM, "fontSize": "7px", "letterSpacing": "2px",
            "textTransform": "uppercase", "fontFamily": _SG, "margin": "0 0 14px 0",
        }),
        *inner,
    ], style={"backgroundColor": CARD, "border": f"1px solid {BDR}",
              "borderRadius": "4px", "padding": "14px 16px", "flex": "1"})


def _sensitivity_panel(result: dict) -> html.Div:
    """Right panel of Section 3: sensitivity stress-test table."""
    sens    = result.get("sensitivity")
    is_free = result.get("is_freighter", False)

    if is_free or sens is None:
        inner = [html.P("Not applicable for freighter aircraft.",
                        style={"color": TDIM, "fontSize": "9px", "fontFamily": _SG})]
    else:
        rows = [
            ("Fuel +20%",          sens["fuel_plus20"],        "Oil price spike or hedging miss"),
            ("Load factor -10pp",  sens["lf_minus10pp"],       "Demand shock or competitor entry"),
            ("Ticket price -15%",  sens["ticket_minus15pct"],  "Yield dilution or fare war"),
        ]

        def _row(label, delta, impact):
            color = GREEN if delta >= 0 else RED
            sign  = "+" if delta >= 0 else ""
            return html.Div([
                html.Div([
                    html.Span(label, style={"color": TMID, "fontSize": "9px",
                                           "fontFamily": _SG, "fontWeight": "500"}),
                    html.Span(f"{sign}${delta:,}", style={"color": color, "fontSize": "11px",
                                                          "fontWeight": "700",
                                                          "fontFamily": _SG}),
                ], style={"display": "flex", "justifyContent": "space-between",
                          "alignItems": "baseline", "marginBottom": "3px"}),
                html.P(impact, style={"color": TDIM, "fontSize": "7px",
                                      "fontFamily": _SG, "margin": "0"}),
            ], style={"marginBottom": "12px", "paddingBottom": "12px",
                      "borderBottom": f"1px solid {BDR}"})

        inner = [_row(l, d, i) for l, d, i in rows]

    return html.Div([
        html.P("SENSITIVITY ANALYSIS", style={
            "color": TDIM, "fontSize": "7px", "letterSpacing": "2px",
            "textTransform": "uppercase", "fontFamily": _SG, "margin": "0 0 14px 0",
        }),
        *inner,
    ], style={"backgroundColor": CARD, "border": f"1px solid {BDR}",
              "borderRadius": "4px", "padding": "14px 16px", "flex": "1"})


# ── Layout ────────────────────────────────────────────────────────────────────
layout = html.Div(
    style={"display": "flex", "minHeight": "calc(100vh - 42px)", "backgroundColor": BG},
    children=[

        # SIDEBAR (unchanged)
        html.Div(style={
            "width": "200px", "minWidth": "200px", "backgroundColor": CARD,
            "borderRight": f"1px solid {BDR}", "padding": "20px 14px",
            "display": "flex", "flexDirection": "column", "gap": "10px", "overflowY": "auto",
        }, children=[
            html.P("PARAMETERS", style={"fontFamily": _RAJ, "fontWeight": "700",
                                        "fontSize": "13px", "letterSpacing": "3px",
                                        "color": GOLD, "margin": "0 0 4px 0"}),
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
                "backgroundColor": CYAN, "color": BG, "border": "none",
                "borderRadius": "3px", "padding": "10px", "fontWeight": "700",
                "fontSize": "8px", "letterSpacing": "2px", "cursor": "pointer",
                "width": "100%", "fontFamily": _SG, "textTransform": "uppercase",
            }),
        ]),

        # MAIN (welcome state)
        html.Div(id="az-main", style={"flex": "1", "padding": "28px 32px", "overflowY": "auto"},
            children=[
                html.Div(style={"backgroundColor": CARD, "border": f"1px solid {BDR}",
                                "borderRadius": "4px", "padding": "48px",
                                "textAlign": "center", "marginTop": "40px"}, children=[
                    html.H1("ROUTE ANALYZER", style={"fontFamily": _RAJ, "fontWeight": "700",
                                                     "fontSize": "26px", "letterSpacing": "5px",
                                                     "color": CYAN, "margin": "0 0 10px 0"}),
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

    # ── Feasibility check ─────────────────────────────────────────────────────
    if result["fuel_burned_kg"] > ac["max_fuel"] * 0.95:
        g   = 9.80665
        W_i = ac["MTOW"] * g
        W_f = (ac["MTOW"] - ac["max_fuel"] * 0.95) * g
        from physics import isa as _isa, best_LD as _best_LD
        T, _, _ = _isa(ac["cruise_alt"])
        V_cr    = ac["cruise_mach"] * (1.4 * 287.05 * T) ** 0.5
        _, ld   = _best_LD(ac["CD0"], ac["k"])
        max_km  = int((V_cr / (ac["TSFC"] * g)) * ld * math.log(W_i / W_f) / 1000)
        return html.Div(style={"backgroundColor": "#1a0a0a", "border": f"1px solid {RED}",
                               "borderRadius": "4px", "padding": "20px 24px",
                               "maxWidth": "560px"}, children=[
            html.Div("⚠", style={"color": RED, "fontSize": "20px", "margin": "0 0 10px 0"}),
            html.H2("ROUTE NOT FEASIBLE", style={"fontFamily": _RAJ, "fontWeight": "700",
                                                  "fontSize": "16px", "letterSpacing": "2px",
                                                  "color": RED, "margin": "0 0 12px 0"}),
            html.P(f"The {aircraft} does not have sufficient fuel capacity. "
                   f"Maximum range is approximately {max_km:,} km, but this route "
                   f"requires {result['distance_km']:,} km.",
                   style={"color": TMID, "fontSize": "10px", "fontFamily": _SG,
                          "lineHeight": "1.7", "margin": "0 0 10px 0"}),
            html.P("Try a longer-range aircraft such as the Boeing 787-9 or Airbus A350-900.",
                   style={"color": TDIM, "fontSize": "9px", "fontFamily": _SG,
                          "fontStyle": "italic", "margin": "0"}),
        ])

    # ── Altitude sweep for charts ─────────────────────────────────────────────
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

    _ch = dict(paper_bgcolor=CARD, plot_bgcolor=CARD,
               font=dict(color=TDIM, size=10, family=_SG),
               xaxis=dict(gridcolor=BDR, color=TDIM, title_font_color=TDIM),
               yaxis=dict(gridcolor=BDR, color=TDIM, title_font_color=TDIM),
               margin=dict(l=44, r=12, t=32, b=32), height=220)

    fig_ld   = go.Figure(go.Scatter(x=alts/1000, y=ld_v,   mode="lines", line=dict(color=CYAN,  width=1.5)))
    fig_fuel = go.Figure(go.Scatter(x=alts/1000, y=fuel_v, mode="lines", line=dict(color=AMBER, width=1.5)))
    fig_co2  = go.Figure(go.Scatter(x=alts/1000, y=co2_v,  mode="lines", line=dict(color=RED,   width=1.5)))
    fig_ld.update_layout(  title=dict(text="L/D vs Altitude",  font=dict(color=TDIM, size=9)), **_ch)
    fig_fuel.update_layout(title=dict(text="Fuel Burn vs Alt", font=dict(color=TDIM, size=9)), **_ch)
    fig_co2.update_layout( title=dict(text="CO2 vs Altitude",  font=dict(color=TDIM, size=9)), **_ch)

    # ── Folium map ────────────────────────────────────────────────────────────
    mid_lat = (AIRPORTS[origin]["lat"] + AIRPORTS[destination]["lat"]) / 2
    mid_lon = (AIRPORTS[origin]["lon"] + AIRPORTS[destination]["lon"]) / 2
    m = folium.Map(location=[mid_lat, mid_lon], zoom_start=3, tiles="CartoDB dark_matter")
    folium.PolyLine(result["waypoints"], color=CYAN, weight=2, opacity=0.85).add_to(m)
    for code in [origin, destination]:
        ap = AIRPORTS[code]
        folium.CircleMarker([ap["lat"], ap["lon"]], radius=5, color=CYAN,
                            fill=True, fill_color=CYAN, fill_opacity=1.0,
                            popup=ap["name"]).add_to(m)
    map_html = m._repr_html_()

    # ── Route risk calculations ───────────────────────────────────────────────
    avail      = ac["max_fuel"] * 0.85 - result["fuel_burned_kg"]
    extra200   = result["fuel_burned_kg"] * 200 / result["distance_km"] if result["distance_km"] > 0 else 0
    can_divert = avail >= extra200

    breakeven_lf = None
    if (not result.get("is_freighter") and result.get("seats", 0) > 0
            and result.get("ticket_price", 0) > 0):
        breakeven_lf = min(
            round((result["fuel_cost"] / (result["seats"] * result["ticket_price"])) * 100, 1),
            100.0)

    co2_pax = None
    if not result.get("is_freighter") and result.get("passengers", 0) > 0:
        co2_pax = round(result["co2_kg"] / result["passengers"], 1)

    profit_color = GREEN if result.get("profit",         0) > 0 else RED
    pax_color    = GREEN if result.get("profit_per_pax", 0) > 0 else RED

    # ── Viability score (MODULE 2) ────────────────────────────────────────────
    v   = compute_viability_score(result)
    esg = _compute_esg_layer(result, origin, destination)

    # ── Operating margin color ────────────────────────────────────────────────
    op_margin = result.get("op_margin_pct") or 0.0
    margin_color = GREEN if op_margin > 0 else RED

    # ── Comparison aircraft ───────────────────────────────────────────────────
    comparison = html.Div()
    if aircraft2 and aircraft2 != "none" and aircraft2 != aircraft:
        r2   = analyze_route(origin, destination, aircraft2, payload,
                             fuel_price, load_factor, ticket_mult)
        pc2  = GREEN if r2.get("profit", 0) > 0 else RED
        v2   = compute_viability_score(r2)
        esg2 = _compute_esg_layer(r2, origin, destination)

        def _cmp_col(name, r, pc):
            return html.Div([
                html.P(name, style={"color": WHITE, "fontWeight": "700", "fontSize": "10px",
                                    "fontFamily": _SG, "margin": "0 0 8px 0"}),
                _card("Fuel Burned",  f"{r['fuel_burned_kg']:,} kg", AMBER),
                _card("Fuel Cost",    f"${r['fuel_cost']:,}",        AMBER),
                _card("Passengers",   str(r["passengers"]),          WHITE),
                _card("Revenue",      f"${r['revenue']:,}",          CYAN),
                _card("Profit",       f"${r['profit']:,}",           pc),
                _card("Profit / Pax", f"${r['profit_per_pax']}",     pc),
                _card("CO2",          f"{r['co2_tonnes']} t",        AMBER),
                _card("L/D",          str(r["LD_ratio"]),            WHITE),
            ], style={"flex": "1", "display": "flex", "flexDirection": "column", "gap": "6px"})

        comparison = html.Div([
            _sec("AIRCRAFT COMPARISON"),

            # Compact viability cards side by side
            html.Div([
                _viability_card(v,  aircraft,  compact=True),
                _viability_card(v2, aircraft2, compact=True),
            ], style={"display": "flex", "gap": "12px", "marginBottom": "16px"}),

            # Metrics comparison
            _sec("METRICS COMPARISON"),
            html.Div([
                _cmp_col(aircraft,  result, profit_color),
                _cmp_col(aircraft2, r2,     pc2),
            ], style={"display": "flex", "gap": "12px", "marginBottom": "16px"}),

            # ESG comparison
            _sec("ESG COMPARISON"),
            html.Div([
                html.Div([
                    html.P(aircraft, style={"color": WHITE, "fontWeight": "700",
                                            "fontSize": "10px", "fontFamily": _SG,
                                            "margin": "0 0 8px 0"}),
                    _esg_panel(esg),
                ], style={"flex": "1"}),
                html.Div([
                    html.P(aircraft2, style={"color": WHITE, "fontWeight": "700",
                                             "fontSize": "10px", "fontFamily": _SG,
                                             "margin": "0 0 8px 0"}),
                    _esg_panel(esg2),
                ], style={"flex": "1"}),
            ], style={"display": "flex", "gap": "16px"}),
        ])

    # ── Section 5: Route Risk panel ───────────────────────────────────────────
    risk_panel = html.Div([
        html.Div([
            html.P("Diversion +200 km", style={"color": TDIM, "fontSize": "6px",
                                               "letterSpacing": "1.5px", "textTransform": "uppercase",
                                               "fontFamily": _SG, "margin": "0 0 6px 0"}),
            html.Div([
                html.Span("FUEL OK" if can_divert else "MARGINAL", style={
                    "border":          f"1px solid {CYAN}" if can_divert else f"1px solid {RED}",
                    "color":           CYAN if can_divert else RED,
                    "backgroundColor": "#001a2a" if can_divert else "rgba(240,64,64,0.1)",
                    "borderRadius":    "3px", "padding": "2px 8px", "fontSize": "8px",
                    "fontWeight":      "700", "letterSpacing": "1px", "fontFamily": _SG,
                }),
                html.Span(f"  {avail:,.0f} kg remaining",
                          style={"color": TDIM, "fontSize": "8px",
                                 "marginLeft": "8px", "fontFamily": _SG}),
            ], style={"display": "flex", "alignItems": "center"}),
        ]),
        html.Div([
            html.P("Break-Even LF", style={"color": TDIM, "fontSize": "6px",
                                           "letterSpacing": "1.5px", "textTransform": "uppercase",
                                           "fontFamily": _SG, "margin": "0 0 6px 0"}),
            (html.Span(f"{breakeven_lf:.1f} %", style={
                "color":      GREEN if breakeven_lf <= load_factor else RED,
                "fontSize":   "13px", "fontWeight": "700", "fontFamily": _SG,
             }) if breakeven_lf is not None
             else html.Span("N/A", style={"color": TDIM, "fontFamily": _SG})),
        ]),
        html.Div([
            html.P("CO2 per Passenger", style={"color": TDIM, "fontSize": "6px",
                                               "letterSpacing": "1.5px", "textTransform": "uppercase",
                                               "fontFamily": _SG, "margin": "0 0 6px 0"}),
            (html.Span(f"{co2_pax} kg", style={"color": TMID, "fontSize": "13px",
                                               "fontWeight": "700", "fontFamily": _SG})
             if co2_pax is not None
             else html.Span("N/A", style={"color": TDIM, "fontFamily": _SG})),
        ]),
    ], style={"backgroundColor": CARD, "border": f"1px solid {BDR}", "borderRadius": "4px",
              "padding": "14px 16px", "display": "flex", "flexWrap": "wrap", "gap": "20px"})

    # ── Assemble result layout (8 sections) ───────────────────────────────────
    return html.Div(
        style={"display": "flex", "flexDirection": "column", "gap": "18px"},
        children=[

            # Route title
            html.H2(f"{result['origin']}  →  {result['destination']}",
                    style={"color": WHITE, "margin": "0", "fontSize": "14px",
                           "fontWeight": "700", "fontFamily": _SG}),

            # S1 — Route Viability Score
            _viability_card(v),

            # S2 — Six key metrics
            html.Div([
                _sec("KEY METRICS"),
                html.Div(style={"display": "flex", "gap": "6px", "flexWrap": "wrap"}, children=[
                    _mcard("Distance",    f"{result['distance_km']:,} km", WHITE,
                           "Great circle distance between origin and destination airports",
                           "great circle km"),
                    _mcard("Flight Time", f"{result['flight_time_hr']} hrs", WHITE,
                           "Estimated block time at cruise speed with wind component",
                           "incl. wind component"),
                    _mcard("Fuel Burned", f"{result['fuel_burned_kg']:,} kg", AMBER,
                           "Total fuel burned calculated via the Breguet range equation",
                           "Breguet range equation"),
                    _mcard("CASM",
                           f"{result.get('casm_cents') or 0:.2f}¢" if not result.get("is_freighter") else "N/A",
                           AMBER,
                           "Total operating cost per available seat mile (fuel + non-fuel costs)",
                           "total cost / seat-mile"),
                    _mcard("RASM",
                           f"{result.get('rasm_cents') or 0:.2f}¢" if not result.get("is_freighter") else "N/A",
                           CYAN,
                           "Revenue generated per available seat mile at current load factor and ticket price",
                           "revenue / seat-mile"),
                    _mcard("Op. Margin",
                           f"{result.get('op_margin_pct') or 0:.1f}%" if not result.get("is_freighter") else "N/A",
                           margin_color,
                           "Operating profit as a percentage of revenue (total cost basis including non-fuel costs)",
                           "op. profit / revenue"),
                ]),
            ]),

            # S3 — Economics breakdown
            html.Div([
                _sec("ECONOMICS"),
                html.Div([
                    _unit_economics_panel(result),
                    _sensitivity_panel(result),
                ], style={"display": "flex", "gap": "12px"}),
            ]),

            # S4 — ESG Analysis (MODULE 3)
            html.Div([_sec("ESG ANALYSIS"), _esg_panel(esg)]),

            # S5 — Route Risk
            html.Div([_sec("ROUTE RISK"), risk_panel]),

            # S6 — Performance charts (before map per spec)
            html.Div([
                _sec("PERFORMANCE VS ALTITUDE"),
                html.Div(style={"display": "flex", "gap": "8px"}, children=[
                    html.Div(dcc.Graph(figure=fig, config={"displayModeBar": False}),
                             style={"flex": "1", "backgroundColor": CARD,
                                    "borderRadius": "4px", "border": f"1px solid {BDR}"})
                    for fig in [fig_ld, fig_fuel, fig_co2]
                ]),
            ]),

            # S7 — Route Map
            html.Div([
                _sec("ROUTE MAP"),
                html.Iframe(srcDoc=map_html, style={"width": "100%", "height": "400px",
                                                    "border": f"1px solid {BDR}",
                                                    "borderRadius": "4px"}),
            ]),

            # S8 — Aircraft comparison (if selected)
            comparison,
        ],
    )
