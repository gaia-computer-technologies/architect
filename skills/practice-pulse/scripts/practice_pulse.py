# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Fee burn, earned value and utilisation from timesheet and fee CSVs.

Deps:  none (standard library only)
Usage: uv run practice_pulse.py timesheets.csv fees.csv staff.csv
           [--from 2026-09-01 --to 2026-11-30] [--non-billable OFFICE,LEAVE,TRAINING]
           [--flag-cpi 0.9]

timesheets.csv   date (YYYY-MM-DD), person, project, hours
fees.csv         project, fee, percent_complete[, invoiced]
                 percent_complete = the project lead's estimate of work done (0-100).
                 This is a judgement; the script reports it, it does not derive it.
staff.csv        person, cost_rate, weekly_capacity_hours
                 cost_rate = cost per hour to the practice (salary + overhead), same currency as fee.

Formulas (printed with results):
    cost to date      = sum(hours x person's cost_rate)
    fee burn          = cost to date / fee
    earned value (EV) = fee x percent_complete
    CPI               = EV / cost to date        (< 1 means spending faster than progressing)
    forecast at end   = cost to date / percent_complete
    utilisation       = billable hours / capacity hours in the period
It refuses when a person has no cost rate or a project has hours but no fee row.
"""
import argparse
import csv
import sys
from collections import defaultdict
from datetime import date, timedelta


def read(path, cols):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [{k.strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]
    if not rows:
        sys.exit(f"{path}: no rows")
    miss = [c for c in cols if c not in rows[0]]
    if miss:
        sys.exit(f"{path}: missing columns {miss}")
    return rows


def fnum(s, what):
    try:
        return float(str(s).replace(",", ""))
    except ValueError:
        sys.exit(f"Not a number for {what}: '{s}'")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("timesheets")
    ap.add_argument("fees")
    ap.add_argument("staff")
    ap.add_argument("--from", dest="dfrom")
    ap.add_argument("--to", dest="dto")
    ap.add_argument("--non-billable", default="OFFICE,LEAVE,TRAINING,ADMIN,HOLIDAY,SICK")
    ap.add_argument("--flag-cpi", type=float, default=0.9)
    a = ap.parse_args()

    nonbill = {p.strip().upper() for p in a.non_billable.split(",") if p.strip()}
    ts = read(a.timesheets, ["date", "person", "project", "hours"])
    fees = {r["project"]: r for r in read(a.fees, ["project", "fee", "percent_complete"])}
    staff = {r["person"]: r for r in read(a.staff, ["person", "cost_rate", "weekly_capacity_hours"])}

    dates = [date.fromisoformat(r["date"]) for r in ts]
    d0 = date.fromisoformat(a.dfrom) if a.dfrom else min(dates)
    d1 = date.fromisoformat(a.dto) if a.dto else max(dates)

    errs = set()
    hours_proj, cost_proj = defaultdict(float), defaultdict(float)
    bill_person, total_person = defaultdict(float), defaultdict(float)
    for r in ts:
        d = date.fromisoformat(r["date"])
        h = fnum(r["hours"], f"hours on {r['date']}")
        person, proj = r["person"], r["project"]
        if person not in staff:
            errs.add(f"No cost rate / capacity for person '{person}' in staff.csv")
            continue
        billable = proj.upper() not in nonbill
        if billable and proj not in fees:
            errs.add(f"Project '{proj}' has hours but no row in fees.csv")
            continue
        # Fee burn uses all hours to date; utilisation uses the period only.
        if billable:
            hours_proj[proj] += h
            cost_proj[proj] += h * fnum(staff[person]["cost_rate"], f"cost_rate of {person}")
        if d0 <= d <= d1:
            total_person[person] += h
            if billable:
                bill_person[person] += h
    if errs:
        print("REFUSED: fix these first:")
        for e in sorted(errs):
            print(" - " + e)
        sys.exit(1)

    print("FORMULAS: burn = cost/fee · EV = fee x %complete · CPI = EV/cost · forecast = cost/%complete")
    print(f"\n{'Project':16} {'Hours':>7} {'Cost':>10} {'Fee':>10} {'Burn':>6} {'%Done':>6} {'EV':>10} {'CPI':>5} {'Forecast':>10}  Flag")
    flagged = []
    for proj, f in sorted(fees.items()):
        fee = fnum(f["fee"], f"fee of {proj}")
        pct = fnum(f["percent_complete"], f"percent_complete of {proj}") / 100
        cost = cost_proj.get(proj, 0.0)
        burn = cost / fee if fee else 0
        ev = fee * pct
        cpi = ev / cost if cost else float("nan")
        fc = cost / pct if pct > 0 else float("nan")
        flag = ""
        if cost and cpi < a.flag_cpi:
            flag = f"OVERRUNNING (CPI {cpi:.2f} < {a.flag_cpi})"
        elif pct == 0 and cost > 0:
            flag = "Hours booked, 0% complete: check % estimate"
        if fc == fc and fc > fee:
            flag += ("; " if flag else "") + f"forecast exceeds fee by {fc - fee:,.0f}"
        if flag:
            flagged.append(proj)
        cpis = f"{cpi:5.2f}" if cpi == cpi else "  n/a"
        fcs = f"{fc:10,.0f}" if fc == fc else "       n/a"
        print(f"{proj[:16]:16} {hours_proj.get(proj,0):7.1f} {cost:10,.0f} {fee:10,.0f} {burn:6.0%} {pct:6.0%} {ev:10,.0f} {cpis} {fcs}  {flag}")

    weeks = ((d1 - d0).days + 1) / 7
    print(f"\nUTILISATION {d0} to {d1} ({weeks:.1f} weeks; billable = not in {sorted(nonbill)})")
    print(f"{'Person':16} {'Billable':>9} {'Total':>7} {'Capacity':>9} {'Util.':>6}")
    for p, s in sorted(staff.items()):
        cap = fnum(s["weekly_capacity_hours"], f"capacity of {p}") * weeks
        b = bill_person.get(p, 0.0)
        u = b / cap if cap else 0
        print(f"{p[:16]:16} {b:9.1f} {total_person.get(p,0):7.1f} {cap:9.1f} {u:6.0%}")
    print(f"\nFlagged projects: {', '.join(flagged) if flagged else 'none'}")
    print("Note: % complete is the project lead's estimate. EV and CPI are only as good as that estimate.")


if __name__ == "__main__":
    main()
