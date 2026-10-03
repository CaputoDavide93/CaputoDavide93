#!/usr/bin/env python3
"""Draw every block of the profile README as a departure board.

The README is images end to end, so the style covers the whole page:
header, stack, LinkedIn, section titles, experience, project cards and the
upstream line, all in docs/assets/. Green names and titles, amber
information, split-flap titles that flip into place once on load.

Card facts (language, latest release) come from the GitHub API on every run;
the flap glyphs are seeded from the text, so a run with no new facts writes
identical files and the daily workflow commits nothing.

    GITHUB_TOKEN=$(gh auth token) python3 tools/gen_profile_svgs.py
"""
import hashlib
import json
import os
import pathlib
import urllib.error
import urllib.request
from xml.sax.saxutils import escape

OWNER = "CaputoDavide93"
ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets"

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
HELV = "'Helvetica Neue',Helvetica,Arial,sans-serif"

GREEN, GREEN_DIM = "#4dff7c", "#2fb85a"      # names, titles, labels
AMBER, AMBER_DIM = "#ffa21a", "#e0901a"      # information
WHITE, BOARD, TILE, EDGE = "#ffffff", "#1b1b1b", "#2a2a2a", "#333333"

PW = 640   # full-width blocks: GitHub shrinks them to the phone's width
CW = 420   # cards: two per row on desktop, one per row on a phone

NAME = "Davide Caputo"
ROLE = "Senior Technical Architect"
SECTOR = "Public sector, Scotland"
FOCUS = ["Identity", "Endpoints", "Cloud security", "Large fleets"]
AFTER = ["Home Assistant", "ESP32", "Mobile apps"]
STACK = ["Python", "Swift", "Flutter", "AWS", "Entra ID", "Jamf Pro", "Home Assistant"]
EXPERIENCE = [
    ("Identity & endpoints", "Entra ID, Jamf Pro, joiner-mover-leaver and offboarding across large fleets"),
    ("Cloud & security", "AWS audits from CloudTrail, Linux hardening, monitoring"),
    ("Automation & AI", "Python, Slack bots, AWS Lambda, Claude-powered tools with guard rails"),
    ("Mobile apps", "Baby and lifestyle apps that solve small day-to-day problems"),
]
TITLES = {"experience": "Experience", "work": "Work projects",
          "home": "Home & personal projects", "contributions": "Contributions"}
PROJECTS = [
    ("work", "Jamf-SnipeIT-Suite", "Syncs devices and users between Jamf Pro, Snipe-IT and Azure AD"),
    ("work", "AWS-OffBoarding-Audit", "Cross-account offboarding audit with CloudTrail and backdoor checks"),
    ("work", "Jamf-WakeUp-Call", "Redeploys the Jamf framework to sleeping Macs by group, serial or file"),
    ("work", "EC2-Linux-Security-Monitor", "ClamAV, auto-updates and a status dashboard for Linux servers"),
    ("home", "Mixergy-Home-Assistant", "Mixergy hot-water tank integration for Home Assistant, on HACS"),
    ("home", "InkFrame-Immich", "A weekly Immich photo on a battery e-paper frame"),
    ("home", "Kallsup-Sendspin-MusicAssistant", "An IKEA KALLSUP rebuilt as an ESP32-S3 Music Assistant speaker"),
    ("home", "MacOS-Game-Mode", "Gets your Mac and network ready for cloud gaming"),
]
UPSTREAM = "Upstream: merged fix in Home Assistant core (#183579)"
LINKEDIN = "LinkedIn  davidecaputo93"

FLAP_GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return None
        raise


def wrap(text, limit):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > limit:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line]


