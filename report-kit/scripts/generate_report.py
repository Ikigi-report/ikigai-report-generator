#!/usr/bin/env python3
"""Generate an evidence-aware Ikigai calculation report from basic birth data.

The generator calculates every deterministic system implemented in this kit from:
  - full name in Latin script (required for Pythagorean name numerology)
  - birth date and local birth time
  - birth place (geocoded automatically) or explicit coordinates
  - optional Arabic-script name (for Abjad numerology)

Psychometric results are deliberately optional. When a result is supplied in a JSON
file it is shown as Group A measured evidence; otherwise the report lists only the
missing test links at the end. It does not infer personality, diagnosis or vocation
from birth data.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import numerology as num

TEST_CATALOG = [
    {
        "key": "mbti",
        "system": "MBTI-style type (16Personalities)",
        "purpose": "Communication and preference hypotheses",
        "time": "12 min",
        "link": "https://www.16personalities.com/free-personality-test",
    },
    {
        "key": "big_five",
        "system": "Big Five with facets (IPIP-BFFM)",
        "purpose": "Five personality factors with facet detail",
        "time": "15 min",
        "link": "https://openpsychometrics.org/tests/IPIP-BFFM/",
    },
    {
        "key": "hexaco",
        "system": "HEXACO-60",
        "purpose": "Adds Honesty–Humility to the personality picture",
        "time": "10 min",
        "link": "https://hexaco.org/hexaco-online",
    },
    {
        "key": "via",
        "system": "VIA Character Strengths",
        "purpose": "Ranked character strengths",
        "time": "15 min",
        "link": "https://www.viacharacter.org/survey/account/register",
    },
    {
        "key": "enneagram",
        "system": "Enneagram",
        "purpose": "Type, wing and instinct hypotheses",
        "time": "10 min",
        "link": "https://www.truity.com/test/enneagram-personality-test",
    },
    {
        "key": "riasec",
        "system": "Holland Code (RIASEC)",
        "purpose": "Vocational interest pattern",
        "time": "10 min",
        "link": "https://www.truity.com/test/holland-code-career-test",
    },
    {
        "key": "grit",
        "system": "Grit Scale",
        "purpose": "Perseverance and consistency of interest",
        "time": "2 min",
        "link": "https://www.angeladuckworth.com/grit",
    },
    {
        "key": "ecr_r",
        "system": "ECR-R attachment",
        "purpose": "Attachment pattern, measured rather than guessed",
        "time": "10 min",
        "link": "https://openpsychometrics.org/tests/ECR.php",
    },
    {
        "key": "asrs",
        "system": "Adult ADHD Self-Report Scale (ASRS-v1.1)",
        "purpose": "Executive-function screening baseline; not a diagnosis",
        "time": "5 min",
        "link": "https://www.hcp.med.harvard.edu/ncs/asrs.php",
    },
    {
        "key": "meq",
        "system": "MEQ chronotype",
        "purpose": "Preferred timing for demanding work",
        "time": "5 min",
        "link": "https://chronotype-self-test.info/",
    },
    {
        "key": "cbi",
        "system": "Copenhagen Burnout Inventory",
        "purpose": "Personal, work-related and client-related strain baseline",
        "time": "10 min",
        "link": "https://nfa.elsevierpure.com/en/publications/the-copenhagen-burnout-inventory-a-new-tool-for-the-assessment-of/",
    },
    {
        "key": "wdq",
        "system": "Work Design Questionnaire",
        "purpose": "Task, knowledge, social and contextual work conditions",
        "time": "20 min",
        "link": "http://www.morgeson.com/wdq.html",
    },
]


def clean_cell(value: Any) -> str:
    """Make user-provided text safe inside a Markdown pipe table."""
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def display_reduction(total: int) -> str:
    value, chain = num.reduce_number(total)
    match = re.search(r"master number (\d+)/(\d+)", chain)
    return f"{match.group(1)}/{match.group(2)}" if match else str(value)


def calculate_numerology(name_en: str, birth_date: str, year: int, name_ar: str | None) -> dict[str, Any]:
    dob_digits = [int(char) for char in birth_date if char.isdigit()]
    life_total = sum(dob_digits)
    _, month, day = birth_date.split("-")
    personal_total = sum(int(char) for char in month + day + str(year))
    letters = [char for char in num.strip_accents(name_en).upper() if char.isalpha() and char in num.PYTHAGOREAN]

    def name_number(chars: list[str]) -> dict[str, Any]:
        total = sum(num.PYTHAGOREAN[char] for char in chars)
        return {"total": total, "display": display_reduction(total)}

    pinnacle_data = num.pinnacles_and_challenges(birth_date)
    active_cycle = next(
        (cycle for cycle in pinnacle_data["cycles"] if cycle["start_year"] <= year and (cycle["end_year"] is None or year <= cycle["end_year"])),
        pinnacle_data["cycles"][-1],
    )
    result: dict[str, Any] = {
        "life_path": {"total": life_total, "display": display_reduction(life_total)},
        "personal_year": {"year": year, "total": personal_total, "display": display_reduction(personal_total)},
        "pinnacles_challenges": {**pinnacle_data, "active_cycle": active_cycle},
        "name": {
            "expression": name_number(letters),
            "soul_urge": name_number([char for char in letters if char in num.VOWELS]),
            "personality": name_number([char for char in letters if char not in num.VOWELS]),
            "convention": "Pythagorean values; Y treated as a consonant",
        },
    }
    if name_ar:
        word_values: list[dict[str, Any]] = []
        total = 0
        skipped: set[str] = set()
        for word in name_ar.split():
            word_total = 0
            for char in word:
                normalized = num.ABJAD_NORMALISE.get(char, char)
                if normalized in num.ABJAD:
                    word_total += num.ABJAD[normalized]
                elif normalized.strip():
                    skipped.add(char)
            total += word_total
            word_values.append({"word": word, "value": word_total})
        result["abjad"] = {
            "words": word_values,
            "total": total,
            "display": display_reduction(total),
            "skipped": sorted(skipped),
            "convention": "Standard Abjad hawwaz order; regional orders may differ",
        }
    return result


def geocode_place(place: str) -> dict[str, Any]:
    """Resolve a human place name through the public Nominatim API."""
    query = urlencode({"q": place, "format": "jsonv2", "limit": 1})
    request = Request(
        f"https://nominatim.openstreetmap.org/search?{query}",
        headers={"User-Agent": "ikigai-report-kit/1.0 (https://github.com/example-org/ikigai-report-kit)"},
    )
    try:
        with urlopen(request, timeout=20) as response:  # noqa: S310 - fixed HTTPS endpoint
            matches = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # pragma: no cover - network path
        raise RuntimeError(f"Could not geocode {place!r}: {exc}") from exc
    if not matches:
        raise RuntimeError(f"No place found for {place!r}. Use --lat and --lon to supply coordinates directly.")
    match = matches[0]
    return {"display_name": match["display_name"], "latitude": float(match["lat"]), "longitude": float(match["lon"])}


def timezone_for_coordinates(latitude: float, longitude: float) -> str:
    try:
        from timezonefinder import TimezoneFinder
    except ImportError as exc:  # pragma: no cover - dependency path
        raise RuntimeError("timezonefinder is required for place-only input. Install it with: pip install timezonefinder") from exc
    finder = TimezoneFinder()
    timezone_name = finder.timezone_at(lat=latitude, lng=longitude) or finder.certain_timezone_at(lat=latitude, lng=longitude)
    if not timezone_name:
        raise RuntimeError("Could not determine a time zone from the coordinates. Use --tz to provide the historical UTC offset.")
    return timezone_name


def resolve_birth_location(args: argparse.Namespace) -> dict[str, Any]:
    if (args.lat is None) != (args.lon is None):
        raise RuntimeError("Provide both --lat and --lon, or neither.")
    if args.lat is not None:
        location = {"display_name": args.place or f"{args.lat:.5f}, {args.lon:.5f}", "latitude": args.lat, "longitude": args.lon}
    else:
        if not args.place:
            raise RuntimeError("Provide --place, or supply --lat and --lon.")
        location = geocode_place(args.place)

    timezone_name = args.timezone or timezone_for_coordinates(location["latitude"], location["longitude"])
    try:
        local_dt = datetime.fromisoformat(f"{args.date}T{args.time}").replace(tzinfo=ZoneInfo(timezone_name))
    except Exception as exc:
        raise RuntimeError(f"Could not apply timezone {timezone_name!r}: {exc}") from exc
    offset = local_dt.utcoffset()
    if offset is None:
        raise RuntimeError(f"Could not determine a historical UTC offset for {timezone_name}.")
    location.update({"timezone": timezone_name, "utc_offset_hours": offset.total_seconds() / 3600})
    return location


def load_tests(path: str | None) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Test-result file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Test-result file is not valid JSON: {exc}") from exc
    tests = payload.get("tests", payload)
    if not isinstance(tests, dict):
        raise RuntimeError("Test-result JSON must be an object, or contain an object named 'tests'.")
    normalized: dict[str, dict[str, Any]] = {}
    for key, value in tests.items():
        if isinstance(value, str):
            value = {"result": value}
        if not isinstance(value, dict) or not value.get("result"):
            raise RuntimeError(f"Test {key!r} needs a non-empty 'result' field.")
        normalized[key.lower().replace("-", "_").replace(" ", "_")] = value
    return normalized


def optional_import(module_name: str) -> tuple[Any | None, str | None]:
    try:
        return __import__(module_name), None
    except Exception as exc:  # dependency module errors are rendered, not hidden
        return None, f"{module_name}: {type(exc).__name__}: {exc}"


def collect_calculations(name_en: str, name_ar: str | None, args: argparse.Namespace, location: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    calculations: dict[str, Any] = {
        "numerology": calculate_numerology(name_en, args.date, args.solar_year, name_ar),
    }
    warnings: list[str] = []
    chart, issue = optional_import("chart")
    if chart:
        try:
            calculations["chart"] = chart.collect_chart(args.date, args.time, location["utc_offset_hours"], location["latitude"], location["longitude"], args.solar_year)
        except Exception as exc:
            warnings.append(f"Western/Vedic chart calculations were unavailable: {type(exc).__name__}: {exc}")
    else:
        warnings.append(f"Western/Vedic chart calculations were unavailable: {issue}")

    extended, issue = optional_import("extended_systems")
    if extended:
        try:
            birth_dt_local = datetime.fromisoformat(f"{args.date}T{args.time}")
            calculations["extended"] = {
                "bazi": extended.calculate_bazi(birth_dt_local),
                "human_design": extended.calculate_human_design(args.date, args.time, location["utc_offset_hours"]),
                "destiny_matrix": extended.calculate_destiny_matrix(date.fromisoformat(args.date)),
            }
            calculations["extended"]["gene_keys"] = extended.calculate_gene_keys(calculations["extended"]["human_design"])
        except Exception as exc:
            warnings.append(f"BaZi, Human Design, Gene Keys and Destiny Matrix were unavailable: {type(exc).__name__}: {exc}")
    else:
        warnings.append(f"BaZi, Human Design, Gene Keys and Destiny Matrix were unavailable: {issue}")

    dasha, issue = optional_import("dasha")
    if dasha:
        try:
            from jyotishganit import calculate_birth_chart
            birth_chart = calculate_birth_chart(
                birth_date=datetime.fromisoformat(f"{args.date}T{args.time}"),
                latitude=location["latitude"],
                longitude=location["longitude"],
                timezone_offset=location["utc_offset_hours"],
                name=name_en,
            )
            calculations["dasha"] = dasha.collect(birth_chart, datetime.now())
        except Exception as exc:
            warnings.append(f"Vimshottari dasha timing was unavailable: {type(exc).__name__}: {exc}")
    else:
        warnings.append(f"Vimshottari dasha timing was unavailable: {issue}")
    return calculations, warnings


def result_for(tests: dict[str, dict[str, Any]], key: str) -> dict[str, Any] | None:
    aliases = {"mbti": ("16personalities", "mbti_style"), "big_five": ("bigfive", "ipip_bffm"), "ecr_r": ("ecr", "attachment"), "asrs": ("adhd", "adhd_asrs"), "cbi": ("burnout",), "wdq": ("work_design",)}
    for candidate in (key, *aliases.get(key, ())):
        if candidate in tests:
            return tests[candidate]
    return None


def calculated_rows(calculations: dict[str, Any]) -> list[tuple[str, str, str]]:
    numerology = calculations["numerology"]
    rows: list[tuple[str, str, str]] = [
        ("Numerology — Life Path", numerology["life_path"]["display"], "Calculated from birth date; symbolic reflection."),
        ("Numerology — Personal Year", f"{numerology['personal_year']['display']} ({numerology['personal_year']['year']})", "Calculated from birth month, day and the report year; symbolic reflection."),
        ("Numerology — Pinnacles & Challenges", "; ".join(f"P{index} {cycle['pinnacle']} / C{cycle['challenge']}" for index, cycle in enumerate(numerology['pinnacles_challenges']['cycles'], start=1)), f"Current report-year cycle: P{numerology['pinnacles_challenges']['active_cycle']['pinnacle']} / C{numerology['pinnacles_challenges']['active_cycle']['challenge']}; symbolic reflection."),
        ("Numerology — Expression / Soul / Personality", f"{numerology['name']['expression']['display']} / {numerology['name']['soul_urge']['display']} / {numerology['name']['personality']['display']}", "Calculated from the supplied Latin-script name; symbolic reflection."),
    ]
    if "abjad" in numerology:
        abjad = numerology["abjad"]
        rows.append(("Abjad numerology", f"{abjad['total']} → {abjad['display']}", "Calculated using the standard Abjad hawwaz order; regional orders vary."))
    chart = calculations.get("chart")
    if chart:
        tropical = chart["tropical"]
        rows.extend([
            ("Western astrology", f"Sun {tropical['planets']['Sun']['formatted']}; Moon {tropical['planets']['Moon']['formatted']}; ASC {tropical['ascendant']['formatted']}; MC {tropical['midheaven']['formatted']}", "Calculated from birth date, local time and coordinates; symbolic reflection."),
            ("Nodal axis", f"North Node {tropical['nodes']['north']['formatted']} (House {tropical['nodes']['north']['house']}); South Node {tropical['nodes']['south']['formatted']} (House {tropical['nodes']['south']['house']})", "Calculated chart position; symbolic reflection."),
            ("Vedic astrology", f"Sidereal ASC {chart['sidereal']['ascendant']['formatted']}; Moon {chart['sidereal']['planets']['Moon']['nakshatra']} pada {chart['sidereal']['planets']['Moon']['pada']}", "Lahiri ayanamsa; symbolic reflection."),
            ("Vedic Panchanga", f"{chart['panchanga']['vara']}; {chart['panchanga']['tithi']['paksha']} {chart['panchanga']['tithi']['name']} ({chart['panchanga']['tithi']['number']}); {chart['panchanga']['nakshatra']['name']}; {chart['panchanga']['yoga']['name']}; {chart['panchanga']['karana']}", "Instantaneous natal five-limb Panchanga using Lahiri positions; not a sunrise-based almanac."),
            ("Vedic D9 (Navamsa)", f"D9 lagna {chart['d9']['lagna']}; 9th-house sign {chart['d9']['ninth_house_sign']}", "Lahiri ninth-division chart; symbolic reflection."),
            ("Vedic D10 (career chart)", f"D10 lagna {chart['d10']['lagna']}; 10th-house sign {chart['d10']['tenth_house_sign']}", "Lahiri career divisional-chart data; symbolic reflection."),
            ("Solar return", f"{chart['solar_return']['exact_return_local']}; ASC {chart['solar_return']['ascendant']['formatted']}; MC {chart['solar_return']['midheaven']['formatted']}", "Calculated for the report year; symbolic reflection."),
            ("Astrocartography", "MC/IC longitudes generated for Sun, Moon, Mercury, Venus, Mars, Jupiter and Saturn", "MC/IC lines only; Ascendant/Descendant curves need a mapping tool."),
        ])
    extended = calculations.get("extended")
    if extended:
        bazi = extended["bazi"]
        p = bazi["pillars"]
        rows.extend([
            ("Chinese zodiac / BaZi", f"{bazi['zodiac_animal']}; {p['year']['stem']['name']} {p['year']['branch']['name']} / {p['month']['stem']['name']} {p['month']['branch']['name']} / {p['day']['stem']['name']} {p['day']['branch']['name']} / {p['hour']['stem']['name']} {p['hour']['branch']['name']}", "Deterministic implementation; see limitations for the day-pillar anchor."),
            ("Human Design", f"{extended['human_design']['type']} · {extended['human_design']['profile']} · {extended['human_design']['authority']}", "Computed from the implemented gate/channel model; symbolic reflection."),
            ("Gene Keys — Activation", f"Life's Work {extended['gene_keys']['activation_sequence']['life_work']}; Evolution {extended['gene_keys']['activation_sequence']['evolution']}; Radiance {extended['gene_keys']['activation_sequence']['radiance']}; Purpose {extended['gene_keys']['activation_sequence']['purpose']}", "Direct gate-to-Gene-Key mapping; symbolic reflection."),
            ("Gene Keys — Venus & Pearl", f"Attraction {extended['gene_keys']['venus_sequence']['attraction']}; Core/Vocation {extended['gene_keys']['venus_sequence']['core']}; Culture {extended['gene_keys']['pearl_sequence']['culture']}; Pearl {extended['gene_keys']['pearl_sequence']['pearl']}", "Full Golden Path sphere mapping; coordinates only, not interpretive prose."),
            ("Gene Keys — Star Pearl", f"Creativity {extended['gene_keys']['star_pearl_sequence']['creativity']}; Relating {extended['gene_keys']['star_pearl_sequence']['relating']}; Stability {extended['gene_keys']['star_pearl_sequence']['stability']}", "Extended sphere mapping; coordinates only, not interpretive prose."),
            ("Destiny Matrix", f"Day {extended['destiny_matrix']['core']['day_arcana']}; Month {extended['destiny_matrix']['core']['month_arcana']}; Year {extended['destiny_matrix']['core']['year_arcana']}; Destiny {extended['destiny_matrix']['core']['destiny_arcana']}", "Deterministic Matrix of Destiny 22 reduction; symbolic reflection."),
        ])
    dasha = calculations.get("dasha")
    if dasha:
        maha = dasha["mahadasha"]
        antara = dasha["antardasha"]
        rows.append(("Vimshottari dasha", f"{maha['lord']} mahadasha ({maha['start'][:10]} → {maha['end'][:10]}); current {antara['lord']} antardasha ({antara['start'][:10]} → {antara['end'][:10]})", "Computed timing system. It uses True Chitra Paksha, which can differ slightly from Lahiri near boundaries."))
    return rows


def markdown_table(headers: list[str], rows: list[tuple[Any, ...]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out.extend("| " + " | ".join(clean_cell(cell) for cell in row) + " |" for row in rows)
    return "\n".join(out)


def render_report(name_en: str, name_ar: str | None, args: argparse.Namespace, location: dict[str, Any], calculations: dict[str, Any], warnings: list[str], tests: dict[str, dict[str, Any]]) -> str:
    prepared = datetime.now().strftime("%-d %B %Y")
    title_name = clean_cell(name_en)
    date_label = datetime.fromisoformat(args.date).strftime("%-d %B %Y")
    measured_rows: list[tuple[str, str, str]] = []
    missing_tests: list[dict[str, str]] = []
    for item in TEST_CATALOG:
        supplied = result_for(tests, item["key"])
        if supplied:
            interpretation = supplied.get("interpretation") or supplied.get("notes") or "Result supplied by the report recipient; retain the original test context."
            measured_rows.append((item["system"], supplied["result"], interpretation))
        else:
            missing_tests.append(item)
    extra_tests = [(key, value) for key, value in tests.items() if not any(result_for(tests, item["key"]) is value for item in TEST_CATALOG)]
    for key, value in extra_tests:
        measured_rows.append((key.replace("_", " ").title(), value["result"], value.get("interpretation") or value.get("notes") or "Result supplied by the report recipient."))

    header = f'''<div class="doc-title">IKIGAI CALCULATION REPORT</div>
<div class="doc-name">{title_name}</div>
<div class="doc-meta">Born {date_label} · {clean_cell(location['display_name'])} · {args.time} local</div>
<div class="doc-prepared">Generated {prepared} · Birth-data-first edition</div>

# 1. What this report can calculate

> **Birth data calculates chart and name systems. It does not calculate personality, diagnosis, values, skills or vocation.**

This report is a reproducible calculation record built from the supplied name, date, local birth time and place. It includes every deterministic system currently implemented in the kit. Results from psychometric or wellbeing tests appear only when the person has actually supplied them; otherwise, the missing tests are listed with links at the end.

| Input | Resolved value |
|---|---|
| Full name (Latin script) | {title_name} |
| Birth date and local time | {args.date} · {args.time} |
| Birth place | {clean_cell(location['display_name'])} |
| Coordinates | {location['latitude']:.5f}, {location['longitude']:.5f} |
| Time zone at birth | {location['timezone']} (UTC{location['utc_offset_hours']:+g}) |
| Arabic-script name | {clean_cell(name_ar) if name_ar else 'Not supplied — Abjad is omitted'} |

<p class="note">Time-zone resolution uses the place coordinates and the historical zone rule for the supplied date. Verify the birth time against an official record when accuracy matters: changing it can alter houses, Ascendant, Human Design lines and divisional charts.</p>

# 2. Evidence ledger {{.newpage}}

## How to read this report

| Group | What it means | Weight |
|---|---|---|
| A. Measured | A completed test result was supplied. | Strongest for the construct it actually measures. |
| B. Calculated | Deterministically calculated from name and/or birth data. | Reproducible calculation; symbolic systems are reflective, not validated predictors. |
| C. Not inferred | No personality or wellbeing label is guessed from birth data. | Intentionally omitted until measured. |

## Group A — supplied measurements

{markdown_table(['System', 'Supplied result', 'Report note'], measured_rows) if measured_rows else 'No test results were supplied. The report therefore makes no measured personality, wellbeing or career claims.'}

## Group B — calculated systems

{markdown_table(['System', 'Calculated result', 'Method boundary'], calculated_rows(calculations))}

# 3. Calculation detail {{.newpage}}

## Birth-time sensitivity

'''
    sensitivity = calculations.get("chart", {}).get("birth_time_sensitivity")
    if sensitivity:
        if "local_time" in sensitivity:
            header += f"The Ascendant leaves **{sensitivity['leaves_sign']}** and enters **{sensitivity['enters_sign']}** at approximately **{sensitivity['local_time']} local time**. If the reported birth time is close to that point, present both possibilities rather than treating one as certain.\n\n"
        else:
            header += f"The Ascendant remains in **{sensitivity['start_sign']}** for at least the next **{sensitivity['stable_for_at_least_hours']} hours** after the stated time.\n\n"
    else:
        header += "Birth-time sensitivity could not be calculated in this run; see the calculation status below.\n\n"

    detail_rows: list[tuple[str, str]] = []
    pinnacle_cycles = calculations["numerology"]["pinnacles_challenges"]["cycles"]
    detail_rows.append(("Numerology Pinnacles & Challenges", "; ".join(f"P{index} {cycle['pinnacle']} / C{cycle['challenge']}, ages {cycle['start_age']}–{cycle['end_age'] if cycle['end_age'] is not None else '∞'} ({cycle['start_year']}–{cycle['end_year'] if cycle['end_year'] is not None else 'onward'})" for index, cycle in enumerate(pinnacle_cycles, start=1))))
    chart = calculations.get("chart")
    if chart:
        detail_rows.append(("Tropical chart", "; ".join(f"{name} {value['formatted']}" for name, value in chart['tropical']['planets'].items() if value.get('available', True))))
        detail_rows.append(("Sidereal Moon", f"{chart['sidereal']['planets']['Moon']['formatted']} · {chart['sidereal']['planets']['Moon']['nakshatra']} pada {chart['sidereal']['planets']['Moon']['pada']}"))
        panchanga = chart["panchanga"]
        detail_rows.append(("Vedic Panchanga", f"Vara {panchanga['vara']}; Tithi {panchanga['tithi']['paksha']} {panchanga['tithi']['name']} #{panchanga['tithi']['number']}; Nakshatra {panchanga['nakshatra']['name']} #{panchanga['nakshatra']['index']}; Yoga {panchanga['yoga']['name']} #{panchanga['yoga']['index']}; Karana {panchanga['karana']}"))
        detail_rows.append(("D9 Navamsa chart", "; ".join(f"{name} {value['sign']} house {value['house']}" for name, value in chart['d9']['planets'].items())))
        detail_rows.append(("D10 career chart", "; ".join(f"{name} {value['sign']} house {value['house']}" for name, value in chart['d10']['planets'].items())))
        detail_rows.append(("Astrocartography", "; ".join(f"{name}: MC {values['mc_longitude']:+.1f}°, IC {values['ic_longitude']:+.1f}°" for name, values in chart['astrocartography']['lines'].items())))
    extended = calculations.get("extended")
    if extended:
        detail_rows.append(("Human Design", f"Strategy: {extended['human_design']['strategy']}; defined centres: {', '.join(extended['human_design']['defined_centers']) or 'none'}; defined channels: {', '.join(extended['human_design']['defined_channels']) or 'none'}"))
        detail_rows.append(("Gene Keys Golden Path", f"Venus: Attraction {extended['gene_keys']['venus_sequence']['attraction']}, IQ {extended['gene_keys']['venus_sequence']['iq']}, EQ {extended['gene_keys']['venus_sequence']['eq']}, SQ {extended['gene_keys']['venus_sequence']['sq']}, Core {extended['gene_keys']['venus_sequence']['core']}; Pearl: Culture {extended['gene_keys']['pearl_sequence']['culture']}, Pearl {extended['gene_keys']['pearl_sequence']['pearl']}"))
        detail_rows.append(("BaZi", json.dumps(extended['bazi']['pillars'], ensure_ascii=False).replace('"', '')))
    if calculations.get("dasha"):
        detail_rows.append(("Dasha as of generation", json.dumps(calculations['dasha']['mahadasha'], ensure_ascii=False).replace('"', '')))
    header += markdown_table(["Calculation", "Detail"], detail_rows) if detail_rows else "No detailed chart calculations were available in this run.\n"

    header += '''

# 4. Measurement links — complete only what will change a decision {.newpage}

> **Use a test only when its result will change a practical choice: role, workload, boundary, support or recovery plan.**

'''
    if missing_tests:
        header += markdown_table(["Test", "What it would add", "Time", "Link"], [(item["system"], item["purpose"], item["time"], f"<{item['link']}>") for item in missing_tests])
    else:
        header += "All core measurement links in this version have a supplied result. Retain the original results separately and repeat only when a decision or a seasonal change makes a new baseline useful.\n"

    header += f'''

# 5. Calculation status and limitations {{.newpage}}

'''
    if warnings:
        header += "## Unavailable in this run\n\n" + "\n".join(f"- {clean_cell(warning)}" for warning in warnings) + "\n\n"
    header += f'''
## Method boundaries

Psychometrics, vocational-interest instruments and wellbeing screeners measure their own stated constructs when completed; this generator does not recreate them from birth data. Numerology, astrology, Human Design, Gene Keys, BaZi and the Destiny Matrix are included as reproducible reflective systems, not as validated predictors of character, health, future outcomes or career fit.

The implementation has known technical limitations, documented in the repository README. In particular, Human Design lines may be near-boundary sensitive, the Human Design channel table is incomplete, and the BaZi day-pillar anchor needs independent validation. Vimshottari dasha uses a different ayanamsa convention from the Lahiri chart output, so boundary values may differ slightly.

## Reproduce this report

```bash
python3 scripts/generate_report.py \\
  --name "{name_en}" \\
  --date {args.date} --time {args.time} \\
  --place "{location['display_name']}" \\
  --out report.md
```

Add `--tests tests.json` when verified test results are available. Run `./build.sh report.md` to create the styled PDF after installing the build dependencies.
'''
    return header


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an Ikigai calculation report from birth data and optional verified test results.")
    parser.add_argument("--name", required=True, help="full name in Latin script")
    parser.add_argument("--name-ar", help="optional full name in Arabic script, for Abjad numerology")
    parser.add_argument("--date", required=True, help="birth date: YYYY-MM-DD")
    parser.add_argument("--time", required=True, help="local birth time: HH:MM, 24-hour clock")
    parser.add_argument("--place", help="birth place, for example: Sample City, Example Country")
    parser.add_argument("--lat", type=float, help="optional latitude; supply both --lat and --lon to skip geocoding")
    parser.add_argument("--lon", type=float, help="optional longitude; supply both --lat and --lon to skip geocoding")
    parser.add_argument("--timezone", help="optional IANA zone, for example Asia/Riyadh; overrides automatic lookup")
    parser.add_argument("--solar-year", type=int, default=datetime.now().year, help="year for Personal Year and Solar Return (default: current year)")
    parser.add_argument("--tests", help="optional JSON file of verified test results")
    parser.add_argument("--out", default="ikigai-calculation-report.md", help="Markdown output path")
    parser.add_argument("--data-out", help="optional JSON path for raw calculation data")
    args = parser.parse_args()

    try:
        datetime.fromisoformat(f"{args.date}T{args.time}")
        location = resolve_birth_location(args)
        tests = load_tests(args.tests)
        calculations, warnings = collect_calculations(args.name, args.name_ar, args, location)
        report = render_report(args.name, args.name_ar, args, location, calculations, warnings, tests)
    except RuntimeError as exc:
        parser.error(str(exc))
    except ValueError as exc:
        parser.error(f"Invalid date, time or input value: {exc}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    if args.data_out:
        raw_path = Path(args.data_out)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(json.dumps({"location": location, "calculations": calculations, "warnings": warnings}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"built Markdown report: {out_path}")
    if warnings:
        print(f"completed with {len(warnings)} calculation warning(s); see the report status section")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
