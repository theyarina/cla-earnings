# CLA Earnings Comparison, project guide for Claude Code

## What this project is

This repo holds the earnings comparison data behind charts embedded on Cal Poly
College of Liberal Arts (CLA) department websites. It compares Cal Poly SLO
graduates against graduates of the same major at other **public universities**,
using U.S. Department of Education College Scorecard Field of Study data.

The repo is the single source of truth for the numbers. Charts in Datawrapper
read the CSV files in `data/`, so updating the data here updates every chart.

## Earnings horizons and the year

Earnings are reported at three horizons: 1 year, 4 years, and 5 years after
graduating. The **4-year figure is the standard** for public-facing charts. Each
horizon comes from a DIFFERENT graduating cohort measured in a different year, so
they are separate snapshots, not the same students followed over time. Never
combine horizons into one "over time" chart.

The cohort year, measurement year, and dollar basis for each horizon live in
`config/earnings_metrics.csv`, and are stamped into every output file so the year
is always visible.

## Layout

- `config/cla_majors.csv` Which majors count as CLA. The only place the major list
  is defined. Columns: cip4, label, slug, cla_department, include (yes/no).
- `config/earnings_metrics.csv` One row per horizon: which raw file and column it
  comes from, plus its cohort year, measurement year, and dollar basis. The row
  marked default = yes is the standard (currently 4-year).
- `scripts/build_cla_earnings.py` Reads a folder of raw Scorecard files and writes
  the clean CSVs. One script.
- `data/cla_earnings_summary.csv` Every major and horizon in one long table, with
  the cohort and measurement year as columns. This is the file to share with
  anyone who wants to dig into the numbers, and the provenance record.
- `data/by_major/<slug>.csv` The default (4-year) file for each major. Powers the
  standard department chart.
- `data/by_major/<slug>_1yr.csv` and `_5yr.csv` The other horizons, where data
  exists.

## Annual update

1. Download and unzip the newest raw data from
   https://collegescorecard.ed.gov/data/
2. In `config/earnings_metrics.csv`, confirm each horizon's source_file and its
   cohort / measured / dollar_basis against the current glossary
   (https://collegescorecard.ed.gov/data/glossary/).
3. Run: `python scripts/build_cla_earnings.py --data-dir "path/to/unzipped/folder"`
4. Review the changes in `data/`, then commit and push.

## Rules and conventions

- Comparison pool is public universities only (CONTROL = "Public"), bachelor's
  level only (CREDLEV = 3), Cal Poly excluded from its own peer median.
- Theatre Arts is excluded on purpose: no earnings premium.
- Liberal Studies / Interdisciplinary (CIP 2401) is excluded pending confirmation
  from Institutional Research (likely CSM Liberal Studies, not CLA).
- Anthropology & Geography clears the national public median but falls below the
  California public median, and at the 1-year horizon it falls below the public
  median. Flag it rather than presenting it as a clean win.
- The 1-year and 5-year cohort labels currently read CONFIRM in the metrics config.
  Verify them in the glossary before using those horizons publicly.
- Writing style for public-facing text: first person, no em dashes, use "CLA".

## Caveats to preserve in any public-facing material

- Cohorts are federally aided students, not all graduates.
- Programs with about 15 or fewer students are suppressed.
- Figures are not cost-of-living adjusted. The data supports "our graduates earn
  more," not a causal "our program adds more value."
- 1-year earnings are noisy and reflect people just starting out; some majors that
  lead at 4 years trail at 1 year. The 4-year figure is the fair headline.
