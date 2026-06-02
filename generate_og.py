#!/usr/bin/env python3
"""
Generate FlightOps Suite OG social-preview image.
Output : assets/og_image.png  (1200 × 630)
Run    : python generate_og.py
"""

import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ── canvas ────────────────────────────────────────────────────────────────────
W, H = 1200, 630

# ── palette (FlightOps dark theme) ───────────────────────────────────────────
C_BG    = (8,  10,  15)
C_OCEAN = (10, 28,  65)
C_LAND  = (22, 65,  35)
C_LAND2 = (30, 85,  45)
C_TEAL  = (0,  212, 170)
C_WHITE = (226,232, 240)
C_LIGHT = (200,216, 232)
C_MUTED = (96, 120, 152)
C_DIM   = (45, 64,  96)

# ── globe geometry ────────────────────────────────────────────────────────────
GCX  = int(W * 0.635)   # centre-X (right 63 %)
GCY  = H // 2
GR   = int(H * 0.465)   # radius in pixels
RLON = math.radians(-20)   # view rotation: ~20° west (Atlantic centre)
RLAT = math.radians(22)    # tilt northward


# ── rotation: orthographic projection coords → geographic frame ──────────────
def _rot_arr(xn, yn, zn):
    xa =  xn * math.cos(RLON) + zn * math.sin(RLON)
    za = -xn * math.sin(RLON) + zn * math.cos(RLON)
    yb =  yn * math.cos(RLAT) - za * math.sin(RLAT)
    zb =  yn * math.sin(RLAT) + za * math.cos(RLAT)
    return xa, yb, zb          # (xa=xgeo, yb=sin(lat), atan2(xa,zb)=lon)


def geo_to_screen(lat_deg, lon_deg):
    """Return screen (px,py) for a geographic point; None if behind the globe."""
    lr, lo = math.radians(lat_deg), math.radians(lon_deg)
    xb = math.cos(lr) * math.sin(lo)
    yb = math.sin(lr)
    zb = math.cos(lr) * math.cos(lo)
    # inverse X rotation (RLAT)
    xa  =  xb
    ya  =  yb * math.cos(RLAT) + zb * math.sin(RLAT)
    za  = -yb * math.sin(RLAT) + zb * math.cos(RLAT)
    # inverse Y rotation (RLON)
    xn  =  xa * math.cos(RLON) - za * math.sin(RLON)
    yn  =  ya
    zn  =  xa * math.sin(RLON) + za * math.cos(RLON)
    if zn < 0:
        return None
    return int(GCX + xn * GR), int(GCY - yn * GR)


# ── earth texture (equirectangular 2160 × 1080) ───────────────────────────────
TW, TH = 2160, 1080
tex = np.zeros((TH, TW, 3), dtype=np.uint8)

# ocean: latitudinal depth gradient
for ty in range(TH):
    lat = 90.0 - ty * 180.0 / TH
    f   = 0.55 + 0.45 * abs(lat) / 90.0
    tex[ty] = [min(int(C_OCEAN[0] + f*10), 255),
               min(int(C_OCEAN[1] + f*25), 255),
               min(int(C_OCEAN[2] + f*45), 255)]

tex_img  = Image.fromarray(tex)
tex_draw = ImageDraw.Draw(tex_img)

