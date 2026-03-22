import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import numpy as np
from route import analyze_route, AIRPORTS
from physics import AIRCRAFT, isa, breguet_fuel

st.set_page_config(
    page_title="FlightOps Suite",
    page_icon="",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background-color: #0a0e1a;
        color: #e0e6f0;
    }
    [data-testid="stSidebar"] {
        background-color: #0d1220;
        border-right: 1px solid #1e3a5f;
    }
    [data-testid="stSidebar"] * {
        color: #a0b4cc !important;
    }
    [data-testid="stSidebar"] h2 {
        color: #00bfff !important;
        font-size: 1.3rem !important;
        font-weight: bold !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
    }
    .stSelectbox label, .stSlider label, .stCheckbox label {
        color: #6a8faf !important;
        font-size: 0.8rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    h1 {
        color: #00bfff !important;
        font-size: 2.6rem !important;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    h2, h3 {
        color: #00bfff !important;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetric"] {
        background-color: #0d1a2e;
        border: 1px solid #1e3a5f;
        border-radius: 8px;
        padding: 20px;
    }
    [data-testid="stMetricLabel"] {
        color: #6a8faf !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
    }
    [data-testid="stMetricValue"] {
        color: #00bfff !important;
        font-size: 1.8rem !important;
        font-weight: bold !important;
    }
    .stButton > button {
        background-color: #00bfff !important;
        color: #0a0e1a !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: bold !important;
        font-size: 1rem !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        width: 100% !important;
        padding: 14px !important;
    }
    .stButton > button:hover {
        background-color: #0090cc !important;
    }
    hr {
        border-color: #1e3a5f !important;
    }
    .stAlert {
        background-color: #0d1a2e !important;
        border: 1px solid #1e3a5f !important;
        border-radius: 8px !important;
    }
    .subtitle {
        color: #6a8faf;
        font-size: 0.85rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-top: -10px;
        margin-bottom: 20px;
    }
    .route-header {
        font-size: 1.6rem;
        color: #e0e6f0;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .welcome-box {
        background-color: #0d1a2e;
        border: 1px solid #1e3a5f;
        border-radius: 8px;
        padding: 40px;
        text-align: center;
        margin-top: 60px;
    }
    .welcome-box p {
        color: #6a8faf;
        font-size: 1rem;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================

st.title("FlightOps Suite")
st.markdown('<p class="subtitle">Aircraft Route & Performance Analyzer — Giorgio Turchetti | Illinois Institute of Technology</p>', unsafe_allow_html=True)
st.divider()

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown("## Flight Parameters")

origin_code = st.sidebar.selectbox(
    "Origin Airport",
    list(AIRPORTS.keys()),
    format_func=lambda x: f"{x} — {AIRPORTS[x]['name']}"
)

destination_code = st.sidebar.selectbox(
    "Destination Airport",
    list(AIRPORTS.keys()),
    index=3,
    format_func=lambda x: f"{x} — {AIRPORTS[x]['name']}"
)

aircraft_name = st.sidebar.selectbox(
    "Aircraft",
    list(AIRCRAFT.keys())
)

compare = st.sidebar.checkbox("Compare with a second aircraft")
aircraft_name_2 = None
if compare:
    aircraft_name_2 = st.sidebar.selectbox(
        "Second Aircraft",
        [a for a in AIRCRAFT.keys() if a != aircraft_name]
    )

payload_kg = st.sidebar.slider(
    "Payload (kg)", 5000, 50000, 15000, step=1000
)

st.sidebar.divider()

if "run" not in st.session_state:
    st.session_state.run = False

if st.sidebar.button("Analyze Route", type="primary"):
    st.session_state.run = True

run = st.session_state.run

# ============================================================
# MAIN PANEL
# ============================================================

if run:
    if origin_code == destination_code:
        st.error("Origin and destination must be different.")
    else:
        with st.spinner("Computing route and performance..."):
            result = analyze_route(origin_code, destination_code, aircraft_name, payload_kg)

        st.markdown(f'<p class="route-header">{result["origin"]} → {result["destination"]}</p>', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Distance", f"{result['distance_km']:,} km")
        col2.metric("Cruise Altitude", f"{result['cruise_altitude_ft']:,} ft")
        col3.metric("Fuel Burned", f"{result['fuel_burned_kg']:,} kg")
        col4.metric("Flight Time", f"{result['flight_time_hr']} hrs")

        st.markdown("<br>", unsafe_allow_html=True)

        col5, col6, col7, col8 = st.columns(4)
        col5.metric("Cruise Speed", f"{result['cruise_speed_kts']} kts")
        col6.metric("L/D Ratio", result['LD_ratio'])
        col7.metric("CO2 Emissions", f"{result['co2_tonnes']} tonnes")
        col8.metric("Wind", f"{result['wind_ms']} m/s")

        st.divider()

        # MAP
        st.subheader("Route Map")
        mid_lat = (AIRPORTS[origin_code]["lat"] + AIRPORTS[destination_code]["lat"]) / 2
        mid_lon = (AIRPORTS[origin_code]["lon"] + AIRPORTS[destination_code]["lon"]) / 2
        m = folium.Map(location=[mid_lat, mid_lon], zoom_start=3, tiles="CartoDB dark_matter")

        folium.PolyLine(
            result["waypoints"],
            color="#00bfff",
            weight=2.5,
            opacity=0.9
        ).add_to(m)

        for code in [origin_code, destination_code]:
            ap = AIRPORTS[code]
            folium.CircleMarker(
                [ap["lat"], ap["lon"]],
                radius=6,
                color="#00bfff",
                fill=True,
                fill_color="#00bfff",
                fill_opacity=1.0,
                popup=ap["name"]
            ).add_to(m)

        st_folium(m, width=1100, height=480)

        st.divider()

        # CHARTS
        st.subheader("Performance vs Altitude")

        altitudes = np.arange(5000, 14000, 500)
        ld_values, fuel_values, co2_values = [], [], []

        ac = AIRCRAFT[aircraft_name]
        W_kg = ac["OEW"] + payload_kg + ac["max_fuel"] * 0.85
        W_N = W_kg * 9.80665

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

        chart_config = dict(
            template="plotly_dark", height=350,
            paper_bgcolor="#0d1a2e", plot_bgcolor="#0d1a2e",
            font=dict(color="#a0b4cc"),
            xaxis=dict(gridcolor="#1e3a5f"),
            yaxis=dict(gridcolor="#1e3a5f")
        )

        col_c1, col_c2, col_c3 = st.columns(3)

        with col_c1:
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=altitudes/1000, y=ld_values,
                mode="lines", line=dict(color="#00bfff", width=2.5)))
            fig1.update_layout(title="L/D Ratio vs Altitude",
                xaxis_title="Altitude (km)", yaxis_title="L/D Ratio", **chart_config)
            st.plotly_chart(fig1, width='stretch')

        with col_c2:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=altitudes/1000, y=fuel_values,
                mode="lines", line=dict(color="#ff6b6b", width=2.5)))
            fig2.update_layout(title="Fuel Burn vs Altitude",
                xaxis_title="Altitude (km)", yaxis_title="Fuel Burned (kg)", **chart_config)
            st.plotly_chart(fig2, width='stretch')

        with col_c3:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=altitudes/1000, y=co2_values,
                mode="lines", line=dict(color="#90ee90", width=2.5)))
            fig3.update_layout(title="CO2 Emissions vs Altitude",
                xaxis_title="Altitude (km)", yaxis_title="CO2 (tonnes)", **chart_config)
            st.plotly_chart(fig3, width='stretch')

        # COMPARISON
        if compare and aircraft_name_2:
            st.divider()
            st.subheader("Aircraft Comparison")
            result2 = analyze_route(origin_code, destination_code, aircraft_name_2, payload_kg)

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**{aircraft_name}**")
                st.metric("Fuel Burned", f"{result['fuel_burned_kg']:,} kg")
                st.metric("Flight Time", f"{result['flight_time_hr']} hrs")
                st.metric("Cruise Altitude", f"{result['cruise_altitude_ft']:,} ft")
                st.metric("L/D Ratio", result['LD_ratio'])
                st.metric("CO2 Emissions", f"{result['co2_tonnes']} tonnes")

            with col_b:
                st.markdown(f"**{aircraft_name_2}**")
                st.metric("Fuel Burned", f"{result2['fuel_burned_kg']:,} kg")
                st.metric("Flight Time", f"{result2['flight_time_hr']} hrs")
                st.metric("Cruise Altitude", f"{result2['cruise_altitude_ft']:,} ft")
                st.metric("L/D Ratio", result2['LD_ratio'])
                st.metric("CO2 Emissions", f"{result2['co2_tonnes']} tonnes")

else:
    st.markdown("""
    <div class="welcome-box">
        <p>Select your route and aircraft in the sidebar, then click Analyze Route</p>
    </div>
    """, unsafe_allow_html=True)
    