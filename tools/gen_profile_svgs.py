#!/usr/bin/env python3
"""Draw the profile's terminal header and neon project cards.

Writes docs/assets/header-{light,dark}.svg and
docs/assets/cards/<repo>-{light,dark}.svg. Card facts (language, latest
release, stars) come from the GitHub API on every run, so nothing on a card
is hand-typed except its one-line description.

    GITHUB_TOKEN=$(gh auth token) python3 tools/gen_profile_svgs.py
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
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

SCHEMES = {
    "dark": {
        "bg": "#0d1117", "panel": "#161b22", "edge": "#30363d",
        "text": "#e6edf3", "muted": "#8b949e", "prompt": "#39ff88",
        "out": "#7ee7ff", "path": "#c792ea", "pill": "#21262d",
    },
    "light": {
        "bg": "#ffffff", "panel": "#f6f8fa", "edge": "#d0d7de",
        "text": "#1f2328", "muted": "#59636e", "prompt": "#1a7f37",
        "out": "#0969da", "path": "#8250df", "pill": "#eaeef2",
    },
}

# Each section glows in its own pair of colours.
ACCENTS = {"work": ("#00e5ff", "#7c4dff"), "home": ("#ff4fd8", "#ffb000")}

LANG_COLOURS = {
    "Python": "#3572A5", "Swift": "#F05138", "Shell": "#89e051",
    "Dart": "#00B4AB", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "Kotlin": "#A97BFF", "HTML": "#e34c26", "C++": "#f34b7d",
}

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

# (kind, text): "cmd" lines type themselves out, "out" lines appear whole.
TERMINAL = [
    ("cmd", "whoami"),
    ("out", "davide caputo :: senior technical architect :: public sector"),
    ("cmd", "cat ~/.focus"),
    ("out", "identity | endpoints | cloud security | large fleets"),
    ("cmd", "ls ~/after-hours"),
    ("dir", "home-assistant/  esp32/  mobile-apps/  macos/"),
    ("cmd", "uptime"),
    ("out", "on github since 2016, based in scotland"),
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


def header(scheme):
    c = SCHEMES[scheme]
    size, line_h, char_w = 15, 26, 9.0  # monospace advance is ~0.6em
    prompt = "davide@scotland:~$ "
    width, top = 860, 62
    height = top + line_h * len(TERMINAL) + 24
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="Terminal: Davide Caputo, '
        f'Senior Technical Architect in the public sector">',
        "<defs>",
        '<filter id="glow" x="-20%" y="-50%" width="140%" height="200%">'
        '<feGaussianBlur stdDeviation="2.2" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        "</defs>",
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" '
        f'fill="{c["bg"]}" stroke="{c["edge"]}"/>',
        f'<path d="M1 13a12 12 0 0 1 12-12h{width - 26}a12 12 0 0 1 12 12v23H1z" fill="{c["panel"]}"/>',
        f'<line x1="1" y1="36" x2="{width - 1}" y2="36" stroke="{c["edge"]}"/>',
    ]
    for i, colour in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        parts.append(f'<circle cx="{22 + i * 20}" cy="18.5" r="6" fill="{colour}"/>')
    parts.append(
        f'<text x="{width / 2}" y="23" text-anchor="middle" font-family="{MONO}" '
        f'font-size="13" fill="{c["muted"]}">davide@scotland: ~ (zsh)</text>'
    )

    t, prompt_w = 0.6, len(prompt) * char_w
    defs = []
    for n, (kind, text) in enumerate(TERMINAL):
        y = top + n * line_h
        if kind == "cmd":
            parts.append(_reveal(f"{n}p", 24, y, prompt, c["prompt"], size, t, glow=True))
            t += 0.35
            full = len(text) * char_w
            steps = len(text)
            values = ";".join(f"{k * char_w:.1f}" for k in range(steps + 1))
            times = ";".join(f"{k / steps:.3f}" for k in range(steps + 1))
            dur = 0.07 * steps
            defs.append(
                f'<clipPath id="c{n}"><rect x="{24 + prompt_w}" y="{y - size}" width="0" '
                f'height="{line_h}"><animate attributeName="width" values="{values}" '
                f'keyTimes="{times}" calcMode="discrete" begin="{t:.2f}s" dur="{dur:.2f}s" '
                f'fill="freeze"/></rect></clipPath>'
            )
            parts.append(
                f'<text x="{24 + prompt_w}" y="{y}" font-family="{MONO}" font-size="{size}" '
                f'fill="{c["text"]}" clip-path="url(#c{n})" xml:space="preserve">'
                f"{escape(text)}</text>"
            )
            t += dur + 0.25
        else:
            colour = c["path"] if kind == "dir" else c["out"]
            parts.append(_reveal(f"{n}o", 24, y, text, colour, size, t))
            t += 0.45
    y = top + len(TERMINAL) * line_h
    parts.append(_reveal("end", 24, y, prompt, c["prompt"], size, t, glow=True))
    parts.append(
        f'<rect x="{24 + prompt_w + 2}" y="{y - size + 2}" width="{char_w}" height="{size + 2}" '
        f'fill="{c["prompt"]}" opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" '
        f'fill="freeze"/><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" '
        f'dur="1.1s" begin="{t:.2f}s" repeatCount="indefinite"/></rect>'
    )
    parts.insert(4, "<defs>" + "".join(defs) + "</defs>")
    parts.append("</svg>")
    return "\n".join(parts)


def _reveal(key, x, y, text, colour, size, at, glow=False):
    flt = ' filter="url(#glow)"' if glow else ""
    return (
        f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{colour}"{flt} '
        f'opacity="0" xml:space="preserve">{escape(text)}<set attributeName="opacity" to="1" '
        f'begin="{at:.2f}s" fill="freeze"/></text>'
    )


def wrap(text, limit):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > limit:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line]


def card(section, name, blurb, facts, scheme):
    c = SCHEMES[scheme]
    a1, a2 = ACCENTS[section]
    w, h = 420, 138
    gid = f"g-{name}"
    neon = scheme == "dark"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{escape(name)}: {escape(blurb)}">',
        "<defs>",
        f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{a1}"/><stop offset="1" stop-color="{a2}"/>'
        f'<animateTransform attributeName="gradientTransform" type="rotate" '
        f'values="0 .5 .5;360 .5 .5" dur="6s" repeatCount="indefinite"/></linearGradient>',
        '<filter id="neon" x="-10%" y="-20%" width="120%" height="140%">'
        '<feGaussianBlur stdDeviation="4"/></filter>',
        "</defs>",
    ]
    if neon:
        out.append(
            f'<rect x="7" y="7" width="{w - 14}" height="{h - 14}" rx="12" fill="none" '
            f'stroke="url(#{gid})" stroke-width="3" filter="url(#neon)" opacity="0.9">'
            f'<animate attributeName="opacity" values="0.55;1;0.55" dur="3s" '
            f'repeatCount="indefinite"/></rect>'
        )
    out.append(
        f'<rect x="7" y="7" width="{w - 14}" height="{h - 14}" rx="12" fill="{c["bg"]}" '
        f'stroke="url(#{gid})" stroke-width="{1.6 if neon else 2}"/>'
    )
    out.append(
        f'<text x="24" y="40" font-family="{MONO}" font-size="16" font-weight="700" '
        f'fill="{c["text"]}"><tspan fill="{a1 if neon else c["out"]}">&gt; </tspan>{escape(name)}</text>'
    )
    for i, line in enumerate(wrap(blurb, 50)[:2]):
        out.append(
            f'<text x="24" y="{66 + i * 19}" font-family="{SANS}" font-size="13.5" '
            f'fill="{c["muted"]}">{escape(line)}</text>'
        )
    x, y = 24, 114
    lang = facts["language"]
    if lang:
        out.append(f'<circle cx="{x + 5}" cy="{y - 4.5}" r="5" fill="{LANG_COLOURS.get(lang, c["muted"])}"/>')
        out.append(
            f'<text x="{x + 16}" y="{y}" font-family="{SANS}" font-size="12.5" '
            f'fill="{c["muted"]}">{escape(lang)}</text>'
        )
        x += 26 + len(lang) * 7.2
    # Pills: the latest release (accent edge) and the licence, whichever exist.
    for label, edge in ((facts["release"], a1), (facts["license"], c["edge"])):
        if not label:
            continue
        pw = 18 + len(label) * 7.4
        out.append(
            f'<rect x="{x}" y="{y - 15}" width="{pw}" height="21" rx="10.5" '
            f'fill="{c["pill"]}" stroke="{edge}"/>'
        )
        out.append(
            f'<text x="{x + pw / 2}" y="{y}" text-anchor="middle" font-family="{MONO}" '
            f'font-size="12" fill="{c["text"]}">{escape(label)}</text>'
        )
        x += pw + 8
    if facts["stars"]:
        out.append(
            f'<text x="{w - 24}" y="{y}" text-anchor="end" font-family="{SANS}" '
            f'font-size="12.5" fill="{c["muted"]}">&#9733; {facts["stars"]}</text>'
        )
    out.append("</svg>")
    return "\n".join(out)


def main():
    (ASSETS / "cards").mkdir(parents=True, exist_ok=True)
    for scheme in SCHEMES:
        (ASSETS / f"header-{scheme}.svg").write_text(header(scheme) + "\n")
    for section, name, blurb in PROJECTS:
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
        for scheme in SCHEMES:
            path = ASSETS / "cards" / f"{name}-{scheme}.svg"
            path.write_text(card(section, name, blurb, facts, scheme) + "\n")
        print(f"{name}: {facts}")


if __name__ == "__main__":
    main()
