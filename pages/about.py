"""
FlightOps Suite — About page
"""
import dash
from dash import html

dash.register_page(__name__, path="/about", name="About")

BG    = "#030508"
DARK  = "#030508"
CARD  = "#04080f"
BDR   = "#0a1a2a"
CYAN  = "#00c8ff"
GOLD  = "#ffd060"
TSOFT = "#c8d8e8"
TMID  = "#8ab0c8"
TDIM  = "#3a6080"
TMUTED= "#2a4a65"

_RAJ = "'Rajdhani', sans-serif"
_SG  = "'Space Grotesk', sans-serif"


def _card(title: str, children: list) -> html.Div:
    return html.Div(
        [
            html.P(title, style={
                "color":         GOLD,
                "fontSize":      "8px",
                "fontWeight":    "700",
                "letterSpacing": "2px",
                "textTransform": "uppercase",
                "fontFamily":    _SG,
                "margin":        "0 0 14px 0",
                "borderBottom":  f"1px solid {BDR}",
                "paddingBottom": "8px",
            }),
            *children,
        ],
        style={
            "backgroundColor": CARD,
            "border":          f"1px solid {BDR}",
            "borderRadius":    "4px",
            "padding":         "20px 22px",
            "marginBottom":    "10px",
        },
    )


def _p(text: str, color: str = None) -> html.P:
    return html.P(text, style={
        "color":      color or TMID,
        "fontSize":   "10px",
        "lineHeight": "1.80",
        "margin":     "0 0 10px 0",
        "fontFamily": _SG,
    })


def _formula(text: str) -> html.Div:
    return html.Div(text, style={
        "borderLeft":      f"2px solid {CYAN}",
        "backgroundColor": DARK,
        "padding":         "8px 14px",
        "fontFamily":      "'Courier New', monospace",
        "fontSize":        "11px",
        "color":           CYAN,
        "margin":          "8px 0 12px 0",
        "letterSpacing":   "0.3px",
    })


def _bullet(items: list) -> html.Div:
    return html.Div([
        html.Div([
            html.Span("—", style={
                "color":       GOLD,
                "marginRight": "8px",
                "fontWeight":  "700",
            }),
            html.Span(item, style={
                "color":      TMID,
                "fontSize":   "10px",
                "fontFamily": _SG,
            }),
        ], style={"marginBottom": "6px"})
        for item in items
    ])


layout = html.Div(
    [
        html.Div(
            [
                # Header
                html.H1("ABOUT", style={
                    "fontFamily":    _RAJ,
                    "fontWeight":    "700",
                    "fontSize":      "22px",
                    "letterSpacing": "5px",
                    "color":         CYAN,
                    "margin":        "0 0 4px 0",
                }),
                html.P("What · How · Why", style={
                    "color":         TDIM,
                    "fontSize":      "8px",
                    "letterSpacing": "3px",
                    "textTransform": "uppercase",
                    "fontFamily":    _SG,
                    "margin":        "0 0 24px 0",
                }),

                # Card 1 — What
                _card("What is FlightOps", [
                    _p("FlightOps is a physics-based tool for analysing commercial flight routes. "
                       "Pick any origin, destination and aircraft — it calculates fuel burn, "
                       "flight time, emissions and route economics using real aerodynamic models. "
                       "No black boxes, no guesswork."),
                    _p("I built this because I wanted to understand how airlines actually make "
                       "decisions — not in a textbook sense, but the real tradeoffs: why a 787 "
                       "beats a 777 on efficiency, how much a headwind actually costs, at what "
                       "load factor a route breaks even.", color=TMUTED),
                ]),

                # Card 2 — How it works
                _card("How it works", [
                    _p("Three physics models run under the hood:"),
                    html.P("ISA Atmosphere", style={
                        "color": GOLD, "fontSize": "8px", "fontWeight": "700",
                        "letterSpacing": "1.5px", "textTransform": "uppercase",
                        "fontFamily": _SG, "margin": "10px 0 4px 0",
                    }),
                    _formula("T(h) = 288.15 − 0.0065 · h"),
                    html.P("Breguet Range Equation", style={
                        "color": GOLD, "fontSize": "8px", "fontWeight": "700",
                        "letterSpacing": "1.5px", "textTransform": "uppercase",
                        "fontFamily": _SG, "margin": "4px 0 4px 0",
                    }),
                    _formula("Wf = Wi · exp(−TSFC · g · R / (V · L/D))"),
                    html.P("CO2 Conversion", style={
                        "color": GOLD, "fontSize": "8px", "fontWeight": "700",
                        "letterSpacing": "1.5px", "textTransform": "uppercase",
                        "fontFamily": _SG, "margin": "4px 0 4px 0",
                    }),
                    _formula("CO2 (kg) = Fuel burned × 3.16"),
                    _p("The optimizer finds the altitude that maximises L/D for each aircraft, "
                       "then runs Breguet to get fuel burn. Wind uses NOAA/ECMWF climatological "
                       "averages by latitude band and season.", color=TMUTED),
                ]),

                # Card 3 — Data sources
                _card("Data sources", [
                    _bullet([
                        "Boeing & Airbus Airport Planning documents",
                        "ICAO Engine Emissions Databank",
                        "Published aerodynamic analyses & drag polars",
                        "Eurocontrol BADA 4 reference coefficients",
                    ]),
                    html.Div(style={"marginTop": "14px", "paddingTop": "12px",
                                    "borderTop": f"1px solid {BDR}"}),
                    html.P("Built by Giorgio Turchetti", style={
                        "color":         TSOFT,
                        "fontSize":      "10px",
                        "fontWeight":    "500",
                        "fontFamily":    _SG,
                        "margin":        "0 0 2px 0",
                    }),
                    html.P("Illinois Institute of Technology", style={
                        "color":   TMUTED,
                        "fontSize":"8px",
                        "fontFamily": _SG,
                        "margin":  "0",
                        "opacity": "0.5",
                    }),
                ]),

            ],
            style={
                "maxWidth":  "640px",
                "margin":    "0 auto",
                "padding":   "40px 24px 60px",
                "boxSizing": "border-box",
            },
        )
    ],
    style={"backgroundColor": BG, "minHeight": "calc(100vh - 42px)"},
)
