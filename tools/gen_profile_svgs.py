#!/usr/bin/env python3
"""Draw the profile's amber CRT header and project cards.

Writes docs/assets/header.svg and docs/assets/cards/<repo>.svg. Card facts
(language, latest release, licence, stars) come from the GitHub API on every
run, so nothing on a card is hand-typed except its one-line description.

    GITHUB_TOKEN=$(gh auth token) python3 tools/gen_profile_svgs.py

The header is 640 px wide on purpose: GitHub shrinks it to the phone's width,
and at 860 px its text came out around 7 px tall.
"""
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

BG, AMBER, DIM, DEEP = "#160e03", "#ffb347", "#b8782a", "#6b4512"

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

# (key, value) records the header prints one by one; an empty key continues
# the line above.
RECORDS = [
    ("login", "davide"),
    ("role", "senior technical architect"),
    ("sector", "public, scotland"),
    ("focus", "identity, endpoints"),
    ("", "cloud security, large fleets"),
    ("after hrs", "home assistant, esp32, apps"),
]


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


def _svg(w, h, label, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">\n{body}\n</svg>\n')


def _screen(w, h):
    """Tube background plus the defs the overlay and glow need."""
    return (
        '<defs><pattern id="sl" width="4" height="4" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="2" fill="#000" opacity=".35"/></pattern>'
        '<radialGradient id="vg" cx=".5" cy=".5" r=".75">'
        '<stop offset=".6" stop-color="#000" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#000" stop-opacity=".75"/></radialGradient>'
        '<filter id="ph" x="-5%" y="-20%" width="110%" height="140%">'
        '<feGaussianBlur stdDeviation="1.6" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'
        f'<rect width="{w}" height="{h}" rx="18" fill="{BG}"/>'
    )


def _overlay(w, h):
    """Scanlines that flicker, a vignette, and the bezel edge."""
    return (
        f'<rect width="{w}" height="{h}" rx="18" fill="url(#sl)">'
        '<animate attributeName="opacity" values=".9;1;.93;1" dur="0.18s" repeatCount="indefinite"/></rect>'
        f'<rect width="{w}" height="{h}" rx="18" fill="url(#vg)"/>'
        f'<rect x="3" y="3" width="{w - 6}" height="{h - 6}" rx="16" fill="none" stroke="{DEEP}" stroke-width="2"/>'
    )


def header():
    w, size, line_h, top = 640, 20, 34, 100
    h = top + line_h * len(RECORDS) + 40
    pad = max(len(k) for k, _ in RECORDS) + 2
    o = [_screen(w, h), f'<g filter="url(#ph)" font-family="{MONO}" font-size="{size}">']
    o.append(f'<text x="34" y="48" fill="{DIM}" font-size="15">caputo terminal :: tty1</text>')
    o.append(f'<path d="M34 62H{w - 34}" stroke="{DEEP}" stroke-width="1.5"/>')
    t = 0.4
    for i, (key, value) in enumerate(RECORDS):
        y = top + i * line_h
        lead = f"{key} ".ljust(pad, ".") + " " if key else " " * (pad + 1)
        o.append(
            f'<text x="34" y="{y}" fill="{DIM}" xml:space="preserve" opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" begin="{t:.2f}s" dur="0.05s" fill="freeze"/>'
            f'{"&gt;" if key else " "} {escape(lead)}<tspan fill="{AMBER}">{escape(value)}</tspan></text>'
        )
        t += 0.45
    y = top + len(RECORDS) * line_h
    o.append(
        f'<text x="34" y="{y}" fill="{AMBER}">&gt; <tspan>█<animate attributeName="opacity" '
        f'values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1s" begin="{t:.2f}s" repeatCount="indefinite"/></tspan></text>'
    )
    o.append("</g>")
    o.append(_overlay(w, h))
    return _svg(w, h, "Amber terminal: Davide Caputo, Senior Technical Architect, public sector, Scotland",
                "\n".join(o))


def card(name, blurb, facts):
    w, h = 420, 150
    o = [_screen(w, h), f'<g filter="url(#ph)" font-family="{MONO}">']
    o.append(f'<rect x="20" y="20" width="{w - 40}" height="26" fill="{AMBER}"/>')
    o.append(f'<text x="30" y="38" font-size="14" font-weight="700" fill="{BG}">{escape(name)}</text>')
    for i, line in enumerate(wrap(blurb, 44)[:2]):
        o.append(f'<text x="24" y="{72 + i * 19}" font-size="13" fill="{AMBER}">{escape(line)}</text>')
    line = (f'lang={(facts["language"] or "-").lower()}  rel={facts["release"] or "none"}  '
            f'lic={facts["license"] or "-"}')
    o.append(f'<text x="24" y="{h - 24}" font-size="12" fill="{DIM}" xml:space="preserve">{escape(line)}</text>')
    if facts["stars"]:
        o.append(f'<text x="{w - 24}" y="{h - 24}" text-anchor="end" font-size="12" '
                 f'fill="{AMBER}">*{facts["stars"]}</text>')
    o.append("</g>")
    o.append(_overlay(w, h))
    return _svg(w, h, f"{name}: {blurb}", "\n".join(o))


def main():
    (ASSETS / "cards").mkdir(parents=True, exist_ok=True)
    (ASSETS / "header.svg").write_text(header())
    for _, name, blurb in PROJECTS:
        repo = api(f"/repos/{OWNER}/{name}")
        if repo is None:
            raise SystemExit(f"{name}: repository not found")
        release = api(f"/repos/{OWNER}/{name}/releases/latest")
        facts = {
            "language": repo.get("language"),
            "stars": repo.get("stargazers_count", 0),
            "release": release["tag_name"] if release else None,
            "license": (repo.get("license") or {}).get("spdx_id"),
        }
        (ASSETS / "cards" / f"{name}.svg").write_text(card(name, blurb, facts))
        print(f"{name}: {facts}")


if __name__ == "__main__":
    main()
