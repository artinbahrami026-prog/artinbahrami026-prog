"""Inline fonts and images into the SVG templates in src/ and write them to assets/.

GitHub serves README images through a proxy that blocks external requests from
inside SVGs, so every font and image has to be embedded as a data URI.

Placeholders:
  {{FONT:serif,mono}}  @font-face rules for the named fonts (see FONTS)
  {{IMG:file.webp}}    data URI for a file in assets/src/
  {{BARCODE}}, {{AZTEC}}  fake barcode / 2D code for the boarding pass stub
  {{W1}}..{{W4}}, {{WX}}  measured text offsets (see WIDTHS)

Run: python3 build.py
"""
import base64
import pathlib
import re

import ascii_pass

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


def aztec(x=872, y=198, n=33, size=4, seed=2008):
    """Deterministic Aztec-style 2D code: bullseye in the middle, noise around it."""
    c, rng, cells = n // 2, seed, []
    for r in range(n):
        for col in range(n):
            ring = max(abs(r - c), abs(col - c))
            if ring <= 6:
                on = ring % 2 == 0 or (ring == 6 and (r + col) % 2 == 0)
            else:
                rng = (rng * 1103515245 + 12345) % 2**31
                on = (rng >> 16) % 2 == 0
            if on:
                cells.append(f'<rect x="{x + col * size}" y="{y + r * size}" width="{size}" height="{size}"/>')
    return '<g fill="#1b1b1b">' + "".join(cells) + "</g>"


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
    svg = svg.replace("{{BARCODE}}", barcode()).replace("{{AZTEC}}", aztec())
    if "{{ASCII}}" in svg:
        cw = 9.6  # JetBrains Mono advance at 16px
        rows, done = ascii_pass.svg(x=120, y=128, line_height=22, start=2.0, step=0.07)
        svg = svg.replace("{{ASCII}}", rows)
        for key, val in {"PLANE_IN": f"{2.0 + 7 * 0.07:.2f}", "DONE": f"{done + 0.2:.2f}",
                         "PX": f"{120 + 24 * cw:.1f}", "PY1": 128 + 6 * 22, "PY2": 128 + 7 * 22,
                         "CX": f"{60 + 17 * cw:.1f}", "CW": f"{27 * cw:.1f}", "LX2": f"{60 + 32 * cw + 4:.1f}"}.items():
            svg = svg.replace("{{%s}}" % key, str(val))
    for key, val in WIDTHS.items():
        svg = svg.replace("{{%s}}" % key, str(val))
    out = OUT / tpl.relative_to(SRC)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg)
    print(f"{tpl.relative_to(SRC)}: {len(svg) / 1024:.0f} KB")
