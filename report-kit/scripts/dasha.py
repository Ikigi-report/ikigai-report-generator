#!/usr/bin/env python3
"""
Vimshottari dasha calculator for the Ikigai Report Kit.

Answers the question the chart script cannot: *which planetary period am I in
right now, and how long does it last?* Prints the current mahadasha,
antardasha and pratyantardasha with elapsed percentages, the full antardasha
timeline inside the current mahadasha, and the mahadashas still to come.

Powered by jyotishganit (MIT), which uses NASA JPL DE421 ephemeris data and
the True Chitra Paksha ayanamsa. Note that `chart.py` in this repo uses the
Lahiri ayanamsa; the two differ by a fraction of a degree, which can very
occasionally shift a nakshatra pada at a boundary.

Requires: pip install jyotishganit
(The first run downloads ~17 MB of ephemeris data.)

Example:
  python dasha.py --date 1990-01-15 --time 14:30 --tz +0 \
                  --lat 51.4779 --lon -0.0015
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

try:
    from jyotishganit import calculate_birth_chart
except ImportError:  # pragma: no cover
    sys.exit("error: jyotishganit not installed. Run: pip install jyotishganit")

DAY = 86400.0


def parse_when(date: str, time: str) -> datetime:
    year, month, day = (int(x) for x in date.split("-"))
    hour, minute = (int(x) for x in time.split(":"))
    return datetime(year, month, day, hour, minute)


def pct_elapsed(start: datetime, end: datetime, now: datetime) -> float:
    span = (end - start).total_seconds()
    if span <= 0:
        return 0.0
    return max(0.0, min(100.0, (now - start).total_seconds() / span * 100.0))


def years_between(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds() / DAY / 365.2425


def find_active(periods: dict, now: datetime):
    """Return (lord, data) for the period containing `now`, else None."""
    for lord, data in periods.items():
        if data["start"] <= now < data["end"]:
            return lord, data
    return None


def bar(pct: float, width: int = 28) -> str:
    filled = int(round(pct / 100 * width))
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def collect(chart, now: datetime) -> dict:
    """Pull the active mahadasha / antardasha / pratyantardasha out of the chart."""
    result: dict = {"as_of": now.isoformat(timespec="seconds")}

    mahadashas = chart.dashas.all["mahadashas"]
    active_md = find_active(mahadashas, now)
    if not active_md:
        return result
    md_lord, md_data = active_md
    result["mahadasha"] = {
        "lord": md_lord,
        "start": md_data["start"].isoformat(timespec="seconds"),
        "end": md_data["end"].isoformat(timespec="seconds"),
        "years": round(years_between(md_data["start"], md_data["end"]), 2),
        "percent_elapsed": round(pct_elapsed(md_data["start"], md_data["end"], now), 1),
    }

    antardashas = md_data.get("antardashas", {})
    active_ad = find_active(antardashas, now)
    if active_ad:
        ad_lord, ad_data = active_ad
        result["antardasha"] = {
            "lord": ad_lord,
            "start": ad_data["start"].isoformat(timespec="seconds"),
            "end": ad_data["end"].isoformat(timespec="seconds"),
            "years": round(years_between(ad_data["start"], ad_data["end"]), 2),
            "percent_elapsed": round(pct_elapsed(ad_data["start"], ad_data["end"], now), 1),
        }
        active_pd = find_active(ad_data.get("pratyantardashas", {}), now)
        if active_pd:
            pd_lord, pd_data = active_pd
            result["pratyantardasha"] = {
                "lord": pd_lord,
                "start": pd_data["start"].isoformat(timespec="seconds"),
                "end": pd_data["end"].isoformat(timespec="seconds"),
                "percent_elapsed": round(pct_elapsed(pd_data["start"], pd_data["end"], now), 1),
            }

    result["antardasha_timeline"] = [
        {
            "lord": lord,
            "start": data["start"].isoformat(timespec="seconds"),
            "end": data["end"].isoformat(timespec="seconds"),
            "years": round(years_between(data["start"], data["end"]), 2),
            "status": ("past" if data["end"] <= now
                       else "current" if data["start"] <= now
                       else "future"),
        }
        for lord, data in antardashas.items()
    ]

    result["future_mahadashas"] = [
        {
            "lord": lord,
            "start": data["start"].isoformat(timespec="seconds"),
            "end": data["end"].isoformat(timespec="seconds"),
            "years": round(years_between(data["start"], data["end"]), 2),
        }
        for lord, data in mahadashas.items() if data["start"] > now
    ]
    return result


def report(data: dict) -> None:
    now = datetime.fromisoformat(data["as_of"])
    print(f"\nVimshottari dasha, as of {now:%Y-%m-%d}")

    if "mahadasha" not in data:
        print("  No active period found — check the birth details.")
        return

    print("\n=== WHERE YOU ARE NOW ===")
    for label, key in (("Mahadasha      ", "mahadasha"),
                       ("Antardasha     ", "antardasha"),
                       ("Pratyantardasha", "pratyantardasha")):
        item = data.get(key)
        if not item:
            continue
        start = datetime.fromisoformat(item["start"])
        end = datetime.fromisoformat(item["end"])
        pct = item["percent_elapsed"]
        print(f"  {label} {item['lord']:<9} {start:%Y-%m-%d} -> {end:%Y-%m-%d}"
              f"  {bar(pct)} {pct:>5.1f}%")

    md = data["mahadasha"]
    print(f"\n=== ANTARDASHAS INSIDE THE {md['lord'].upper()} MAHADASHA ===")
    for item in data["antardasha_timeline"]:
        mark = {"past": "  ", "current": "->", "future": "  "}[item["status"]]
        start = datetime.fromisoformat(item["start"])
        end = datetime.fromisoformat(item["end"])
        print(f" {mark} {item['lord']:<9} {start:%Y-%m-%d} -> {end:%Y-%m-%d}"
              f"   {item['years']:>5.2f} yrs   {item['status']}")

    if data["future_mahadashas"]:
        print("\n=== MAHADASHAS STILL TO COME ===")
        for item in data["future_mahadashas"][:4]:
            start = datetime.fromisoformat(item["start"])
            end = datetime.fromisoformat(item["end"])
            print(f"    {item['lord']:<9} {start:%Y-%m-%d} -> {end:%Y-%m-%d}"
                  f"   {item['years']:>5.2f} yrs")
    print()


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Current Vimshottari mahadasha and antardasha.")
    ap.add_argument("--date", required=True, help="birth date, YYYY-MM-DD")
    ap.add_argument("--time", required=True, help="local birth time, HH:MM (24h)")
    ap.add_argument("--tz", required=True, type=float,
                    help="UTC offset in hours at birth, e.g. +3 or -5.5")
    ap.add_argument("--lat", required=True, type=float, help="latitude, north positive")
    ap.add_argument("--lon", required=True, type=float, help="longitude, east positive")
    ap.add_argument("--as-of", help="date to evaluate, YYYY-MM-DD (default: today)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a report")
    args = ap.parse_args()

    now = (datetime.fromisoformat(args.as_of) if args.as_of else datetime.now())

    chart = calculate_birth_chart(
        birth_date=parse_when(args.date, args.time),
        latitude=args.lat,
        longitude=args.lon,
        timezone_offset=args.tz,
        name="report",
    )
    data = collect(chart, now)

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        report(data)


if __name__ == "__main__":
    main()
