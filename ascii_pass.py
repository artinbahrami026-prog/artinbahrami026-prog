"""Builds the text-character boarding pass that fills {{ASCII}} in src/boarding.svg.

Every line is plain ASCII so it renders in the embedded JetBrains Mono subset.
Each line is a list of (text, css_class) segments; lines print one after another.
"""
from html import escape

# Figlet "standard" glyphs, 5 rows each.
GLYPHS = {
    "Y": ["__   __", "\\ \\ / /", " \\ V / ", "  | |  ", "  |_|  "],
    "Z": [" _____", "|__  /", "  / / ", " / /_ ", "/____|"],
    "S": [" ____  ", "/ ___| ", "\\___ \\ ", " ___) |", "|____/ "],
    "F": [" _____ ", "|  ___|", "| |_   ", "|  _|  ", "|_|    "],
    "O": ["  ___  ", " / _ \\ ", "| | | |", "| |_| |", " \\___/ "],
}

MAIN, STUB = 70, 27  # inner widths of the two ticket panels


def big(word):
    return ["".join(GLYPHS[c][r] for c in word) for r in range(5)]


def pad(segs, width):
    used = sum(len(t) for t, _ in segs)
    return segs + [(" " * (width - used), "")]


def row(main, stub=None, sep="|"):
    return [("|", "frame")] + pad(main, MAIN) + [(sep, "frame")] + pad(stub or [], STUB) + [("|", "frame")]


def lines():
    rule = [("+" + "-" * MAIN + "+" + "-" * STUB + "+", "frame")]
    yyz, sfo = big("YYZ"), big("SFO")
    code = "||| || |||| | || ||| |"
    out = [rule]
    out.append(row([("  BOARDING PASS", "head"), (" " * 27, ""), ("[*] ", "live"), ("BOARDING SOON", "live")],
                   [("  AB 2008", "dim")], ":"))
    out.append(row([("  " + "=" * (MAIN - 4), "frame")], [], ":"))
    out.append(row([("  PASSENGER  ", "dim"), ("BAHRAMI / ARTIN", "val")], [("  BAHRAMI / ARTIN", "val")], ":"))
    out.append(row([], [("  YYZ ", "from"), ("-> ", "dim"), ("SFO", "to"), ("   SEAT ", "dim"), ("01A", "val")], ":"))
    gap = " " * 22  # room for the plane, which is drawn separately
    for r in range(5):
        stub = [("  " + code, "val")] if r else []
        out.append(row([("  ", ""), (yyz[r], "from"), (gap, ""), (sfo[r], "to")], stub, ":"))
    out.append(row([("  TORONTO", "dim"), (" " * 39, ""), ("SAN FRANCISCO", "dim")], [("  " + code, "val")], ":"))
    out.append(row([("  " + "-" * (MAIN - 4), "frame")], [], ":"))
    out.append(row([("  FLIGHT ", "dim"), ("AB 2008", "val"), ("   DATE ", "dim"), ("SOON", "val"),
                    ("   GATE ", "dim"), ("TBA", "val"), ("   SEAT ", "dim"), ("01A", "val"),
                    ("   ZONE ", "dim"), ("1", "val")], [("  SEQ 001", "dim")], ":"))
    out.append(rule)
    return out


def svg(x, y, line_height, start, step):
    """Return <text> rows plus the timing of the last row."""
    parts = []
    for i, segs in enumerate(lines()):
        spans = "".join(f'<tspan class="{c}">{escape(t)}</tspan>' if c else escape(t) for t, c in segs)
        delay = start + i * step
        parts.append(f'<text x="{x}" y="{y + i * line_height}" class="row" '
                     f'style="animation-delay:{delay:.2f}s" xml:space="preserve">{spans}</text>')
    return "\n    ".join(parts), start + len(lines()) * step
