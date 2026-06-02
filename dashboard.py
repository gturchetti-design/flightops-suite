"""
FlightOps Suite — single-entry app
Run:  python dashboard.py  →  localhost:8050
"""
import json, random, os
import numpy as np
import dash
from dash import dcc, html, Input, Output, State, dash_table, ctx, ALL
import plotly.graph_objects as go
import folium

from route import analyze_route, AIRPORTS, great_circle_distance

# ── Extend airport database to ~100 airports ──────────────────────────────────
AIRPORTS.update({
    # North America (extra)
    "IAH": {"name": "Houston Intercontinental", "lat": 29.9902,  "lon": -95.3368},
    "DFW": {"name": "Dallas Fort Worth",        "lat": 32.8998,  "lon": -97.0403},
    "PHX": {"name": "Phoenix Sky Harbor",       "lat": 33.4373,  "lon": -112.0078},
    "LAS": {"name": "Las Vegas McCarran",       "lat": 36.0840,  "lon": -115.1537},
    "MSP": {"name": "Minneapolis St. Paul",     "lat": 44.8848,  "lon": -93.2223},
    "DTW": {"name": "Detroit Metropolitan",     "lat": 42.2124,  "lon": -83.3534},
    "PHL": {"name": "Philadelphia Intl.",       "lat": 39.8719,  "lon": -75.2411},
    "YUL": {"name": "Montreal Trudeau",         "lat": 45.4706,  "lon": -73.7408},
    "YYC": {"name": "Calgary Intl.",            "lat": 51.1315,  "lon": -114.0106},
    "PTY": {"name": "Panama City Tocumen",      "lat":  9.0714,  "lon": -79.3836},
    "HAV": {"name": "Havana Jose Marti",        "lat": 22.9892,  "lon": -82.4091},
    "UIO": {"name": "Quito Mariscal Sucre",     "lat": -0.1292,  "lon": -78.3575},
    "GYE": {"name": "Guayaquil Simon Bolivar",  "lat": -2.1574,  "lon": -79.8836},
    "MVD": {"name": "Montevideo Carrasco",      "lat": -34.8383, "lon": -56.0308},
    "CCS": {"name": "Caracas Simon Bolivar",    "lat": 10.6031,  "lon": -66.9910},
    # Europe (extra)
    "HEL": {"name": "Helsinki Vantaa",          "lat": 60.3183,  "lon": 24.9630},
    "OSL": {"name": "Oslo Gardermoen",          "lat": 60.1939,  "lon": 11.1004},
    "ARN": {"name": "Stockholm Arlanda",        "lat": 59.6519,  "lon": 17.9186},
    "WAW": {"name": "Warsaw Chopin",            "lat": 52.1657,  "lon": 20.9671},
    "BUD": {"name": "Budapest Ferenc Liszt",    "lat": 47.4362,  "lon": 19.2556},
    "PRG": {"name": "Prague Vaclav Havel",      "lat": 50.1008,  "lon": 14.2600},
    "BER": {"name": "Berlin Brandenburg",       "lat": 52.3667,  "lon": 13.5033},
    "DUS": {"name": "Dusseldorf Intl.",         "lat": 51.2895,  "lon":  6.7668},
    "GVA": {"name": "Geneva Intl.",             "lat": 46.2381,  "lon":  6.1089},
    "OTP": {"name": "Bucharest Otopeni",        "lat": 44.5711,  "lon": 26.0850},
    "SVO": {"name": "Moscow Sheremetyevo",      "lat": 55.9726,  "lon": 37.4146},
    # Asia (extra)
    "KIX": {"name": "Osaka Kansai",            "lat": 34.4269,  "lon": 135.2441},
    "CAN": {"name": "Guangzhou Baiyun",         "lat": 23.3924,  "lon": 113.2988},
    "CTU": {"name": "Chengdu Shuangliu",        "lat": 30.5785,  "lon": 103.9479},
    "MNL": {"name": "Manila Ninoy Aquino",      "lat": 14.5086,  "lon": 121.0197},
    "CGK": {"name": "Jakarta Soekarno-Hatta",  "lat": -6.1275,  "lon": 106.6537},
    "TPE": {"name": "Taipei Taoyuan",           "lat": 25.0777,  "lon": 121.2328},
    "DAC": {"name": "Dhaka Hazrat Shahjalal",   "lat": 23.8433,  "lon": 90.3978},
    "CMB": {"name": "Colombo Bandaranaike",     "lat":  7.1806,  "lon": 79.8842},
    "KHI": {"name": "Karachi Jinnah Intl.",    "lat": 24.9065,  "lon": 67.1608},
    "RUH": {"name": "Riyadh King Khalid",       "lat": 24.9578,  "lon": 46.6988},
    # Middle East & Africa (extra)
    "TLV": {"name": "Tel Aviv Ben Gurion",      "lat": 32.0114,  "lon": 34.8867},
    "JED": {"name": "Jeddah King Abdulaziz",    "lat": 21.6796,  "lon": 39.1565},
    "MCT": {"name": "Muscat Seeb Intl.",        "lat": 23.5933,  "lon": 58.2844},
    "LOS": {"name": "Lagos Murtala Muhammed",   "lat":  6.5774,  "lon":  3.3212},
    "ADD": {"name": "Addis Ababa Bole",         "lat":  8.9779,  "lon": 38.7993},
    "ACC": {"name": "Accra Kotoka",             "lat":  5.6052,  "lon": -0.1668},
    # Oceania (extra)
    "PER": {"name": "Perth Intl.",              "lat": -31.9403, "lon": 115.9670},
    "BNE": {"name": "Brisbane Intl.",           "lat": -27.3842, "lon": 153.1175},
    "NAN": {"name": "Nadi Fiji",               "lat": -17.7553, "lon": 177.4430},
})
from physics import (AIRCRAFT, isa, best_LD, breguet_fuel,
                     base_ticket_price, nonfuel_cost_per_asm)
from components.viability import compute_viability_score

# ══════════════════════════════════════════════════════════════════════════════
# PALETTE  (spec-exact)
# ══════════════════════════════════════════════════════════════════════════════
BG      = "#080a0f"
SIDEBAR = "#04060a"
CARD    = "#08090e"
BDR     = "#111820"
BDR2    = "#182030"
TEAL    = "#00d4aa"
PURPLE  = "#a064f0"
AMBER   = "#f0b830"
RED     = "#f04040"
MUTED   = "#607898"
DIM     = "#2d4060"
BODY    = "#8899aa"
LIGHT   = "#c8d8e8"
WHITE   = "#e2e8f0"

FONT       = "'Space Grotesk', sans-serif"
FONTS_URL  = ("https://fonts.googleapis.com/css2?"
              "family=Space+Grotesk:wght@300;400;500;700"
              "&family=Rajdhani:wght@700&display=swap")

RANK_C = [TEAL, PURPLE, AMBER, MUTED]
RANK_B = ["★ 1st", "2nd", "3rd", "4th"]

# ── Per-flight additional cost estimates (USD) ────────────────────────────────
# Sources: IATA Cost Management Report, airline 10-K disclosures, Boeing/Airbus
# cost analysis. Values represent averages; private jets excluded (cost/hr model).
_LEASING = {
    "Boeing 747-8F":         22000, "Airbus A380-800":      28000,
    "Boeing 777-300ER":      22000, "Boeing 777X (777-9)":  26000,
    "Boeing 787-9":          18000, "Airbus A350-900":      20000,
    "Airbus A330-900neo":    17000, "Airbus A330-200F":     16000,
    "Boeing 767-300ER":      13000, "Boeing 757-200":        9500,
    "Airbus A321neo":         9000, "Boeing 737 MAX 9":      7500,
    "Boeing 737-800":         7000, "Airbus A320neo":        7000,
    "Airbus A220-300":        5000, "Embraer E195-E2":       4800,
    "Bombardier CRJ-900":     4200, "ATR 72-600":            2000,
    "Concorde":              35000, "Boom Overture":         30000,
}
_OVERHEAD = {  # corporate overhead allocated per flight
    "Boeing 747-8F":14000,"Airbus A380-800":14000,"Boeing 777-300ER":13000,
    "Boeing 777X (777-9)":13000,"Boeing 787-9":12000,"Airbus A350-900":13000,
    "Airbus A330-900neo":12000,"Airbus A330-200F":11000,"Boeing 767-300ER":10000,
    "Boeing 757-200":8000,"Airbus A321neo":7500,"Boeing 737 MAX 9":7000,
    "Boeing 737-800":6500,"Airbus A320neo":7000,"Airbus A220-300":5500,
    "Embraer E195-E2":5000,"Bombardier CRJ-900":4000,"ATR 72-600":3000,
    "Concorde":20000,"Boom Overture":18000,
}
_INSURANCE = {  # hull + liability per flight
    "Boeing 747-8F":6000,"Airbus A380-800":6500,"Boeing 777-300ER":5500,
    "Boeing 777X (777-9)":5800,"Boeing 787-9":4800,"Airbus A350-900":5200,
    "Airbus A330-900neo":4500,"Airbus A330-200F":4200,"Boeing 767-300ER":3800,
    "Boeing 757-200":3200,"Airbus A321neo":2800,"Boeing 737 MAX 9":2600,
    "Boeing 737-800":2400,"Airbus A320neo":2600,"Airbus A220-300":2200,
    "Embraer E195-E2":2000,"Bombardier CRJ-900":1600,"ATR 72-600":1200,
    "Concorde":8000,"Boom Overture":7000,
}
_EU_ETS_CODES = {
    "MAD","BCN","CDG","FRA","AMS","MXP","FCO","MUC","ZRH","VIE",
    "LIS","ATH","CPH","HEL","ARN","WAW","BUD","PRG","OTP","BER",
    "DUS","OSL",  # Norway in ETS; Switzerland linked ETS
}
_EUR_USD = 1.08
_ETS_EUR_PER_TONNE = 65.0

# ── Aircraft split ────────────────────────────────────────────────────────────
def _mfr_key(name: str) -> str:
    return {"Boeing":"1","Airbus":"2","Embraer":"3","Bombardier":"4","ATR":"5",
            "Gulfstream":"6","Dassault":"7","Cessna":"8","Comac":"9"}.get(name.split()[0], "Z")

COMMERCIAL = dict(sorted(
    {n: ac for n, ac in AIRCRAFT.items() if ac.get("category") != "private"}.items(),
    key=lambda kv: (_mfr_key(kv[0]), kv[1]["seats"]),
))
PRIVATE = dict(sorted(
    {n: ac for n, ac in AIRCRAFT.items() if ac.get("category") == "private"}.items(),
    key=lambda kv: (_mfr_key(kv[0]), kv[1]["seats"]),
))


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def can_complete_route(ac_name: str, distance_km: float) -> bool:
    ac   = AIRCRAFT[ac_name]
    W_kg = ac["OEW"] + ac["max_fuel"]
    W_N  = W_kg * 9.80665
    T, _, _ = isa(ac["cruise_alt"])
    V    = ac["cruise_mach"] * np.sqrt(1.4 * 287.05 * T)
    _, LD = best_LD(ac["CD0"], ac["k"])
    rng_m = (V / (ac["TSFC"] * 9.80665)) * LD * np.log(
        W_N / (W_N - ac["max_fuel"] * 9.80665 * 0.95))
    return (rng_m / 1000) > distance_km * 1.1


def get_dist(origin: str, dest: str):
    if not origin or not dest or origin == dest:
        return None
    o, d = AIRPORTS[origin], AIRPORTS[dest]
    return great_circle_distance(o["lat"], o["lon"], d["lat"], d["lon"]) / 1000


def _lbl(text: str) -> html.P:
    return html.P(text, style={"color": BODY, "fontSize": "7px", "fontWeight": "500",
                               "letterSpacing": "2px", "textTransform": "uppercase",
                               "fontFamily": FONT, "margin": "0 0 3px 0"})


def _sec(text: str) -> html.P:
    return html.P(text, style={"color": BODY, "fontSize": "7px", "letterSpacing": "2.5px",
                               "textTransform": "uppercase", "fontFamily": FONT,
                               "borderBottom": f"1px solid {BDR}",
                               "paddingBottom": "4px", "margin": "0 0 8px 0"})


def _mini(label: str, value: str, color=WHITE) -> html.Div:
    return html.Div([
        html.P(label, style={"color": MUTED, "fontSize": "6px", "letterSpacing": "1px",
                             "textTransform": "uppercase", "fontFamily": FONT,
                             "margin": "0 0 3px 0"}),
        html.P(value, style={"color": color, "fontSize": "11px", "fontWeight": "700",
                             "fontFamily": FONT, "margin": "0", "lineHeight": "1"}),
    ], style={"backgroundColor": BG, "border": f"1px solid {BDR}",
              "borderRadius": "3px", "padding": "6px 8px"})


def score_circle(score, color: str, size: int = 76) -> dcc.Graph:
    raw = score or 0
    s   = int(raw)
    # show one decimal only when the score has a meaningful fractional part
    label = f"{raw:.1f}" if (raw % 1) >= 0.05 else str(s)
    fig = go.Figure(go.Pie(
        values=[s, max(100 - s, 0)], hole=0.72, sort=False,
        marker=dict(colors=[color, BDR2]),
        textinfo="none", hoverinfo="skip",
    ))
    fig.add_annotation(text=label,
                       font=dict(size=15, color=color, family="Rajdhani,sans-serif"),
                       showarrow=False, x=0.5, y=0.5)
    fig.update_layout(showlegend=False,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=0, r=0, t=0, b=0))
    return dcc.Graph(figure=fig, config={"displayModeBar": False},
                     style={"width": f"{size}px", "height": f"{size}px", "flexShrink": "0"})


