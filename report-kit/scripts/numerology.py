#!/usr/bin/env python3
"""
Numerology calculator for the Ikigai Report Kit.

Computes:
  - Life Path, and the Personal Year for a chosen year
  - Expression, Soul Urge and Personality numbers (Pythagorean, from a Latin-script name)
  - Abjad values (standard abjad hawwaz order, from an Arabic-script name)

Master numbers 11, 22 and 33 are reported in the conventional "11/2" form.
No third-party dependencies.

Example:
  python numerology.py --dob 1990-01-15 \
                       --name-en "Your Full Name" \
                       --name-ar "اسمك الكامل" \
                       --year 2026
"""
from __future__ import annotations

import argparse
import unicodedata

PYTHAGOREAN = {c: (i % 9) + 1 for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
VOWELS = set("AEIOU")

# Standard abjad hawwaz values.
ABJAD = {
    "ا": 1, "ب": 2, "ج": 3, "د": 4, "ه": 5, "و": 6, "ز": 7, "ح": 8, "ط": 9,
    "ي": 10, "ك": 20, "ل": 30, "م": 40, "ن": 50, "س": 60, "ع": 70, "ف": 80,
    "ص": 90, "ق": 100, "ر": 200, "ش": 300, "ت": 400, "ث": 500, "خ": 600,
    "ذ": 700, "ض": 800, "ظ": 900, "غ": 1000,
}

# Letter forms that carry the value of their base letter.
ABJAD_NORMALISE = {
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ئ": "ي",
    "ؤ": "و", "ة": "ه", "ﻻ": "ا",
}

MASTERS = (11, 22, 33)


def reduce_number(total: int) -> tuple[int, str]:
    """Reduce to a single digit, stopping to note any master number on the way."""
    chain = [total]
    value = total
    while value > 9:
        value = sum(int(d) for d in str(value))
        chain.append(value)
        if value in MASTERS:
            final = sum(int(d) for d in str(value))
            chain.append(final)
            return final, " -> ".join(str(c) for c in chain) + f"   (master number {value}/{final})"
    return value, " -> ".join(str(c) for c in chain)


def life_path(dob: str) -> None:
    digits = [int(c) for c in dob if c.isdigit()]
    total = sum(digits)
    value, chain = reduce_number(total)
    print("\n=== LIFE PATH ===")
    print(f"  digits of {dob}: {' + '.join(str(d) for d in digits)} = {total}")
    print(f"  {chain}")
    print(f"  Life Path: {value}")


def personal_year(dob: str, year: int) -> None:
    _, month, day = dob.split("-")
    total = sum(int(c) for c in month + day + str(year))
    value, chain = reduce_number(total)
    print(f"\n=== PERSONAL YEAR {year} ===")
    print(f"  month + day + year digits = {total}")
    print(f"  {chain}")
    print(f"  Personal Year: {value}")


def reduce_single(total: int) -> int:
    """Reduce to one digit, intentionally not retaining master numbers."""
    while total > 9:
        total = sum(int(digit) for digit in str(total))
    return total


def reduce_pinnacle(total: int) -> int:
    """Reduce a Pinnacle value, retaining 11, 22 and 33 if reached."""
    while total > 9 and total not in MASTERS:
        total = sum(int(digit) for digit in str(total))
    return total


def display_pinnacle(value: int) -> str:
    """Render a Pinnacle master number in the familiar master/reduced form."""
    return f"{value}/{sum(int(digit) for digit in str(value))}" if value in MASTERS else str(value)


def pinnacles_and_challenges(dob: str) -> dict:
    """Calculate the four Pythagorean Pinnacles and Challenges from a birth date.

    Month, day and year are reduced to a single digit before combination. Pinnacle
    combinations retain a terminal master number; Challenges always reduce to a
    single digit. The first cycle ends at age 36 minus the reduced Life Path,
    followed by two nine-year cycles and an open-ended fourth cycle.
    """
    year, month, day = (int(part) for part in dob.split("-"))
    month_value = reduce_single(month)
    day_value = reduce_single(day)
    year_value = reduce_single(sum(int(digit) for digit in str(year)))
    life_path = reduce_single(sum(int(digit) for digit in dob if digit.isdigit()))

    p1 = reduce_pinnacle(month_value + day_value)
    p2 = reduce_pinnacle(day_value + year_value)
    p3 = reduce_pinnacle(p1 + p2)
    p4 = reduce_pinnacle(month_value + year_value)
    c1 = reduce_single(abs(month_value - day_value))
    c2 = reduce_single(abs(day_value - year_value))
    c3 = reduce_single(abs(c1 - c2))
    c4 = reduce_single(abs(month_value - year_value))

    first_end_age = 36 - life_path
    second_start_age = first_end_age + 1
    second_end_age = second_start_age + 8
    third_start_age = second_end_age + 1
    third_end_age = third_start_age + 8
    fourth_start_age = third_end_age + 1
    cycles = [
        {"pinnacle": display_pinnacle(p1), "challenge": c1, "start_age": 0, "end_age": first_end_age, "start_year": year, "end_year": year + first_end_age},
        {"pinnacle": display_pinnacle(p2), "challenge": c2, "start_age": second_start_age, "end_age": second_end_age, "start_year": year + second_start_age, "end_year": year + second_end_age},
        {"pinnacle": display_pinnacle(p3), "challenge": c3, "start_age": third_start_age, "end_age": third_end_age, "start_year": year + third_start_age, "end_year": year + third_end_age},
        {"pinnacle": display_pinnacle(p4), "challenge": c4, "start_age": fourth_start_age, "end_age": None, "start_year": year + fourth_start_age, "end_year": None},
    ]
    return {
        "method": "Pythagorean Pinnacles and Challenges: reduced month/day/year combinations",
        "base_numbers": {"month": month_value, "day": day_value, "year": year_value, "life_path": life_path},
        "pinnacles": [p1, p2, p3, p4],
        "challenges": [c1, c2, c3, c4],
        "cycles": cycles,
    }


def print_pinnacles_and_challenges(dob: str) -> None:
    data = pinnacles_and_challenges(dob)
    print("\n=== PINNACLES & CHALLENGES ===")
    for index, cycle in enumerate(data["cycles"], start=1):
        window = f"{cycle['start_year']}–{cycle['end_year']}" if cycle["end_year"] else f"{cycle['start_year']} onward"
        print(f"  Pinnacle {index}: {cycle['pinnacle']:<5} Challenge {cycle['challenge']}  ages {cycle['start_age']}–{cycle['end_age'] if cycle['end_age'] is not None else '∞'}  ({window})")


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text)
                   if unicodedata.category(c) != "Mn")


