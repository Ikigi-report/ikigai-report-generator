# Ikigai Report Kit

Generate a **reproducible, evidence-aware personal calculation report** from four inputs: full name, birth date, local birth time, and birth place. The generator calculates every deterministic system currently implemented in this repository, then adds verified psychometric or wellbeing results only when the recipient provides them.

> **Birth data can calculate chart and name systems. It cannot truthfully calculate personality, diagnosis, values, skills, mental health, or vocation.**

That distinction is built into the output. Calculated systems appear as **Group B**, supplied test results appear as **Group A**, and anything not measured is left unclaimed with optional test links at the end.

## The one-command workflow

```bash
python3 scripts/generate_report.py \
  --name "Casey Example" \
  --date 1990-01-15 --time 14:30 \
  --place "Greenwich, London, United Kingdom" \
  --out alex-example-report.md \
  --data-out alex-example-calculations.json
```

The generator resolves the place to coordinates, identifies its time zone, calculates the historical UTC offset for the supplied birth date, produces a report-ready Markdown file, and can also save the raw calculations as JSON.

| Required input | Example | Why it matters |
|---|---|---|
| Full name in Latin script | `Casey Example` | Pythagorean name numerology |
| Birth date | `1990-01-15` | All date-based systems |
| Local birth time | `14:30` | Houses, Ascendant, Human Design, divisional charts and timing |
| Birth place | `Greenwich, London, United Kingdom` | Coordinates and historical time-zone rule |

Add `--name-ar "اسم عربي كامل"` when an Arabic-script name is available. This adds the Abjad calculation; it is otherwise omitted cleanly.

## What the generator calculates today

| Input basis | Calculated systems | Report treatment |
|---|---|---|
| Birth date + name | Life Path, Personal Year, Pinnacles and Challenges, Expression, Soul Urge and Personality numbers; Abjad when Arabic name is supplied | Symbolic, reproducible calculation |
| Birth date + time + place | Tropical natal positions, Ascendant, Midheaven, lunar nodes, birth-time sensitivity, solar return and MC/IC astrocartography lines | Symbolic, reproducible calculation |
| Birth date + time + place | Sidereal Lahiri positions and nakshatra/pada, five-limb Panchanga, Navamsa D9, D10 career-chart positions, Vimshottari dasha timing | Symbolic, reproducible calculation |
| Birth date + time | Chinese zodiac, BaZi pillars, Human Design type/profile/centres/channels, full Gene Keys Golden Path sphere coordinates, Destiny Matrix 22 reduction | Symbolic, reproducible calculation |

The generator contains all the systems the current code can calculate. It does **not** pretend to calculate systems that are not implemented, such as Mayan Tzolkin, Nine Star Ki, full Ascendant/Descendant astrocartography curves, a full Gene Keys interpretive text library, or professionally administered psychological assessments.

## What is optional: real test results

Psychometric, vocational-interest and wellbeing results are **optional additions**, not requirements. If a recipient has results, give them in a JSON file using [`examples/test-results.example.json`](examples/test-results.example.json) as the shape:

```bash
python3 scripts/generate_report.py \
  --name "Casey Example" \
  --date 1990-01-15 --time 14:30 \
  --place "Greenwich, London, United Kingdom" \
  --tests examples/test-results.example.json \
  --out alex-example-report.md
```

| If the recipient provides… | The report does… |
|---|---|
| A verified result in `tests.json` | Adds it to **Group A — supplied measurements** with the supplied source note. |
| No result | Leaves the construct unclaimed and lists the relevant test link in **Measurement links**. |
| A result from a test not in the standard list | Includes it as an additional supplied measurement without treating it as birth-data output. |

The standard optional links cover Big Five, HEXACO, VIA Character Strengths, Enneagram, RIASEC, Grit, ECR-R, ASRS-v1.1, chronotype, Copenhagen Burnout Inventory, and the Work Design Questionnaire. An ASRS result is always described as a screening/support-planning baseline—not a diagnosis.

## Install once

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

The first Vimshottari dasha run downloads its JPL ephemeris data. To build a PDF as well, install Pandoc and use a Chromium-based browser:

```bash
./build.sh alex-example-report.md
```

The generator needs internet only when you pass `--place` and want it to resolve coordinates automatically. For an offline or controlled workflow, supply coordinates and an IANA time zone directly:

