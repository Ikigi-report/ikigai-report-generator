#!/usr/bin/env python3
"""
Test suite for the Ikigai Report Kit.

Runs with plain Python — no pytest required:

    .venv/bin/python tests/test_kit.py

Checks are grouped:
  - PURE      arithmetic and mapping logic, no dependencies
  - EPHEM     needs pyswisseph or ephem
  - NETWORK   needs jyotishganit's ephemeris download (skipped with --offline)
  - KNOWN     documents bugs we already know about; reported, never fatal

Exit code is non-zero only if a real check fails. Known issues are printed
so they stay visible without blocking the suite.
"""
from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

OFFLINE = "--offline" in sys.argv

passed: list[str] = []
failed: list[tuple[str, str]] = []
skipped: list[tuple[str, str]] = []
known: list[str] = []


def check(name: str, got, want, tol: float | None = None) -> None:
    if tol is not None:
        ok = abs(got - want) <= tol
    else:
        ok = got == want
    if ok:
        passed.append(name)
    else:
        failed.append((name, f"got {got!r}, want {want!r}"))


def skip(name: str, why: str) -> None:
    skipped.append((name, why))


# ---------------------------------------------------------------- PURE
def test_numerology() -> None:
    import numerology as n

    # Life Path: plain digit sum, no master number.
    check("numerology: life path 2000-01-01 -> 4",
          n.reduce_number(sum(int(c) for c in "20000101"))[0], 4)

    # Master number 11 must reduce to 2 but be flagged on the way.
    value, chain = n.reduce_number(38)
    check("numerology: 38 -> 11 -> 2", value, 2)
    check("numerology: 38 flags master 11", "master number 11" in chain, True)

    # Pythagorean letter values: A=1 .. I=9, J wraps back to 1.
    check("numerology: pythagorean A", n.PYTHAGOREAN["A"], 1)
    check("numerology: pythagorean I", n.PYTHAGOREAN["I"], 9)
    check("numerology: pythagorean J wraps", n.PYTHAGOREAN["J"], 1)
    check("numerology: pythagorean Z", n.PYTHAGOREAN["Z"], 8)

    # Abjad: محمد = m40 + h8 + m40 + d4 = 92
    check("numerology: abjad محمد = 92",
          sum(n.ABJAD[c] for c in "محمد"), 92)
    # الله = a1 + l30 + l30 + h5 = 66
    check("numerology: abjad الله = 66",
          sum(n.ABJAD[c] for c in "الله"), 66)
    # Alef variants normalise to the plain alef.
    check("numerology: abjad normalises أ -> ا", n.ABJAD_NORMALISE["أ"], "ا")

    pinnacle = n.pinnacles_and_challenges("1986-07-06")
    check("numerology: Pinnacle 1 for 1986-07-06", pinnacle["cycles"][0]["pinnacle"], "4")
    check("numerology: Challenge 1 for 1986-07-06", pinnacle["cycles"][0]["challenge"], 1)
    check("numerology: Pinnacle 3 for 1986-07-06", pinnacle["cycles"][2]["pinnacle"], "7")
    check("numerology: fourth Pinnacle is open-ended", pinnacle["cycles"][3]["end_age"], None)