def english_name(name: str) -> None:
    letters = [c for c in strip_accents(name).upper() if c.isalpha() and c in PYTHAGOREAN]
    if not letters:
        return
    vowels = [c for c in letters if c in VOWELS]
    consonants = [c for c in letters if c not in VOWELS]
    print(f"\n=== PYTHAGOREAN — {name} ===")
    for label, group in (("Expression (all letters)", letters),
                         ("Soul Urge (vowels)", vowels),
                         ("Personality (consonants)", consonants)):
        total = sum(PYTHAGOREAN[c] for c in group)
        value, chain = reduce_number(total)
        print(f"  {label:<26} {chain}  =>  {value}")
    print("  Note: Y is treated as a consonant here. Some traditions count it as a vowel")
    print("  when it carries the vowel sound; if that applies to your name, compute both.")


def arabic_name(name: str) -> None:
    print(f"\n=== ABJAD — {name} ===")
    grand_total = 0
    unknown: set[str] = set()
    for word in name.split():
        word_total = 0
        for ch in word:
            ch = ABJAD_NORMALISE.get(ch, ch)
            if ch in ABJAD:
                word_total += ABJAD[ch]
            elif unicodedata.category(ch) != "Mn":   # ignore diacritics silently
                unknown.add(ch)
        grand_total += word_total
        print(f"  {word:<14} = {word_total}")
    value, chain = reduce_number(grand_total)
    print(f"  {'TOTAL':<14} = {grand_total}")
    print(f"  {chain}  =>  {value}")
    if unknown:
        print(f"  Skipped unrecognised characters: {' '.join(sorted(unknown))}")
    print("  Note: regional abjad orders differ; totals vary between traditions.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Numerology figures for an Ikigai report.")
    ap.add_argument("--dob", help="date of birth, YYYY-MM-DD")
    ap.add_argument("--name-en", help="full name in Latin script")
    ap.add_argument("--name-ar", help="full name in Arabic script")
    ap.add_argument("--year", type=int, help="year for the Personal Year figure")
    args = ap.parse_args()

    if not any((args.dob, args.name_en, args.name_ar)):
        ap.error("give at least one of --dob, --name-en, --name-ar")

    if args.dob:
        life_path(args.dob)
        print_pinnacles_and_challenges(args.dob)
        if args.year:
            personal_year(args.dob, args.year)
    if args.name_en:
        english_name(args.name_en)
    if args.name_ar:
        arabic_name(args.name_ar)
    print()


if __name__ == "__main__":
    main()