```bash
python3 scripts/generate_report.py \
  --name "Casey Example" \
  --date 1990-01-15 --time 14:30 \
  --lat 51.4779 --lon -0.0015 --timezone Europe/London \
  --out alex-example-report.md
```

## Output files

| File | Purpose |
|---|---|
| `report.md` | Clean report source, ready to edit or convert to PDF with `build.sh` |
| `calculations.json` | Raw calculated data for audit, a web application, or later report expansion |
| `tests.json` | Optional recipient-supplied test results only; it is never generated from birth data |

The Markdown output has five parts: input verification, evidence ledger, detailed calculation record, links for uncompleted tests, and clear implementation limitations.

## Inputs and accuracy checks

Birth time is the sensitive input. The report automatically states whether the Ascendant changes within the next four hours and, if so, gives the transition time. Confirm close calls against an official record before relying on house-dependent, Human Design or divisional-chart output.

Place lookup uses the public [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/) service. Always check the resolved place and coordinates printed in the report. If a place name is ambiguous, rerun with `--lat`, `--lon` and `--timezone`.

## Method boundaries

The report separates **calculated** from **measured** evidence by design. The psychometric tests in the optional appendix have research behind them within their stated limits. Numerology, astrology, Human Design, Gene Keys, BaZi and the Destiny Matrix are reflective systems, not validated predictors of personality, health, future outcomes or career fit.

Technical constraints currently documented in the code still apply:

- Human Design lines can be near-boundary sensitive because of the underlying ephemeris convention, and the channel table is incomplete.
- The BaZi day-pillar anchor is deterministic but needs independent validation before high-stakes use.
- The dasha module uses True Chitra Paksha while the chart module’s sidereal output uses Lahiri, so boundary values may differ slightly.
- MC/IC astrocartography lines are calculated; Ascendant/Descendant curves need a dedicated mapping implementation.
- Gene Keys outputs are calculated sphere coordinates from the official natal/design activation mapping; the kit does not reproduce proprietary interpretive prose. The mapping source is documented in [`docs/expansion-research.md`](docs/expansion-research.md).
- Navamsa D9 uses the same Lahiri sidereal convention as the kit’s existing D10 implementation and remains a symbolic divisional-chart output.
- Panchanga records the five instantaneous natal limbs—Vara, Tithi, Nakshatra, Yoga and Karana—at the supplied birth moment. It is not a location-specific sunrise almanac.
- Pinnacles and Challenges use one documented Pythagorean reduction convention, including the first-cycle age boundary of `36 − Life Path`; different numerology traditions may present timing differently.

## Developer commands

```bash
# Run the repository tests
.venv/bin/python tests/test_kit.py

# Generate Markdown from a fully specified input
.venv/bin/python scripts/generate_report.py --help

# Inspect the individual calculation tools
.venv/bin/python scripts/chart.py --help
.venv/bin/python scripts/dasha.py --help
.venv/bin/python scripts/extended_systems.py --help
.venv/bin/python scripts/numerology.py --help
```

## Repository map

| Path | Role |
|---|---|
| `scripts/generate_report.py` | Universal generator: input resolution, calculations, optional test-results logic and report rendering |
| `scripts/chart.py` | Western/Vedic chart, Panchanga, Navamsa D9, D10, solar return and astrocartography; also supports `--json` |
| `scripts/dasha.py` | Current Vimshottari mahadasha and antardasha timing |
| `scripts/extended_systems.py` | BaZi, Human Design, full Gene Keys Golden Path sphere coordinates and Destiny Matrix |
| `scripts/numerology.py` | Life Path, Personal Year, Pinnacles and Challenges, Pythagorean name figures and Arabic Abjad |
| `template/report-template.md` | Long-form human-authored report template for an expanded, curated report |
| `template/v7-measurement-layer.md` | Optional V7 measurement section for reports with completed WDQ, HEXACO, ASRS and CBI data |
| `examples/test-results.example.json` | Safe shape for optional verified test inputs |
| `build.sh` | Markdown-to-PDF build script |

## Licence

MIT. No warranty. This repository is not medical, psychological, legal, financial or clinical advice.

The Swiss Ephemeris behind `pyswisseph` is dual-licensed: AGPL-3.0 or a paid commercial licence from Astrodienst. This repository does not bundle or redistribute it; check the relevant licence before shipping a closed-source product built on it.
