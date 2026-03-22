import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import numpy as np
import folium
from route import analyze_route, AIRPORTS
from physics import AIRCRAFT, isa, breguet_fuel, base_ticket_price

app = dash.Dash(__name__)
app.title = "FlightOps Suite"

C = {
    "bg": "#0a0e1a",
    "sidebar": "#0d1220",
    "card": "#0d1a2e",
    "border": "#1e3a5f",
    "blue": "#00bfff",
    "text": "#e0e6f0",
    "muted": "#6a8faf",
    "red": "#ff6b6b",
    "green": "#90ee90",
    "gold": "#ffd700",
}

def metric_card(label, value, color=None):
    return html.Div([
        html.P(label, style={
            "color": C["muted"], "fontSize": "0.7rem",
            "textTransform": "uppercase", "letterSpacing": "2px",
            "margin": "0 0 6px 0"
        }),
        html.P(value, style={
            "color": color or C["blue"], "fontSize": "1.5rem",
            "fontWeight": "bold", "margin": "0"
        }),
    ], style={
        "backgroundColor": C["card"],
        "border": f"1px solid {C['border']}",
        "borderRadius": "8px",
        "padding": "18px",
        "flex": "1",
        "minWidth": "140px"
    })

app.layout = html.Div(style={
    "display": "flex", "minHeight": "100vh",
    "backgroundColor": C["bg"], "fontFamily": "Arial, sans-serif"
}, children=[

    # SIDEBAR
    html.Div(style={
        "width": "300px", "minWidth": "300px",
        "backgroundColor": C["sidebar"],
        "borderRight": f"1px solid {C['border']}",
        "padding": "30px 20px",
        "display": "flex", "flexDirection": "column", "gap": "14px",
        "overflowY": "auto"
    }, children=[

        html.H2("FlightOps Suite", style={
            "color": C["blue"], "fontSize": "1.1rem",
            "letterSpacing": "3px", "textTransform": "uppercase", "margin": "0"
        }),
        html.P("Route & Performance Analyzer", style={
            "color": C["muted"], "fontSize": "0.7rem",
            "letterSpacing": "2px", "textTransform": "uppercase", "margin": "0 0 10px 0"
        }),

        html.Hr(style={"borderColor": C["border"], "margin": "0"}),

        html.Label("Origin Airport", style={"color": C["muted"], "fontSize": "0.72rem", "letterSpacing": "1px", "textTransform": "uppercase"}),
        dcc.Dropdown(id="origin",
            options=[{"label": f"{k} — {v['name']}", "value": k} for k, v in AIRPORTS.items()],
            value="ORD",
            style={"backgroundColor": C["card"], "color": "#000", "border": f"1px solid {C['border']}"}
        ),

        html.Label("Destination Airport", style={"color": C["muted"], "fontSize": "0.72rem", "letterSpacing": "1px", "textTransform": "uppercase"}),
        dcc.Dropdown(id="destination",
            options=[{"label": f"{k} — {v['name']}", "value": k} for k, v in AIRPORTS.items()],
            value="LHR",
            style={"backgroundColor": C["card"], "color": "#000", "border": f"1px solid {C['border']}"}
        ),

        html.Label("Aircraft", style={"color": C["muted"], "fontSize": "0.72rem", "letterSpacing": "1px", "textTransform": "uppercase"}),
        dcc.Dropdown(id="aircraft",
            options=[{"label": k, "value": k} for k in AIRCRAFT.keys()],
            value="Boeing 787-9",
            style={"backgroundColor": C["card"], "color": "#000", "border": f"1px solid {C['border']}"}
        ),

        html.Label("Compare Aircraft", style={"color": C["muted"], "fontSize": "0.72rem", "letterSpacing": "1px", "textTransform": "uppercase"}),
        dcc.Dropdown(id="aircraft2",
            options=[{"label": "None", "value": "none"}] + [{"label": k, "value": k} for k in AIRCRAFT.keys()],
            value="none",
            style={"backgroundColor": C["card"], "color": "#000", "border": f"1px solid {C['border']}"}
        ),

        html.Hr(style={"borderColor": C["border"], "margin": "0"}),

        html.Label("Payload (kg)", style={"color": C["muted"], "fontSize": "0.72rem", "letterSpacing": "1px", "textTransform": "uppercase"}),
        dcc.Slider(id="payload", min=5000, max=50000, step=1000, value=15000,
            marks={5000: "5k", 25000: "25k", 50000: "50k"},
            tooltip={"placement": "bottom", "always_visible": True}
        ),

        html.Label("Fuel Price ($/kg)", style={"color": C["muted"], "fontSize": "0.72rem", "letterSpacing": "1px", "textTransform": "uppercase"}),
        dcc.Slider(id="fuel-price", min=0.3, max=1.5, step=0.05, value=0.75,
            marks={0.3: "$0.30", 0.75: "$0.75", 1.5: "$1.50"},
            tooltip={"placement": "bottom", "always_visible": True}
        ),

        html.Label("Load Factor (%)", style={"color": C["muted"], "fontSize": "0.72rem", "letterSpacing": "1px", "textTransform": "uppercase"}),
        dcc.Slider(id="load-factor", min=50, max=100, step=5, value=85,
            marks={50: "50%", 75: "75%", 100: "100%"},
            tooltip={"placement": "bottom", "always_visible": True}
        ),

        html.Label("Ticket Price Adjustment", style={"color": C["muted"], "fontSize": "0.72rem", "letterSpacing": "1px", "textTransform": "uppercase"}),
        dcc.Slider(id="ticket-multiplier", min=0.5, max=2.0, step=0.1, value=1.0,
            marks={0.5: "Budget", 1.0: "Base", 2.0: "Premium"},
            tooltip={"placement": "bottom", "always_visible": True}
        ),

        html.Hr(style={"borderColor": C["border"], "margin": "0"}),

        html.Button("ANALYZE ROUTE", id="analyze-btn", n_clicks=0, style={
            "backgroundColor": C["blue"],
            "color": "#0a0e1a",
            "border": "none",
            "borderRadius": "6px",
            "padding": "14px",
            "fontWeight": "bold",
            "fontSize": "0.95rem",
            "letterSpacing": "2px",
            "cursor": "pointer",
            "width": "100%",
            "marginTop": "6px"
        }),

        html.P("Built by Giorgio Turchetti | Illinois Tech", style={
            "color": C["muted"], "fontSize": "0.65rem",
            "textAlign": "center", "marginTop": "auto", "paddingTop": "20px"
        }),
    ]),

    # MAIN CONTENT
    html.Div(id="main-content", style={
        "flex": "1", "padding": "40px", "overflowY": "auto"
    }, children=[
        html.Div(style={
            "backgroundColor": C["card"],
            "border": f"1px solid {C['border']}",
            "borderRadius": "8px",
            "padding": "60px",
            "textAlign": "center",
            "marginTop": "80px"
        }, children=[
            html.H1("FlightOps Suite", style={
                "color": C["blue"], "fontSize": "2.5rem",
                "letterSpacing": "4px", "textTransform": "uppercase"
            }),
            html.P("Select your route and aircraft, then click Analyze Route", style={
                "color": C["muted"], "fontSize": "0.9rem",
                "letterSpacing": "2px", "textTransform": "uppercase"
            })
        ])
    ])
])


