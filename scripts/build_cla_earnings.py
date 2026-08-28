#!/usr/bin/env python3
"""
Build CLA earnings comparison files from raw College Scorecard Field of Study data.

WHAT IT DOES
  For each earnings horizon listed in config/earnings_metrics.csv (1 year, 4 year,
  5 year), reads the matching raw College Scorecard file and compares Cal Poly SLO
  against OTHER PUBLIC universities offering the same major. Writes chart-ready CSVs
  with the graduating cohort and measurement year stamped into every file.

WHY EACH HORIZON HAS ITS OWN FILE AND YEAR
  College Scorecard measures earnings 1, 4, and 5 years after graduation, and each
  horizon comes from a DIFFERENT graduating cohort measured in a different year.
  They are separate snapshots, not the same students followed over time. The cohort
  and measurement years for each horizon live in config/earnings_metrics.csv so the
  year is always visible and travels with the data.

ANNUAL UPDATE
  1. Download the newest raw data zip from https://collegescorecard.ed.gov/data/
     and unzip it somewhere.
  2. Open config/earnings_metrics.csv and, for each horizon, confirm the source_file
     name and the cohort / measured / dollar_basis values against the current
     glossary (https://collegescorecard.ed.gov/data/glossary/). Update as needed.
  3. Run, pointing --data-dir at the unzipped folder:
        python scripts/build_cla_earnings.py --data-dir "path/to/unzipped/scorecard"
  4. Commit the changed files in data/. The charts update automatically.

WHICH MAJORS COUNT AS CLA
  Edit config/cla_majors.csv (include = yes/no). Nothing is hard-coded here.
"""

import argparse
import csv
import os
import statistics

SLO_NAME = "California Polytechnic State University-San Luis Obispo"
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def norm_cip(code):
    return str(code).replace(".", "").strip().zfill(4)


def load_majors(path):
    out = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["include"].strip().lower() == "yes":
                row["cip4"] = norm_cip(row["cip4"])
                out.append(row)
    return out


def load_metrics(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def to_num(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def compute_metric(fos_path, column, majors):
    """Return {cip4: (cal_poly, public_median, premium, percentile, n_peers) or None}."""
    buckets = {m["cip4"]: [] for m in majors}
    wanted = set(buckets)
    with open(fos_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("CREDLEV") != "3":            # bachelor's only
                continue
            cip = norm_cip(row.get("CIPCODE", ""))
            if cip not in wanted:
                continue
            buckets[cip].append((row.get("INSTNM", ""), row.get("CONTROL", ""),
                                 to_num(row.get(column))))
    results = {}
    for cip in wanted:
        recs = buckets[cip]
        slo = next((e for (n, c, e) in recs if n == SLO_NAME and e is not None), None)
        pub = [e for (n, c, e) in recs if c == "Public" and n != SLO_NAME and e is not None]
        if slo is None or not pub:
            results[cip] = None
            continue
        med = statistics.median(pub)
        pct = sum(1 for e in pub if e < slo) / len(pub) * 100
        results[cip] = (slo, med, slo - med, pct, len(pub))
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True,
                    help="Folder containing the unzipped raw Scorecard CSV files")
    ap.add_argument("--majors", default=os.path.join(REPO, "config", "cla_majors.csv"))
    ap.add_argument("--metrics", default=os.path.join(REPO, "config", "earnings_metrics.csv"))
    args = ap.parse_args()

    majors = load_majors(args.majors)
    metrics = load_metrics(args.metrics)
    label_by_cip = {m["cip4"]: m["label"] for m in majors}
    slug_by_cip = {m["cip4"]: m["slug"] for m in majors}

    summary_path = os.path.join(REPO, "data", "cla_earnings_summary.csv")
    summary_fields = ["major", "metric", "horizon", "cohort_award_years", "measured_years",
                      "dollar_basis", "verified", "cal_poly", "public_median", "premium",
                      "national_percentile", "n_public_peers"]
    summary_rows = []

    for met in metrics:
        fos = os.path.join(args.data_dir, met["source_file"])
        if not os.path.exists(fos):
            print(f"  [skip] {met['key']}: file not found: {met['source_file']}")
            continue
        res = compute_metric(fos, met["column"], majors)
        header = (f"Median earnings, {met['horizon_label']} "
                  f"({met['cohort_award_years']} graduates, {met['dollar_basis']})")
        wrote = 0
        for cip, vals in res.items():
            if vals is None:
                continue
            cp, med, prem, pct, n = vals
            slug = slug_by_cip[cip]
            name = (slug + ".csv") if met["default"].strip().lower() == "yes" else f"{slug}_{met['key']}.csv"
            with open(os.path.join(REPO, "data", "by_major", name), "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["Group", header])
                w.writerow(["Cal Poly SLO", round(cp)])
                w.writerow(["Other public universities (median)", round(med)])
            wrote += 1
            summary_rows.append({
                "major": label_by_cip[cip], "metric": met["key"], "horizon": met["horizon_label"],
                "cohort_award_years": met["cohort_award_years"], "measured_years": met["measured_years"],
                "dollar_basis": met["dollar_basis"], "verified": met["verified"],
                "cal_poly": round(cp), "public_median": round(med), "premium": round(prem),
                "national_percentile": round(pct, 1), "n_public_peers": n,
            })
        print(f"  {met['key']}: wrote {wrote} major files from {met['source_file']}")

    order = {m["key"]: i for i, m in enumerate(metrics)}
    summary_rows.sort(key=lambda r: (order.get(r["metric"], 9), -r["premium"]))
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=summary_fields)
        w.writeheader()
        w.writerows(summary_rows)
    print(f"\nWrote summary: {summary_path}  ({len(summary_rows)} rows)")


if __name__ == "__main__":
    main()
