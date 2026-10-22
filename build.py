"""Inline fonts and images into the SVG templates in src/ and write them to assets/.

GitHub serves README images through a proxy that blocks external requests from
inside SVGs, so every font and image has to be embedded as a data URI.

Placeholders:
  {{FONT:serif,mono}}  @font-face rules for the named fonts (see FONTS)
  {{IMG:file.webp}}    data URI for a file in assets/src/
  {{BARCODE}}          a fake barcode for the boarding pass stub
  {{W1}}..{{W4}}, {{WX}}  measured text offsets (see WIDTHS)

Run: python3 build.py
"""
import base64
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
SRC, OUT, ART = ROOT / "src", ROOT / "assets", ROOT / "assets" / "src"

# name -> (family, file, style, weight range)
FONTS = {
    "nunito": ("Nunito", "nunito-latin.woff2", "normal", "200 1000"),
    "serif": ("Instrument Serif", "serif.woff2", "normal", "400"),
    "serif-italic": ("Instrument Serif", "serif-italic.woff2", "italic", "400"),
    "mono": ("JetBrains Mono", "mono.woff2", "normal", "100 800"),
    "grotesk": ("Space Grotesk", "grotesk.woff2", "normal", "300 700"),
}

# Highlighter widths under the rotating words in rumy/hero.svg (measured in a browser).
WIDTHS = {"W1": 135, "W2": 94, "W3": 224, "W4": 283, "WX": 131, "LX": 146, "SX": 208, "BX": 432}

MIME = {".webp": "image/webp", ".png": "image/png", ".woff2": "font/woff2"}


def data_uri(path):
    return f"data:{MIME[path.suffix]};base64," + base64.b64encode(path.read_bytes()).decode()


def barcode(x=868, y=292, width=214, height=96, seed=2008):
    """Deterministic fake barcode: bars of 1-4px with 1-3px gaps."""
    rng, bars, cx = seed, [], x
    while True:
        rng = (rng * 1103515245 + 12345) % 2**31
        w, gap = 1 + rng % 4, 1 + (rng >> 8) % 3
        if cx + w > x + width:
            break
        bars.append(f'<rect x="{cx}" y="{y}" width="{w}" height="{height}"/>')
        cx += w + gap
    return '<g fill="#14151c">' + "".join(bars) + "</g>"


def font_faces(names):
    rules = []
    for name in names.split(","):
        family, file, style, weight = FONTS[name.strip()]
        rules.append(
            f"@font-face {{ font-family: '{family}'; font-style: {style}; font-weight: {weight}; "
            f"src: url({data_uri(ART / file)}) format('woff2'); }}"
        )
    return "\n".join(rules)


for tpl in sorted(SRC.rglob("*.svg")):
    svg = tpl.read_text().replace("{{FONT}}", font_faces("nunito"))
    svg = re.sub(r"\{\{FONT:([^}]+)\}\}", lambda m: font_faces(m.group(1)), svg)
    svg = re.sub(r"\{\{IMG:([^}]+)\}\}", lambda m: data_uri(ART / m.group(1)), svg)
    svg = svg.replace("{{BARCODE}}", barcode())
    for key, val in WIDTHS.items():
        svg = svg.replace("{{%s}}" % key, str(val))
    out = OUT / tpl.relative_to(SRC)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg)
    print(f"{tpl.relative_to(SRC)}: {len(svg) / 1024:.0f} KB")
