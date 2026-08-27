# CLA Earnings Comparison, project guide for Claude Code

## What this project is

This repo holds the earnings comparison data behind charts embedded on Cal Poly
College of Liberal Arts (CLA) department websites. It compares Cal Poly SLO
graduates against graduates of the same major at other **public universities**,
using U.S. Department of Education College Scorecard Field of Study data. The
metric is median earnings 4 years after completing a bachelor's degree.

The repo is the single source of truth for the numbers. Charts in Datawrapper
read the CSV files in `data/`, so updating the data here updates every chart.

## Layout

- `config/cla_majors.csv` The list of majors that count as CLA. This is the only
  place the major list is defined. Columns: cip4, label, slug, cla_department,
  include (yes/no).
- `scripts/build_cla_earnings.py` Reads a raw Scorecard Field of Study file and
  writes the clean CSVs. This is the only script.
- `data/cla_earnings_summary.csv` All included majors in one table. Powers the
  college-level chart and is the file to share with anyone who wants the numbers.
- `data/by_major/<slug>.csv` One small two-row file per major (Cal Poly vs the
  public-university median). Each powers one department chart.
- Raw Scorecard files are gitignored. They are large and are not committed.

## Common tasks

### Annual update
1. The user downloads the newest raw data zip from
   https://collegescorecard.ed.gov/data/ and unzips it. The needed file is named
   `FieldOfStudyData<year>_PP.csv`.
2. Run the build, pointing at that file:
       python scripts/build_cla_earnings.py --fos "<path to FieldOfStudyData file>"
   Add `--merged "<path to MERGED file>"` only if California-only columns are
   wanted. Both files are in the same zip.
3. Review the changes in `data/`, then commit and push.

### Add, remove, or exclude a major
Edit `config/cla_majors.csv` and rerun the build. Do not hard-code majors
anywhere else. Setting `include` to `no` keeps a row documented but drops it from
all outputs.

## Rules and conventions

- Comparison pool is public universities only (CONTROL = "Public"), bachelor's
  level only (CREDLEV = 3), with Cal Poly excluded from its own peer median.
- Theatre Arts is excluded on purpose: no earnings premium, and per the dean we
  skip majors without a positive story.
- Liberal Studies / Interdisciplinary (CIP 2401) is excluded pending
  confirmation from Institutional Research. CIP 2401 most likely maps to the
  Liberal Studies teacher-prep major in the College of Science and Mathematics,
  not a CLA major. Do not mark it include=yes until IR confirms.
- Anthropology & Geography clears the national public median but falls below the
  California public median. If a California framing is used anywhere, flag this
  major rather than presenting it as a win.
- Writing style for any public-facing text: first person, no em dashes, use "CLA"
  rather than spelling out the college.

## Caveats to preserve in any public-facing material

- Cohorts are federally aided students, not all graduates.
- Programs with about 15 or fewer students are suppressed, so the pool is public
  programs large enough to report, not every program.
- Figures are not cost-of-living adjusted. The data supports "our graduates earn
  more," not a causal "our program adds more value."
