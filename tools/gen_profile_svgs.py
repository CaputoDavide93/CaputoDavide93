#!/usr/bin/env python3
"""Draw the profile header: a small, quiet departure board.

Writes docs/assets/header-{light,dark}.svg in GitHub's own palette so the
board sits in the page instead of shouting over it. Only the name moves: its
split-flap tiles spin once on load and settle. The spin glyphs are seeded
from the text, so re-running writes identical files.

    python3 tools/gen_profile_svgs.py
"""
import hashlib
import pathlib
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets"

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

# GitHub Primer colours: canvas, border, tile, text, muted, accent (attention)
SCHEMES = {
    "dark": dict(bg="#161b22", edge="#30363d", tile="#21262d", seam="#0d1117",
                 text="#e6edf3", muted="#8b949e", accent="#d29922", spin="#6e7681"),
    "light": dict(bg="#f6f8fa", edge="#d0d7de", tile="#eaeef2", seam="#d0d7de",
                  text="#1f2328", muted="#59636e", accent="#9a6700", spin="#8c959f"),
}

NAME = "DAVIDE CAPUTO"
ROWS = [
    ("Now", "Senior Technical Architect"),
    ("From", "Public sector, Scotland"),
    ("Focus", "Identity, endpoints, cloud security"),
]
GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def flaps(c, x, y, text, size, tile_w):
    seed = hashlib.sha256(text.encode()).digest()
    tile_h, step, spins = size * 1.35, 0.07, 4
    out = []
    for i, ch in enumerate(text):
        cx = x + i * (tile_w + 2)
        out.append(f'<rect x="{cx:.1f}" y="{y}" width="{tile_w}" height="{tile_h:.1f}" rx="2" fill="{c["tile"]}"/>'
                   f'<path d="M{cx:.1f} {y + tile_h / 2:.1f}h{tile_w}" stroke="{c["seam"]}" stroke-width="1"/>')
        if ch == " ":
            continue
        tx, ty, t0 = cx + tile_w / 2, y + size * 1.02, 0.2 + i * 0.05

        def glyph(g, colour, sets):
            return (f'<text x="{tx:.1f}" y="{ty:.1f}" font-family="{MONO}" font-size="{size}" font-weight="700" '
                    f'fill="{colour}" text-anchor="middle" visibility="hidden">{escape(g)}{sets}</text>')

        for k in range(spins):
            g = GLYPHS[seed[(i * spins + k) % len(seed)] % len(GLYPHS)]
            on, off = t0 + k * step, t0 + (k + 1) * step
            out.append(glyph(g, c["spin"], f'<set attributeName="visibility" to="visible" begin="{on:.2f}s"/>'
                                           f'<set attributeName="visibility" to="hidden" begin="{off:.2f}s"/>'))
        land = t0 + spins * step
        out.append(glyph(ch, c["text"], f'<set attributeName="visibility" to="visible" begin="{land:.2f}s" fill="freeze"/>'))
    return "".join(out)


def header(scheme):
    c = SCHEMES[scheme]
    w, h = 560, 182
    o = [f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="8" fill="{c["bg"]}" stroke="{c["edge"]}"/>',
         flaps(c, 24, 22, NAME, 24, 19.5)]
    for i, (k, v) in enumerate(ROWS):
        y = 96 + i * 27
        o.append(f'<text x="24" y="{y}" font-family="{MONO}" font-size="14" fill="{c["muted"]}">{k}</text>'
                 f'<text x="96" y="{y}" font-family="{MONO}" font-size="15" font-weight="{700 if i == 0 else 400}" '
                 f'fill="{c["accent"] if i == 0 else c["text"]}">{escape(v)}</text>')
    label = "Davide Caputo: " + "; ".join(f"{k} {v}" for k, v in ROWS)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}">\n' + "\n".join(o) + "\n</svg>\n")


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    for scheme in SCHEMES:
        (ASSETS / f"header-{scheme}.svg").write_text(header(scheme))


if __name__ == "__main__":
    main()
