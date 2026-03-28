"""
FlightOps Suite — Home page
"""
import random
import dash
from dash import html, dcc

dash.register_page(__name__, path="/", name="Home")

# ── Palette ───────────────────────────────────────────────────────────────────
BG      = "#030508"
CARD2   = "#060e1a"
BORDER2 = "#0d2030"
CYAN    = "#00c8ff"
GOLD    = "#ffd060"
WHITE   = "#ffffff"
TMUTED  = "#2a4a65"
TDIM    = "#3a6080"

# ── Stars (fixed seed → stable layout) ───────────────────────────────────────
_rng = random.Random(7)

def _stars(n=110):
    out = []
    for _ in range(n):
        x    = _rng.uniform(1, 99)
        y    = _rng.uniform(1, 99)
        sz   = _rng.uniform(1.0, 2.2)
        dur  = _rng.uniform(3, 10)
        dly  = _rng.uniform(0, 8)
        out.append(html.Div(style={
            "position":        "absolute",
            "left":            f"{x}%",
            "top":             f"{y}%",
            "width":           f"{sz}px",
            "height":          f"{sz}px",
            "borderRadius":    "50%",
            "backgroundColor": "#ffffff",
            "animation":       f"starPulse {dur:.1f}s {dly:.1f}s ease-in-out infinite alternate",
            "pointerEvents":   "none",
        }))
    return out


# ── HUD corner bracket ────────────────────────────────────────────────────────
def _corner(pos: str) -> html.Div:
    """pos: 'tl' | 'tr' | 'bl' | 'br'"""
    top    = pos[0] == "t"
    left   = pos[1] == "l"
    return html.Div(style={
        "position":    "absolute",
        "top":         "24px" if top    else "auto",
        "bottom":      "24px" if not top  else "auto",
        "left":        "32px" if left   else "auto",
        "right":       "32px" if not left else "auto",
        "width":       "14px",
        "height":      "14px",
        "borderTop":   f"1.5px solid {GOLD}" if top    else "none",
        "borderBottom":f"1.5px solid {GOLD}" if not top  else "none",
        "borderLeft":  f"1.5px solid {GOLD}" if left   else "none",
        "borderRight": f"1.5px solid {GOLD}" if not left else "none",
        "opacity":     "0.6",
        "pointerEvents":"none",
    })


# ── Nav button ────────────────────────────────────────────────────────────────
def _btn(icon, title, sub, href):
    return dcc.Link(
        html.Div([
            html.Span(icon, style={
                "fontSize":     "20px",
                "color":        CYAN,
                "display":      "block",
                "marginBottom": "8px",
            }),
            html.Div(title, style={
                "fontSize":      "9px",
                "fontWeight":    "700",
                "color":         CYAN,
                "letterSpacing": "2px",
                "textTransform": "uppercase",
                "marginBottom":  "4px",
                "fontFamily":    "'Space Grotesk', sans-serif",
            }),
            html.Div(sub, style={
                "fontSize": "8px",
                "color":    TMUTED,
                "fontFamily": "'Space Grotesk', sans-serif",
            }),
        ], style={
            "border":          f"1px solid {BORDER2}",
            "backgroundColor": CARD2,
            "borderRadius":    "4px",
            "padding":         "16px 20px",
            "minWidth":        "150px",
            "cursor":          "pointer",
            "transition":      "border-color 0.2s, background 0.2s",
        }, className="fo-btn"),
        href=href,
        style={"textDecoration": "none"},
    )


# ── Page layout ───────────────────────────────────────────────────────────────
layout = html.Div(
    style={"backgroundColor": BG, "position": "relative", "overflow": "hidden"},
    children=[

        # Starfield
        html.Div(
            _stars(110),
            style={
                "position":      "absolute",
                "inset":         "0",
                "pointerEvents": "none",
                "zIndex":        "0",
                "overflow":      "hidden",
            },
        ),

        # HUD top gradient line
        html.Div(style={
            "position":   "absolute",
            "top":        "0",
            "left":       "0",
            "right":      "0",
            "height":     "1px",
            "background": "linear-gradient(90deg, transparent, rgba(255,208,96,0.08), transparent)",
            "zIndex":     "1",
            "pointerEvents": "none",
        }),
        # HUD bottom gradient line
        html.Div(style={
            "position":   "absolute",
            "bottom":     "0",
            "left":       "0",
            "right":      "0",
            "height":     "1px",
            "background": "linear-gradient(90deg, transparent, rgba(255,208,96,0.08), transparent)",
            "zIndex":     "1",
            "pointerEvents": "none",
        }),

        # Corner brackets
        _corner("tl"), _corner("tr"), _corner("bl"), _corner("br"),

        # Foreground
        html.Div(
            style={
                "position":       "relative",
                "zIndex":         "2",
                "minHeight":      "calc(100vh - 42px)",
                "display":        "flex",
                "flexDirection":  "column",
                "justifyContent": "center",
                "alignItems":     "center",
                "padding":        "60px 40px",
                "boxSizing":      "border-box",
                "textAlign":      "center",
            },
            children=[

                # Title
                html.H1(
                    [
                        html.Span("FLIGHT", style={"color": WHITE}),
                        html.Span("OPS", style={"color": GOLD}),
                        html.Span(" SUITE", style={"color": WHITE}),
                    ],
                    className="fo-title",
                    style={
                        "fontFamily":    "'Rajdhani', sans-serif",
                        "fontWeight":    "700",
                        "fontSize":      "42px",
                        "letterSpacing": "10px",
                        "margin":        "0 0 10px 0",
                        "lineHeight":    "1",
                    },
                ),

                # Subtitle
                html.P(
                    "Aircraft Route & Performance Analyzer",
                    className="fo-subtitle",
                    style={
                        "color":         TMUTED,
                        "fontSize":      "13px",
                        "letterSpacing": "3px",
                        "textTransform": "uppercase",
                        "margin":        "0 0 20px 0",
                        "fontFamily":    "'Space Grotesk', sans-serif",
                    },
                ),

                # Divider
                html.Div(style={
                    "width":           "60px",
                    "height":          "1px",
                    "backgroundColor": f"rgba(255,208,96,0.2)",
                    "margin":          "0 auto 28px",
                }),

                # Buttons
                html.Div(
                    [
                        _btn("◈", "ROUTE ANALYZER", "Plan any route",     "/analyzer"),
                        _btn("▦", "FLEET INTEL",    "Compare aircraft",   "/fleet"),
                        _btn("◎", "ABOUT",          "Methodology",        "/about"),
                    ],
                    className="fo-buttons",
                    style={
                        "display":        "flex",
                        "gap":            "12px",
                        "justifyContent": "center",
                        "flexWrap":       "wrap",
                    },
                ),
            ],
        ),
    ],
)
