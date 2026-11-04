#!/usr/bin/env python3
"""Scrape the public contribution calendar into data/contributions.json. No token needed.

Exits non-zero without touching the existing data if the page looks wrong, so a change
to GitHub's HTML fails the workflow instead of wiping the graph.
"""
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USERNAME", "yahyahere")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = "data/contributions.json"
MIN_DAYS = 300  # a real calendar has about 365 cells


def parse(html: str) -> tuple[list[dict], int | None]:
    soup = BeautifulSoup(html, "html.parser")

    tips = {t.get("for"): t.get_text(" ", strip=True) for t in soup.find_all("tool-tip") if t.get("for")}

    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        tip = tips.get(cell.get("id"), "")
        m = re.match(r"([\d,]+) contributions? on", tip)
        count = int(m.group(1).replace(",", "")) if m else 0
        days.append({"date": cell["data-date"], "count": count, "level": int(cell.get("data-level", 0))})
    days.sort(key=lambda d: d["date"])

    # A cell with a colour but no readable count means the tooltip format changed.
    if any(d["level"] > 0 and d["count"] == 0 for d in days):
        raise ValueError("coloured cell with no count: tooltip format may have changed")

    heading = soup.find(id="js-contribution-activity-description") or soup.find("h2")
    total = None
    if heading:
        m = re.search(r"([\d,]+)\s+contributions?", heading.get_text(" ", strip=True))
        if m:
            total = int(m.group(1).replace(",", ""))
    return days, total


def stats(days: list[dict], total: int | None) -> dict:
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)

    # Today not having a contribution yet does not break the current streak.
    current = 0
    tail = days[:-1] if days and days[-1]["count"] == 0 else days
    for d in reversed(tail):
        if not d["count"]:
            break
        current += 1

    months = defaultdict(int)
    for d in days:
        months[d["date"][:7]] += d["count"]

    best = max(days, key=lambda d: d["count"])
    return {
        "total": total if total is not None else sum(d["count"] for d in days),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": dict(sorted(months.items())),
    }


def main() -> None:
    resp = requests.get(URL, headers={"User-Agent": "profile-art-refresh"}, timeout=30)
    resp.raise_for_status()
    days, total = parse(resp.text)
    if len(days) < MIN_DAYS:
        sys.exit(f"only found {len(days)} day cells: page structure may have changed, keeping old data")

    payload = {
        "username": USERNAME,
        # Changes every run, so the daily commit keeps the repo active.
        # GitHub disables scheduled workflows after 60 days without repo activity.
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "stats": stats(days, total),
        "days": days,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
    print(f"{len(days)} days, {payload['stats']['total']} contributions")


if __name__ == "__main__":
    main()
