"""
FlightOps Suite — Multi-page Dash entry point
"""
import os
import dash
from dash import html, dcc
from components.navbar import create_navbar

_FONTS = (
    "https://fonts.googleapis.com/css2?"
    "family=Space+Grotesk:wght@300;400;500;700"
    "&family=Rajdhani:wght@700&display=swap"
)

app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[_FONTS],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.title = "FlightOps Suite"

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        create_navbar(),
        html.Div(dash.page_container, style={"flex": "1", "overflowY": "auto"}),
    ],
    style={
        "backgroundColor": "#030508",
        "minHeight":       "100vh",
        "display":         "flex",
        "flexDirection":   "column",
        "fontFamily":      "'Space Grotesk', sans-serif",
        "margin":          "0",
        "padding":         "0",
    },
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8050)), debug=True)
