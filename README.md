# CLA Earnings Comparison

Public-facing earnings data for College of Liberal Arts majors at Cal Poly SLO,
comparing our graduates against graduates of the same major at **other public
universities**. Source: U.S. Department of Education, College Scorecard Field of
Study data (https://collegescorecard.ed.gov/data/).

This repo is the single source of truth for the numbers. Charts embedded on
department websites read the CSV files in `data/`, so updating the data here
updates every chart.

## Earnings horizons and the year

Earnings are reported 1 year, 4 years, and 5 years after graduating. The **4-year
figure is the standard** for public charts: settled enough to be meaningful,
recent enough to be relevant. Important: each horizon comes from a different
graduating cohort measured in a different year, so they are separate snapshots,
not the same students tracked over time. Do not combine them into one trend chart.

Every data file is stamped with the graduating cohort and dollar year so the
timing is always visible. The full detail lives in `data/cla_earnings_summary.csv`,
which carries cohort year and measurement year as columns.

## What's in here

    config/cla_majors.csv       Which majors count as CLA. Edit to add, remove, or
                                exclude a major.
    config/earnings_metrics.csv Which raw file and column each horizon comes from,
                                plus its cohort year, measurement year, and dollars.
    scripts/build_cla_earnings.py  Turns the raw Scorecard files into the CSVs below.
    data/cla_earnings_summary.csv  Every major and horizon in one table, with years.
    data/by_major/<slug>.csv    The default 4-year file for each major.
    data/by_major/<slug>_1yr.csv, _5yr.csv  The other horizons, where data exists.
    data/schools/<slug>.csv     Every institution nationally with data for that
                                major, named, with state and control, sorted high
                                to low, Cal Poly flagged. Use this to compare any
                                school against any other and highlight your picks.
    data/cla_benchmarks.csv     Per major: Cal Poly's figure, the public-university
                                median (computed), the UC-system median (computed),
                                and the official national median across all
                                institutions (Dept of Education), plus counts and
                                Cal Poly's percentile against each pool.

## Two ways to compare

1. Against a benchmark: use `data/by_major/<slug>.csv` (Cal Poly vs the public
   median) or `data/cla_benchmarks.csv` for the numbers behind it, including the
   official national median across all institutions.
2. School vs school: use `data/schools/<slug>.csv`, which lists every institution
   for that major. Filter it to whichever schools you want (California only, a few
   named rivals, the top ten) and chart those, with Cal Poly highlighted. The full
   list can be long, so filtering or highlighting is usually the point.

Build these with:

    python scripts/build_school_comparison.py --data-dir "path/to/unzipped/folder"

Note: this currently covers the CLA majors in the config. Widening it to every
major in the country is a one-line change (remove the major filter), if you ever
want it.

## Annual update

1. Download and unzip the newest raw data from
   https://collegescorecard.ed.gov/data/
2. In `config/earnings_metrics.csv`, confirm each horizon's source file and its
   cohort / measured / dollar_basis against the current glossary
   (https://collegescorecard.ed.gov/data/glossary/).
3. Run:

       python scripts/build_cla_earnings.py --data-dir "path/to/unzipped/folder"

4. Commit the changed files in `data/`. The charts update automatically.

## Which file powers which chart

- Standard department chart: `data/by_major/<slug>.csv` (4-year figure).
- A 1-year or 5-year chart: the matching `_1yr` or `_5yr` file. Note the 1-year
  and 5-year cohort labels currently read CONFIRM in the metrics config; verify
  them in the glossary before publishing those horizons.

## Publishing (Datawrapper -> Drupal)

1. Turn on GitHub Pages (Settings > Pages) so the CSVs have public HTTPS URLs.
2. In Datawrapper, create a chart, choose "Link external dataset," paste the CSV
   URL, and pick "Serve data file directly" (not the cached option, which stops
   updating after 30 days).
3. Publish and copy the responsive iframe.
4. In Drupal, paste the iframe. The text format must allow embeds from
   datawrapper.dwcdn.net; if it strips the embed, ask UCM to allowlist it.

## Caveats to keep with any public use

- Cohorts are federally aided students, not all graduates.
- Programs with about 15 or fewer students are suppressed.
- Not cost-of-living adjusted; Cal Poly graduates cluster in coastal California.
  The data supports "our graduates earn more," not "our program adds more value."
- 1-year earnings are noisy and reflect people just starting; some majors that
  lead at 4 years trail at 1 year. The 4-year figure is the fair headline.
