"""Inline fonts and images into the SVG templates in src/ and write them to assets/.

GitHub serves README images through a proxy that blocks external requests from
inside SVGs, so every font and image has to be embedded as a data URI.
Run: python3 build.py
"""
import base64
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
SRC, OUT, ART = ROOT / "src", ROOT / "assets", ROOT / "assets" / "src"

# Highlighter widths under the rotating words in hero.svg (measured in a browser).
WIDTHS = {"W1": 135, "W2": 94, "W3": 224, "W4": 283}


def data_uri(path, mime):
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


FONT = (
    "@font-face { font-family: 'Nunito'; font-weight: 200 1000; "
    f"src: url({data_uri(ART / 'nunito-latin.woff2', 'font/woff2')}) format('woff2'); }}"
)

for tpl in sorted(SRC.glob("*.svg")):
    svg = tpl.read_text().replace("{{FONT}}", FONT)
    svg = re.sub(r"\{\{IMG:([^}]+)\}\}", lambda m: data_uri(ART / m.group(1), "image/webp"), svg)
    for key, val in WIDTHS.items():
        svg = svg.replace("{{%s}}" % key, str(val))
    (OUT / tpl.name).write_text(svg)
    print(f"{tpl.name}: {len(svg) / 1024:.0f} KB")
