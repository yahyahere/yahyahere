#!/usr/bin/env python3
"""Write info-card.svg, a neofetch-style panel. Edit the content below to update it.

Set STATIC=1 to write a frozen frame with no animation.
"""
import os
from xml.sax.saxutils import escape

TITLE = "yahya@github"

# (key, value). An empty key continues the row above.
ROWS = [
    ("Name", "Mohammed Yahiya Khan"),
    ("Role", "Cybersecurity Analyst, SOC & Threat Detection"),
    ("Base", "United Kingdom"),
    ("MSc", "Cybersecurity, Coventry University (2025-2026)"),
    ("Exp", "Cyber Security Analyst, Cognizant (2023-2025)"),
    ("BTech", "CSE (AI-ML), SR University (2019-2023)"),
    None,
    ("SOC", "QRadar, IDS/IPS, FIM, Wireshark, MITRE ATT&CK"),
    ("Detect", "Zeek, NetFlow, Sysmon, Splunk, Elastic Stack"),
    ("Pentest", "Kali Linux, Nmap, Metasploit, SQLMap"),
    ("DFIR", "Autopsy, FTK Imager"),
    ("Crypto", "ChaCha20, Ed25519"),
    ("Build", "Python, FastAPI, Next.js, Playwright, MySQL"),
    None,
    ("Projects", "LLM Security Testing Framework (dissertation)"),
    ("", "Insider Threat Detection System"),
    ("", "Secure Contract Exchange Protocol"),
    ("", "SME network penetration test"),
    ("", "IoT forensics research"),
    ("", "BERT disaster classifier (97.99% precision)"),
    None,
    ("Certs", "Azure AI Fundamentals, Intro to IoT"),
    ("", "Cybersecurity Essentials, Data Analytics"),
    ("", "Developing Front-End Apps with React"),
    ("LinkedIn", "linkedin.com/in/yahiyakhhan"),
]

WIDTH, HEIGHT = 460, 480  # same height as the portrait so the two columns line up
PAD_X, FONT_SIZE, KEY_W = 18, 12.5, 74
LINE, GAP = 16.5, 8

BG, BORDER, TITLE_C, KEY, VALUE, RULE = "#0d1117", "#30363d", "#39d353", "#39d353", "#c9d1d9", "#30363d"
SWATCHES = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0", "#8b949e", "#c9d1d9"]
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"

STAGGER, START = 0.09, 0.3


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    out = []
    n = 0

    def line(content: str) -> None:
        nonlocal n
        cls = "" if static else f' class="l" style="animation-delay:{START + n * STAGGER:.2f}s"'
        out.append(f"<g{cls}>{content}</g>")
        n += 1

    y = 34
    line(f'<text x="{PAD_X}" y="{y}" fill="{TITLE_C}" font-weight="700">{TITLE}</text>')
    y += 10
    line(f'<rect x="{PAD_X}" y="{y}" width="{WIDTH - 2 * PAD_X}" height="1" fill="{RULE}"/>')
    y += 22

    for row in ROWS:
        if row is None:
            y += GAP
            continue
        key, value = row
        k = f'<text x="{PAD_X}" y="{y}" fill="{KEY}" font-weight="700">{escape(key)}</text>' if key else ""
        line(f'{k}<text x="{PAD_X + KEY_W}" y="{y}" fill="{VALUE}">{escape(value)}</text>')
        y += LINE

    y += 2
    s = 22
    line("".join(
        f'<rect x="{PAD_X + i * s}" y="{y}" width="{s}" height="11" fill="{c}"/>' for i, c in enumerate(SWATCHES)
    ))
    if y + 11 > HEIGHT - 10:
        raise SystemExit(f"card content overflows: needs {y + 21}px, has {HEIGHT}px")

    css = "" if static else (
        "<style>.l{opacity:0;animation:p .35s ease-out forwards}"
        "@keyframes p{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}</style>"
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Profile summary">{css}'
        f'<rect x=".5" y=".5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="8" fill="{BG}" stroke="{BORDER}"/>'
        f'<g font-family="{FONT}" font-size="{FONT_SIZE}">{"".join(out)}</g></svg>'
    )
    with open("info-card.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote info-card.svg, content ends at y={y + 11}")


if __name__ == "__main__":
    main()