@app.callback(
    Output("main-content", "children"),
    Input("analyze-btn", "n_clicks"),
    State("origin", "value"),
    State("destination", "value"),
    State("aircraft", "value"),
    State("aircraft2", "value"),
    State("payload", "value"),
    State("fuel-price", "value"),
    State("load-factor", "value"),
    State("ticket-multiplier", "value"),
    prevent_initial_call=True
)
def update(n_clicks, origin, destination, aircraft, aircraft2,
           payload, fuel_price, load_factor, ticket_multiplier):

    if not origin or not destination or origin == destination:
        return html.P("Please select different origin and destination.",
                     style={"color": C["red"]})

    result = analyze_route(origin, destination, aircraft, payload,
                          fuel_price, load_factor, ticket_multiplier)

    # PERFORMANCE CHARTS
    altitudes = np.arange(5000, 14000, 500)
    ld_values, fuel_values, co2_values = [], [], []
    ac = AIRCRAFT[aircraft]
    W_N = (ac["OEW"] + payload + ac["max_fuel"] * 0.85) * 9.80665

    for alt in altitudes:
        T, P, rho = isa(alt)
        V = ac["cruise_mach"] * np.sqrt(1.4 * 287.05 * T)
        CL = (2 * W_N) / (rho * V**2 * ac["S"])
        CD = ac["CD0"] + ac["k"] * CL**2
        ld = CL / CD
        ld_values.append(ld)
        fuel, _ = breguet_fuel(W_N, result["distance_km"] * 1000, ac["TSFC"], ld, V)
        fuel_kg = fuel / 9.80665
        fuel_values.append(fuel_kg)
        co2_values.append(fuel_kg * 3.16 / 1000)

    chart_style = dict(
        paper_bgcolor=C["card"], plot_bgcolor=C["card"],
        font=dict(color=C["muted"], size=11),
        xaxis=dict(gridcolor=C["border"], color=C["muted"]),
        yaxis=dict(gridcolor=C["border"], color=C["muted"]),
        margin=dict(l=50, r=20, t=40, b=40),
        height=280
    )

    fig1 = go.Figure(go.Scatter(x=altitudes/1000, y=ld_values, mode="lines",
        line=dict(color=C["blue"], width=2.5)))
    fig1.update_layout(title=dict(text="L/D Ratio vs Altitude",
        font=dict(color=C["blue"])), **chart_style)

    fig2 = go.Figure(go.Scatter(x=altitudes/1000, y=fuel_values, mode="lines",
        line=dict(color=C["red"], width=2.5)))
    fig2.update_layout(title=dict(text="Fuel Burn vs Altitude",
        font=dict(color=C["blue"])), **chart_style)

    fig3 = go.Figure(go.Scatter(x=altitudes/1000, y=co2_values, mode="lines",
        line=dict(color=C["green"], width=2.5)))
    fig3.update_layout(title=dict(text="CO2 vs Altitude",
        font=dict(color=C["blue"])), **chart_style)

    # MAP
    mid_lat = (AIRPORTS[origin]["lat"] + AIRPORTS[destination]["lat"]) / 2
    mid_lon = (AIRPORTS[origin]["lon"] + AIRPORTS[destination]["lon"]) / 2
    m = folium.Map(location=[mid_lat, mid_lon], zoom_start=3,
                  tiles="CartoDB dark_matter")
    folium.PolyLine(result["waypoints"], color="#00bfff",
                   weight=2.5, opacity=0.9).add_to(m)
    for code in [origin, destination]:
        ap = AIRPORTS[code]
        folium.CircleMarker([ap["lat"], ap["lon"]], radius=6,
            color="#00bfff", fill=True, fill_color="#00bfff",
            fill_opacity=1.0, popup=ap["name"]).add_to(m)
    map_html = m._repr_html_()

    # PROFITABILITY COLOR
    profit_color = C["green"] if result["profit"] > 0 else C["red"]

    # COMPARISON
    comparison = html.Div()
    if aircraft2 and aircraft2 != "none" and aircraft2 != aircraft:
        result2 = analyze_route(origin, destination, aircraft2, payload,
                               fuel_price, load_factor, ticket_multiplier)
        profit_color2 = C["green"] if result2["profit"] > 0 else C["red"]

        comparison = html.Div([
            html.H3("Aircraft Comparison", style={
                "color": C["blue"], "letterSpacing": "1px", "margin": "0 0 16px 0"
            }),
            html.Div(style={"display": "flex", "gap": "20px"}, children=[

                # Aircraft 1
                html.Div(style={"flex": "1", "display": "flex",
                    "flexDirection": "column", "gap": "10px"}, children=[
                    html.P(aircraft, style={"color": C["text"],
                        "fontWeight": "bold", "fontSize": "1rem", "margin": "0"}),
                    metric_card("Fuel Burned", f"{result['fuel_burned_kg']:,} kg"),
                    metric_card("Fuel Cost", f"${result['fuel_cost']:,}"),
                    metric_card("Passengers", str(result['passengers'])),
                    metric_card("Revenue", f"${result['revenue']:,}"),
                    metric_card("Profit", f"${result['profit']:,}", profit_color),
                    metric_card("Profit/Pax", f"${result['profit_per_pax']}"),
                    metric_card("CO2", f"{result['co2_tonnes']} t"),
                    metric_card("L/D Ratio", str(result['LD_ratio'])),
                ]),

                # Aircraft 2
                html.Div(style={"flex": "1", "display": "flex",
                    "flexDirection": "column", "gap": "10px"}, children=[
                    html.P(aircraft2, style={"color": C["text"],
                        "fontWeight": "bold", "fontSize": "1rem", "margin": "0"}),
                    metric_card("Fuel Burned", f"{result2['fuel_burned_kg']:,} kg"),
                    metric_card("Fuel Cost", f"${result2['fuel_cost']:,}"),
                    metric_card("Passengers", str(result2['passengers'])),
                    metric_card("Revenue", f"${result2['revenue']:,}"),
                    metric_card("Profit", f"${result2['profit']:,}", profit_color2),
                    metric_card("Profit/Pax", f"${result2['profit_per_pax']}"),
                    metric_card("CO2", f"{result2['co2_tonnes']} t"),
                    metric_card("L/D Ratio", str(result2['LD_ratio'])),
                ]),
            ])
        ], style={"marginTop": "10px"})

    return html.Div(style={"display": "flex", "flexDirection": "column", "gap": "24px"}, children=[

        # Route title
        html.H2(f"{result['origin']} → {result['destination']}",
            style={"color": C["text"], "margin": "0", "fontSize": "1.5rem"}),

        # PERFORMANCE METRICS
        html.Div([
            html.P("FLIGHT PERFORMANCE", style={"color": C["muted"],
                "fontSize": "0.7rem", "letterSpacing": "2px", "margin": "0 0 10px 0"}),
            html.Div(style={"display": "flex", "gap": "12px", "flexWrap": "wrap"}, children=[
                metric_card("Distance", f"{result['distance_km']:,} km"),
                metric_card("Cruise Altitude", f"{result['cruise_altitude_ft']:,} ft"),
                metric_card("Cruise Speed", f"{result['cruise_speed_kts']} kts"),
                metric_card("Flight Time", f"{result['flight_time_hr']} hrs"),
                metric_card("L/D Ratio", str(result['LD_ratio'])),
                metric_card("Wind", f"{result['wind_ms']} m/s"),
            ]),
        ]),

        # FUEL & EMISSIONS
        html.Div([
            html.P("FUEL & EMISSIONS", style={"color": C["muted"],
                "fontSize": "0.7rem", "letterSpacing": "2px", "margin": "0 0 10px 0"}),
            html.Div(style={"display": "flex", "gap": "12px", "flexWrap": "wrap"}, children=[
                metric_card("Fuel Burned", f"{result['fuel_burned_kg']:,} kg"),
                metric_card("Fuel Cost", f"${result['fuel_cost']:,}"),
                metric_card("CO2 Emissions", f"{result['co2_tonnes']} t"),
            ]),
        ]),

        # PROFITABILITY
        html.Div([
            html.P("ROUTE PROFITABILITY", style={"color": C["muted"],
                "fontSize": "0.7rem", "letterSpacing": "2px", "margin": "0 0 10px 0"}),
            html.Div(style={"display": "flex", "gap": "12px", "flexWrap": "wrap"}, children=[
                metric_card("Ticket Price", f"${result['ticket_price']}"),
                metric_card("Passengers", str(result['passengers'])),
                metric_card("Revenue", f"${result['revenue']:,}"),
                metric_card("Profit", f"${result['profit']:,}", profit_color),
                metric_card("Profit / Pax", f"${result['profit_per_pax']}"),
            ]),
        ]) if not result.get("is_freighter") else html.Div([
            html.P("CARGO / FREIGHTER AIRCRAFT — No passenger profitability data",
                style={"color": C["muted"], "fontSize": "0.85rem"})
        ]),

        # MAP
        html.Div([
            html.P("ROUTE MAP", style={"color": C["muted"],
                "fontSize": "0.7rem", "letterSpacing": "2px", "margin": "0 0 10px 0"}),
            html.Iframe(srcDoc=map_html, style={
                "width": "100%", "height": "440px",
                "border": f"1px solid {C['border']}",
                "borderRadius": "8px"
            })
        ]),

        # CHARTS
        html.Div([
            html.P("PERFORMANCE VS ALTITUDE", style={"color": C["muted"],
                "fontSize": "0.7rem", "letterSpacing": "2px", "margin": "0 0 10px 0"}),
            html.Div(style={"display": "flex", "gap": "12px"}, children=[
                html.Div(dcc.Graph(figure=fig1, config={"displayModeBar": False}),
                    style={"flex": "1", "backgroundColor": C["card"],
                        "borderRadius": "8px", "border": f"1px solid {C['border']}"}),
                html.Div(dcc.Graph(figure=fig2, config={"displayModeBar": False}),
                    style={"flex": "1", "backgroundColor": C["card"],
                        "borderRadius": "8px", "border": f"1px solid {C['border']}"}),
                html.Div(dcc.Graph(figure=fig3, config={"displayModeBar": False}),
                    style={"flex": "1", "backgroundColor": C["card"],
                        "borderRadius": "8px", "border": f"1px solid {C['border']}"}),
            ])
        ]),

        comparison,
    ])


if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8050)), debug=False)