def test_extended_pure() -> None:
    import extended_systems as ex

    # Sexagenary tables are the right size.
    check("bazi: 10 heavenly stems", len(ex.HEAVENLY_STEMS), 10)
    check("bazi: 12 earthly branches", len(ex.EARTHLY_BRANCHES), 12)

    # Zodiac animal by year, using the Li Chun boundary.
    for year, animal in ((1993, "Rooster"), (2000, "Dragon"), (1984, "Rat")):
        got = ex.calculate_bazi(datetime(year, 7, 1, 12, 0))["zodiac_animal"]
        check(f"bazi: {year} -> {animal}", got, animal)

    # Li Chun: 3 Feb belongs to the previous cycle year, 5 Feb to the current one.
    check("bazi: 1993-02-03 falls in the 1992 cycle",
          ex.bazi_year_for_lichun(datetime(1993, 2, 3, 12, 0)), 1992)
    check("bazi: 1993-02-05 falls in the 1993 cycle",
          ex.bazi_year_for_lichun(datetime(1993, 2, 5, 12, 0)), 1993)

    # Hour branches: Zi spans 23:00-01:00.
    check("bazi: 23:30 -> Zi hour", ex.bazi_hour_pillar_indices(datetime(2000, 1, 1, 23, 30), 0)[1], 0)
    check("bazi: 00:30 -> Zi hour", ex.bazi_hour_pillar_indices(datetime(2000, 1, 1, 0, 30), 0)[1], 0)
    check("bazi: 22:30 -> Hai hour", ex.bazi_hour_pillar_indices(datetime(2000, 1, 1, 22, 30), 0)[1], 11)

    # Rave Mandala: 64 gates, each used exactly once.
    check("hd: 64 gates in sequence", len(ex.HD_GATE_SEQUENCE), 64)
    check("hd: gate sequence has no duplicates", len(set(ex.HD_GATE_SEQUENCE)), 64)
    check("hd: gates are 1..64", sorted(ex.HD_GATE_SEQUENCE), list(range(1, 65)))

    # The mandala starts at 28°15' Pisces, so that degree is gate 25 line 1.
    check("hd: start degree maps to first gate, line 1",
          ex.hd_degree_to_gate_line(ex.HD_START_DEGREE), (ex.HD_GATE_SEQUENCE[0], 1))
    # One line further in is line 2.
    check("hd: +1 line width -> line 2",
          ex.hd_degree_to_gate_line(ex.HD_START_DEGREE + 360 / 64 / 6)[1], 2)
    # One full gate further is the second gate in the sequence.
    check("hd: +1 gate width -> next gate",
          ex.hd_degree_to_gate_line(ex.HD_START_DEGREE + 360 / 64)[0], ex.HD_GATE_SEQUENCE[1])

    # Every gate maps to exactly one center, and all 64 are covered.
    g2c = ex.hd_gate_to_center()
    check("hd: all 64 gates map to a center", len(g2c), 64)

    # Destiny Matrix reduction keeps values in 1..22.
    for n_in, want in ((18, 18), (22, 22), (23, 5), (47, 11), (1993, 22)):
        check(f"matrix: reduce_to_22({n_in}) -> {want}", ex.reduce_to_22(n_in), want)

    # Full Gene Keys mapping uses existing natal/personality and design activations.
    personality = {name: {"gate": index + 1, "line": 1} for index, name in enumerate(ex.HD_PLANET_ORDER)}
    design = {name: {"gate": index + 1, "line": 2} for index, name in enumerate(ex.HD_PLANET_ORDER)}
    keys = ex.calculate_gene_keys({"personality": personality, "design": design})
    check("gene keys: Venus attraction uses design Moon", keys["venus_sequence"]["attraction"], "5.2")
    check("gene keys: Pearl uses natal Jupiter", keys["pearl_sequence"]["pearl"], "9.1")
    check("gene keys: Star Pearl creativity uses design Uranus", keys["star_pearl_sequence"]["creativity"], "11.2")


def test_generator_pure() -> None:
    import generate_report as generator

    numbers = generator.calculate_numerology("Test Person", "1990-01-15", 2026, None)
    check("generator: Life Path rendered", numbers["life_path"]["display"], "8")
    check("generator: Personal Year rendered", numbers["personal_year"]["display"], "8")
    check("generator: no Arabic name omits Abjad", "abjad" in numbers, False)
    check("generator: Pinnacles included", "pinnacles_challenges" in numbers, True)
    check("generator: master-number display", generator.display_reduction(38), "11/2")
    check("generator: standard tests include WDQ", any(item["key"] == "wdq" for item in generator.TEST_CATALOG), True)
    check("generator: standard tests include ASRS", any(item["key"] == "asrs" for item in generator.TEST_CATALOG), True)

    args = type("Args", (), {"date": "1990-01-15", "time": "14:30", "solar_year": 2026})()
    location = {"display_name": "Greenwich", "latitude": 51.4779, "longitude": -0.0015, "timezone": "Europe/London", "utc_offset_hours": 0.0}
    rendered = generator.render_report("Test Person", None, args, location, {"numerology": numbers}, [], {})
    check("generator: reproduce command is populated", '--name "Test Person"' in rendered, True)
    check("generator: reproduce command has no placeholders", "{name_en}" in rendered, False)