def T(x, y, text, size, fill, font=MONO, weight=400, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" xml:space="preserve"{extra}>{escape(text)}</text>')


def svg(w, h, label, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}">\n{body}\n</svg>\n')


def board(w, h):
    return (f'<rect width="{w}" height="{h}" rx="8" fill="{BOARD}"/>'
            f'<rect x="5" y="5" width="{w - 10}" height="{h - 10}" rx="5" fill="none" stroke="{EDGE}"/>')


def flaps(x, y, text, size, tile_w, start=0.2):
    """A row of split-flap tiles; each spins through a few glyphs, then settles.

    Tiles start a beat apart, left to right, so the word reads as it lands.
    """
    seed = hashlib.sha256(text.encode()).digest()
    tile_h, step, spins = size * 1.35, 0.07, 5
    out = []
    for i, ch in enumerate(text):
        cx = x + i * (tile_w + 2)
        out.append(f'<rect x="{cx:.1f}" y="{y}" width="{tile_w}" height="{tile_h:.1f}" rx="2" fill="{TILE}"/>'
                   f'<path d="M{cx:.1f} {y + tile_h / 2:.1f}h{tile_w}" stroke="#111" stroke-width="1.2"/>')
        if ch == " ":
            continue
        tx, ty, t0 = cx + tile_w / 2, y + size * 1.02, start + i * 0.05

        def glyph(text, colour, sets):
            return (f'<text x="{tx:.1f}" y="{ty:.1f}" font-family="{MONO}" font-size="{size}" '
                    f'font-weight="700" fill="{colour}" text-anchor="middle" visibility="hidden">'
                    f'{escape(text)}{sets}</text>')

        for k in range(spins):
            g = FLAP_GLYPHS[seed[(i * spins + k) % len(seed)] % len(FLAP_GLYPHS)]
            on, off = t0 + k * step, t0 + (k + 1) * step
            out.append(glyph(g, GREEN_DIM,
                             f'<set attributeName="visibility" to="visible" begin="{on:.2f}s"/>'
                             f'<set attributeName="visibility" to="hidden" begin="{off:.2f}s"/>'))
        land = t0 + spins * step
        out.append(glyph(ch, GREEN, f'<set attributeName="visibility" to="visible" begin="{land:.2f}s" fill="freeze"/>'))
    return "".join(out)


def header():
    w, h = PW, 320
    o = [board(w, h), T(28, 44, "Departures", 22, WHITE, HELV, 700),
         T(w - 28, 44, "Scotland", 18, AMBER_DIM, HELV, 400, "end"),
         flaps(28, 64, NAME.upper(), 30, 24.6)]
    rows = [("Now", ROLE), ("From", SECTOR), ("Calling at", ", ".join(FOCUS[:2])),
            ("", ", ".join(FOCUS[2:])), ("Evenings", ", ".join(AFTER))]
    for i, (k, v) in enumerate(rows):
        y = 152 + i * 32
        o.append(T(28, y, k, 16, GREEN_DIM) + T(160, y, v, 18, AMBER, weight=700))
    return svg(w, h, f"Departure board: {NAME}, {ROLE}, {SECTOR}. Calling at {', '.join(FOCUS)}. "
                     f"Evenings: {', '.join(AFTER)}", "\n".join(o))


def chip(x, y, label):
    cw = 20 + len(label) * 15 * 0.62
    return (f'<rect x="{x:.1f}" y="{y}" width="{cw:.1f}" height="32" rx="3" fill="{TILE}"/>'
            + T(x + cw / 2, y + 21, label, 15, GREEN, weight=700, anchor="middle"), cw)


def stack():
    w, rows, row, used = PW, [], [], 0
    for s in STACK:
        cw = 20 + len(s) * 15 * 0.62
        if used + cw > w - 60 and row:
            rows.append(row)
            row, used = [], 0
        row.append(s)
        used += cw + 10
    rows.append(row)
    h = 40 + len(rows) * 44
    o = [board(w, h)]
    for r, items in enumerate(rows):
        total = sum(20 + len(s) * 15 * 0.62 for s in items) + 10 * (len(items) - 1)
        x = (w - total) / 2
        for s in items:
            part, cw = chip(x, 20 + r * 44, s)
            o.append(part)
            x += cw + 10
    return svg(w, h, "Stack: " + ", ".join(STACK), "\n".join(o))


def linkedin():
    w, h = 360, 64
    part, cw = chip(0, 0, LINKEDIN)
    return svg(w, h, "LinkedIn: davidecaputo93",
               board(w, h) + f'<g transform="translate({(w - cw) / 2:.1f},16)">{part}</g>')


def title(text):
    w, h = PW, 76
    return svg(w, h, text, board(w, h) + flaps(24, 16, text.upper()[:24], 22, 19))


def experience():
    w, row_h = PW, 84
    h = 30 + row_h * len(EXPERIENCE)
    o = [board(w, h)]
    for i, (area, focus) in enumerate(EXPERIENCE):
        y = 22 + i * row_h
        if i:
            o.append(f'<path d="M24 {y - 4}H{w - 24}" stroke="{EDGE}" stroke-width="2"/>')
        for j, line in enumerate(wrap(area, 16)):
            o.append(T(32, y + 30 + j * 22, line, 19, GREEN, weight=700))
        for j, line in enumerate(wrap(focus, 40)[:3]):
            o.append(T(240, y + 28 + j * 21, line, 16, AMBER_DIM))
    return svg(w, h, "Experience: " + "; ".join(f"{a}: {f}" for a, f in EXPERIENCE), "\n".join(o))


def card(name, blurb, facts):
    w, h = CW, 168
    o = [board(w, h), T(24, 44, name, 17, GREEN, weight=700)]
    for i, line in enumerate(wrap(blurb, 44)[:2]):
        o.append(T(26, 82 + i * 21, line, 15, AMBER_DIM))
    o.append(T(24, h - 24, "Platform " + (facts["language"] or "-"), 14, WHITE))
    status = f"Released {facts['release']}" if facts["release"] else "On time"
    o.append(T(w - 24, h - 24, status, 14, WHITE if facts["release"] else AMBER_DIM, weight=700, anchor="end"))
    return svg(w, h, f"{name}: {blurb}", "\n".join(o))


def strip(text):
    w, h = PW, 64
    return svg(w, h, text, board(w, h) + T(w / 2, 40, text, 16, AMBER, anchor="middle"))


def main():
    (ASSETS / "cards").mkdir(parents=True, exist_ok=True)
    files = {"header.svg": header(), "stack.svg": stack(), "linkedin.svg": linkedin(),
             "experience.svg": experience(), "upstream.svg": strip(UPSTREAM)}
    for key, text in TITLES.items():
        files[f"title-{key}.svg"] = title(text)
    for _, name, blurb in PROJECTS:
        repo = api(f"/repos/{OWNER}/{name}")
        if repo is None:
            raise SystemExit(f"{name}: repository not found")
        release = api(f"/repos/{OWNER}/{name}/releases/latest")
        facts = {"language": repo.get("language"), "release": release["tag_name"] if release else None}
        files[f"cards/{name}.svg"] = card(name, blurb, facts)
        print(f"{name}: {facts}")
    for path, text in files.items():
        (ASSETS / path).write_text(text)


if __name__ == "__main__":
    main()