# ── Globe canvas ──────────────────────────────────────────────────────────────
def build_airport_map() -> str:
    """Interactive Folium map with all airports — clicking posts airport code to parent."""
    m = folium.Map(
        location=[20, 10], zoom_start=2, min_zoom=2,
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB", prefer_canvas=True,
    )
    for code, ap in AIRPORTS.items():
        safe_name = ap["name"].replace("'", " ")
        safe_code = code
        popup_js  = (
            "window.parent.postMessage({type:'setAirport',"
            "code:'" + safe_code + "',name:'" + safe_name + "'}, '*');"
        )
        title_txt = safe_code + " — " + safe_name
        div_html  = (
            '<div onclick="' + popup_js + '" style="'
            'width:10px;height:10px;border-radius:50%;'
            'background:#00d4aa;border:2px solid #00d4aa80;'
            'cursor:pointer;box-shadow:0 0 6px #00d4aa60;" '
            'title="' + title_txt + '"></div>'
        )
        icon = folium.DivIcon(html=div_html, icon_size=(10, 10), icon_anchor=(5, 5))
        folium.Marker(location=[ap["lat"], ap["lon"]], icon=icon).add_to(m)
    m.get_root().html.add_child(folium.Element(
        "<style>body{background:#080a0f;margin:0}"
        ".leaflet-container{background:#080a0f}</style>"
    ))
    return m._repr_html_()


def build_globe_html(waypoints, origin_code: str, dest_code: str) -> str:
    lats = [w[0] for w in waypoints]
    lons = [w[1] for w in waypoints]
    clat = sum(lats) / len(lats)
    clon = sum(lons) / len(lons)
    oa   = AIRPORTS[origin_code]
    da   = AIRPORTS[dest_code]
    wj   = json.dumps([[la, lo] for la, lo in waypoints])
    oj   = json.dumps([oa["lat"], oa["lon"]])
    dj   = json.dumps([da["lat"], da["lon"]])
    return f"""<!DOCTYPE html><html><head>
<style>body{{margin:0;background:#02040a;overflow:hidden;}}canvas{{display:block;}}</style>
</head><body><canvas id="g"></canvas><script>
const W=window.innerWidth,H=window.innerHeight,c=document.getElementById('g');
c.width=W;c.height=H;const ctx=c.getContext('2d');
const CLA={clat},CLO={clon},WP={wj},OP={oj},DP={dj};
const R=Math.min(W,H)*0.42,CX=W/2,CY=H/2;
const rad=d=>d*Math.PI/180;
function proj(lat,lon){{
  const l0=rad(CLO),p0=rad(CLA),l=rad(lon),p=rad(lat);
  const cc=Math.sin(p0)*Math.sin(p)+Math.cos(p0)*Math.cos(p)*Math.cos(l-l0);
  if(cc<0)return null;
  return{{x:CX+R*Math.cos(p)*Math.sin(l-l0),
          y:CY-R*(Math.cos(p0)*Math.sin(p)-Math.sin(p0)*Math.cos(p)*Math.cos(l-l0))}};
}}
const bg=ctx.createRadialGradient(CX,CY,0,CX,CY,Math.sqrt(W*W+H*H)/2);
bg.addColorStop(0,'#030812');bg.addColorStop(.5,'#051228');bg.addColorStop(1,'#08183a');
ctx.fillStyle=bg;ctx.fillRect(0,0,W,H);
let _s=42;const sr=()=>{{_s^=_s<<13;_s^=_s>>17;_s^=_s<<5;return(_s>>>0)/4294967296;}};
for(let i=0;i<180;i++){{ctx.beginPath();ctx.arc(sr()*W,sr()*H*.55,sr()*1.2+.3,0,Math.PI*2);ctx.fillStyle=`rgba(160,190,220,${{sr()*.6+.2}})`;ctx.fill();}}
ctx.beginPath();ctx.arc(CX,CY,R,0,Math.PI*2);
const og=ctx.createRadialGradient(CX-R*.2,CY-R*.2,0,CX,CY,R);
og.addColorStop(0,'#0d2e55');og.addColorStop(1,'#0a2040');ctx.fillStyle=og;ctx.fill();
const ag=ctx.createRadialGradient(CX,CY,R*.9,CX,CY,R*1.1);
ag.addColorStop(0,'rgba(40,120,255,0)');ag.addColorStop(.5,'rgba(40,120,255,.08)');ag.addColorStop(1,'rgba(40,120,255,0)');
ctx.beginPath();ctx.arc(CX,CY,R*1.1,0,Math.PI*2);ctx.fillStyle=ag;ctx.fill();
ctx.save();ctx.beginPath();ctx.arc(CX,CY,R,0,Math.PI*2);ctx.clip();
function land(pts){{
  const pp=pts.map(([a,b])=>proj(a,b)).filter(p=>p);if(pp.length<3)return;
  ctx.beginPath();ctx.moveTo(pp[0].x,pp[0].y);pp.slice(1).forEach(p=>ctx.lineTo(p.x,p.y));
  ctx.closePath();ctx.fillStyle='rgba(22,65,35,.72)';ctx.fill();
  ctx.strokeStyle='rgba(30,80,45,.35)';ctx.lineWidth=.5;ctx.stroke();
}}
land([[70,-140],[70,-60],[55,-55],[47,-53],[30,-81],[25,-80],[15,-83],[8,-77],[25,-78],[35,-75],[40,-73],[44,-66],[49,-55],[58,-65],[62,-63],[65,-65],[70,-72],[75,-85],[75,-120],[70,-140]]);
land([[83,-40],[83,-10],[75,-15],[72,-22],[60,-43],[65,-50],[70,-55],[80,-45],[83,-40]]);
land([[70,30],[70,10],[60,5],[55,-5],[50,-5],[43,-9],[36,-6],[36,5],[44,8],[44,15],[38,15],[40,26],[43,22],[46,13],[48,17],[52,21],[57,21],[60,22],[63,14],[68,16],[70,30]]);
land([[71,28],[68,14],[62,5],[58,5],[57,8],[59,10],[63,10],[65,14],[68,17],[71,28]]);
land([[66,-24],[64,-13],[63,-18],[64,-22],[66,-24]]);
land([[70,30],[70,140],[60,140],[50,140],[45,130],[38,120],[22,114],[15,108],[5,103],[15,100],[22,88],[15,74],[25,67],[22,60],[15,52],[18,38],[22,37],[30,32],[36,36],[40,36],[38,26],[43,41],[48,60],[55,60],[65,60],[68,55],[70,30]]);
land([[37,-6],[37,10],[30,32],[15,42],[10,42],[5,35],[0,40],[-5,40],[-20,35],[-34,26],[-34,18],[-25,15],[-5,10],[5,2],[10,-15],[20,-17],[30,-13],[35,-4],[37,-6]]);
land([[12,-72],[5,-52],[0,-50],[-10,-37],[-20,-40],[-30,-52],[-40,-62],[-50,-68],[-55,-68],[-50,-73],[-40,-73],[-30,-70],[-15,-72],[-5,-80],[5,-77],[12,-72]]);
land([[-15,130],[-18,140],[-28,153],[-35,150],[-39,140],[-35,137],[-30,115],[-22,114],[-17,122],[-15,130]]);
[[40.7,-74],[51.5,-.1],[48.9,2.3],[52.5,13.4],[55.8,37.6],[35.7,139.8],[31.2,121.5],[22.3,114],[25.2,55.3],[19.1,72.9],[28.6,77.2],[1.4,103.9],[33.9,-118],[41.9,-87.9],[40.6,-73.8],[37.6,-122.4],[43.7,-79.6],[-33.9,151.2],[19.4,-99.1],[-23.4,-46.5],[30.1,31.4],[25.3,55.4]].forEach(([la,lo])=>{{const p=proj(la,lo);if(!p)return;ctx.beginPath();ctx.arc(p.x,p.y,1.5,0,Math.PI*2);ctx.fillStyle='rgba(255,220,100,.6)';ctx.fill();}});
ctx.restore();
ctx.beginPath();ctx.arc(CX,CY,R,0,Math.PI*2);ctx.strokeStyle='rgba(30,80,140,.45)';ctx.lineWidth=1;ctx.stroke();
function drawRoute(lw,col){{
  let s=false;ctx.beginPath();
  WP.forEach(([la,lo])=>{{const p=proj(la,lo);if(!p){{s=false;return;}}s?ctx.lineTo(p.x,p.y):(ctx.moveTo(p.x,p.y),s=true);}});
  ctx.strokeStyle=col;ctx.lineWidth=lw;ctx.lineJoin='round';ctx.stroke();
}}
drawRoute(14,'rgba(180,60,255,.12)');drawRoute(2.5,'#c060f0');
[OP,DP].forEach(([la,lo])=>{{
  const p=proj(la,lo);if(!p)return;
  [10,7].forEach(r=>{{ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);
    ctx.strokeStyle=r===10?'rgba(0,212,170,.25)':'rgba(0,212,170,.55)';ctx.lineWidth=1;ctx.stroke();}});
  ctx.beginPath();ctx.arc(p.x,p.y,4,0,Math.PI*2);ctx.fillStyle='#00d4aa';ctx.fill();
}});
</script></body></html>"""


def _range_circle_pts(lat, lon, range_km, n=120):
    """Return n+1 [[lat,lon]] points forming a geodesic circle of range_km from (lat,lon).
    Works correctly at any distance, including intercontinental ranges."""
    import math
    R = 6371.0
    d = min(range_km / R, math.pi)          # clamp: circle can't exceed hemisphere
    lr, lo = math.radians(lat), math.radians(lon)
    pts = []
    for i in range(n + 1):
        b = math.radians(i * 360.0 / n)
        sinlat = math.sin(lr)*math.cos(d) + math.cos(lr)*math.sin(d)*math.cos(b)
        sinlat = max(-1.0, min(1.0, sinlat))
        lat2 = math.asin(sinlat)
        lon2 = lo + math.atan2(
            math.sin(b)*math.sin(d)*math.cos(lr),
            math.cos(d) - math.sin(lr)*math.sin(lat2),
        )
        pts.append([math.degrees(lat2), math.degrees(lon2)])
    return pts


def _split_antimeridian(wps):
    """Split [[lat,lon],...] waypoints into segments at ±180° crossings.
    Prevents Folium from drawing a horizontal line across the map on
    transpacific/trans-antimeridian routes."""
    if len(wps) < 2:
        return [wps]
    segs, cur = [], [wps[0]]
    for i in range(1, len(wps)):
        p, q = cur[-1], wps[i]
        d = q[1] - p[1]
        if abs(d) > 180:
            # true direction is the short way around
            actual_d = d - 360 if d > 180 else d + 360
            if actual_d < 0:  # westward crossing at -180 / +180
                t = (-180 - p[1]) / actual_d
                cross_lat = p[0] + t * (q[0] - p[0])
                cur.append([cross_lat, -180])
                segs.append(cur)
                cur = [[cross_lat, 180], q]
            else:              # eastward crossing at +180 / -180
                t = (180 - p[1]) / actual_d
                cross_lat = p[0] + t * (q[0] - p[0])
                cur.append([cross_lat, 180])
                segs.append(cur)
                cur = [[cross_lat, -180], q]
        else:
            cur.append(q)
    segs.append(cur)
    return [s for s in segs if len(s) >= 2]


# ══════════════════════════════════════════════════════════════════════════════
# FLEET PRE-COMPUTED DATA
# ══════════════════════════════════════════════════════════════════════════════

def _ac_type(name: str, ac: dict) -> str:
    if ac["cruise_mach"] >= 1.5:             return "Supersonic"
    if ac["seats"] == 0:                     return "Freighter"
    if ac["seats"] >= 200 or ac["S"] >= 280: return "Widebody"
    if ac["seats"] < 100:                    return "Regional"
    return "Narrowbody"


def _max_r(ac: dict) -> int:
    g  = 9.80665
    Wi = (ac["OEW"] + ac["max_fuel"] * 0.95) * g
    Wf = (ac["OEW"] + ac["max_fuel"] * 0.05) * g
    if Wf <= 0 or Wi <= Wf: return 0
    T, _, _ = isa(ac["cruise_alt"])
    V = ac["cruise_mach"] * np.sqrt(1.4 * 287.05 * T)
    _, ld = best_LD(ac["CD0"], ac["k"])
    return int((V / (ac["TSFC"] * g)) * ld * np.log(Wi / Wf) / 1000)


def _casm_at(name: str, ac: dict, dist_km: float):
    if ac["seats"] == 0: return None
    g  = 9.80665
    WN = (ac["OEW"] + 15000 + ac["max_fuel"] * 0.70) * g
    T, _, rho = isa(ac["cruise_alt"])
    V  = ac["cruise_mach"] * np.sqrt(1.4 * 287.05 * T)
    CL = (2 * WN) / (rho * V**2 * ac["S"])
    CD = ac["CD0"] + ac["k"] * CL**2
    fN, _ = breguet_fuel(WN, dist_km * 1000, ac["TSFC"], CL / CD, V)
    asm = ac["seats"] * dist_km * 0.621371
    if asm <= 0: return None
    nf = nonfuel_cost_per_asm(name) * asm
    return round((fN / g * 0.75 + nf) / asm * 100, 2)


def _co2pp(ac: dict, dist_km: float):
    if ac["seats"] == 0: return None
    g  = 9.80665
    WN = (ac["OEW"] + 15000 + ac["max_fuel"] * 0.70) * g
    T, _, rho = isa(ac["cruise_alt"])
    V  = ac["cruise_mach"] * np.sqrt(1.4 * 287.05 * T)
    CL = (2 * WN) / (rho * V**2 * ac["S"])
    CD = ac["CD0"] + ac["k"] * CL**2
    fN, _ = breguet_fuel(WN, dist_km * 1000, ac["TSFC"], CL / CD, V)
    pax = int(ac["seats"] * 0.85)
    return round(fN / g * 3.16 / pax, 1) if pax > 0 else None


def _best_use(ac: dict, mr: int) -> str:
    m, s = ac["cruise_mach"], ac["seats"]
    if m >= 1.5:  return "Premium supersonic"
    if s == 0:    return "Cargo / freight"
    if s < 100:   return "Short-haul regional"
    wb = s >= 200 or ac["S"] >= 280
    if not wb:
        return ("Short-haul domestic" if mr < 4000 else
                "Medium-haul / thin routes" if mr <= 7000 else
                "Transatlantic narrowbody")
    return ("Medium-haul widebody" if mr < 8000 else
            "Long-haul intercontinental" if mr <= 14000 else
            "Ultra long haul / flag routes")


