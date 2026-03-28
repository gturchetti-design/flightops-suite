"""
FlightOps Suite — Navbar
"""
from dash import html, dcc, Input, Output, callback

BG    = "#030508"
GOLD  = "#ffd060"
TDIM  = "#3a6080"
WHITE = "#ffffff"
BDR   = "#0a1520"

_LINKS = [
    {"label": "HOME",           "href": "/"},
    {"label": "ROUTE ANALYZER", "href": "/analyzer"},
    {"label": "FLEET",          "href": "/fleet"},
    {"label": "ABOUT",          "href": "/about"},
]

_BASE = {
    "color":          TDIM,
    "textDecoration": "none",
    "fontSize":       "9px",
    "letterSpacing":  "2px",
    "fontWeight":     "500",
    "padding":        "4px 0",
    "borderBottom":   "1px solid transparent",
    "transition":     "color 0.2s, border-color 0.2s",
    "whiteSpace":     "nowrap",
    "fontFamily":     "'Space Grotesk', sans-serif",
    "textTransform":  "uppercase",
}
_ACTIVE = {
    **_BASE,
    "color":        WHITE,
    "borderBottom": f"1px solid {GOLD}",
}


def create_navbar() -> html.Div:
    return html.Div(
        [
            dcc.Link(
                html.Span("FLIGHTOPS", style={
                    "color":         GOLD,
                    "fontFamily":    "'Rajdhani', sans-serif",
                    "fontWeight":    "700",
                    "fontSize":      "18px",
                    "letterSpacing": "5px",
                }),
                href="/",
                style={"textDecoration": "none"},
            ),
            html.Div(
                [
                    dcc.Link(
                        lnk["label"], href=lnk["href"],
                        id=f"navlink-{i}", style=_BASE,
                    )
                    for i, lnk in enumerate(_LINKS)
                ],
                style={"display": "flex", "gap": "28px", "alignItems": "center"},
            ),
        ],
        style={
            "display":         "flex",
            "justifyContent":  "space-between",
            "alignItems":      "center",
            "backgroundColor": BG,
            "borderBottom":    f"1px solid {BDR}",
            "padding":         "0 36px",
            "height":          "42px",
            "position":        "sticky",
            "top":             "0",
            "zIndex":          "1000",
            "boxSizing":       "border-box",
        },
    )


@callback(
    [Output(f"navlink-{i}", "style") for i in range(len(_LINKS))],
    Input("url", "pathname"),
)
def _active(pathname):
    cur = pathname or "/"
    return [_ACTIVE if cur == lnk["href"] else _BASE for lnk in _LINKS]
