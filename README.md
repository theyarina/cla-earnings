# CLA Earnings Comparison

Public-facing earnings data for College of Liberal Arts majors at Cal Poly SLO,
comparing our graduates against graduates of the same major at **other public
universities**. Source: U.S. Department of Education, College Scorecard Field of
Study data (https://collegescorecard.ed.gov/data/). Metric: median earnings 4
years after completing a bachelor's degree.

This repo is the single source of truth for the numbers. Charts embedded on
department websites read from the CSV files in `data/`, so updating the data
here updates every chart.

## What's in here

    config/cla_majors.csv        Which majors count as CLA. Edit this to add,
                                 remove, or exclude a major. Nothing is
                                 hard-coded anywhere else.
    scripts/build_cla_earnings.py  Turns the raw Scorecard file into the clean
                                 CSVs below. Run once a year.
    data/cla_earnings_summary.csv  All majors in one table. Powers the
                                 college-level chart and is the file to hand to
                                 anyone who wants to dig into the numbers.
    data/by_major/<major>.csv    One small file per major (Cal Poly vs the
                                 public-university median). Each powers one
                                 department chart.

## Annual update (the entire workflow)

1. Download the newest raw data zip from https://collegescorecard.ed.gov/data/
   and unzip it. You want the file named `FieldOfStudyData<year>_PP.csv`.
2. Regenerate the CSVs:

       python scripts/build_cla_earnings.py --fos "FieldOfStudyData<newest>_PP.csv"

   To also produce California-only columns, add the merged institution file
   (it's in the same zip):

       python scripts/build_cla_earnings.py \
           --fos "FieldOfStudyData<newest>_PP.csv" \
           --merged "MERGED<newest>_PP.csv"

3. Commit the changed files in `data/` (drag-and-drop in the GitHub website is
   fine; no command line needed). The charts pick up the new numbers on their
   next load.

That's it. One file in, all charts update.

## Changing which majors are shown

Open `config/cla_majors.csv` and set `include` to `yes` or `no`, or add/remove a
row. Two rows to be aware of:

- **Theatre Arts** is set to `no` because its graduates do not show an earnings
  premium; per the dean, we skip majors without a positive story.
- **Liberal Studies / Interdisciplinary (CIP 2401)** is set to `no` pending
  confirmation from Institutional Research. CIP 2401 most likely maps to the
  Liberal Studies teacher-prep major in the College of Science and Mathematics,
  not a CLA major. Do not publish it as CLA until IR confirms the mapping.

## Publishing a chart (Datawrapper -> Drupal)

1. Turn on GitHub Pages for this repo (Settings > Pages) so the CSV files have
   public HTTPS URLs, e.g.
   `https://<org>.github.io/cla-earnings/data/by_major/philosophy.csv`
2. In Datawrapper, create a chart. At the upload step choose **Link external
   dataset**, paste the CSV URL, and pick **"Serve data file directly."**
   (Do not use the option where Datawrapper's own server caches the file; that
   one stops auto-updating 30 days after publishing.)
3. Style the chart, publish, and copy the **responsive iframe** embed code.
4. In Drupal, paste the iframe into a page. Note: the Drupal text format has to
   allow iframes from `datawrapper.dwcdn.net`. If it strips the embed, ask UCM
   to allowlist that domain (a one-time request).

## Caveats to keep with any public use

- Earnings cohorts are built from federally aided students, not all graduates.
- Programs with roughly 15 or fewer students are suppressed, so the comparison
  pool is "public programs large enough to report," not literally every program.
- Figures are not adjusted for cost of living; Cal Poly graduates concentrated
  in coastal California will show higher nominal earnings than identical
  graduates elsewhere. The data supports "our graduates earn more," not a causal
  "our program adds more value."
- California-only pools are small for some majors (Graphic Communication has
  just one other CA public program), so prefer the national-public comparison
  for anything public-facing.