LAND_POLYS = [
    # North America
    [(70,-140),(70,-60),(55,-55),(47,-53),(30,-81),(25,-80),(15,-83),(8,-77),
     (25,-78),(35,-75),(40,-73),(44,-66),(49,-55),(58,-65),(62,-63),(65,-65),
     (70,-72),(75,-85),(75,-120),(70,-140)],
    # Greenland
    [(83,-40),(83,-10),(75,-15),(72,-22),(60,-43),(65,-50),(70,-55),(80,-45),(83,-40)],
    # Iceland
    [(66,-24),(64,-13),(63,-18),(64,-22),(66,-24)],
    # Europe
    [(70,30),(70,10),(60,5),(55,-5),(50,-5),(43,-9),(36,-6),(36,5),(44,8),
     (44,15),(38,15),(40,26),(43,22),(46,13),(48,17),(52,21),(57,21),(60,22),
     (63,14),(68,16),(70,30)],
    # Scandinavia
    [(71,28),(68,14),(62,5),(58,5),(57,8),(59,10),(63,10),(65,14),(68,17),(71,28)],
    # Eurasia
    [(70,30),(70,100),(70,140),(60,140),(50,140),(45,130),(38,120),(22,114),
     (15,108),(5,103),(15,100),(22,88),(15,74),(25,67),(22,60),(15,52),(18,38),
     (22,37),(30,32),(36,36),(40,36),(38,26),(43,41),(48,60),(55,60),(65,60),
     (68,55),(70,30)],
    # Africa
    [(37,-6),(37,10),(30,32),(15,42),(10,42),(5,35),(0,40),(-5,40),(-20,35),
     (-34,26),(-34,18),(-25,15),(-5,10),(5,2),(10,-15),(20,-17),(30,-13),
     (35,-4),(37,-6)],
    # South America
    [(12,-72),(5,-52),(0,-50),(-10,-37),(-20,-40),(-30,-52),(-40,-62),(-50,-68),
     (-55,-68),(-50,-73),(-40,-73),(-30,-70),(-15,-72),(-5,-80),(5,-77),(12,-72)],
    # Australia
    [(-15,130),(-18,140),(-28,153),(-35,150),(-39,140),(-35,137),(-30,115),
     (-22,114),(-17,122),(-15,130)],
]

def _poly_px(poly):
    return [(int((lon+180)/360*TW) % TW,
             max(0, min(TH-1, int((90-lat)/180*TH)))) for lat,lon in poly]

for poly in LAND_POLYS:
    px = _poly_px(poly)
    if len(px) >= 3:
        tex_draw.polygon(px, fill=C_LAND)
        tex_draw.polygon(px, outline=C_LAND2)

tex = np.array(tex_img)


# ── sphere pixel render ───────────────────────────────────────────────────────
ys_g, xs_g = np.mgrid[0:H, 0:W]
dxg = (xs_g - GCX).astype(np.float32)
dyg = (ys_g - GCY).astype(np.float32)
r2g = dxg**2 + dyg**2
IN  = r2g <= float(GR**2)

xn_m = dxg / GR
yn_m = -dyg / GR
zn_m = np.where(IN, np.sqrt(np.maximum(0.0, 1.0 - xn_m*xn_m - yn_m*yn_m)), 0.0)

xb_m, yb_m, zb_m = _rot_arr(xn_m, yn_m, zn_m)

lat_m = np.degrees(np.arcsin(np.clip(yb_m, -1.0, 1.0)))
lon_m = np.degrees(np.arctan2(xb_m, zb_m))

tx_i = ((lon_m + 180.0) / 360.0 * TW).astype(np.int32) % TW
ty_i = np.clip(((90.0 - lat_m) / 180.0 * TH).astype(np.int32), 0, TH-1)

sr = tex[ty_i, tx_i, 0].astype(np.float32)
sg = tex[ty_i, tx_i, 1].astype(np.float32)
sb = tex[ty_i, tx_i, 2].astype(np.float32)

# 3-D lighting: key light upper-left-front
LX, LY, LZ = 0.42, 0.32, 0.85
Ln = math.sqrt(LX**2 + LY**2 + LZ**2)
lx, ly, lz = LX/Ln, LY/Ln, LZ/Ln

diffuse  = np.maximum(0.0, xb_m*lx + yb_m*ly + zb_m*lz)
specular = np.power(np.maximum(0.0, diffuse), 10) * 0.30
rim      = (np.clip(1.0 - diffuse, 0.0, 1.0)**3) * IN * 0.65
light    = 0.28 + 0.72 * diffuse + specular

sr = np.clip(sr*light + rim*20,  0, 255)
sg = np.clip(sg*light + rim*60,  0, 255)
sb = np.clip(sb*light + rim*130, 0, 255)

