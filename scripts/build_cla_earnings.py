#!/usr/bin/env python3
"""
Build CLA earnings comparison files from raw College Scorecard Field of Study data.

WHAT IT DOES
  Reads one raw "FieldOfStudyData<year>_PP.csv" file from College Scorecard,
  filters to the CLA majors listed in config/cla_majors.csv (include = yes),
  and for each major compares Cal Poly SLO's median earnings 4 years after
  completion against the median for OTHER PUBLIC universities offering the
  same major. Writes Datawrapper-ready CSVs.

ANNUAL UPDATE (the whole workflow)
  1. Download the newest College Scorecard raw data zip from
     https://collegescorecard.ed.gov/data/  and unzip it.
  2. Run:
       python scripts/build_cla_earnings.py \
           --fos "path/to/FieldOfStudyData<newest>_PP.csv"
     (optional, only if you want California-only columns too:)
           --merged "path/to/MERGED<newest>_PP.csv"
  3. Commit the changed files in data/ . The charts update automatically.

EDITING WHICH MAJORS COUNT AS CLA
  Edit config/cla_majors.csv . Set include to yes/no. Add or remove rows.
  Nothing here is hard-coded to a major.
"""

import argparse
import csv
import os
import sys
import statistics

SLO_NAME = "California Polytechnic State University-San Luis Obispo"
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def norm_cip(code):
    """Normalize a CIP code to a 4-character, zero-padded string with no dot."""
    return str(code).replace(".", "").strip().zfill(4)


def load_majors(path):
    majors = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["include"].strip().lower() == "yes":
                row["cip4"] = norm_cip(row["cip4"])
                majors.append(row)
    return majors


def load_state_map(merged_path):
    """UNITID -> two-letter state, from a MERGED institution file. Optional."""
    if not merged_path:
        return None
    state = {}
    with open(merged_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            state[row["UNITID"]] = row.get("STABBR", "")
    return state


def to_num(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return None  # suppressed / blank / "PrivacySuppressed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fos", required=True, help="Field of Study raw CSV")
    ap.add_argument("--merged", default=None, help="MERGED institution CSV (optional, enables CA columns)")
    ap.add_argument("--config", default=os.path.join(REPO, "config", "cla_majors.csv"))
    args = ap.parse_args()

    majors = load_majors(args.config)
    state_map = load_state_map(args.merged)

    # Bucket bachelor-level rows by CIP for the majors we care about.
    wanted = {m["cip4"] for m in majors}
    # cip -> list of dicts {inst, control, state, earn}
    buckets = {c: [] for c in wanted}

    with open(args.fos, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("CREDLEV") != "3":       # 3 = Bachelor's Degree
                continue
            cip = norm_cip(row.get("CIPCODE", ""))
            if cip not in wanted:
                continue
            earn = to_num(row.get("EARN_MDN_4YR"))
            buckets[cip].append({
                "inst": row.get("INSTNM", ""),
                "control": row.get("CONTROL", ""),
                "state": (state_map or {}).get(row.get("UNITID", ""), ""),
                "earn": earn,
            })

    summary_rows = []
    for m in majors:
        cip = m["cip4"]
        recs = buckets.get(cip, [])
        slo = next((r for r in recs if r["inst"] == SLO_NAME and r["earn"] is not None), None)
        cp = slo["earn"] if slo else None

        pub = [r["earn"] for r in recs
               if r["control"] == "Public" and r["inst"] != SLO_NAME and r["earn"] is not None]
        pub_median = statistics.median(pub) if pub else None
        pct = (sum(1 for e in pub if e < cp) / len(pub) * 100) if (cp is not None and pub) else None
        premium = (cp - pub_median) if (cp is not None and pub_median is not None) else None

        ca_median = ca_pct = ca_n = None
        if state_map is not None:
            pub_ca = [r["earn"] for r in recs
                      if r["control"] == "Public" and r["inst"] != SLO_NAME
                      and r["state"] == "CA" and r["earn"] is not None]
            if pub_ca:
                ca_median = statistics.median(pub_ca)
                ca_pct = (sum(1 for e in pub_ca if e < cp) / len(pub_ca) * 100) if cp is not None else None
                ca_n = len(pub_ca)

        summary_rows.append({
            "major": m["label"], "slug": m["slug"], "cip4": cip,
            "cal_poly": cp, "public_median": pub_median,
            "premium": premium, "national_percentile": pct, "n_public_peers": len(pub),
            "ca_public_median": ca_median, "ca_percentile": ca_pct, "n_ca_public_peers": ca_n,
        })

        # Per-major 2-row file for a clean department bar chart.
        if cp is not None and pub_median is not None:
            per_path = os.path.join(REPO, "data", "by_major", m["slug"] + ".csv")
            with open(per_path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["Group", "Median earnings 4 years after graduating"])
                w.writerow(["Cal Poly SLO", round(cp)])
                w.writerow(["Other public universities (median)", round(pub_median)])

    # Summary file: powers the college-level chart and is the "play with the data" file.
    summary_path = os.path.join(REPO, "data", "cla_earnings_summary.csv")
    fields = ["major", "cip4", "cal_poly", "public_median", "premium",
              "national_percentile", "n_public_peers",
              "ca_public_median", "ca_percentile", "n_ca_public_peers", "slug"]
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in sorted(summary_rows, key=lambda x: -(x["premium"] or -1e9)):
            out = dict(r)
            for k in ("cal_poly", "public_median", "premium", "ca_public_median"):
                if out[k] is not None:
                    out[k] = round(out[k])
            for k in ("national_percentile", "ca_percentile"):
                if out[k] is not None:
                    out[k] = round(out[k], 1)
            w.writerow({k: out.get(k, "") for k in fields})

    print("Wrote:", summary_path)
    print("Wrote per-major files to:", os.path.join(REPO, "data", "by_major"))
    print("\nSummary (public-university comparison):")
    for r in sorted(summary_rows, key=lambda x: -(x["premium"] or -1e9)):
        prem = f"{r['premium']:+,.0f}" if r["premium"] is not None else "n/a"
        pct = f"{r['national_percentile']:.0f}th pct" if r["national_percentile"] is not None else "n/a"
        print(f"  {r['major']:<26} Cal Poly ${r['cal_poly'] or 0:>7,.0f}  "
              f"vs public ${r['public_median'] or 0:>7,.0f}  premium {prem:>9}  "
              f"{pct}  (n={r['n_public_peers']})")


if __name__ == "__main__":
    main()