# Published manufacturer list prices (USD millions, approximate)
_LIST_PRICE = {
    "Boeing 737-800":        "$82M",
    "Boeing 737 MAX 9":      "$125M",
    "Boeing 757-200":        "$95M est.",
    "Airbus A220-300":       "$91M",
    "Airbus A320neo":        "$110M",
    "Airbus A321neo":        "$130M",
    "Embraer E195-E2":       "$64M",
    "Bombardier CRJ-900":    "$47M",
    "ATR 72-600":            "$27M",
    "Boeing 767-300ER":      "$200M est.",
    "Boeing 777-300ER":      "$375M",
    "Boeing 777X (777-9)":   "$440M",
    "Boeing 787-9":          "$292M",
    "Boeing 747-8F":         "$418M",
    "Airbus A330-900neo":    "$296M",
    "Airbus A330-200F":      "$230M",
    "Airbus A350-900":       "$317M",
    "Airbus A380-800":       "$445M",
    "Concorde":              "Historical",
    "Boom Overture":         "$200M est.",
    "Gulfstream G700":       "$75M",
    "Bombardier Global 7500":"$73M",
    "Dassault Falcon 10X":   "$80M",
    "Gulfstream G650ER":     "$66M",
    "Boeing BBJ 787":        "$300M+",
    "Boeing BBJ 737 MAX":    "$100M",
    "Embraer Lineage 1000E": "$53M",
    "Cessna Citation Longitude": "$27M",
    "Cessna Citation XLS+":      "$13M",
    "Cessna Citation Sovereign+":"$18M",
    "Bombardier Challenger 350": "$27M",
    "Bombardier Challenger 650": "$32M",
    "Bombardier Global 6500":    "$52M",
    "Dassault Falcon 2000LXS":   "$36M",
    "Dassault Falcon 8X":        "$58M",
    "Embraer Praetor 600":       "$21M",
    "Gulfstream G280":           "$25M",
    "Gulfstream G550":           "$62M",
    "Gulfstream G600":           "$57M",
}

_COMM_ROWS = []
for _n, _ac in COMMERCIAL.items():
    _, _ld = best_LD(_ac["CD0"], _ac["k"])
    _mr    = _max_r(_ac)
    _c500  = _casm_at(_n, _ac, 500)
    _c3k   = _casm_at(_n, _ac, 3000)
    _COMM_ROWS.append({
        "Aircraft":      _n,
        "Type":          _ac_type(_n, _ac),
        "Seats":         _ac["seats"] if _ac["seats"] > 0 else "—",
        "Max Range km":  _mr,
        "Mach":          _ac["cruise_mach"],
        "L/D max":       round(_ld, 1),
        "CO2/pax 3k kg": _co2pp(_ac, 3000) or "—",
        "CASM 500km c":  f"{_c500:.2f}" if _c500 else "—",
        "CASM 3000km c": f"{_c3k:.2f}"  if _c3k  else "—",
        "List price":    _LIST_PRICE.get(_n, "—"),
        "Best use":      _best_use(_ac, _mr),
        "_c500": _c500, "_c3k": _c3k,
    })

_PRIV_ROWS = []
for _n, _ac in PRIVATE.items():
    _rnm = _ac.get("range_nm", 0)
    _cat = ("Ultra-long" if _rnm >= 7000 else
            "VIP Widebody" if _ac["seats"] >= 30 else
            "Large cabin"  if _ac["seats"] >= 16 else "Super-mid")
    _PRIV_ROWS.append({
        "Aircraft":      _n,
        "Category":      _cat,
        "Pax":           _ac["seats"],
        "Range nm":      _rnm or "—",
        "Mach":          _ac["cruise_mach"],
        "Cruise alt ft": int(_ac["cruise_alt"] * 3.28084),
        "Cost/hr $":     f"{_ac.get('cost_hr', 0):,}",
        "List price":    _LIST_PRICE.get(_n, "—"),
        "Use case":      ("Intercontinental" if _rnm >= 7000 else
                          "Transatlantic"     if _rnm >= 5000 else "Continental"),
    })

_c3k_l  = [(r["Aircraft"], r["_c3k"]) for r in _COMM_ROWS if r["_c3k"]]
_MOST_EFF    = min(_c3k_l, key=lambda x: x[1])[0]   if _c3k_l  else "—"
_co2_l  = [(r["Aircraft"], r["CO2/pax 3k kg"]) for r in _COMM_ROWS
            if isinstance(r["CO2/pax 3k kg"], float)]
_LOW_CO2     = min(_co2_l, key=lambda x: x[1])[0]   if _co2_l  else "—"
_c500_n = [(r["Aircraft"], r["_c500"]) for r in _COMM_ROWS
            if r["_c500"] and r["Type"] in ("Narrowbody", "Regional")]
_BEST_SHORT  = min(_c500_n, key=lambda x: x[1])[0]  if _c500_n else "—"
_BEST_PRIV   = max(_PRIV_ROWS, key=lambda r: r["Range nm"]
                   if isinstance(r["Range nm"], int) else 0)["Aircraft"]
_c3k_idx = [(i, float(r["CASM 3000km c"])) for i, r in enumerate(_COMM_ROWS)
             if r["CASM 3000km c"] != "—"]
_BEST_IDX    = min(_c3k_idx, key=lambda x: x[1])[0] if _c3k_idx else None


# ══════════════════════════════════════════════════════════════════════════════
# TOPBAR
# ══════════════════════════════════════════════════════════════════════════════

def topbar(page_title: str = "") -> html.Div:
    _link_base = {
        "color": DIM, "fontSize": "9px", "fontWeight": "700",
        "letterSpacing": "1.5px", "textTransform": "uppercase",
        "fontFamily": FONT, "textDecoration": "none", "padding": "4px 0",
    }
    def _nav(label, href, active):
        style = {**_link_base, "color": WHITE if active else DIM,
                 "borderBottom": f"1px solid {TEAL}" if active else "1px solid transparent"}
        return dcc.Link(label, href=href, style=style)

    active_analyzer = page_title == "ROUTE ANALYZER"
    active_fleet    = page_title == "FLEET INTELLIGENCE"

    return html.Div([
        dcc.Link(html.Span([
            html.Span("FLIGHT", style={"color": WHITE}),
            html.Span("OPS",    style={"color": TEAL}),
        ], style={"fontFamily": "'Rajdhani', sans-serif", "fontWeight": "800",
                  "fontSize": "16px", "letterSpacing": "3px"}),
        href="/", style={"textDecoration": "none"}),
        html.Div([
            _nav("Route Analyzer",   "/analyzer", active_analyzer),
            _nav("Fleet Intelligence", "/fleet",  active_fleet),
        ], style={"display": "flex", "gap": "24px", "alignItems": "center"}),
    ], style={
        "display": "flex", "justifyContent": "space-between", "alignItems": "center",
        "backgroundColor": SIDEBAR, "borderBottom": f"1px solid {BDR}",
        "padding": "0 28px", "height": "48px",
        "position": "sticky", "top": "0", "zIndex": "1000",
        "boxSizing": "border-box",
    })


# ══════════════════════════════════════════════════════════════════════════════
# HOME PAGE
# ══════════════════════════════════════════════════════════════════════════════

def home_layout() -> html.Div:
    rng = random.Random(13)
    _drifts = ["starDrift1","starDrift2","starDrift3","starDrift4","starDrift5"]
    stars = []
    for _ in range(60):
        sz       = rng.choice([1, 1, 1, 2, 2, 3])
        op       = rng.uniform(0.35, 0.9)
        blur     = f"blur({rng.randint(0,1)}px)"
        drift    = rng.choice(_drifts)
        duration = round(rng.uniform(18, 38), 1)
        delay    = round(rng.uniform(0, 12), 1)
        stars.append(html.Div(style={
            "position":        "absolute",
            "left":            f"{rng.uniform(1, 99)}%",
            "top":             f"{rng.uniform(1, 95)}%",
            "width":           f"{sz}px",
            "height":          f"{sz}px",
            "borderRadius":    "50%",
            "backgroundColor": f"rgba(180,210,255,{op:.2f})",
            "filter":          blur,
            "pointerEvents":   "none",
            "animation":       f"{drift} {duration}s {delay}s infinite ease-in-out",
        }))

    def _cta(accent, icon, title, desc, cta_text, href):
        return dcc.Link(html.Div([
            html.Div(style={"height": "2px", "backgroundColor": accent,
                            "borderRadius": "2px 2px 0 0"}),
            html.Div([
                html.Span(icon, style={
                    "fontSize": "22px", "color": accent,
                    "backgroundColor": f"{accent}14",
                    "border": f"1px solid {accent}30",
                    "padding": "8px", "borderRadius": "4px",
                    "marginBottom": "14px", "display": "inline-block",
                }),
                html.P(title, style={"color": WHITE, "fontSize": "13px", "fontWeight": "800",
                                     "letterSpacing": "2px", "textTransform": "uppercase",
                                     "fontFamily": FONT, "margin": "0 0 8px 0"}),
                html.P(desc, style={"color": MUTED, "fontSize": "12px", "lineHeight": "1.65",
                                    "fontFamily": FONT, "margin": "0 0 14px 0"}),
                html.Span(cta_text, style={"color": accent, "fontSize": "12px",
                                           "fontWeight": "700", "fontFamily": FONT}),
            ], style={"padding": "20px"}),
        ], style={"backgroundColor": CARD, "border": f"1px solid {BDR}",
                  "borderRadius": "4px", "overflow": "hidden"}),
        href=href, style={"textDecoration": "none"})

    return html.Div([
        *stars,
        html.Div([
            # Eyebrow
            html.Span("Aviation Route Analytics",
                      style={"color": TEAL, "fontSize": "12px", "fontWeight": "700",
                             "letterSpacing": "3px", "textTransform": "uppercase",
                             "fontFamily": FONT, "display": "block",
                             "marginBottom": "24px"}),
            # Title
            html.H1([
                html.Span("FLIGHT", style={"color": WHITE}),
                html.Span("OPS",    style={"color": TEAL}),
            ], style={"fontFamily": "'Rajdhani', sans-serif", "fontWeight": "900",
                      "fontSize": "76px", "letterSpacing": "-2px",
                      "margin": "0 0 24px 0", "lineHeight": "1"}),
            # Tagline
            html.P(
                "Analyze routes. Compare aircraft.",
                style={"color": LIGHT, "fontSize": "22px", "maxWidth": "540px",
                       "lineHeight": "1.45", "fontFamily": FONT,
                       "margin": "0 auto 0 auto", "textAlign": "center",
                       "fontWeight": "500"}
            ),
            html.P(
                "Make better decisions.",
                style={"color": TEAL, "fontSize": "22px", "maxWidth": "540px",
                       "lineHeight": "1.45", "fontFamily": FONT,
                       "margin": "10px auto 14px auto", "textAlign": "center",
                       "fontWeight": "500"}
            ),
            html.P(
                "Built around the engineering and economics of aviation.",
                style={"color": BODY, "fontSize": "15px", "maxWidth": "460px",
                       "lineHeight": "1.65", "fontFamily": FONT,
                       "margin": "0 auto 44px auto", "textAlign": "center"}
            ),
            # CTA cards
            html.Div([
                _cta(TEAL,   "◈", "ROUTE ANALYZER",
                     "Pick any city pair, select your aircraft, "
                     "and get a full cost and revenue breakdown in seconds.",
                     "Open Analyzer →", "/analyzer"),
                _cta(PURPLE, "▦", "FLEET INTELLIGENCE",
                     "Browse every commercial and private aircraft side by side. "
                     "Cost per seat, range, emissions, and best-fit routes.",
                     "Explore Fleet →", "/fleet"),
            ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                      "gap": "20px", "maxWidth": "640px", "margin": "0 auto"}),
        ], style={
            "position": "relative", "zIndex": "2",
            "display": "flex", "flexDirection": "column",
            "alignItems": "center", "justifyContent": "center",
            "textAlign": "center",
            "minHeight": "calc(100vh - 110px)", "padding": "48px 32px",
        }),
        # Footer
        html.Div([
            html.Span("50 aircraft · 100 airports · real physics based analysis",
                      style={"color": DIM, "fontSize": "10px", "fontFamily": FONT}),
            html.Span("G. TURCHETTI",
                      style={"color": DIM, "fontSize": "10px", "fontFamily": FONT,
                             "letterSpacing": "1.5px"}),
        ], style={
            "position": "relative", "zIndex": "2",
            "borderTop": f"1px solid {BDR}", "padding": "14px 40px",
            "display": "flex", "justifyContent": "space-between",
        }),
    ], style={"position": "relative", "overflow": "hidden",
              "backgroundColor": BG, "minHeight": "calc(100vh - 48px)",
              "zoom": "0.917"})


# ══════════════════════════════════════════════════════════════════════════════
# FLEET PAGE
# ══════════════════════════════════════════════════════════════════════════════

_TH = {"backgroundColor": "#060a10", "color": DIM, "fontWeight": "500",
       "borderBottom": f"1px solid {BDR}", "textTransform": "uppercase",
       "letterSpacing": "1px", "fontSize": "7px", "padding": "8px 10px",
       "whiteSpace": "nowrap", "fontFamily": FONT}
_TD = {"backgroundColor": CARD, "color": BODY, "borderBottom": f"1px solid {BDR}",
       "fontSize": "9px", "padding": "7px 10px", "fontFamily": FONT}

_COND_COMM = [
    {"if": {"row_index": "odd"},  "backgroundColor": BG},
    {"if": {"state": "active"},   "backgroundColor": BDR2,
     "color": WHITE, "border": f"1px solid {BDR2}"},
    {"if": {"column_id": ["CASM 500km c", "CASM 3000km c"]}, "color": AMBER},
    *(([{"if": {"row_index": _BEST_IDX, "column_id": "Aircraft"},
          "color": WHITE, "fontWeight": "700"},
        {"if": {"row_index": _BEST_IDX}, "color": TEAL}])
      if _BEST_IDX is not None else []),
]
_COND_PRIV = [
    {"if": {"row_index": "odd"},  "backgroundColor": BG},
    {"if": {"state": "active"},   "backgroundColor": BDR2,
     "color": WHITE, "border": f"1px solid {BDR2}"},
    {"if": {"column_id": "Cost/hr $"}, "color": AMBER},
    {"if": {"filter_query": '{Aircraft} = "Gulfstream G700"', "column_id": "Aircraft"},
     "color": AMBER, "fontWeight": "700"},
]


def _wchip(label, value, color):
    return html.Div([
        html.Span(label, style={"color": MUTED, "fontSize": "6px", "letterSpacing": "1.5px",
                                "textTransform": "uppercase", "fontFamily": FONT,
                                "display": "block", "marginBottom": "3px"}),
        html.Span(value, style={"color": color, "fontSize": "9px",
                                "fontWeight": "700", "fontFamily": FONT}),
    ], style={"backgroundColor": CARD, "border": f"1px solid {BDR}",
              "borderLeft": f"2px solid {color}", "borderRadius": "3px",
              "padding": "8px 12px", "flex": "1", "minWidth": "140px"})


