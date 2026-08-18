#!/usr/bin/env python3
"""
Extended symbolic systems calculator for the Ikigai Report Kit.

Computes four systems in a deterministic, documented way:
  1) Chinese Zodiac / BaZi (Four Pillars, Li Chun year boundary)
  2) Human Design (Type, Strategy, Authority, Profile, centers, key activations)
  3) Gene Keys (Activation Sequence from Human Design activations)
  4) Destiny Matrix 22 (Tarot-arcana reduction model)

Dependencies:
  - Python standard library
  - ephem (required for Human Design/Gene Keys planetary longitudes)

Example:
  python scripts/extended_systems.py \
    --date 1990-01-15 --time 14:30 --tz +0 \
    --lat 51.4779 --lon -0.0015
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date, datetime, timedelta

try:
    import ephem
except ImportError:  # pragma: no cover
    ephem = None


HEAVENLY_STEMS = [
    ("Jia", "甲", "Yang Wood"),
    ("Yi", "乙", "Yin Wood"),
    ("Bing", "丙", "Yang Fire"),
    ("Ding", "丁", "Yin Fire"),
    ("Wu", "戊", "Yang Earth"),
    ("Ji", "己", "Yin Earth"),
    ("Geng", "庚", "Yang Metal"),
    ("Xin", "辛", "Yin Metal"),
    ("Ren", "壬", "Yang Water"),
    ("Gui", "癸", "Yin Water"),
]

EARTHLY_BRANCHES = [
    ("Zi", "子", "Rat"),
    ("Chou", "丑", "Ox"),
    ("Yin", "寅", "Tiger"),
    ("Mao", "卯", "Rabbit"),
    ("Chen", "辰", "Dragon"),
    ("Si", "巳", "Snake"),
    ("Wu", "午", "Horse"),
    ("Wei", "未", "Goat"),
    ("Shen", "申", "Monkey"),
    ("You", "酉", "Rooster"),
    ("Xu", "戌", "Dog"),
    ("Hai", "亥", "Pig"),
]

# Approximate solar-month boundaries for BaZi months, using common fixed-date
# practice so outputs remain deterministic across environments.
# Index meaning:
#   0=Tiger, 1=Rabbit, ..., 10=Rat, 11=Ox
SOLAR_MONTH_BOUNDARIES = [
    ((1, 6), 11),   # Ox
    ((2, 4), 0),    # Tiger (Li Chun)
    ((3, 6), 1),    # Rabbit
    ((4, 5), 2),    # Dragon
    ((5, 6), 3),    # Snake
    ((6, 6), 4),    # Horse
    ((7, 7), 5),    # Goat
    ((8, 8), 6),    # Monkey
    ((9, 8), 7),    # Rooster
    ((10, 8), 8),   # Dog
    ((11, 7), 9),   # Pig
    ((12, 7), 10),  # Rat
]


# Human Design mapping (Rave Mandala).
# 64 equal slices (5.625° each), sequence starts at 28°15' Pisces.
HD_START_DEGREE = 358.25
HD_GATE_SEQUENCE = [
    25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12,
    15, 52, 39, 53, 62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6,
    46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34, 9, 5, 26, 11,
    10, 58, 38, 54, 61, 60, 41, 19, 13, 49, 30, 55, 37, 63, 22, 36,
]

HD_CENTERS = {
    "Head": [61, 63, 64],
    "Ajna": [4, 11, 17, 24, 43, 47],
    "Throat": [8, 12, 16, 20, 23, 31, 33, 35, 45, 56, 62],
    "Self": [1, 2, 7, 10, 13, 15, 25, 46],
    "Sacral": [3, 5, 9, 14, 27, 29, 34, 42, 59],
    "Root": [19, 28, 38, 39, 41, 52, 53, 54, 58, 60],
    "Spleen": [18, 28, 32, 44, 48, 50, 57],
    "Solar Plexus": [6, 22, 30, 36, 37, 49, 55],
    "Heart": [21, 26, 40, 51],
}

HD_CHANNELS = [
    (1, 8), (2, 14), (3, 60), (4, 63), (5, 15), (6, 59), (7, 31), (9, 52),
    (10, 20), (11, 56), (12, 22), (13, 33), (16, 48), (17, 62), (18, 58),
    (19, 49), (20, 34), (20, 57), (21, 45), (23, 43), (24, 61), (25, 51),
    (26, 44), (27, 50), (28, 38), (29, 46), (30, 41), (32, 54), (34, 57),
    (35, 36), (37, 40), (39, 55), (42, 53), (47, 64),
]

HD_PLANET_ORDER = [
    "Sun",
    "Earth",
    "North Node",
    "South Node",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
]

EPHEM_BODIES = {
    "Sun": ephem.Sun if ephem else None,
    "Moon": ephem.Moon if ephem else None,
    "Mercury": ephem.Mercury if ephem else None,
    "Venus": ephem.Venus if ephem else None,
    "Mars": ephem.Mars if ephem else None,
    "Jupiter": ephem.Jupiter if ephem else None,
    "Saturn": ephem.Saturn if ephem else None,
    "Uranus": ephem.Uranus if ephem else None,
    "Neptune": ephem.Neptune if ephem else None,
    "Pluto": ephem.Pluto if ephem else None,
}


def angle_diff(a: float, b: float) -> float:
    """Signed shortest angular difference a-b in range [-180, 180)."""
    return (a - b + 180.0) % 360.0 - 180.0


def sum_digits(n: int) -> int:
    return sum(int(c) for c in str(abs(n)))


def julian_day_utc(dt_utc: datetime) -> float:
    year = dt_utc.year
    month = dt_utc.month
    day = dt_utc.day
    frac_day = (dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0) / 24.0
    day = day + frac_day
    if month <= 2:
        year -= 1
        month += 12
    a = year // 100
    b = 2 - a + a // 4
    return (
        int(365.25 * (year + 4716))
        + int(30.6001 * (month + 1))
        + day
        + b
        - 1524.5
    )


def parse_birth(date_str: str, time_str: str) -> datetime:
    year, month, day = (int(x) for x in date_str.split("-"))
    hour, minute = (int(x) for x in time_str.split(":"))
    return datetime(year, month, day, hour, minute)


def local_to_utc(dt_local: datetime, tz_hours: float) -> datetime:
    return dt_local - timedelta(hours=tz_hours)


def stem_branch_label(stem_idx: int, branch_idx: int) -> str:
    stem = HEAVENLY_STEMS[stem_idx]
    branch = EARTHLY_BRANCHES[branch_idx]
    return f"{stem[0]} {branch[0]} ({stem[1]}{branch[1]})"


def stem_branch_struct(stem_idx: int, branch_idx: int) -> dict:
    stem = HEAVENLY_STEMS[stem_idx]
    branch = EARTHLY_BRANCHES[branch_idx]
    return {
        "pillar": stem_branch_label(stem_idx, branch_idx),
        "stem": {"name": stem[0], "hanzi": stem[1], "element_polarity": stem[2]},
        "branch": {"name": branch[0], "hanzi": branch[1], "animal": branch[2]},
    }


def bazi_year_for_lichun(dt_local: datetime) -> int:
    # Fixed-date Li Chun approximation: Feb 4 at 00:00 local.
    if (dt_local.month, dt_local.day, dt_local.hour, dt_local.minute) < (2, 4, 0, 0):
        return dt_local.year - 1
    return dt_local.year


def bazi_month_index(dt_local: datetime) -> int:
    # Before Jan 6 => Rat month from previous cycle.
    idx = 10
    mmdd = (dt_local.month, dt_local.day)
    for boundary, month_idx in SOLAR_MONTH_BOUNDARIES:
        if mmdd >= boundary:
            idx = month_idx
    return idx


def bazi_day_pillar_indices(dt_local: datetime) -> tuple[int, int]:
    # Common deterministic base used in many implementations:
    # 1900-01-31 is treated as Jia-Zi day.
    base = date(1900, 1, 31)
    offset = (dt_local.date() - base).days
    return offset % 10, offset % 12


def bazi_hour_pillar_indices(dt_local: datetime, day_stem_idx: int) -> tuple[int, int]:
    # Zi hour starts at 23:00, each branch spans 2 hours.
    hour_branch_idx = ((dt_local.hour + 1) // 2) % 12
    zi_hour_stem_idx = ((day_stem_idx % 5) * 2) % 10
    hour_stem_idx = (zi_hour_stem_idx + hour_branch_idx) % 10
    return hour_stem_idx, hour_branch_idx


def calculate_bazi(dt_local: datetime) -> dict:
    year_for_bazi = bazi_year_for_lichun(dt_local)
    year_stem_idx = (year_for_bazi - 4) % 10
    year_branch_idx = (year_for_bazi - 4) % 12

    month_idx = bazi_month_index(dt_local)
    month_branch_idx = (2 + month_idx) % 12  # Tiger starts at branch index 2
    tiger_month_stem_idx = ((year_stem_idx % 5) * 2 + 2) % 10
    month_stem_idx = (tiger_month_stem_idx + month_idx) % 10

    day_stem_idx, day_branch_idx = bazi_day_pillar_indices(dt_local)
    hour_stem_idx, hour_branch_idx = bazi_hour_pillar_indices(dt_local, day_stem_idx)

    zodiac_animal = EARTHLY_BRANCHES[year_branch_idx][2]

    return {
        "method": {
            "year_boundary": "Li Chun fixed-date approximation (Feb 4 local)",
            "month_boundaries": "Fixed solar-month boundaries (deterministic, no ephemeris)",
            "day_reference": "1900-01-31 treated as Jia-Zi day",
            "hour_rule": "Zi hour starts at 23:00 local",
        },
        "zodiac_animal": zodiac_animal,
        "pillars": {
            "year": stem_branch_struct(year_stem_idx, year_branch_idx),
            "month": stem_branch_struct(month_stem_idx, month_branch_idx),
            "day": stem_branch_struct(day_stem_idx, day_branch_idx),
            "hour": stem_branch_struct(hour_stem_idx, hour_branch_idx),
        },
    }


def ecliptic_longitude_ephem(planet_name: str, dt_utc: datetime) -> float:
    if ephem is None:
        sys.exit("error: ephem not installed. Run: pip install ephem")
    body_cls = EPHEM_BODIES[planet_name]
    body = body_cls(dt_utc)
    ecl = ephem.Ecliptic(body)
    return math.degrees(float(ecl.lon)) % 360.0


def mean_lunar_node_longitude(dt_utc: datetime) -> float:
    # Meeus-style approximation for mean ascending node, deterministic.
    t = (julian_day_utc(dt_utc) - 2451545.0) / 36525.0
    omega = 125.04452 - 1934.136261 * t + 0.0020708 * (t ** 2) + (t ** 3) / 450000.0
    return omega % 360.0


def hd_degree_to_gate_line(degree: float) -> tuple[int, int]:
    gate_size = 360.0 / 64.0
    line_size = gate_size / 6.0
    adjusted = (degree - HD_START_DEGREE) % 360.0
    gate_idx = int(adjusted / gate_size)
    line = int((adjusted % gate_size) / line_size) + 1
    return HD_GATE_SEQUENCE[gate_idx], line


def hd_planet_degrees(dt_utc: datetime) -> dict[str, float]:
    sun_deg = ecliptic_longitude_ephem("Sun", dt_utc)
    earth_deg = (sun_deg + 180.0) % 360.0
    nn_deg = mean_lunar_node_longitude(dt_utc)
    sn_deg = (nn_deg + 180.0) % 360.0

    out = {
        "Sun": sun_deg,
        "Earth": earth_deg,
        "North Node": nn_deg,
        "South Node": sn_deg,
    }
    for name in ("Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"):
        out[name] = ecliptic_longitude_ephem(name, dt_utc)
    return out


def hd_activations(dt_utc: datetime) -> dict[str, dict]:
    degs = hd_planet_degrees(dt_utc)
    out = {}
    for name in HD_PLANET_ORDER:
        deg = degs[name]
        gate, line = hd_degree_to_gate_line(deg)
        out[name] = {"degree": round(deg, 6), "gate": gate, "line": line}
    return out


def find_design_datetime_utc(birth_dt_utc: datetime) -> datetime:
    birth_sun_deg = ecliptic_longitude_ephem("Sun", birth_dt_utc)
    target_deg = (birth_sun_deg - 88.0) % 360.0

    # Newton-Raphson with finite-difference derivative in deg/day.
    dt = birth_dt_utc - timedelta(days=88.0)
    for _ in range(25):
        sun_deg = ecliptic_longitude_ephem("Sun", dt)
        diff = angle_diff(sun_deg, target_deg)
        if abs(diff) < 1e-8:
            break

        dt_prev = dt - timedelta(hours=6)
        dt_next = dt + timedelta(hours=6)
        sun_prev = ecliptic_longitude_ephem("Sun", dt_prev)
        sun_next = ecliptic_longitude_ephem("Sun", dt_next)
        speed = angle_diff(sun_next, sun_prev) / 0.5  # 12h = 0.5 day
        if abs(speed) < 1e-8:
            break
        dt -= timedelta(days=(diff / speed))
    return dt


def hd_defined_channels(active_gates: set[int]) -> list[tuple[int, int]]:
    defined = []
    for g1, g2 in HD_CHANNELS:
        if g1 in active_gates and g2 in active_gates:
            defined.append((g1, g2))
    return defined


def hd_gate_to_center() -> dict[int, str]:
    mapping = {}
    for center, gates in HD_CENTERS.items():
        for gate in gates:
            mapping[gate] = center
    return mapping


def hd_center_graph(defined_channels: list[tuple[int, int]]) -> dict[str, set[str]]:
    g2c = hd_gate_to_center()
    graph = {center: set() for center in HD_CENTERS}
    for g1, g2 in defined_channels:
        c1 = g2c[g1]
        c2 = g2c[g2]
        graph[c1].add(c2)
        graph[c2].add(c1)
    return graph


def hd_defined_centers(defined_channels: list[tuple[int, int]]) -> set[str]:
    g2c = hd_gate_to_center()
    defined = set()
    for g1, g2 in defined_channels:
        defined.add(g2c[g1])
        defined.add(g2c[g2])
    return defined


def hd_motor_to_throat(graph: dict[str, set[str]], defined_centers: set[str]) -> bool:
    if "Throat" not in defined_centers:
        return False
    motors = {"Sacral", "Heart", "Solar Plexus", "Root"}
    visited = set()
    queue = ["Throat"]
    while queue:
        cur = queue.pop(0)
        if cur in visited:
            continue
        visited.add(cur)
        if cur in motors:
            return True
        queue.extend(sorted(graph[cur] - visited))
    return False


def hd_definition_type(graph: dict[str, set[str]], defined_centers: set[str]) -> str:
    if not defined_centers:
        return "No Definition"
    visited = set()
    components = 0
    for center in defined_centers:
        if center in visited:
            continue
        components += 1
        stack = [center]
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            stack.extend(sorted(graph[cur] - visited))
    if components == 1:
        return "Single Definition"
    if components == 2:
        return "Split Definition"
    if components == 3:
        return "Triple Split Definition"
    return "Quadruple Split Definition"


def hd_type_strategy_authority(defined_centers: set[str], graph: dict[str, set[str]]) -> tuple[str, str, str]:
    if not defined_centers:
        return "Reflector", "Wait a Lunar Cycle", "Lunar"

    has_sacral = "Sacral" in defined_centers
    motor_to_throat = hd_motor_to_throat(graph, defined_centers)

    if has_sacral and motor_to_throat:
        hd_type = "Manifesting Generator"
        strategy = "Wait to Respond, then Inform"
    elif has_sacral:
        hd_type = "Generator"
        strategy = "Wait to Respond"
    elif motor_to_throat:
        hd_type = "Manifestor"
        strategy = "Inform before Acting"
    else:
        hd_type = "Projector"
        strategy = "Wait for the Invitation"

    if "Solar Plexus" in defined_centers:
        authority = "Emotional"
    elif "Sacral" in defined_centers:
        authority = "Sacral"
    elif "Spleen" in defined_centers:
        authority = "Splenic"
    elif "Heart" in defined_centers:
        authority = "Ego"
    elif "Self" in defined_centers:
        authority = "Self-Projected"
    else:
        authority = "Mental/Environmental"

    return hd_type, strategy, authority


def calculate_human_design(date_str: str, time_str: str, tz: float) -> dict:
    dt_local = parse_birth(date_str, time_str)
    birth_dt_utc = local_to_utc(dt_local, tz)
    design_dt_utc = find_design_datetime_utc(birth_dt_utc)

    personality = hd_activations(birth_dt_utc)
    design = hd_activations(design_dt_utc)

    active_gates = {
        activation["gate"] for activation in personality.values()
    } | {
        activation["gate"] for activation in design.values()
    }

    defined_channels = hd_defined_channels(active_gates)
    graph = hd_center_graph(defined_channels)
    defined_centers = hd_defined_centers(defined_channels)
    open_centers = sorted(set(HD_CENTERS.keys()) - defined_centers)

    hd_type, strategy, authority = hd_type_strategy_authority(defined_centers, graph)
    profile = f"{personality['Sun']['line']}/{design['Sun']['line']}"
    definition = hd_definition_type(graph, defined_centers)

    return {
        "method": {
            "mandala_start_degree": HD_START_DEGREE,
            "gate_mapping": "64 equal arcs using fixed Rave Mandala sequence",
            "design_timestamp": "exact Sun position 88° before natal Sun (iterative solve)",
            "ephemeris_backend": "PyEphem geocentric ecliptic longitudes",
            "node_model": "Mean ascending lunar node approximation",
        },
        "type": hd_type,
        "strategy": strategy,
        "authority": authority,
        "profile": profile,
        "definition": definition,
        "defined_centers": sorted(defined_centers),
        "open_centers": open_centers,
        "active_gates": sorted(active_gates),
        "defined_channels": [f"{a}-{b}" for a, b in defined_channels],
        "personality": personality,
        "design": design,
    }


def calculate_gene_keys(hd: dict) -> dict:
    """Calculate the Golden Path spheres from Human Design activations.

    This is a deterministic gate-and-line mapping. It deliberately returns only
    the sphere coordinates, not copyrighted Gene Keys prose or claims about a
    person's character, health, relationships, or future.
    """
    p = hd["personality"]
    d = hd["design"]

    def key(activation: dict) -> str:
        return f"{activation['gate']}.{activation['line']}"

    activation = {
        "life_work": key(p["Sun"]),
        "evolution": key(p["Earth"]),
        "radiance": key(d["Sun"]),
        "purpose": key(d["Earth"]),
    }
    venus = {
        "attraction": key(d["Moon"]),
        "iq": key(p["Venus"]),
        "eq": key(p["Mars"]),
        "sq": key(d["Venus"]),
        "core": key(d["Mars"]),
    }
    pearl = {
        "vocation": key(d["Mars"]),
        "culture": key(d["Jupiter"]),
        "brand": key(p["Sun"]),
        "pearl": key(p["Jupiter"]),
    }
    star_pearl = {
        "creativity": key(d["Uranus"]),
        "relating": key(p["Mercury"]),
        "stability": key(d["Saturn"]),
    }
    return {
        "method": "Direct mapping: Gene Key number = Human Design gate number",
        "source": "https://genekeys.com/docs/what-planets-does-each-sphere-of-the-golden-path-profile-correlate-to/",
        "activation_sequence": activation,
        "venus_sequence": venus,
        "pearl_sequence": pearl,
        "star_pearl_sequence": star_pearl,
    }


def reduce_to_22(n: int) -> int:
    # Matrix of Destiny 22 convention:
    # repeatedly sum digits until <=22; keep 22 as a master value.
    while n > 22:
        n = sum_digits(n)
    return 22 if n == 0 else n


def calculate_destiny_matrix(dob: date) -> dict:
    day_arc = reduce_to_22(dob.day)
    month_arc = reduce_to_22(dob.month)
    year_sum = sum_digits(dob.year)
    year_arc = reduce_to_22(year_sum)
    destiny_arc = reduce_to_22(day_arc + month_arc + year_arc)

    # Deterministic derived points (cross + diagonals model).
    talent_arc = reduce_to_22(day_arc + month_arc)
    realization_arc = reduce_to_22(year_arc + destiny_arc)
    male_line_arc = reduce_to_22(day_arc + destiny_arc)
    female_line_arc = reduce_to_22(month_arc + destiny_arc)
    integration_arc = reduce_to_22(talent_arc + realization_arc)

    return {
        "method": "Matrix of Destiny 22 (Tarot-arcana reduction model, deterministic)",
        "core": {
            "day_arcana": day_arc,
            "month_arcana": month_arc,
            "year_arcana": year_arc,
            "destiny_arcana": destiny_arc,
        },
        "derived": {
            "talent_arcana": talent_arc,
            "realization_arcana": realization_arc,
            "male_line_arcana": male_line_arc,
            "female_line_arcana": female_line_arc,
            "integration_arcana": integration_arc,
        },
    }


def print_pretty(result: dict) -> None:
    bazi = result["bazi"]
    hd = result["human_design"]
    gk = result["gene_keys"]
    dm = result["destiny_matrix"]

    print("\n=== CHINESE ZODIAC / BAZI ===")
    print(f"  Zodiac animal: {bazi['zodiac_animal']}")
    for key in ("year", "month", "day", "hour"):
        print(f"  {key.capitalize():<6} pillar: {bazi['pillars'][key]['pillar']}")

    print("\n=== HUMAN DESIGN ===")
    print(f"  Type: {hd['type']}")
    print(f"  Strategy: {hd['strategy']}")
    print(f"  Authority: {hd['authority']}")
    print(f"  Profile: {hd['profile']}")
    print(f"  Definition: {hd['definition']}")
    print(f"  Defined centers: {', '.join(hd['defined_centers']) if hd['defined_centers'] else 'None'}")

    print("\n=== GENE KEYS (Activation Sequence) ===")
    seq = gk["activation_sequence"]
    print(f"  Life's Work: {seq['life_work']}")
    print(f"  Evolution:   {seq['evolution']}")
    print(f"  Radiance:    {seq['radiance']}")
    print(f"  Purpose:     {seq['purpose']}")

    print("\n=== DESTINY MATRIX 22 ===")
    print(f"  Core (day/month/year/destiny): "
          f"{dm['core']['day_arcana']}/"
          f"{dm['core']['month_arcana']}/"
          f"{dm['core']['year_arcana']}/"
          f"{dm['core']['destiny_arcana']}")
    print(f"  Derived (talent/realization/male-line/female-line/integration): "
          f"{dm['derived']['talent_arcana']}/"
          f"{dm['derived']['realization_arcana']}/"
          f"{dm['derived']['male_line_arcana']}/"
          f"{dm['derived']['female_line_arcana']}/"
          f"{dm['derived']['integration_arcana']}")
    print()


def main() -> None:
    ap = argparse.ArgumentParser(description="Compute BaZi, Human Design, Gene Keys, and Destiny Matrix.")
    ap.add_argument("--date", required=True, help="birth date, YYYY-MM-DD")
    ap.add_argument("--time", required=True, help="birth time, HH:MM (24h)")
    ap.add_argument("--tz", required=True, type=float, help="UTC offset at birth, e.g. +3")
    ap.add_argument("--lat", type=float, default=None,
                    help="latitude, north positive (optional; recorded in output only)")
    ap.add_argument("--lon", type=float, default=None,
                    help="longitude, east positive (optional; recorded in output only)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of pretty text")
    args = ap.parse_args()

    if ephem is None:
        sys.exit("error: ephem not installed. Run: pip install ephem")

    dt_local = parse_birth(args.date, args.time)

    result = {
        "input": {
            "date": args.date,
            "time": args.time,
            "tz": args.tz,
            "lat": args.lat,
            "lon": args.lon,
        },
        "bazi": calculate_bazi(dt_local),
        "human_design": calculate_human_design(args.date, args.time, args.tz),
        "gene_keys": None,
        "destiny_matrix": calculate_destiny_matrix(dt_local.date()),
    }
    result["gene_keys"] = calculate_gene_keys(result["human_design"])

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_pretty(result)


if __name__ == "__main__":
    main()