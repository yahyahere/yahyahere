#!/usr/bin/env python3
"""Render data/contributions.json as an animated calendar: contrib-heatmap.svg.

With no data file yet, renders an empty calendar that says it is waiting for the first run.
Usage: python scripts/render_heatmap_svg.py [data.json] [output.svg]
Set STATIC=1 to write a frozen frame with no animation.
"""
import json
import os
import sys
from datetime import date, timedelta

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG, BORDER, TEXT, MUTED = "#0d1117", "#30363d", "#c9d1d9", "#8b949e"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"

WIDTH = 860
LEFT, TOP = 44, 44
STEP, CELL = 15.0, 12.0
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def empty_calendar() -> list[dict]:
    today = date.today()
    return [{"date": (today - timedelta(days=i)).isoformat(), "count": 0, "level": 0} for i in range(364, -1, -1)]


def shade(day: dict, top_cut: int) -> int:
    """GitHub's levels 0-4, plus a neon level 5 for the busiest days."""
    if top_cut and day["level"] == 4 and day["count"] >= top_cut:
        return 5
    return day["level"]


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else "data/contributions.json"
    dst = sys.argv[2] if len(sys.argv) > 2 else "contrib-heatmap.svg"
    static = os.environ.get("STATIC") == "1"

    data = None
    if os.path.exists(src):
        with open(src, encoding="utf-8") as f:
            data = json.load(f)
    days = data["days"] if data else empty_calendar()

    top = sorted(d["count"] for d in days if d["level"] == 4)
    top_cut = top[int(len(top) * 0.8)] if len(top) >= 5 else 0

    # Column = weeks since the Sunday on or before the first day, same layout as GitHub.
    first = date.fromisoformat(days[0]["date"])
    origin = first - timedelta(days=(first.weekday() + 1) % 7)

    cells, labels = [], []
    last_month, last_label_col = None, -9
    for d in days:
        dt = date.fromisoformat(d["date"])
        offset = (dt - origin).days
        col, row = offset // 7, offset % 7
        x, y = LEFT + col * STEP, TOP + row * STEP
        fill = PALETTE[shade(d, top_cut)]
        delay = 0.2 + (col + row) * 0.022  # diagonal sweep
        attr = "" if static else f' class="c" style="animation-delay:{delay:.2f}s"'
        cells.append(
            f'<rect{attr} x="{x:.0f}" y="{y:.0f}" width="{CELL:.0f}" height="{CELL:.0f}" rx="2.5" fill="{fill}">'
            f'<title>{d["date"]}: {d["count"]}</title></rect>'
        )
        if dt.month != last_month and row == 0 or (last_month is None):
            if col - last_label_col >= 3:
                labels.append(f'<text x="{x:.0f}" y="{TOP - 9}" fill="{MUTED}">{MONTHS[dt.month - 1]}</text>')
                last_label_col = col
            last_month = dt.month

    for name, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        labels.append(f'<text x="{LEFT - 8}" y="{TOP + row * STEP + 10:.0f}" fill="{MUTED}" text-anchor="end">{name}</text>')

    base = TOP + 7 * STEP + 22
    if data:
        s = data["stats"]
        best = s["best_day"]
        footer = (
            f'<tspan fill="{TEXT}" font-weight="700">{s["total"]:,}</tspan> contributions in the last year'
            f'  |  streak {s["current_streak"]}d, longest {s["longest_streak"]}d, best day {best["count"]}'
        )
    else:
        footer = "waiting for the first refresh"

    legend_x = WIDTH - 20 - (6 * 15) - 34
    legend = f'<text x="{legend_x - 8}" y="{base}" fill="{MUTED}" text-anchor="end">Less</text>'
    for i, c in enumerate(PALETTE):
        legend += f'<rect x="{legend_x + i * 15}" y="{base - 10}" width="12" height="12" rx="2.5" fill="{c}"/>'
    legend += f'<text x="{legend_x + 6 * 15 + 4}" y="{base}" fill="{MUTED}">More</text>'

    height = base + 18
    css = "" if static else (
        "<style>.c{opacity:0;animation:d .3s ease-out forwards}"
        "@keyframes d{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}</style>"
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height:.0f}" '
        f'viewBox="0 0 {WIDTH} {height:.0f}" role="img" aria-label="GitHub contribution calendar">{css}'
        f'<rect x=".5" y=".5" width="{WIDTH - 1}" height="{height - 1:.0f}" rx="8" fill="{BG}" stroke="{BORDER}"/>'
        f'<g font-family="{FONT}" font-size="11">{"".join(labels)}{"".join(cells)}'
        f'<text x="{LEFT}" y="{base}" fill="{MUTED}">{footer}</text>{legend}</g></svg>'
    )
    with open(dst, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {dst}: {len(days)} days, {len(svg) // 1024} KB")


if __name__ == "__main__":
    main()
