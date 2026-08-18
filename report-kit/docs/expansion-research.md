# Calculation Expansion Research

## Gene Keys full profile mapping

The official Gene Keys documentation maps Golden Path spheres to natal and pre-natal/design activations as follows:

| Sphere | Activation |
|---|---|
| Life’s Work / Brand | Natal Sun |
| Evolution | Natal Earth |
| Radiance | Pre-natal / Design Sun |
| Purpose | Pre-natal / Design Earth |
| Attraction | Pre-natal / Design Moon |
| IQ | Natal Venus |
| EQ | Natal Mars |
| SQ | Pre-natal / Design Venus |
| Core / Vocation | Pre-natal / Design Mars |
| Culture | Pre-natal / Design Jupiter |
| Pearl | Natal Jupiter |
| Creativity | Pre-natal / Design Uranus |
| Relating | Natal Mercury |
| Stability | Pre-natal / Design Saturn |

This supports extending the current Activation Sequence into deterministic Venus, Pearl and expanded three-sphere profile data, using the project’s existing Human Design activation calculations. Source: [Gene Keys official documentation](https://genekeys.com/docs/what-planets-does-each-sphere-of-the-golden-path-profile-correlate-to/), accessed 15 August 2026.

## Vedic Navamsa D9

Navamsa D9 is a ninth subdivision of a 30-degree sign. It is calculated from sidereal positions and must be labelled as a symbolic Vedic divisional-chart output. The kit will use Lahiri sidereal positions, matching its existing Vedic/D10 implementation. Source: [Astro-Seek Navamsa D9 calculator documentation](https://horoscopes.astro-seek.com/navamsa-9-harmonic-chart-astrology-calculator), accessed 15 August 2026.

## Editorial boundary

Both extensions are deterministic output from the supplied birth data under their stated conventions. They are not evidence-based assessments and must remain in Group B, with no claims of predictive validity.

## Vedic Panchanga

Panchanga is calculated here as five components: **Vara** (weekday), **Nakshatra** (Moon’s sidereal lunar mansion), **Tithi** (Sun–Moon angular difference divided into 12-degree units), **Yoga** (sum of sidereal Sun and Moon longitudes divided into 13°20′ units), and **Karana** (half a Tithi, or 6-degree Sun–Moon angular units). The implementation records the instantaneous values at the supplied birth moment and uses the kit’s Lahiri sidereal convention for Nakshatra and Yoga. Sources: [Komilla Sutton, *Personal Panchanga*](https://komilla.com/lib-personal-panchang.html); [Panchanga calculation overview](https://www.melooha.com/blog/panchanga), accessed 15 August 2026.

## Numerology Pinnacles and Challenges

The chosen Pythagorean convention reduces birth month, day and year components while preserving master-number display for Pinnacles. Pinnacles are: P1 = month + day; P2 = day + year; P3 = P1 + P2; P4 = month + year. Challenges are absolute differences: C1 = |month − day|; C2 = |day − year|; C3 = |C1 − C2|; C4 = |month − year|. The first Pinnacle ends at age `36 − Life Path`; the second and third run for nine years each; the fourth continues thereafter. Source: [Hans Decoz, *Pinnacle Cycles*](https://www.worldnumerology.com/numerology-pinnacles/), accessed 15 August 2026. These remain symbolic numerology output, not a validated forecast.
