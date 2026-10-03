#!/usr/bin/env python3
"""Remove the progress bar under the contribution snake and crop it off.

Platane/snk has no option for this. The bar is the run of <rect class="u ...">
elements below the grid; the grid itself ends 16 px under its last row.

    python3 tools/strip_snake_bar.py docs/assets/snake-*.svg
"""
import re
import sys

BAR = re.compile(r'<rect class="u u\w*"[^>]*/>')
VIEWBOX = re.compile(r'viewBox="(-?[\d.]+) (-?[\d.]+) ([\d.]+) ([\d.]+)" width="([\d.]+)" height="([\d.]+)"')


def strip(path):
    svg = open(path).read()
    svg, removed = BAR.subn("", svg)
    ys = [float(y) for y in re.findall(r'class="c[^"]*"[^>]*\by="([\d.]+)"', svg)]
    m = VIEWBOX.search(svg)
    if not m or not ys:
        raise SystemExit(f"{path}: unexpected snake layout, left unchanged")
    x, y, w, _, width, _ = m.groups()
    h = max(ys) + 16 + 16 - float(y)          # last row + cell + margin
    svg = svg[:m.start()] + f'viewBox="{x} {y} {w} {h:g}" width="{width}" height="{h:g}"' + svg[m.end():]
    open(path, "w").write(svg)
    print(f"{path}: removed {removed} bar segments, height {h:g}")


for p in sys.argv[1:]:
    strip(p)