# ── compose base image ────────────────────────────────────────────────────────
arr = np.zeros((H, W, 3), dtype=np.uint8)
arr[:] = C_BG
arr[IN, 0] = sr[IN].astype(np.uint8)
arr[IN, 1] = sg[IN].astype(np.uint8)
arr[IN, 2] = sb[IN].astype(np.uint8)

img  = Image.fromarray(arr, "RGB").convert("RGBA")
draw = ImageDraw.Draw(img)

# atmosphere glow (soft blue halo around sphere)
glow = Image.new("RGBA", (W, H), (0,0,0,0))
gd   = ImageDraw.Draw(glow)
for i in range(22, 0, -1):
    a = int(55 * (1 - i/22))
    ra = GR + i*2
    gd.ellipse([GCX-ra, GCY-ra, GCX+ra, GCY+ra], outline=(35, 95, 210, a), width=2)
img = Image.alpha_composite(img, glow)
draw = ImageDraw.Draw(img)


# ── flight routes ─────────────────────────────────────────────────────────────
ROUTES = [
    (40.7,-74.0,  51.5,-0.1),    # NYC-London
    (40.7,-74.0,  48.9, 2.3),    # NYC-Paris
    (40.7,-74.0,  52.5,13.4),    # NYC-Berlin
    (40.7,-74.0,  35.7,139.8),   # NYC-Tokyo
    (40.7,-74.0,   1.4,103.9),   # NYC-Singapore
    (40.7,-74.0, -23.4,-46.5),   # NYC-São Paulo
    (40.7,-74.0, -33.9,151.2),   # NYC-Sydney
    (51.5,-0.1,   35.7,139.8),   # London-Tokyo
    (51.5,-0.1,   25.3, 55.4),   # London-Dubai
    (51.5,-0.1,    1.4,103.9),   # London-Singapore
    (51.5,-0.1,  -33.9,151.2),   # London-Sydney
    (51.5,-0.1,  -23.4,-46.5),   # London-São Paulo
    (48.9, 2.3,   25.3, 55.4),   # Paris-Dubai
    (48.9, 2.3,   30.1, 31.4),   # Paris-Cairo
    (48.9, 2.3,   35.7,139.8),   # Paris-Tokyo
    (33.9,-118.4, 35.7,139.8),   # LA-Tokyo
    (33.9,-118.4,  1.4,103.9),   # LA-Singapore
    (33.9,-118.4,-33.9,151.2),   # LA-Sydney
    (35.7,139.8,   1.4,103.9),   # Tokyo-Singapore
    (25.3, 55.4,   1.4,103.9),   # Dubai-Singapore
    (25.3, 55.4,  19.1, 72.9),   # Dubai-Mumbai
    (51.5,-0.1,   55.8, 37.6),   # London-Moscow
    (40.7,-74.0,  19.4,-99.1),   # NYC-Mexico City
    (48.9, 2.3,    1.4,103.9),   # Paris-Singapore
    (41.8,-87.6,  51.5,-0.1),    # Chicago-London
]

COLORS = [
    (0,  200, 160),   # teal
    (0,  200, 160),
    (130, 85, 215),   # purple
    (0,  200, 160),
    (130, 85, 215),
]

def slerp_pts(lat1,lon1,lat2,lon2, n=90):
    lr1,lo1 = math.radians(lat1),math.radians(lon1)
    lr2,lo2 = math.radians(lat2),math.radians(lon2)
    p1 = np.array([math.cos(lr1)*math.sin(lo1), math.sin(lr1), math.cos(lr1)*math.cos(lo1)])
    p2 = np.array([math.cos(lr2)*math.sin(lo2), math.sin(lr2), math.cos(lr2)*math.cos(lo2)])
    w  = math.acos(float(np.clip(np.dot(p1,p2),-1,1)))
    pts = []
    for i in range(n+1):
        t = i/n
        p = (math.sin((1-t)*w)/math.sin(w))*p1 + (math.sin(t*w)/math.sin(w))*p2 \
            if w > 1e-7 else p1.copy()
        p = p / np.linalg.norm(p)
        pts.append((math.degrees(math.asin(float(p[1]))),
                    math.degrees(math.atan2(float(p[0]),float(p[2])))))
    return pts

