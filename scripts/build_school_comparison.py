#!/usr/bin/env python3
"""
Build school-vs-school comparison files for CLA majors (4-year earnings).

Produces, for each included major:
  data/schools/<slug>.csv     Every institution in the country with reported
                              earnings for that major, named, with state, control
                              (public / private / for-profit), the earnings figure,
                              and a flag marking Cal Poly SLO. Sorted high to low.
                              This is what lets you compare any school against any
                              other and highlight whichever ones you want.

And one summary across all majors:
  data/cla_benchmarks.csv     Per major: Cal Poly's figure, the median across
                              PUBLIC universities (computed here), and the official
                              national median across ALL institutions (Scorecard's
                              EARN_MDN_4YR_NAT), plus counts and Cal Poly's
                              percentile against each pool.

Reads the default (4-year) metric defined in config/earnings_metrics.csv.
Run: python scripts/build_school_comparison.py --data-dir "path/to/unzipped/scorecard"
"""
import argparse, csv, os, statistics

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
        majors = [r for r in csv.DictReader(f) if r["include"].strip().lower() == "yes"]
    with open(args.metrics, newline="", encoding="utf-8-sig") as f:
        met = next(r for r in csv.DictReader(f) if r["default"].strip().lower() == "yes")

    fos = os.path.join(args.data_dir, met["source_file"])
    col, nat_col = met["column"], met["column"] + "_NAT"
    # state crosswalk
    state = {}
    for name in os.listdir(args.data_dir):
        if name.startswith("MERGED") and name.endswith("_PP.csv"):
            with open(os.path.join(args.data_dir, name), newline="", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    state[row["UNITID"]] = row.get("STABBR", "")
            break

    wanted = {norm(m["cip4"]): m for m in majors}
    rows = {c: [] for c in wanted}
    nat = {}
    with open(fos, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("CREDLEV") != "3": continue
            cip = norm(row.get("CIPCODE", ""))
            if cip not in wanted: continue
            e = num(row.get(col))
            if e is None: continue
            rows[cip].append((row.get("INSTNM", ""), state.get(row.get("UNITID", ""), ""),
                              row.get("CONTROL", ""), e))
            if cip not in nat:
                nat[cip] = num(row.get(nat_col))

    bench = []
    for cip, m in wanted.items():
        recs = sorted(rows[cip], key=lambda r: -r[3])
        # per-major school file
        with open(os.path.join(REPO, "data", "schools", m["slug"] + ".csv"), "w",
                  newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Institution", "State", "Control", "Median earnings 4 years after graduating", "Cal Poly?"])
            for name, st, ctrl, e in recs:
                w.writerow([name, st, ctrl, round(e), "Yes" if name == SLO else ""])
        # Cal Poly + UC campuses only, for a clean UC comparison chart
        uc_recs = [(n, e) for (n, s, c, e) in recs
                   if n == SLO or n.startswith("University of California-")]
        if any(n == SLO for n, _ in uc_recs) and len(uc_recs) > 1:
            with open(os.path.join(REPO, "data", "vs_uc", m["slug"] + ".csv"), "w",
                      newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["Institution", "Median earnings 4 years after graduating", "Cal Poly?"])
                for name, e in uc_recs:
                    short = name.replace("University of California-", "UC ")
                    w.writerow([short, round(e), "Yes" if name == SLO else ""])
        # benchmarks
        allv = [e for _, _, _, e in recs]
        pubv = [e for _, _, c, e in recs if c == "Public"]
        ucv = [e for n, _, _, e in recs if n.startswith("University of California-")]
        cp = next((e for n, _, _, e in recs if n == SLO), None)
        def pct(pool, x): return round(sum(1 for v in pool if v < x) / len(pool) * 100, 1) if (x and pool) else ""
        bench.append({
            "major": m["label"], "cip4": cip,
            "cal_poly": round(cp) if cp else "",
            "public_median": round(statistics.median(pubv)) if pubv else "",
            "uc_median": round(statistics.median(ucv)) if ucv else "",
            "national_median_all_official": round(nat[cip]) if nat.get(cip) else "",
            "n_all_institutions": len(allv), "n_public": len(pubv), "n_uc": len(ucv),
            "cal_poly_pctile_vs_public": pct(pubv, cp),
            "cal_poly_pctile_vs_uc": pct(ucv, cp),
            "cal_poly_pctile_vs_all": pct(allv, cp),
        })

    bf = ["major","cip4","cal_poly","public_median","uc_median","national_median_all_official",
          "n_all_institutions","n_public","n_uc","cal_poly_pctile_vs_public",
          "cal_poly_pctile_vs_uc","cal_poly_pctile_vs_all"]
    bench.sort(key=lambda r: -(r["cal_poly"] if isinstance(r["cal_poly"], int) else -1))
    with open(os.path.join(REPO, "data", "cla_benchmarks.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=bf); w.writeheader(); w.writerows(bench)
    print(f"Wrote {len(wanted)} school files to data/schools/ and data/cla_benchmarks.csv")

if __name__ == "__main__":
    main()
