"""
FlightOps Suite — Multi-page Dash entry point
"""
import os
import dash
from dash import html, dcc
from components.navbar import create_navbar

# ── Generate preview.png at startup (LinkedIn / OG preview image) ────────────
def _generate_preview():
    """Creates assets/preview.png (1200×630) if it doesn't already exist."""
    out = os.path.join(os.path.dirname(__file__), "assets", "preview.png")
    if os.path.exists(out):
        return
    try:
        from PIL import Image, ImageDraw, ImageFont

        W, H = 1200, 630
        img  = Image.new("RGB", (W, H), color="#030508")
        draw = ImageDraw.Draw(img)

        # Subtle grid
        for x in range(0, W, 60):
            draw.line([(x, 0), (x, H)], fill="#0a1520", width=1)
        for y in range(0, H, 60):
            draw.line([(0, y), (W, y)], fill="#0a1520", width=1)

        # Corner brackets
        pad, sz, thick, GOLD = 40, 28, 3, "#ffd060"
        draw.line([(pad, pad),     (pad+sz, pad)],     fill=GOLD, width=thick)
        draw.line([(pad, pad),     (pad, pad+sz)],     fill=GOLD, width=thick)
        draw.line([(W-pad, pad),   (W-pad-sz, pad)],   fill=GOLD, width=thick)
        draw.line([(W-pad, pad),   (W-pad, pad+sz)],   fill=GOLD, width=thick)
        draw.line([(pad, H-pad),   (pad+sz, H-pad)],   fill=GOLD, width=thick)
        draw.line([(pad, H-pad),   (pad, H-pad-sz)],   fill=GOLD, width=thick)
        draw.line([(W-pad, H-pad), (W-pad-sz, H-pad)], fill=GOLD, width=thick)
        draw.line([(W-pad, H-pad), (W-pad, H-pad-sz)], fill=GOLD, width=thick)

        # Fonts (fall back to default on servers without Windows fonts)
        def _font(path, size):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                return ImageFont.load_default()

        fnt_title = _font("C:/Windows/Fonts/arialbd.ttf", 108)
        fnt_sub   = _font("C:/Windows/Fonts/arial.ttf",    34)
        fnt_tag   = _font("C:/Windows/Fonts/arial.ttf",    22)

        # Title — FLIGHT (white) + OPS (gold) + SUITE (white)
        title_y = 190
        parts   = [("FLIGHT", "#ffffff"), ("OPS", "#ffd060"), (" SUITE", "#ffffff")]
        widths  = [draw.textbbox((0, 0), t, font=fnt_title)[2] for t, _ in parts]
        x       = (W - sum(widths)) // 2
        for (text, color), w in zip(parts, widths):
            draw.text((x, title_y), text, font=fnt_title, fill=color)
            x += w

        # Divider
        title_h = draw.textbbox((0, 0), "FLIGHT", font=fnt_title)[3]
        div_y   = title_y + title_h + 22
        draw.line([(W//2 - 60, div_y), (W//2 + 60, div_y)], fill="#555030", width=2)

        # Subtitle
        sub = "Aircraft Route & Performance Analyzer"
        bb  = draw.textbbox((0, 0), sub, font=fnt_sub)
        draw.text(((W - (bb[2] - bb[0])) // 2, div_y + 20), sub, font=fnt_sub, fill="#00c8ff")

        # URL tag
        tag = "flightops-suite-1.onrender.com"
        bb2 = draw.textbbox((0, 0), tag, font=fnt_tag)
        draw.text(((W - (bb2[2] - bb2[0])) // 2, H - 70), tag, font=fnt_tag, fill="#2a4a65")

        os.makedirs(os.path.dirname(out), exist_ok=True)
        img.save(out, "PNG")
    except Exception as e:
        print(f"[preview] Could not generate preview.png: {e}")

_generate_preview()

# ── App ───────────────────────────────────────────────────────────────────────
_FONTS = (
    "https://fonts.googleapis.com/css2?"
    "family=Space+Grotesk:wght@300;400;500;700"
    "&family=Rajdhani:wght@700&display=swap"
)

_BASE_URL = "https://flightops-suite-1.onrender.com"

_INDEX = """<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>

    <!-- Open Graph / LinkedIn -->
    <meta property="og:type"        content="website">
    <meta property="og:title"       content="FlightOps Suite">
    <meta property="og:description" content="Aircraft Route &amp; Performance Analyzer — physics-based route analysis tool">
    <meta property="og:image"       content="{base_url}/assets/preview.png">
    <meta property="og:url"         content="{base_url}">

    <!-- Twitter card -->
    <meta name="twitter:card"        content="summary_large_image">
    <meta name="twitter:title"       content="FlightOps Suite">
    <meta name="twitter:description" content="Aircraft Route &amp; Performance Analyzer — physics-based route analysis tool">
    <meta name="twitter:image"       content="{base_url}/assets/preview.png">

    {%favicon%}
    {%css%}
</head>
<body>
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>""".replace("{base_url}", _BASE_URL)

app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[_FONTS],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    index_string=_INDEX,
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