# --------------------------------------------------------------- EPHEM
def test_chart_ephem() -> None:
    try:
        import swisseph as swe
    except ImportError:
        skip("chart: swiss ephemeris checks", "pyswisseph not installed")
        return
    import chart

    # At J2000.0 the Sun's *mean* longitude is the familiar 280.466°, but its
    # apparent longitude is about 0.098° less once the equation of centre is
    # applied. Assert the apparent value, which is what calc_ut returns.
    jd = swe.julday(2000, 1, 1, 12.0)
    sun = swe.calc_ut(jd, swe.SUN)[0][0]
    check("chart: apparent Sun at J2000.0 ~ 280.37 deg", sun, 280.369, tol=0.01)

    # Independent anchor: at the March 2000 equinox the Sun crosses 0° Aries.
    jd_equinox = swe.julday(2000, 3, 20, 7.6)   # 2000-03-20 07:35 UT
    sun_eq = swe.calc_ut(jd_equinox, swe.SUN)[0][0]
    check("chart: Sun at March 2000 equinox ~ 0 deg Aries",
          min(sun_eq, 360.0 - sun_eq), 0.0, tol=0.05)

    # Formatting: 0° is Aries 0°00', 359.99° is late Pisces.
    check("chart: fmt(0)", chart.fmt(0.0), "Aries 0°00'")
    check("chart: fmt(120.5)", chart.fmt(120.5), "Leo 0°30'")

    # D10: odd signs (Aries=index 0) count from themselves.
    check("chart: d10 Aries 0° -> Aries", chart.d10_sign(0.0), 0)
    check("chart: d10 Aries 3° -> Taurus", chart.d10_sign(3.0), 1)
    # Even signs (Taurus=index 1) count from the 9th sign.
    check("chart: d10 Taurus 0° -> Capricorn", chart.d10_sign(30.0), 9)
    # Navamsa: cardinal signs begin from themselves, fixed signs from the ninth,
    # and dual signs from the fifth.
    check("chart: d9 Aries 0° -> Aries", chart.d9_sign(0.0), 0)
    check("chart: d9 Aries 3°20' -> Taurus", chart.d9_sign(30 / 9), 1)
    check("chart: d9 Taurus 0° -> Capricorn", chart.d9_sign(30.0), 9)
    check("chart: d9 Gemini 0° -> Libra", chart.d9_sign(60.0), 6)

    # Houses wrap correctly across 0° Aries.
    cusps = [350.0, 20.0, 50.0, 80.0, 110.0, 140.0,
             170.0, 200.0, 230.0, 260.0, 290.0, 320.0]
    check("chart: house_of wraps past 0 Aries", chart.house_of(5.0, cusps), 1)
    check("chart: house_of mid-chart", chart.house_of(115.0, cusps), 5)

    payload = chart.collect_chart("2000-01-15", "14:30", 0.0, 51.4779, -0.0015, 2026)
    check("chart: structured payload includes tropical chart", "tropical" in payload, True)
    check("chart: structured payload includes Panchanga", "panchanga" in payload, True)
    check("chart: Panchanga has five limbs", set(payload["panchanga"]) >= {"vara", "tithi", "nakshatra", "yoga", "karana"}, True)
    check("chart: Panchanga Tithi range", 1 <= payload["panchanga"]["tithi"]["number"] <= 15, True)
    check("chart: structured payload includes D9", "d9" in payload, True)
    check("chart: structured payload includes D10", "d10" in payload, True)
    check("chart: structured payload includes solar return", "solar_return" in payload, True)
    check("chart: structured payload has formatted Ascendant", "formatted" in payload["tropical"]["ascendant"], True)


def test_extended_ephem() -> None:
    try:
        import ephem  # noqa: F401
    except ImportError:
        skip("hd: design-time solve", "ephem not installed")
        return
    import extended_systems as ex

    # The design moment is ~88 days before birth and the Sun must be
    # exactly 88° earlier in the zodiac.
    birth = datetime(1990, 1, 15, 14, 30)
    design = ex.find_design_datetime_utc(birth)
    days_back = (birth - design).days
    check("hd: design instant is 84-92 days before birth", 84 <= days_back <= 92, True)

    sun_birth = ex.ecliptic_longitude_ephem("Sun", birth)
    sun_design = ex.ecliptic_longitude_ephem("Sun", design)
    arc = (sun_birth - sun_design) % 360.0
    check("hd: solar arc to design is 88 deg", arc, 88.0, tol=0.01)