for idx, (lat1,lon1,lat2,lon2) in enumerate(ROUTES):
    col = COLORS[idx % len(COLORS)] + (170,)
    seg = []
    for lat_p, lon_p in slerp_pts(lat1,lon1,lat2,lon2):
        px = geo_to_screen(lat_p, lon_p)
        if px is None:
            if len(seg) >= 2:
                draw.line(seg, fill=col, width=1)
            seg = []
        else:
            seg.append(px)
    if len(seg) >= 2:
        draw.line(seg, fill=col, width=1)

# city dots
CITIES = [
    (40.7,-74.0), (51.5,-0.1), (48.9,2.3), (35.7,139.8),
    (1.4,103.9), (25.3,55.4), (-33.9,151.2), (33.9,-118.4),
    (30.1,31.4), (19.4,-99.1), (-23.4,-46.5), (55.8,37.6),
    (19.1,72.9), (41.8,-87.6), (52.5,13.4), (28.6,77.2),
]
for lat_c, lon_c in CITIES:
    px = geo_to_screen(lat_c, lon_c)
    if px:
        cx, cy = px
        draw.ellipse([cx-3, cy-3, cx+3, cy+3], fill=C_TEAL+(230,))
        draw.ellipse([cx-6, cy-6, cx+6, cy+6], outline=C_TEAL+(90,), width=1)


# ── left text panel ───────────────────────────────────────────────────────────
# subtle stars
rng = random.Random(42)
for _ in range(50):
    sx  = int(rng.uniform(8, W*0.41))
    sy  = int(rng.uniform(8, H-8))
    sr_ = rng.choice([1,1,1,2])
    a_  = int(rng.uniform(25, 90))
    draw.ellipse([sx-sr_, sy-sr_, sx+sr_, sy+sr_], fill=(180,210,255,a_))

# soft vertical divider
for y in range(15, H-15):
    a = int(55 * abs(math.sin(math.pi * y / H)))
    draw.point((int(W*0.44), y), fill=(30,52,85,a))

# fonts
try:
    f_xl   = ImageFont.truetype("C:/Windows/Fonts/ArialBd.ttf",  76)
    f_lg   = ImageFont.truetype("C:/Windows/Fonts/ArialBd.ttf",  28)
    f_md   = ImageFont.truetype("C:/Windows/Fonts/Arial.ttf",    19)
    f_sm   = ImageFont.truetype("C:/Windows/Fonts/Arial.ttf",    14)
except Exception:
    f_xl = f_lg = f_md = f_sm = ImageFont.load_default()

PAD = 48
y_eye = 148

# eyebrow
draw.text((PAD, y_eye), "AVIATION ROUTE ANALYTICS",
          font=f_sm, fill=C_TEAL+(210,))

# title  FLIGHT OPS
y_title = y_eye + 28
draw.text((PAD, y_title), "FLIGHT", font=f_xl, fill=C_WHITE+(255,))
try:
    bw = draw.textlength("FLIGHT", font=f_xl)
except AttributeError:
    bw = 268   # fallback estimate
draw.text((PAD + bw, y_title), "OPS", font=f_xl, fill=C_TEAL+(255,))

# taglines
y_tag = y_title + 90
draw.text((PAD, y_tag),       "Analyze routes.",         font=f_lg, fill=C_LIGHT+(240,))
draw.text((PAD, y_tag + 40),  "Compare aircraft.",       font=f_lg, fill=C_LIGHT+(240,))
draw.text((PAD, y_tag + 80),  "Make better decisions.",  font=f_lg, fill=C_TEAL+(230,))

# stats
y_stat = y_tag + 140
draw.text((PAD, y_stat),      "50 aircraft · 100 airports",   font=f_md, fill=C_MUTED+(200,))
draw.text((PAD, y_stat + 26), "Real physics based analysis",  font=f_md, fill=C_MUTED+(200,))


# ── save ─────────────────────────────────────────────────────────────────────
out = img.convert("RGB")
out.save("assets/og_image.png", "PNG", optimize=True)
print("OK  assets/og_image.png  (1200 x 630)")