def fleet_layout() -> html.Div:
    comm_display = [{k: v for k, v in r.items() if not k.startswith("_")}
                    for r in _COMM_ROWS]
    return html.Div([html.Div([
        html.H2("Fleet Intelligence",
                style={"color": WHITE, "fontFamily": "'Rajdhani', sans-serif",
                       "fontWeight": "900", "fontSize": "20px", "margin": "0 0 4px 0"}),
        html.P("Full fleet · Commercial & Private",
               style={"color": MUTED, "fontSize": "8px", "letterSpacing": "2px",
                      "textTransform": "uppercase", "fontFamily": FONT,
                      "margin": "0 0 20px 0"}),

        html.Div([
            _wchip("Most Efficient",  _MOST_EFF,   TEAL),
            _wchip("Lowest CO2/pax",  _LOW_CO2,    TEAL),
            _wchip("Best Short Haul", _BEST_SHORT, TEAL),
            _wchip("Best Private",    _BEST_PRIV,  AMBER),
        ], style={"display": "flex", "gap": "8px", "flexWrap": "wrap",
                  "marginBottom": "28px", "justifyContent": "flex-end"}),

        _sec("COMMERCIAL AIRLINERS"),
        html.Div(
            dash_table.DataTable(
                columns=[{"name": c, "id": c} for c in comm_display[0]],
                data=comm_display, sort_action="native", page_action="none",
                style_table={"overflowX": "auto"},
                style_header=_TH, style_data=_TD,
                style_data_conditional=_COND_COMM,
                style_cell={"fontFamily": FONT, "textAlign": "left",
                            "border": f"1px solid {BDR}", "whiteSpace": "nowrap"},
                style_cell_conditional=[
                    {"if": {"column_id": "Aircraft"}, "minWidth": "160px"},
                    {"if": {"column_id": "Best use"},  "minWidth": "200px"},
                ],
            ),
            style={"border": f"1px solid {BDR}", "borderRadius": "4px",
                   "overflow": "hidden", "marginBottom": "32px"},
        ),

        _sec("BUSINESS & PRIVATE JETS"),
        html.Div(
            dash_table.DataTable(
                columns=[{"name": c, "id": c} for c in _PRIV_ROWS[0]] if _PRIV_ROWS else [],
                data=_PRIV_ROWS, sort_action="native", page_action="none",
                style_table={"overflowX": "auto"},
                style_header=_TH, style_data=_TD,
                style_data_conditional=_COND_PRIV,
                style_cell={"fontFamily": FONT, "textAlign": "left",
                            "border": f"1px solid {BDR}", "whiteSpace": "nowrap"},
                style_cell_conditional=[
                    {"if": {"column_id": "Aircraft"}, "minWidth": "180px"},
                    {"if": {"column_id": "Use case"},  "minWidth": "140px"},
                ],
            ),
            style={"border": f"1px solid {BDR}", "borderRadius": "4px", "overflow": "hidden"},
        ),
    ], style={"maxWidth": "1400px", "margin": "0 auto",
              "padding": "32px 28px 60px", "boxSizing": "border-box"})],
    style={"backgroundColor": BG, "minHeight": "calc(100vh - 48px)"})


# ══════════════════════════════════════════════════════════════════════════════
# ANALYZER — SIDEBAR (static, persistent)
# ══════════════════════════════════════════════════════════════════════════════

_AP_OPTS = [{"label": f"{k} — {v['name']}", "value": k} for k, v in AIRPORTS.items()]
_DD_STY  = {"backgroundColor": CARD, "color": "#000",
            "border": f"1px solid {BDR2}", "fontSize": "9px", "borderRadius": "3px"}

analyzer_sidebar = html.Div([
    # ── Route ────────────────────────────────────────────────────────────────
    _sec("ROUTE"),
    html.Div([
        html.Span(style={"width": "7px", "height": "7px", "borderRadius": "50%",
                         "backgroundColor": TEAL, "flexShrink": "0",
                         "display": "inline-block", "marginRight": "6px", "marginTop": "2px"}),
        dcc.Dropdown(id="az-origin", options=_AP_OPTS, value="ORD",
                     clearable=False, style=_DD_STY),
    ], style={"display": "flex", "alignItems": "flex-start"}),
    html.Div([
        html.Span(style={"width": "7px", "height": "7px", "borderRadius": "50%",
                         "backgroundColor": PURPLE, "flexShrink": "0",
                         "display": "inline-block", "marginRight": "6px", "marginTop": "2px"}),
        dcc.Dropdown(id="az-dest", options=_AP_OPTS, value="LHR",
                     clearable=False, style=_DD_STY),
    ], style={"display": "flex", "alignItems": "flex-start"}),

    html.Div(style={"height": "1px", "backgroundColor": BDR, "margin": "6px 0"}),

    # ── Commercial aircraft chips ─────────────────────────────────────────────
    html.P("COMMERCIAL AIRCRAFT",
           style={"color": MUTED, "fontSize": "8px", "letterSpacing": "2.5px",
                  "textTransform": "uppercase", "fontFamily": FONT, "margin": "0 0 2px 0"}),
    html.P("Capable of completing this route",
           style={"color": BDR2, "fontSize": "7px", "fontFamily": FONT, "margin": "0 0 6px 0"}),
    dcc.Store(id="selected-comm", data=[]),
    dcc.Store(id="selected-priv", data=[]),
    html.Div(id="comm-chips-container"),

    html.Div(style={"height": "1px", "backgroundColor": BDR, "margin": "8px 0"}),

    # ── Private jets chips ────────────────────────────────────────────────────
    html.P("BUSINESS & PRIVATE JETS",
           style={"color": MUTED, "fontSize": "8px", "letterSpacing": "2.5px",
                  "textTransform": "uppercase", "fontFamily": FONT, "margin": "0 0 2px 0"}),
    html.P("Ultra long-range capable",
           style={"color": BDR2, "fontSize": "7px", "fontFamily": FONT, "margin": "0 0 6px 0"}),
    html.Div(id="priv-chips-container"),

    html.Div(style={"height": "1px", "backgroundColor": BDR, "margin": "8px 0"}),

    # ── Sliders ───────────────────────────────────────────────────────────────
    html.Div([
        html.Div([_lbl("Payload (kg)"),
                  html.Span(id="lbl-pay", style={"color": LIGHT, "fontSize": "9px",
                                                  "fontWeight": "700", "fontFamily": FONT})],
                 style={"display": "flex", "justifyContent": "space-between"}),
        dcc.Slider(id="az-payload", min=5000, max=50000, step=1000, value=23000,
                   marks={5000: "5k", 50000: "50k"},
                   tooltip={"placement": "bottom", "always_visible": False}),
    ]),
    html.Div([
        html.Div([_lbl("Fuel price ($/kg)"),
                  html.Span(id="lbl-fuel", style={"color": LIGHT, "fontSize": "9px",
                                                   "fontWeight": "700", "fontFamily": FONT})],
                 style={"display": "flex", "justifyContent": "space-between"}),
        dcc.Slider(id="az-fuel", min=0.30, max=1.50, step=0.05, value=0.75,
                   marks={0.30: "0.30", 1.50: "1.50"},
                   tooltip={"placement": "bottom", "always_visible": False}),
    ]),
    html.Div([
        html.Div([_lbl("Load factor (%)"),
                  html.Span(id="lbl-lf", style={"color": LIGHT, "fontSize": "9px",
                                                 "fontWeight": "700", "fontFamily": FONT})],
                 style={"display": "flex", "justifyContent": "space-between"}),
        dcc.Slider(id="az-lf", min=50, max=100, step=5, value=85,
                   marks={50: "50", 100: "100"},
                   tooltip={"placement": "bottom", "always_visible": False}),
    ]),
    html.Div([
        html.Div([_lbl("Ticket multiplier (×)"),
                  html.Span(id="lbl-tm", style={"color": LIGHT, "fontSize": "9px",
                                                 "fontWeight": "700", "fontFamily": FONT})],
                 style={"display": "flex", "justifyContent": "space-between"}),
        dcc.Slider(id="az-tm", min=0.5, max=2.0, step=0.1, value=1.0,
                   marks={0.5: "0.5×", 2.0: "2×"},
                   tooltip={"placement": "bottom", "always_visible": False}),
    ]),

    html.Div(style={"height": "1px", "backgroundColor": BDR, "margin": "6px 0"}),

    html.Button("ANALYZE ROUTE", id="az-btn", n_clicks=0, style={
        "backgroundColor": TEAL, "color": BG, "border": "none",
        "borderRadius": "3px", "padding": "12px", "fontWeight": "800",
        "fontSize": "9px", "letterSpacing": "2px", "cursor": "pointer",
        "width": "100%", "fontFamily": FONT, "textTransform": "uppercase",
    }),

], style={
    "width": "210px", "minWidth": "210px", "backgroundColor": SIDEBAR,
    "borderRight": f"1px solid {BDR}", "padding": "14px 12px",
    "display": "flex", "flexDirection": "column", "gap": "7px",
    "overflowY": "auto", "boxSizing": "border-box",
})

analyzer_layout = html.Div([
    analyzer_sidebar,
    html.Div(id="az-main",
             style={"flex": "1", "padding": "20px 24px", "overflowY": "auto"},
             children=[html.Div(style={
                 "backgroundColor": CARD, "border": f"1px solid {BDR}",
                 "borderRadius": "4px", "padding": "48px",
                 "textAlign": "center", "marginTop": "40px",
             }, children=[
                 html.H2("ROUTE ANALYZER",
                         style={"color": TEAL, "fontFamily": "'Rajdhani', sans-serif",
                                "fontWeight": "700", "fontSize": "22px",
                                "letterSpacing": "4px", "margin": "0 0 10px 0"}),
                 html.P("Select origin · destination · aircraft — then click ANALYZE ROUTE",
                        style={"color": DIM, "fontSize": "9px", "letterSpacing": "2px",
                               "textTransform": "uppercase", "fontFamily": FONT}),
             ])]),
], style={"display": "flex", "minHeight": "calc(100vh - 48px)", "backgroundColor": BG})


# ══════════════════════════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════════════════════════

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[FONTS_URL],
    meta_tags=[
        {"name": "viewport",        "content": "width=device-width, initial-scale=1"},
        {"property": "og:title",       "content": "FlightOps — Aviation Route Analytics"},
        {"property": "og:description", "content": "Analyze routes. Compare aircraft. Make better decisions."},
        {"property": "og:image",       "content": "https://flightops-suite-1.onrender.com/assets/og_image.png"},
        {"property": "og:type",        "content": "website"},
        {"property": "og:url",         "content": "https://flightops-suite-1.onrender.com"},
        {"name": "twitter:card",       "content": "summary_large_image"},
        {"name": "twitter:title",      "content": "FlightOps — Aviation Route Analytics"},
        {"name": "twitter:description","content": "Analyze routes. Compare aircraft. Make better decisions."},
        {"name": "twitter:image",      "content": "https://flightops-suite-1.onrender.com/assets/og_image.png"},
    ],
)
app.title = "FlightOps"

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="fo-topbar"),
    html.Div(id="fo-page"),
], style={"backgroundColor": BG, "minHeight": "100vh",
          "fontFamily": FONT, "margin": "0", "padding": "0",
          "zoom": "1.2"})


# ══════════════════════════════════════════════════════════════════════════════
# CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════

# ── URL routing ───────────────────────────────────────────────────────────────
@app.callback(
    Output("fo-topbar", "children"),
    Output("fo-page",   "children"),
    Input("url", "pathname"),
)
def route_pages(pathname):
    p = (pathname or "/").rstrip("/") or "/"
    if p == "/fleet":    return topbar("FLEET INTELLIGENCE"), fleet_layout()
    if p == "/analyzer": return topbar("ROUTE ANALYZER"),     analyzer_layout
    return topbar(""), home_layout()


# ── Slider live labels ────────────────────────────────────────────────────────
@app.callback(
    Output("lbl-pay",  "children"),
    Output("lbl-fuel", "children"),
    Output("lbl-lf",   "children"),
    Output("lbl-tm",   "children"),
    Input("az-payload", "value"),
    Input("az-fuel",    "value"),
    Input("az-lf",      "value"),
    Input("az-tm",      "value"),
    prevent_initial_call=True,
)
def slider_labels(pay, fuel, lf, tm):
    return f"{pay:,} kg", f"${fuel:.2f}/kg", f"{lf}%", f"{tm:.1f}×"


# ── Chip rendering ────────────────────────────────────────────────────────────
@app.callback(
    Output("comm-chips-container", "children"),
    Output("priv-chips-container", "children"),
    Input("selected-comm", "data"),
    Input("selected-priv", "data"),
    Input("az-origin", "value"),
    Input("az-dest",   "value"),
)
def render_chips(sel_comm, sel_priv, origin, dest):
    dist = get_dist(origin, dest)

    def make_chip(name, selected, capable, is_priv=False):
        color = "#f0b830" if is_priv else "#00d4aa"
        return html.Button(
            name,
            id={"type": "priv-chip" if is_priv else "comm-chip", "index": name},
            style={
                "background":      f"{color}14" if selected else "#0e1520",
                "color":           color if selected else "#4a6080",
                "border":          f"1px solid {color}40" if selected else "1px solid #182030",
                "borderRadius":    "20px",
                "padding":         "4px 10px",
                "fontSize":        "10px",
                "fontWeight":      "700",
                "cursor":          "pointer" if capable else "not-allowed",
                "opacity":         "1" if capable else "0.35",
                "textDecoration":  "none" if capable else "line-through",
                "fontFamily":      "inherit",
            },
            disabled=not capable,
            n_clicks=0,
        )

    comm_chips = [
        make_chip(n, n in (sel_comm or []),
                  can_complete_route(n, dist) if dist else True, False)
        for n in COMMERCIAL
    ]
    priv_chips = [
        make_chip(n, n in (sel_priv or []),
                  can_complete_route(n, dist) if dist else True, True)
        for n in PRIVATE
    ]
    wrap = {"display": "flex", "flexWrap": "wrap", "gap": "5px"}
    return html.Div(comm_chips, style=wrap), html.Div(priv_chips, style=wrap)