# ------------------------------------------------------------- NETWORK
def test_dasha() -> None:
    if OFFLINE:
        skip("dasha: reference chart", "--offline")
        return
    try:
        from jyotishganit import calculate_birth_chart
    except ImportError:
        skip("dasha: reference chart", "jyotishganit not installed")
        return
    import dasha

    # jyotishganit's own documented example: Jupiter mahadasha 2017-06-21 to 2033-06-22.
    chart = calculate_birth_chart(
        birth_date=datetime(1996, 7, 4, 9, 10, 0),
        latitude=18.404, longitude=75.195,
        timezone_offset=5.5, name="reference",
    )
    data = dasha.collect(chart, datetime(2026, 8, 8))
    check("dasha: reference chart mahadasha lord", data["mahadasha"]["lord"], "Jupiter")
    check("dasha: reference mahadasha start", data["mahadasha"]["start"][:10], "2017-06-21")
    check("dasha: reference mahadasha end", data["mahadasha"]["end"][:10], "2033-06-22")
    check("dasha: antardasha present", "antardasha" in data, True)
    check("dasha: timeline covers 9 antardashas", len(data["antardasha_timeline"]), 9)
    # Percentages must be sane.
    pct = data["mahadasha"]["percent_elapsed"]
    check("dasha: percent elapsed in range", 0 <= pct <= 100, True)


# --------------------------------------------------------------- KNOWN
def report_known_issues() -> None:
    import extended_systems as ex

    if len(ex.HD_CHANNELS) != 36:
        missing = []
        have = {frozenset(c) for c in ex.HD_CHANNELS}
        for pair in ((10, 34), (10, 57)):
            if frozenset(pair) not in have:
                missing.append(f"{pair[0]}-{pair[1]}")
        known.append(
            f"extended_systems: HD_CHANNELS has {len(ex.HD_CHANNELS)}/36 channels"
            + (f", missing {', '.join(missing)}" if missing else "")
            + " — can misclassify Generator/MG as Projector"
        )

    dupes = {}
    for center, gates in ex.HD_CENTERS.items():
        for gate in gates:
            dupes.setdefault(gate, []).append(center)
    for gate, centers in dupes.items():
        if len(centers) > 1:
            known.append(
                f"extended_systems: gate {gate} listed in {' and '.join(centers)}"
                " — correct only because of dict ordering"
            )

    try:
        import ephem
        import math
        body = ephem.Sun(datetime(1990, 1, 15, 14, 30))
        j2000 = math.degrees(float(ephem.Ecliptic(body).lon)) % 360
        of_date = math.degrees(float(ephem.Ecliptic(body, epoch=datetime(1990, 1, 15)).lon)) % 360
        drift = abs(j2000 - of_date)
        if drift > 0.01:
            known.append(
                f"extended_systems: ecliptic_longitude_ephem uses J2000, not epoch-of-date "
                f"({drift:.3f}° drift) — flips ~{drift / (360/64/6) * 100:.0f}% of HD lines"
            )
    except ImportError:
        pass

    known.append(
        "extended_systems: BaZi day-pillar anchor (1900-01-31) disagrees with the "
        "1984-02-02 anchor by 22 days — Day Master unvalidated"
    )


def main() -> int:
    for fn in (test_numerology, test_extended_pure, test_generator_pure,
               test_chart_ephem, test_extended_ephem, test_dasha):
        try:
            fn()
        except Exception as exc:  # a crash is a failure, not an excuse
            failed.append((fn.__name__, f"raised {type(exc).__name__}: {exc}"))
    report_known_issues()

    for name in passed:
        print(f"  PASS  {name}")
    for name, why in skipped:
        print(f"  SKIP  {name}  ({why})")
    for name, why in failed:
        print(f"  FAIL  {name}  -- {why}")

    if known:
        print("\nKnown issues (documented in README, not failures):")
        for item in known:
            print(f"  !  {item}")

    print(f"\n{len(passed)} passed, {len(failed)} failed, {len(skipped)} skipped, "
          f"{len(known)} known issues")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
