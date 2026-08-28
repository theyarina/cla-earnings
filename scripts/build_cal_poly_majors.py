#!/usr/bin/env python3
"""
Build a single table of EVERY Cal Poly SLO bachelor's major with 4-year earnings,
flagged as CLA or not, so any major can be compared against any other. Useful for
finding non-CLA majors that a CLA major out-earns.

Output:
  data/cal_poly_all_majors.csv
    Columns: cip4, major, median_earnings_4yr, is_cla, note
    Sorted high to low. Suppressed majors are listed with a blank figure so the
    record is complete.

Reads the default (4-year) metric from config/earnings_metrics.csv.
Run: python scripts/build_cal_poly_majors.py --data-dir "path/to/unzipped/scorecard"
"""
import argparse, csv, os

SLO = "California Polytechnic State University-San Luis Obispo"
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)

def norm(c): return str(c).replace(".", "").strip().zfill(4)
def num(v):
    try: return float(v)
    except (ValueError, TypeError): return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--majors", default=os.path.join(REPO, "config", "cla_majors.csv"))
    ap.add_argument("--metrics", default=os.path.join(REPO, "config", "earnings_metrics.csv"))
    args = ap.parse_args()

    with open(args.majors, newline="", encoding="utf-8-sig") as f:
        cla = {norm(r["cip4"]): r["label"] for r in csv.DictReader(f)
               if r["include"].strip().lower() == "yes"}
    with open(args.metrics, newline="", encoding="utf-8-sig") as f:
        met = next(r for r in csv.DictReader(f) if r["default"].strip().lower() == "yes")

    fos = os.path.join(args.data_dir, met["source_file"])
    col = met["column"]
    rows = []
    with open(fos, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("INSTNM") != SLO or row.get("CREDLEV") != "3":
                continue
            cip = norm(row.get("CIPCODE", ""))
            e = num(row.get(col))
            rows.append({
                "cip4": cip,
                "major": (row.get("CIPDESC", "") or "").strip().rstrip("."),
                "median_earnings_4yr": round(e) if e is not None else "",
                "is_cla": "yes" if cip in cla else "no",
                "note": "suppressed (too few graduates to report)" if e is None else "",
            })

    rows.sort(key=lambda r: (r["median_earnings_4yr"] == "", -(r["median_earnings_4yr"] or 0)))
    out = os.path.join(REPO, "data", "cal_poly_all_majors.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cip4", "major", "median_earnings_4yr", "is_cla", "note"])
        w.writeheader(); w.writerows(rows)
    n_data = sum(1 for r in rows if r["median_earnings_4yr"] != "")
    print(f"Wrote {out}: {len(rows)} Cal Poly majors ({n_data} with earnings data)")

if __name__ == "__main__":
    main()