@app.callback(
    Output("selected-comm", "data"),
    Input({"type": "comm-chip", "index": ALL}, "n_clicks"),
    State({"type": "comm-chip", "index": ALL}, "id"),
    State("selected-comm", "data"),
    prevent_initial_call=True,
)
def toggle_comm(clicks, ids, current):
    if not ctx.triggered_id:
        return current
    # n_clicks=0 is a re-render reset, not a real click — ignore it
    if not ctx.triggered or not ctx.triggered[0].get("value"):
        return current
    name = ctx.triggered_id["index"]
    sel = list(current or [])
    if name in sel:
        sel.remove(name)
    elif len(sel) < 4:
        sel.append(name)
    return sel


@app.callback(
    Output("selected-priv", "data"),
    Input({"type": "priv-chip", "index": ALL}, "n_clicks"),
    State({"type": "priv-chip", "index": ALL}, "id"),
    State("selected-priv", "data"),
    prevent_initial_call=True,
)
def toggle_priv(clicks, ids, current):
    if not ctx.triggered_id:
        return current
    # n_clicks=0 is a re-render reset, not a real click — ignore it
    if not ctx.triggered or not ctx.triggered[0].get("value"):
        return current
    name = ctx.triggered_id["index"]
    sel = list(current or [])
    if name in sel:
        sel.remove(name)
    elif len(sel) < 4:
        sel.append(name)
    return sel


# ── Private-jet analysis layout ───────────────────────────────────────────────
def _private_jet_layout(entries, origin, dest, oa, da, dk, dnm, haul, region):
    """Full analysis panel shown when all selected aircraft are private jets."""

    # Re-sort: nonstop jets first, then cheapest within each group
    entries = sorted(entries, key=lambda e: (
        0 if e["ac"].get("range_nm", 0) >= dnm * 1.05 else 1,
        e["charter_rev"] or 9e9,
    ))
    W    = entries[0]
    W_ac = W["ac"]
    W_r  = W["result"]

    def _nonstop(e):
        return e["ac"].get("range_nm", 0) >= dnm * 1.05

    nonstop_n = sum(1 for e in entries if _nonstop(e))

    # ── Banner ────────────────────────────────────────────────────────────────
    banner = html.Div([
        html.Div([
            html.Div([
                html.Span("PRIVATE CHARTER ANALYSIS",
                          style={"color": AMBER, "fontSize": "7px", "letterSpacing": "2.5px",
                                 "fontWeight": "700", "fontFamily": FONT,
                                 "display": "block", "marginBottom": "4px"}),
                html.H2(f"{oa['name']} ({origin}) → {da['name']} ({dest})",
                        style={"color": WHITE, "fontSize": "15px", "fontWeight": "800",
                               "fontFamily": FONT, "margin": "0 0 4px 0"}),
                html.P(
                    f"{region} · {haul} · {dk:,.0f} km · {dnm:,} nm"
                    f" · Est. {W_r['flight_time_hr']:.1f}h",
                    style={"color": MUTED, "fontSize": "8px", "letterSpacing": "1.5px",
                           "textTransform": "uppercase", "fontFamily": FONT, "margin": "0"},
                ),
            ], style={"flex": "1"}),
            html.Div([
                html.Span(
                    f"{nonstop_n}/{len(entries)} nonstop capable",
                    style={"backgroundColor": f"{TEAL}18", "color": TEAL,
                           "border": f"1px solid {TEAL}45", "borderRadius": "20px",
                           "padding": "3px 10px", "fontSize": "8px", "fontFamily": FONT},
                ),
                html.Span(
                    f"{len(entries)} jet{'s' if len(entries) > 1 else ''} compared",
                    style={"backgroundColor": f"{AMBER}18", "color": AMBER,
                           "border": f"1px solid {AMBER}45", "borderRadius": "20px",
                           "padding": "3px 10px", "fontSize": "8px", "fontFamily": FONT},
                ),
            ], style={"display": "flex", "gap": "8px", "alignItems": "center"}),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "alignItems": "flex-start"}),
    ], style={
        "backgroundColor": CARD, "border": f"1px solid {BDR}",
        "borderLeft": f"3px solid {AMBER}", "borderRadius": "4px",
        "padding": "14px 18px",
    })

    # ── Jet comparison cards ──────────────────────────────────────────────────
    def _cabin_class(ac):
        seats, rng = ac["seats"], ac.get("range_nm", 0)
        if seats >= 30:   return "VIP Widebody"
        if rng  >= 7000:  return "Ultra-Long Range"
        if seats >= 16:   return "Large Cabin"
        if seats >= 12:   return "Super-Midsize"
        return "Midsize"

    def _jet_card(idx, e):
        col  = RANK_C[idx]
        ac   = e["ac"]
        rng  = ac.get("range_nm", 0)
        seats = ac["seats"]
        flt  = e["result"].get("flight_time_hr", 1)
        price = e["charter_rev"] or 0
        cpp   = price / seats if seats else 0
        cpnm  = price / dnm   if dnm   else 0
        spare = rng - dnm
        ok    = _nonstop(e)
        pct   = min(100, int(dnm / rng * 100)) if rng else 100
        T, _, _ = isa(ac["cruise_alt"])
        spd_kts = int(ac["cruise_mach"] * np.sqrt(1.4 * 287.05 * T) * 1.94384)
        fl      = int(ac["cruise_alt"] * 3.28084 / 100)

        return html.Div([
            html.Span(RANK_B[idx], style={
                "backgroundColor": f"{col}20", "color": col,
                "border": f"1px solid {col}60", "borderRadius": "20px",
                "padding": "2px 8px", "fontSize": "7px", "fontWeight": "700",
                "fontFamily": FONT, "display": "inline-block", "marginBottom": "8px",
            }),
            html.P(e["name"],
                   style={"color": WHITE, "fontSize": "10px", "fontWeight": "800",
                          "fontFamily": FONT, "margin": "0 0 2px 0", "lineHeight": "1.2"}),
            html.P(f"{_cabin_class(ac)} · {seats} seats",
                   style={"color": MUTED, "fontSize": "7px",
                          "fontFamily": FONT, "margin": "0 0 10px 0"}),
            # Charter price — hero number
            html.P(f"${price:,.0f}",
                   style={"color": AMBER, "fontSize": "24px", "fontWeight": "700",
                          "fontFamily": "'Rajdhani', sans-serif",
                          "margin": "0 0 1px 0", "lineHeight": "1"}),
            html.P("estimated all-in charter price",
                   style={"color": MUTED, "fontSize": "6px", "fontFamily": FONT,
                          "letterSpacing": "0.4px", "margin": "0 0 10px 0"}),
            # Nonstop badge
            html.Span(
                "✓ NONSTOP" if ok else "⚠ FUEL STOP REQUIRED",
                style={
                    "backgroundColor": f"{TEAL}15" if ok else f"{RED}15",
                    "color": TEAL if ok else RED,
                    "border":  f"1px solid {TEAL}40" if ok else f"1px solid {RED}40",
                    "borderRadius": "3px", "padding": "2px 8px",
                    "fontSize": "7px", "fontWeight": "700",
                    "fontFamily": FONT, "letterSpacing": "1px",
                },
            ),
            # Range utilisation bar
            html.Div([
                html.Div(style={
                    "height": "3px", "backgroundColor": col if ok else RED,
                    "width": f"{pct}%", "borderRadius": "2px",
                    "transition": "width .4s",
                }),
                html.Div(style={
                    "height": "3px", "backgroundColor": BDR2,
                    "width": f"{100 - pct}%", "borderRadius": "2px",
                }),
            ], style={"display": "flex", "gap": "1px", "margin": "7px 0 2px 0"}),
            html.P(
                f"Uses {pct}% of its range — {spare:,} nm left over" if ok
                else f"Route is {-spare:,} nm beyond this jet's range",
                style={"color": MUTED, "fontSize": "6px",
                       "fontFamily": FONT, "margin": "0 0 10px 0"},
            ),
            # Stats grid
            html.Div([
                _mini("Flight time",      f"{flt:.1f}h",           LIGHT),
                _mini("Per person",       f"${cpp:,.0f}",          TEAL),
                _mini("Price per nm",     f"${cpnm:.1f}",          BODY),
                _mini("Altitude & speed", f"FL{fl} · {spd_kts} kts", BODY),
            ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                      "gap": "4px"}),
        ], style={
            "backgroundColor": CARD, "border": f"1px solid {col}30",
            "borderTop": f"2px solid {col}", "borderRadius": "4px",
            "padding": "14px 12px", "flex": "1", "minWidth": "160px",
        })

    jet_cards = html.Div(
        [_jet_card(i, e) for i, e in enumerate(entries)],
        style={"display": "grid",
               "gridTemplateColumns": f"repeat({len(entries)}, 1fr)",
               "gap": "10px"},
    )

    # ── Charter economics table ───────────────────────────────────────────────
    def _erow(label, vals, highlight=False, val_col=BODY):
        cells = [
            html.Td(label, style={"color": BODY, "fontSize": "8px", "fontFamily": FONT,
                                   "padding": "6px 10px",
                                   "borderBottom": f"1px solid {BDR}",
                                   "whiteSpace": "nowrap"}),
        ]
        for i, v in enumerate(vals):
            cells.append(html.Td(v, style={
                "color": RANK_C[i] if highlight else val_col,
                "fontSize": "9px", "fontFamily": FONT,
                "fontWeight": "700" if highlight else "400",
                "padding": "6px 10px",
                "borderBottom": f"1px solid {BDR}",
            }))
        return html.Tr(cells)

    econ_rows_data = [
        ("Estimated charter price",
         [f"${e['charter_rev']:,.0f}" for e in entries], True, AMBER),
        ("Hourly base rate",
         [f"${e['cost_hr_rate']:,.0f}/hr" for e in entries], False, BODY),
        ("Price per nautical mile",
         [f"${(e['charter_rev'] or 0)/dnm:.1f}" for e in entries], False, BODY),
        ("Per person (full cabin)",
         [f"${(e['charter_rev'] or 0)/e['ac']['seats']:,.0f}" for e in entries],
         False, TEAL),
        ("Fuel cost",
         [f"${e['result'].get('fuel_cost', 0):,.0f}" for e in entries], False, MUTED),
        ("Fuel used",
         [f"{e['result']['fuel_burned_kg']:,.0f} kg" for e in entries], False, MUTED),
        ("Estimated flight time",
         [f"{e['result']['flight_time_hr']:.1f}h" for e in entries], False, LIGHT),
        ("Maximum range",
         [f"{e['ac'].get('range_nm', 0):,} nm" for e in entries], False, BODY),
        ("Range buffer after this route",
         [f"{e['ac'].get('range_nm', 0) - dnm:,} nm" for e in entries], False, TEAL),
    ]

    econ_hdr = [html.Th("", style={"color": MUTED, "fontSize": "7px", "fontFamily": FONT,
                                    "padding": "6px 10px", "textTransform": "uppercase",
                                    "letterSpacing": "1px"})]
    for i, e in enumerate(entries):
        short = " ".join(e["name"].split()[-2:])
        econ_hdr.append(html.Th(short, style={
            "color": RANK_C[i], "fontSize": "7px",
            "fontFamily": FONT, "padding": "6px 10px",
        }))

    econ_table = html.Div([
        _sec("PRICE COMPARISON"),
        html.P(
            "The charter price shown includes the broker's fee (~38% markup on top of the "
            "operator's base rate). Published hourly rates are a starting point. "
            "Your actual quote will vary by operator, season, and positioning.",
            style={"color": MUTED, "fontSize": "7px", "fontFamily": FONT,
                   "lineHeight": "1.5", "margin": "0 0 10px 0"},
        ),
        html.Div(html.Table([
            html.Thead(html.Tr(econ_hdr)),
            html.Tbody([_erow(l, v, h, c) for l, v, h, c in econ_rows_data]),
        ], style={"width": "100%", "borderCollapse": "collapse"}),
            style={"overflowX": "auto"}),
    ], style={"backgroundColor": CARD, "border": f"1px solid {BDR}",
              "borderRadius": "4px", "padding": "14px 16px"})

    # ── Range vs route chart ──────────────────────────────────────────────────
    range_fig = go.Figure()
    for i, e in enumerate(entries):
        rng   = e["ac"].get("range_nm", 0)
        short = " ".join(e["name"].split()[-2:])
        range_fig.add_trace(go.Bar(
            y=[short], x=[rng],
            orientation="h",
            marker_color=RANK_C[i],
            name=short,
            text=f"  {rng:,} nm",
            textposition="outside",
            textfont=dict(size=9, color=RANK_C[i], family=FONT),
            hovertemplate=(
                f"<b>{e['name']}</b><br>"
                f"Range: {rng:,} nm<br>"
                f"Route: {dnm:,} nm<br>"
                f"Spare: {rng-dnm:,} nm<extra></extra>"
            ),
        ))
    max_rng = max(e["ac"].get("range_nm", 0) for e in entries)
    range_fig.add_shape(
        type="line", x0=dnm, x1=dnm, y0=-0.5, y1=len(entries) - 0.5,
        line=dict(color=AMBER, width=2, dash="dash"),
    )
    range_fig.add_annotation(
        x=dnm, y=len(entries) - 0.5,
        text=f"Route: {dnm:,} nm",
        showarrow=False,
        font=dict(color=AMBER, size=8, family=FONT),
        yanchor="bottom", xanchor="left", xshift=6,
    )
    range_fig.update_layout(
        showlegend=False, barmode="overlay",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=80, t=10, b=10),
        height=max(80, len(entries) * 44 + 30),
        xaxis=dict(
            range=[0, max_rng * 1.15],
            tickfont=dict(size=8, color=BODY, family=FONT),
            showgrid=True, gridcolor=BDR,
            ticksuffix=" nm",
        ),
        yaxis=dict(
            tickfont=dict(size=9, color=LIGHT, family=FONT),
            showgrid=False,
        ),
        font=dict(family=FONT),
    )

    range_panel = html.Div([
        _sec("CAN IT FLY NONSTOP?"),
        html.P(
            "The amber dashed line marks this route's distance. "
            "Any jet whose bar extends past it can fly nonstop — the longer the bar beyond the line, the more buffer.",
            style={"color": MUTED, "fontSize": "7px", "fontFamily": FONT,
                   "margin": "0 0 8px 0"},
        ),
        dcc.Graph(figure=range_fig, config={"displayModeBar": False}),
    ], style={"backgroundColor": CARD, "border": f"1px solid {BDR}",
              "borderRadius": "4px", "padding": "14px 16px"})

    # ── Flight profile (best-ranked jet) ─────────────────────────────────────
    mach = W_ac["cruise_mach"]
    T, _, _ = isa(W_ac["cruise_alt"])
    spd_kts = int(mach * np.sqrt(1.4 * 287.05 * T) * 1.94384)
    fl = int(W_ac["cruise_alt"] * 3.28084 / 100)

    profile_items = [
        ("Cruising speed",        f"Mach {mach:.3f}  ·  {spd_kts} kts",           LIGHT),
        ("Cruising altitude",     f"FL{fl}  ({int(W_ac['cruise_alt']/0.3048/1000):.0f},000 ft)", LIGHT),
        ("Estimated flight time", f"{W_r['flight_time_hr']:.1f} hours",            TEAL),
        ("Fuel used",             f"{W_r['fuel_burned_kg']:,.0f} kg",              BODY),
        ("CO₂ emissions",         f"{W_r['co2_kg']:,.0f} kg  ({W_r['co2_kg']/1000:.1f} t)", BODY),
        ("Passenger capacity",    f"{W_ac['seats']} passengers",                   LIGHT),
        ("Fuel efficiency (L/D)", f"{W_r['LD_ratio']}  (higher = more efficient)", MUTED),
        ("Route vs max range",    f"Uses {int(W_ac.get('range_nm',0)/dnm*100) if dnm else '—'}% of this jet's range", MUTED),
    ]

    profile_panel = html.Div([
        _sec(f"FLIGHT PROFILE — {W['name'].upper()}"),
        html.Div([
            html.Div([
                html.P(lbl, style={"color": MUTED, "fontSize": "7px",
                                   "letterSpacing": "1px", "textTransform": "uppercase",
                                   "fontFamily": FONT, "margin": "0 0 2px 0"}),
                html.P(val, style={"color": col, "fontSize": "11px", "fontWeight": "700",
                                   "fontFamily": FONT, "margin": "0"}),
            ], style={"padding": "8px 14px", "borderRight": f"1px solid {BDR}",
                      "flex": "1", "minWidth": "140px"})
            for lbl, val, col in profile_items
        ], style={"display": "flex", "flexWrap": "wrap",
                  "borderTop": f"1px solid {BDR}"}),
    ], style={"backgroundColor": CARD, "border": f"1px solid {BDR}",
              "borderRadius": "4px", "padding": "14px 16px"})

    # ── CO2 & sustainability ──────────────────────────────────────────────────
    co2_kg  = W_r["co2_kg"]
    co2_t   = co2_kg / 1000
    offset  = co2_t * 20               # $20/tonne REDD+ reference
    # Equivalent economy passengers: ~0.10 kg CO2 per pax-km
    equiv   = int(co2_kg / max(dk * 0.10, 1))

    co2_panel = html.Div([
        _sec("CARBON FOOTPRINT"),
        html.Div([
            html.Div([
                html.P("Total CO₂ for this flight",
                       style={"color": MUTED, "fontSize": "7px", "letterSpacing": "1px",
                              "textTransform": "uppercase", "fontFamily": FONT,
                              "margin": "0 0 2px 0"}),
                html.P(f"{co2_kg:,.0f} kg",
                       style={"color": RED, "fontSize": "20px", "fontWeight": "700",
                              "fontFamily": "'Rajdhani', sans-serif",
                              "margin": "0 0 2px 0", "lineHeight": "1"}),
                html.P(f"{co2_t:.1f} tonnes — whole charter",
                       style={"color": MUTED, "fontSize": "7px",
                              "fontFamily": FONT, "margin": "0"}),
            ], style={"flex": "1", "padding": "10px 14px",
                      "borderRight": f"1px solid {BDR}"}),
            html.Div([
                html.P("Estimated carbon offset cost",
                       style={"color": MUTED, "fontSize": "7px", "letterSpacing": "1px",
                              "textTransform": "uppercase", "fontFamily": FONT,
                              "margin": "0 0 2px 0"}),
                html.P(f"~${offset:,.0f}",
                       style={"color": AMBER, "fontSize": "20px", "fontWeight": "700",
                              "fontFamily": "'Rajdhani', sans-serif",
                              "margin": "0 0 2px 0", "lineHeight": "1"}),
                html.P("at $20/tonne — voluntary carbon market rate",
                       style={"color": MUTED, "fontSize": "7px",
                              "fontFamily": FONT, "margin": "0"}),
            ], style={"flex": "1", "padding": "10px 14px",
                      "borderRight": f"1px solid {BDR}"}),
            html.Div([
                html.P("vs. flying commercial",
                       style={"color": MUTED, "fontSize": "7px", "letterSpacing": "1px",
                              "textTransform": "uppercase", "fontFamily": FONT,
                              "margin": "0 0 2px 0"}),
                html.P(f"~{equiv} seats",
                       style={"color": BODY, "fontSize": "20px", "fontWeight": "700",
                              "fontFamily": "'Rajdhani', sans-serif",
                              "margin": "0 0 2px 0", "lineHeight": "1"}),
                html.P("economy passengers would produce the same emissions",
                       style={"color": MUTED, "fontSize": "7px",
                              "fontFamily": FONT, "margin": "0"}),
            ], style={"flex": "1", "padding": "10px 14px"}),
        ], style={"display": "flex"}),
    ], style={"backgroundColor": CARD, "border": f"1px solid {BDR}",
              "borderRadius": "4px", "padding": "14px 16px"})

    # ── Recommendation block ──────────────────────────────────────────────────
    best_val = min(entries, key=lambda e: (e["charter_rev"] or 9e9) / max(dnm, 1))
    best_rng = max(entries, key=lambda e: e["ac"].get("range_nm", 0) - dnm)
    best_cab = max(entries, key=lambda e: e["ac"]["seats"])

    def _rec_block(accent, tag, name, detail):
        return html.Div([
            html.P(tag,  style={"color": accent, "fontSize": "7px", "letterSpacing": "1.5px",
                                "textTransform": "uppercase", "fontFamily": FONT,
                                "margin": "0 0 4px 0"}),
            html.P(name, style={"color": WHITE, "fontSize": "10px", "fontWeight": "700",
                                "fontFamily": FONT, "margin": "0 0 2px 0"}),
            html.P(detail, style={"color": BODY, "fontSize": "8px",
                                  "fontFamily": FONT, "margin": "0"}),
        ], style={"flex": "1", "padding": "12px 16px",
                  "backgroundColor": BG, "borderLeft": f"3px solid {accent}",
                  "borderRadius": "3px"})

    rec = html.Div([
        html.Div([
            html.Span("◈ ", style={"color": AMBER, "fontSize": "13px"}),
            html.Span("FlightOps Charter Recommendation",
                      style={"color": WHITE, "fontSize": "12px",
                             "fontWeight": "700", "fontFamily": FONT}),
        ], style={"marginBottom": "12px"}),
        html.Div([
            _rec_block(
                AMBER, "Best Value",
                best_val["name"],
                f"${(best_val['charter_rev'] or 0)/dnm:.1f}/nm · "
                f"${best_val['charter_rev']:,.0f} total",
            ),
            _rec_block(
                TEAL, "Most Range to Spare",
                best_rng["name"],
                f"{best_rng['ac'].get('range_nm',0)-dnm:,} nm left after the route. "
                f"Safest nonstop option.",
            ),
            _rec_block(
                PURPLE, "Largest Cabin",
                best_cab["name"],
                f"{best_cab['ac']['seats']} seats · "
                f"most space & flexibility for your party",
            ),
        ], style={"display": "flex", "gap": "8px", "flexWrap": "wrap"}),
        html.P(
            "⚠ Prices shown are estimates. Actual quotes depend on availability, "
            "positioning costs, catering, and seasonal demand. "
            "Always request a formal quote from a licensed charter broker before booking.",
            style={"color": MUTED, "fontSize": "7px", "fontFamily": FONT,
                   "lineHeight": "1.5", "margin": "14px 0 0 0"},
        ),
    ], style={
        "backgroundColor": CARD, "border": f"1px solid {BDR}",
        "borderLeft": f"3px solid {AMBER}", "borderRadius": "4px",
        "padding": "16px 18px",
    })

    # ── Route map ─────────────────────────────────────────────────────────────
    mid_lat = (oa["lat"] + da["lat"]) / 2
    mid_lon = (oa["lon"] + da["lon"]) / 2
    fmap = folium.Map(
        location=[mid_lat, mid_lon], zoom_start=3,
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB", prefer_canvas=True,
    )
    # Range circles from origin — drawn as geodesic PolyLines so they
    # render correctly at any distance (folium.Circle fails above ~5000 nm)
    for i, e in enumerate(entries):
        rng_km = e["ac"].get("range_nm", 0) * 1.852  # nm → km
        if rng_km > 0:
            circle_pts = _range_circle_pts(oa["lat"], oa["lon"], rng_km)
            for seg in _split_antimeridian(circle_pts):
                folium.PolyLine(
                    seg, color=RANK_C[i],
                    weight=2, opacity=0.65, dash_array="8,5",
                    tooltip=f"{e['name']}: {e['ac'].get('range_nm',0):,} nm max range",
                ).add_to(fmap)
    # Route line (split at antimeridian to avoid horizontal map artefacts)
    for seg in _split_antimeridian(W_r["waypoints"]):
        folium.PolyLine(seg, color=AMBER, weight=2.5, opacity=0.9).add_to(fmap)
    for code_ap, ap in [(origin, oa), (dest, da)]:
        folium.CircleMarker(
            location=[ap["lat"], ap["lon"]], radius=6,
            color=AMBER, fill=True, fill_color=AMBER, fill_opacity=1.0,
            tooltip=ap["name"] + " (" + code_ap + ")",
        ).add_to(fmap)

    globe = html.Div([
        _sec("ROUTE MAP"),
        html.Iframe(srcDoc=fmap._repr_html_(),
                    style={"width": "100%", "height": "300px",
                           "border": f"1px solid {BDR}", "borderRadius": "4px"}),
    ])

    return html.Div([
        banner,
        jet_cards,
        econ_table,
        range_panel,
        profile_panel,
        co2_panel,
        rec,
        globe,
    ], style={"display": "flex", "flexDirection": "column", "gap": "12px",
              "padding": "20px 24px"})


# ── Main analysis ─────────────────────────────────────────────────────────────
@app.callback(
    Output("az-main", "children"),
    Input("az-btn",          "n_clicks"),
    State("az-origin",       "value"),
    State("az-dest",         "value"),
    State("selected-comm",   "data"),
    State("selected-priv",   "data"),
    State("az-payload",      "value"),
    State("az-fuel",         "value"),
    State("az-lf",           "value"),
    State("az-tm",           "value"),
    prevent_initial_call=True,
)
def run_analysis(n, origin, dest, comm_sel, priv_sel,
                 payload, fuel_price, lf, ticket_mult):
    if not origin or not dest or origin == dest:
        return html.P("Select different origin and destination.",
                      style={"color": RED, "padding": "20px", "fontFamily": FONT})

    selected = (list(comm_sel or []) + list(priv_sel or []))[:4]
    if not selected:
        return html.Div([
            html.P("No aircraft selected",
                   style={"color": LIGHT, "fontSize": "14px", "fontWeight": "700",
                          "fontFamily": FONT, "margin": "0 0 8px 0"}),
            html.P("Select at least one aircraft from the sidebar before clicking Analyze Route.",
                   style={"color": MUTED, "fontSize": "10px", "fontFamily": FONT,
                          "margin": "0"}),
        ], style={"backgroundColor": CARD, "border": f"1px solid {BDR}",
                  "borderRadius": "4px", "padding": "40px", "textAlign": "center",
                  "marginTop": "40px"})

    oa, da = AIRPORTS[origin], AIRPORTS[dest]

    # ── Run engine ────────────────────────────────────────────────────────────
    entries = []
    for name in selected:
        try:
            r = analyze_route(origin, dest, name, payload, fuel_price, lf, ticket_mult)
        except Exception:
            continue
        ac      = AIRCRAFT[name]
        is_priv = ac.get("category") == "private"
        is_free = r.get("is_freighter", False)

        if is_priv:
            # Charter economics — ticket/seat model doesn't apply to private jets
            cost_hr_rate   = ac.get("cost_hr", 10000)
            flt_hr         = r.get("flight_time_hr", 1)
            charter_cost   = cost_hr_rate * flt_hr          # operator cost
            charter_rev    = charter_cost * 1.38            # typical charter markup ~38%
            charter_profit = charter_rev - charter_cost
            charter_margin = 27.5                           # fixed charter margin ~27.5%
            fuel_c         = r.get("fuel_cost", 0)
            dist_nm        = r["distance_km"] * 0.539957 or 1
            cost_per_nm    = charter_cost / dist_nm
            casm = rasm = 0.0
            margin  = charter_margin
            profit  = charter_profit
            co2pax  = round(r["co2_kg"], 1)                # total CO2, not per pax
        else:
            cost_hr_rate = charter_cost = charter_rev = charter_profit = cost_per_nm = None
            casm    = r.get("casm_cents")    or 0.0
            rasm    = r.get("rasm_cents")    or 0.0
            margin  = r.get("op_margin_pct") or 0.0
            profit  = r.get("op_profit")     or 0.0
            co2pax  = (round(r["co2_kg"] / r["passengers"], 1)
                       if not is_free and r.get("passengers", 0) > 0 else 0)

        v = compute_viability_score(r)
        entries.append({
            "name": name, "result": r, "ac": ac,
            "is_free": is_free, "is_priv": is_priv,
            "casm": casm, "rasm": rasm, "margin": margin,
            "profit": profit, "co2pax": co2pax,
            "score": v.get("total_score") or 0,
            "verdict": v.get("verdict", "N/A"),
            "viability": v,
            # private jet extras
            "cost_hr_rate":   cost_hr_rate,
            "charter_cost":   charter_cost,
            "charter_rev":    charter_rev,
            "cost_per_nm":    cost_per_nm,
        })

    if not entries:
        return html.P("No results — check inputs.",
                      style={"color": RED, "padding": "20px", "fontFamily": FONT})

    entries.sort(key=lambda x: (
        -x["score"],
        -x["profit"],
        x["casm"]   if x["casm"]   else 999,
        x["co2pax"] if x["co2pax"] else 999,
        x["name"],
    ))
    # Assign unique float display scores so no two circles show the same number
    _max_p = max((abs(e["profit"]) for e in entries), default=1) or 1
    for _e in entries:
        _bonus = (_e["profit"] / _max_p) * 0.9
        _e["display_score"] = round(_e["score"] + _bonus, 1)
    # If still tied after rounding, add a tiny positional increment
    for _i in range(1, len(entries)):
        if entries[_i]["display_score"] >= entries[_i-1]["display_score"]:
            entries[_i]["display_score"] = round(entries[_i-1]["display_score"] - 0.1, 1)

    W  = entries[0]
    r0 = W["result"]
    dk = r0["distance_km"]
    dnm  = round(dk * 0.539957)
    haul = ("Long Haul" if dk > 5000 else "Medium Haul" if dk > 2000 else "Short Haul")
    region = "Transatlantic" if dk > 5000 else ("Long-haul" if dk > 3000 else "Medium-haul")

    if all(e["is_priv"] for e in entries):
        return _private_jet_layout(entries, origin, dest, oa, da, dk, dnm, haul, region)

    # ── Route banner (border-left 3px teal) ───────────────────────────────────
    banner = html.Div([
        html.Div([
            html.H2(
                f"{oa['name']} ({origin}) → {da['name']} ({dest})",
                style={"color": WHITE, "fontSize": "15px", "fontWeight": "800",
                       "fontFamily": FONT, "margin": "0 0 4px 0"},
            ),
            html.P(
                f"{region} · {haul} · {dk:,.1f} KM · {r0['flight_time_hr']:.2f}H EST.",
                style={"color": MUTED, "fontSize": "8px", "letterSpacing": "1.5px",
                       "textTransform": "uppercase", "fontFamily": FONT, "margin": "0"},
            ),
        ], style={"flex": "1"}),
        html.Div([
            html.Div([
                html.Span(f"{dnm:,} nm",
                          style={"backgroundColor": BDR2, "color": LIGHT, "borderRadius": "20px",
                                 "padding": "3px 10px", "fontSize": "8px",
                                 "fontFamily": FONT, "marginRight": "6px"}),
                html.Span(
                    [
                        f"Viability {W['score']}/100",
                        html.Span(" ⓘ", title=(
                            "Viability Score (0–100)\n"
                            "Financial 40pt — operating margin, RASM/CASM spread, profit per pax\n"
                            "Operational 25pt — fuel headroom, aerodynamic efficiency (L/D), break-even LF\n"
                            "ESG 20pt — CO₂/pax vs IATA distance-band benchmarks\n"
                            "Market fit 15pt — aircraft type vs route distance category"
                        ), style={"cursor": "help", "color": TEAL,
                                  "fontSize": "9px", "fontWeight": "700"}),
                    ],
                    style={"backgroundColor": f"{TEAL}20", "color": TEAL,
                           "border": f"1px solid {TEAL}50", "borderRadius": "20px",
                           "padding": "3px 10px", "fontSize": "8px", "fontFamily": FONT,
                           "display": "inline-flex", "alignItems": "center", "gap": "2px"}
                ),
            ], style={"display": "flex", "alignItems": "center"}),
            html.P(
                "40pt Financial · 25pt Operational · 20pt ESG · 15pt Market fit",
                style={"color": MUTED, "fontSize": "6px", "fontFamily": FONT,
                       "margin": "4px 0 0 0", "textAlign": "right", "letterSpacing": "0.4px"},
            ),
        ], style={"display": "flex", "flexDirection": "column", "alignItems": "flex-end"}),
    ], style={
        "backgroundColor": CARD, "border": f"1px solid {BDR}",
        "borderLeft": "3px solid " + TEAL, "borderRadius": "4px",
        "padding": "14px 18px", "display": "flex",
        "justifyContent": "space-between", "alignItems": "center",
    })

    # ── Aircraft score cards ──────────────────────────────────────────────────
    def _score_card(idx: int, d: dict) -> html.Div:
        col   = RANK_C[idx]
        r     = d["result"]
        is_pv = d.get("is_priv", False)
        cat   = "Private Charter" if is_pv else _ac_type(d["name"], d["ac"])
        seats = d["ac"]["seats"]
        sub   = f"Private · {seats} seats" if is_pv else f"{cat} · {seats} pax"

        if is_pv:
            stats = [
                _mini("Cost/hr",       f"${d['cost_hr_rate']:,}"              if d['cost_hr_rate'] else "—", AMBER),
                _mini("Charter est.",  f"${d['charter_rev']:,.0f}"            if d['charter_rev']  else "—", TEAL),
                _mini("Fuel burn",     f"{r['fuel_burned_kg']:,.0f} kg",                                      BODY),
                _mini("Range",         f"{d['ac'].get('range_nm', 0):,} nm",                                  LIGHT),
            ]
        else:
            stats = [
                _mini("CASM",      f"{d['casm']:.2f}¢"     if not d["is_free"] else "—", AMBER),
                _mini("Op.Margin", f"{d['margin']:.1f}%"   if not d["is_free"] else "—",
                      TEAL if d["margin"] > 0 else RED),
                _mini("CO₂/pax",   f"{d['co2pax']:.0f} kg" if not d["is_free"] else "—", BODY),
                _mini("RASM",      f"{d['rasm']:.2f}¢"     if not d["is_free"] else "—", TEAL),
            ]

        return html.Div([
            html.Span(RANK_B[idx], style={
                "backgroundColor": f"{col}20", "color": col,
                "border": f"1px solid {col}60", "borderRadius": "20px",
                "padding": "2px 8px", "fontSize": "7px", "fontWeight": "700",
                "fontFamily": FONT, "display": "inline-block", "marginBottom": "8px",
            }),
            html.P(d["name"],
                   style={"color": WHITE, "fontSize": "10px", "fontWeight": "800",
                          "fontFamily": FONT, "margin": "0 0 2px 0", "lineHeight": "1.2"}),
            html.P(sub, style={"color": MUTED, "fontSize": "7px", "fontFamily": FONT,
                               "margin": "0 0 10px 0"}),
            html.Div(score_circle(d["display_score"], col, 72),
                     style={"margin": "0 auto 10px auto", "width": "72px"}),
            html.Div(stats, style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                                   "gap": "4px"}),
        ], style={
            "backgroundColor": CARD, "border": f"1px solid {col}30",
            "borderTop": f"2px solid {col}", "borderRadius": "4px",
            "padding": "14px 12px", "flex": "1", "minWidth": "160px",
        })

    score_cards = html.Div(
        [_score_card(i, d) for i, d in enumerate(entries)],
        style={"display": "grid",
               "gridTemplateColumns": f"repeat({len(entries)}, 1fr)",
               "gap": "10px"},
    )

    # ── Comparative metrics (collapsible, default closed) ─────────────────────
    metric_defs = [
        ("Op. Profit",    [f"${d['profit']:,}"           if not d["is_free"] else "—" for d in entries], True),
        ("Fuel Burn kg",  [f"{d['result']['fuel_burned_kg']:,.0f}"                    for d in entries], False),
        ("CO₂/pax kg",    [f"{d['co2pax']:.0f}"          if not d["is_free"] else "—" for d in entries], False),
        ("CASM ¢",        [f"{d['casm']:.2f}"             if not d["is_free"] else "—" for d in entries], False),
        ("RASM ¢",        [f"{d['rasm']:.2f}"             if not d["is_free"] else "—" for d in entries], True),
        ("Break-even LF", [f"{d['result'].get('breakeven_lf', '—')}%"
                           if d["result"].get("breakeven_lf") else "—"                for d in entries], False),
        ("L/D Ratio",     [str(d["result"]["LD_ratio"])                               for d in entries], True),
    ]

    def _winner_idx(vals, higher):
        try:
            nums = [float(str(v).replace("$","").replace(",","").replace("%","").replace("¢",""))
                    for v in vals if v != "—"]
            if not nums: return None
            target = max(nums) if higher else min(nums)
            flat = [float(str(v).replace("$","").replace(",","").replace("%","").replace("¢",""))
                    if v != "—" else None for v in vals]
            return next(i for i, x in enumerate(flat) if x == target)
        except Exception:
            return None

    def _cmp_row(metric, vals, hib):
        bi = _winner_idx(vals, hib)
        cells = [html.Td(metric, style={"color": BODY, "fontSize": "8px",
                                        "fontFamily": FONT, "padding": "5px 8px",
                                        "borderBottom": f"1px solid {BDR}",
                                        "whiteSpace": "nowrap"})]
        for i, v in enumerate(vals):
            ib = bi == i
            cells.append(html.Td([
                v,
                html.Span("W", style={
                    "backgroundColor": f"{RANK_C[i]}20", "color": RANK_C[i],
                    "border": f"1px solid {RANK_C[i]}60",
                    "borderRadius": "3px", "padding": "1px 4px",
                    "fontSize": "6px", "marginLeft": "4px", "fontFamily": FONT,
                }) if ib else "",
            ], style={"color": RANK_C[i] if ib else LIGHT,
                      "fontSize": "8px", "fontFamily": FONT,
                      "fontWeight": "700" if ib else "400",
                      "padding": "5px 8px",
                      "borderBottom": f"1px solid {BDR}"}))
        wn = " ".join(entries[bi]["name"].split()[1:]) if bi is not None else "—"
        cells.append(html.Td(wn,
                             style={"color": RANK_C[bi] if bi is not None else MUTED,
                                    "fontSize": "7px", "fontFamily": FONT,
                                    "padding": "5px 8px",
                                    "borderBottom": f"1px solid {BDR}"}))
        return html.Tr(cells)

    hdr_cells = [html.Th("Metric", style={"color": MUTED, "fontSize": "7px",
                                           "fontFamily": FONT, "padding": "6px 8px",
                                           "textTransform": "uppercase",
                                           "letterSpacing": "1px"})]
    for i, d in enumerate(entries):
        hdr_cells.append(html.Th(" ".join(d["name"].split()[1:]),
                                 style={"color": RANK_C[i], "fontSize": "7px",
                                        "fontFamily": FONT, "padding": "6px 8px"}))
    hdr_cells.append(html.Th("Best", style={"color": MUTED, "fontSize": "7px",
                                             "fontFamily": FONT, "padding": "6px 8px"}))

    comp = html.Div([
        html.Div("▶  COMPARATIVE METRICS — TECHNICAL ANALYSIS",
                 id="comp-toggle", style={
                     "color": MUTED, "fontSize": "8px", "letterSpacing": "2px",
                     "textTransform": "uppercase", "fontFamily": FONT,
                     "cursor": "pointer", "padding": "10px 14px",
                     "backgroundColor": CARD, "border": f"1px solid {BDR}",
                     "borderRadius": "4px", "userSelect": "none",
                 }),
        html.Div(
            html.Table([
                html.Thead(html.Tr(hdr_cells)),
                html.Tbody([_cmp_row(m, v, h) for m, v, h in metric_defs]),
            ], style={"width": "100%", "borderCollapse": "collapse"}),
            id="comp-body",
            style={"display": "none", "backgroundColor": CARD,
                   "border": f"1px solid {BDR}", "borderTop": "none",
                   "borderRadius": "0 0 4px 4px", "overflow": "hidden"},
        ),
    ])

    # ── FlightOps Suite Recommendation block ──────────────────────────────────
    wv     = W["viability"]
    vc     = wv.get("verdict_color", TEAL)
    vscore = W["score"]
    verd   = wv.get("verdict", "—")
    expl   = wv.get("explanation", "")

    advs, trds = [], []
    if W["margin"] > 30:
        advs.append(f"Strong operating margin ({W['margin']:.1f}%)")
    if W["casm"] > 0 and W["rasm"] > 0 and W["rasm"] / W["casm"] > 1.3:
        advs.append(f"Favourable RASM/CASM ratio ({W['rasm']/W['casm']:.2f}×)")
    if r0.get("LD_ratio", 0) > 17:
        advs.append(f"High aerodynamic efficiency (L/D {r0['LD_ratio']})")
    if r0.get("breakeven_lf") and r0["breakeven_lf"] < 55:
        advs.append(f"Low break-even load factor ({r0['breakeven_lf']:.1f}%)")
    if W["co2pax"] > 200:
        trds.append(f"CO₂/pax above IATA benchmark ({W['co2pax']:.0f} kg)")
    if 0 < W["margin"] < 20 and not W["is_free"]:
        trds.append(f"Thin operating margin ({W['margin']:.1f}%)")
    if not advs:
        advs.append("Competitive unit economics for route profile")

    def _dot(text, color):
        return html.Div([
            html.Span("·", style={"color": color, "marginRight": "6px",
                                  "fontWeight": "700", "fontSize": "12px"}),
            html.Span(text, style={"color": BODY, "fontSize": "8px", "fontFamily": FONT}),
        ], style={"display": "flex", "alignItems": "baseline", "marginBottom": "4px"})

    rec = html.Div([
        html.Div([
            html.Span("◈ ", style={"color": TEAL, "fontSize": "13px"}),
            html.Span(f"FlightOps Suite Recommendation — {W['name']}",
                      style={"color": WHITE, "fontSize": "12px", "fontWeight": "700",
                             "fontFamily": FONT}),
        ], style={"marginBottom": "4px"}),
        html.P(f"Viability Score {vscore}/100 · Verdict: {verd} · Confidence {vscore}%",
               style={"color": MUTED, "fontSize": "8px",
                      "fontFamily": FONT, "margin": "0 0 14px 0"}),
        html.Div([
            # Left — advantages + trade-offs
            html.Div([
                html.P("Advantages",
                       style={"color": TEAL, "fontSize": "7px", "letterSpacing": "1.5px",
                              "textTransform": "uppercase", "fontFamily": FONT,
                              "margin": "0 0 6px 0"}),
                *[_dot(a, TEAL) for a in advs],
                html.P("Trade-offs",
                       style={"color": AMBER, "fontSize": "7px", "letterSpacing": "1.5px",
                              "textTransform": "uppercase", "fontFamily": FONT,
                              "margin": "10px 0 6px 0"}),
                *([_dot(t, AMBER) for t in trds]
                  if trds else [_dot("No major trade-offs identified", MUTED)]),
            ], style={"flex": "1", "paddingRight": "20px"}),
            # Right — confidence circle + weights
            html.Div([
                score_circle(vscore, vc, 70),
                html.P("40pt Financial / 25pt Operational",
                       style={"color": MUTED, "fontSize": "7px", "fontFamily": FONT,
                              "margin": "6px 0 2px 0", "textAlign": "center"}),
                html.P("20pt ESG / 15pt Market",
                       style={"color": MUTED, "fontSize": "7px", "fontFamily": FONT,
                              "margin": "0", "textAlign": "center"}),
            ], style={"width": "90px", "flexShrink": "0", "display": "flex",
                      "flexDirection": "column", "alignItems": "center"}),
        ], style={"display": "flex", "alignItems": "flex-start"}),
    ], style={
        "backgroundColor": CARD, "border": f"1px solid {BDR}",
        "borderLeft": f"3px solid {TEAL}", "borderRadius": "4px",
        "padding": "16px 18px",
    })

    # ── Economic Analysis ─────────────────────────────────────────────────────
    fuel_c  = r0.get("fuel_cost", 0)
    tot_opx = r0.get("total_opex") or max(fuel_c, 1)
    revenue = r0.get("revenue", 0)
    op_prof = r0.get("op_profit", 0)
    margin  = r0.get("op_margin_pct", 0)
    casm    = r0.get("casm_cents", 0) or 0
    rasm    = r0.get("rasm_cents",  0) or 0
    belf    = r0.get("breakeven_lf")
    fhr     = r0.get("flight_time_hr", 1)
    sw      = W["ac"]["seats"]
    cabin   = max(4, sw // 50) if sw > 0 else 0
    crew_c  = min((450 + 280 + 2*250 + cabin*120) * fhr, tot_opx * 0.30)
    maint_c = tot_opx * 0.17
    airp_c  = tot_opx * 0.14
    other_c = max(0.0, tot_opx - fuel_c - crew_c - maint_c - airp_c)
    prof_col = TEAL if op_prof >= 0 else RED

    # ── Real Net Profit — additional fixed costs not in CASM model ────────────
    ac_name   = W["name"]
    is_priv   = W["ac"].get("category") == "private"
    leasing_c = _LEASING.get(ac_name, 8000 if sw < 150 else 18000)
    overhead_c= _OVERHEAD.get(ac_name, 6000 if sw < 150 else 12000)
    insure_c  = _INSURANCE.get(ac_name, 2000 if sw < 150 else 4000)
    # Air navigation: Eurocontrol/oceanic charges scale with distance & haul
    if dk > 5000:
        nav_c = 12000
    elif dk > 2000:
        nav_c = 6000
    else:
        nav_c = 3000
    # EU ETS surcharge (only when both airports are in EU ETS scheme)
    co2_tonnes = r0.get("co2_tonnes", 0)
    ets_c = (co2_tonnes * _ETS_EUR_PER_TONNE * _EUR_USD
             if origin in _EU_ETS_CODES and dest in _EU_ETS_CODES else 0)
    # Private jets already priced via cost/hr — skip leasing/overhead/insurance
    if is_priv:
        extra_total = nav_c + ets_c
    else:
        extra_total = leasing_c + nav_c + overhead_c + insure_c + ets_c
    real_net   = op_prof - extra_total
    real_col   = TEAL if real_net >= 0 else RED
    extra_items = [
        ("Aircraft leasing",      leasing_c  if not is_priv else None),
        ("Air navigation / ATC",  nav_c),
        ("Corporate overhead",    overhead_c if not is_priv else None),
        ("Insurance",             insure_c   if not is_priv else None),
        ("EU ETS carbon cost",    ets_c      if ets_c > 0 else None),
    ]
    extra_items = [(lbl, val) for lbl, val in extra_items if val]

    # Cost donut
    donut_fig = go.Figure(go.Pie(
        labels=["Fuel", "Crew", "Maintenance", "Airport / ATC", "Other"],
        values=[fuel_c, crew_c, maint_c, airp_c, other_c],
        hole=0.60, sort=False,
        marker=dict(colors=[TEAL, PURPLE, AMBER, MUTED, DIM],
                    line=dict(color=CARD, width=2)),
        textinfo="label+percent",
        textfont=dict(size=9, color=WHITE, family=FONT),
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f} (%{percent})<extra></extra>",
    ))
    donut_fig.update_layout(
        showlegend=False,
        annotations=[dict(text=f"${tot_opx:,.0f}<br><span style='font-size:8px'>total cost</span>",
                          x=0.5, y=0.5, showarrow=False,
                          font=dict(size=11, color=WHITE, family=FONT))],
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10), height=200,
        font=dict(family=FONT),
    )

    # Revenue vs Cost bar
    rev_cost_fig = go.Figure()
    rev_cost_fig.add_trace(go.Bar(
        name="Revenue", x=["Revenue"], y=[revenue],
        marker_color=TEAL, text=[f"${revenue:,.0f}"],
        textposition="outside", textfont=dict(size=9, color=TEAL, family=FONT),
    ))
    rev_cost_fig.add_trace(go.Bar(
        name="Total Cost", x=["Total Cost"], y=[tot_opx],
        marker_color=AMBER, text=[f"${tot_opx:,.0f}"],
        textposition="outside", textfont=dict(size=9, color=AMBER, family=FONT),
    ))
    rev_cost_fig.add_trace(go.Bar(
        name="Net Profit", x=["Net Profit"], y=[max(op_prof, 0)],
        base=[min(op_prof, 0)] if op_prof < 0 else [0],
        marker_color=prof_col, text=[f"${op_prof:,.0f}"],
        textposition="outside", textfont=dict(size=9, color=prof_col, family=FONT),
    ))
    rev_cost_fig.update_layout(
        barmode="group", showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10), height=200,
        xaxis=dict(tickfont=dict(size=9, color=BODY, family=FONT), showgrid=False),
        yaxis=dict(visible=False, showgrid=False),
        bargap=0.3,
        font=dict(family=FONT),
    )

    # KPI grid
    def _kpi(lbl, val, color=LIGHT, sub=""):
        return html.Div([
            html.P(lbl, style={"color": MUTED, "fontSize": "7px", "letterSpacing": "1px",
                               "textTransform": "uppercase", "fontFamily": FONT,
                               "margin": "0 0 2px 0"}),
            html.P(val, style={"color": color, "fontSize": "13px", "fontWeight": "700",
                               "fontFamily": FONT, "margin": "0 0 1px 0", "lineHeight": "1"}),
            html.P(sub, style={"color": MUTED, "fontSize": "7px", "fontFamily": FONT, "margin": "0"}),
        ], style={"flex": "1", "padding": "10px 12px",
                  "borderRight": f"1px solid {BDR}", "minWidth": "80px"})

    kpi_row = html.Div([
        _kpi("RASM",         f"{rasm:.2f}¢",    TEAL,     "revenue / seat-mile"),
        _kpi("CASM",         f"{casm:.2f}¢",    AMBER,    "cost / seat-mile"),
        _kpi("Op. Margin",   f"{margin:.1f}%",  prof_col, "net profit / revenue"),
        _kpi("Break-even LF",f"{belf:.1f}%"     if belf else "—", LIGHT, "min load factor"),
        html.Div([
            html.P("CO₂ / pax", style={"color": MUTED, "fontSize": "7px", "letterSpacing": "1px",
                                       "textTransform": "uppercase", "fontFamily": FONT,
                                       "margin": "0 0 2px 0"}),
            html.P(f"{W['co2pax']:.0f} kg" if W["co2pax"] else "—",
                   style={"color": LIGHT, "fontSize": "13px", "fontWeight": "700",
                          "fontFamily": FONT, "margin": "0 0 1px 0", "lineHeight": "1"}),
            html.P("per passenger", style={"color": MUTED, "fontSize": "7px",
                                           "fontFamily": FONT, "margin": "0"}),
        ], style={"flex": "1", "padding": "10px 12px", "minWidth": "80px"}),
    ], style={"display": "flex", "borderTop": f"1px solid {BDR}", "flexWrap": "wrap"})

    # Real Net Profit side-by-side block
    def _profit_box(label, value, color, sub=""):
        return html.Div([
            html.P(label, style={"color": MUTED, "fontSize": "7px", "letterSpacing": "1px",
                                 "textTransform": "uppercase", "fontFamily": FONT,
                                 "margin": "0 0 4px 0"}),
            html.P(f"${value:,.0f}", style={"color": color, "fontSize": "18px",
                                             "fontWeight": "700", "fontFamily": FONT,
                                             "margin": "0 0 4px 0", "lineHeight": "1"}),
            html.P(sub, style={"color": MUTED, "fontSize": "7px",
                               "fontFamily": FONT, "margin": "0"}),
        ], style={"flex": "1", "padding": "14px 16px", "textAlign": "center",
                  "backgroundColor": BG, "borderRadius": "4px",
                  "border": f"1px solid {color}30"})

    extra_rows = [
        html.Div([
            html.Span(lbl, style={"color": BODY, "fontSize": "8px", "fontFamily": FONT}),
            html.Span(f"−${val:,.0f}", style={"color": MUTED, "fontSize": "8px",
                                               "fontFamily": FONT, "fontWeight": "600"}),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "padding": "3px 0", "borderBottom": f"1px solid {BDR}"})
        for lbl, val in extra_items
    ]

    real_net_block = html.Div([
        html.Div(style={"height": "1px", "backgroundColor": BDR, "margin": "14px 0 12px 0"}),
        _sec("CONTRIBUTION MARGIN vs REAL NET PROFIT"),
        html.Div([
            _profit_box("Contribution Margin",
                        op_prof, TEAL,
                        "fuel + direct ops costs only"),
            html.Div("→", style={"color": DIM, "fontSize": "18px", "alignSelf": "center",
                                 "padding": "0 8px"}),
            _profit_box("Real Net Profit (est.)",
                        real_net, real_col,
                        "after leasing · nav · overhead · insurance"),
        ], style={"display": "flex", "alignItems": "stretch", "gap": "8px",
                  "marginBottom": "12px"}),
        html.Div([
            html.P("Deductions applied:", style={"color": MUTED, "fontSize": "7px",
                                                  "letterSpacing": "1px", "textTransform": "uppercase",
                                                  "fontFamily": FONT, "margin": "0 0 6px 0"}),
            *extra_rows,
            html.Div([
                html.Span("Total additional costs", style={"color": BODY, "fontSize": "8px",
                                                            "fontFamily": FONT, "fontWeight": "600"}),
                html.Span(f"−${extra_total:,.0f}", style={"color": AMBER, "fontSize": "9px",
                                                           "fontFamily": FONT, "fontWeight": "700"}),
            ], style={"display": "flex", "justifyContent": "space-between", "padding": "5px 0"}),
        ], style={"backgroundColor": BG, "borderRadius": "4px",
                  "border": f"1px solid {BDR}", "padding": "10px 14px",
                  "marginBottom": "8px"}),
        html.P(
            "⚠ Estimates based on published airline cost benchmarks (IATA, Boeing Cost Analysis). "
            "Leasing rates vary by contract, operator, and aircraft age. "
            "EU ETS applied when both airports are within the European Emissions Trading Scheme. "
            "Use for directional analysis only — not a substitute for actual airline accounting.",
            style={"color": MUTED, "fontSize": "7px", "fontFamily": FONT,
                   "lineHeight": "1.5", "margin": "0"},
        ),
    ])

    econ_panel = html.Div([
        _sec("ECONOMIC ANALYSIS"),
        html.Div([
            html.Div([
                html.P("Cost structure", style={"color": MUTED, "fontSize": "7px",
                                                "letterSpacing": "1px", "textTransform": "uppercase",
                                                "fontFamily": FONT, "margin": "0 0 4px 0"}),
                dcc.Graph(figure=donut_fig, config={"displayModeBar": False}),
            ], style={"flex": "1"}),
            html.Div([
                html.P("Revenue vs cost", style={"color": MUTED, "fontSize": "7px",
                                                  "letterSpacing": "1px", "textTransform": "uppercase",
                                                  "fontFamily": FONT, "margin": "0 0 4px 0"}),
                dcc.Graph(figure=rev_cost_fig, config={"displayModeBar": False}),
            ], style={"flex": "1"}),
        ], style={"display": "flex", "gap": "10px"}),
        kpi_row,
        real_net_block,
    ], style={"backgroundColor": CARD, "border": f"1px solid {BDR}",
              "borderRadius": "4px", "padding": "14px 16px"})

    # ── Folium route map ──────────────────────────────────────────────────────
    mid_lat = (oa["lat"] + da["lat"]) / 2
    mid_lon = (oa["lon"] + da["lon"]) / 2
    fmap = folium.Map(
        location=[mid_lat, mid_lon], zoom_start=3,
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB", prefer_canvas=True,
    )
    # Route line (split at antimeridian to avoid horizontal map artefacts)
    for seg in _split_antimeridian(r0["waypoints"]):
        folium.PolyLine(seg, color=TEAL, weight=2.5, opacity=0.9).add_to(fmap)
    for code_ap, ap in [(origin, oa), (dest, da)]:
        folium.CircleMarker(
            location=[ap["lat"], ap["lon"]], radius=6, color=TEAL,
            fill=True, fill_color=TEAL, fill_opacity=1.0,
            tooltip=ap["name"] + " (" + code_ap + ")",
        ).add_to(fmap)
    globe = html.Div([
        _sec("ROUTE MAP"),
        html.Iframe(srcDoc=fmap._repr_html_(),
                    style={"width": "100%", "height": "300px",
                           "border": f"1px solid {BDR}", "borderRadius": "4px"}),
    ])

    # ── Assemble ──────────────────────────────────────────────────────────────
    return html.Div([
        banner,
        score_cards,
        comp,
        rec,
        econ_panel,
        globe,
    ], style={"display": "flex", "flexDirection": "column", "gap": "12px",
              "padding": "20px 24px"})


# ── Collapsible metrics toggle ────────────────────────────────────────────────
@app.callback(
    Output("comp-body",  "style"),
    Input("comp-toggle", "n_clicks"),
    State("comp-body",   "style"),
    prevent_initial_call=True,
)
def toggle_comp(_, style):
    s = dict(style or {})
    s["display"] = "block" if s.get("display") == "none" else "none"
    return s


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8050)), debug=False)
