# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Early-stage embodied carbon from a quantities CSV and a factors CSV.

Deps:  none (standard library only)
Usage: uv run carbon_estimate.py quantities.csv factors.csv [--gia 1200]
           [--benchmark 600 --benchmark-source "RIBA 2030 Climate Challenge, 2021 v2, A1-A5 target"]
           [--out results.csv]

quantities.csv columns (header required):
    element, material, quantity, unit
    e.g.  Ground slab, Concrete C32/40, 180, m3

factors.csv columns (header required):
    material, factor, factor_unit, stages, source[, density_kg_m3, density_source]
    factor       number, kgCO2e per factor_unit
    factor_unit  the declared unit the factor is per: kg, m3, m2, t, m, item
    stages       the life-cycle modules covered, e.g. A1-A3
    source       citation: database + version + entry, EPD number + URL, or EC3 + attribution
    density_*    optional, only used to convert a quantity in m3 to a factor per kg (or t)

It refuses (exit 1) rather than guessing when:
    - a material has no factor, or a factor has no source
    - the quantity unit does not match the factor unit and no density converts it
    - factors cover different stages (mixing A1-A3 with A1-A5 makes the total meaningless)
Every line prints its arithmetic so the basis of the total is visible.
"""
import argparse
import csv
import sys

UNIT_ALIASES = {"m³": "m3", "m^3": "m3", "m²": "m2", "m^2": "m2", "tonne": "t", "tonnes": "t",
                "kgs": "kg", "nr": "item", "no": "item", "each": "item", "ea": "item"}


def norm_unit(u):
    u = (u or "").strip().lower()
    return UNIT_ALIASES.get(u, u)


def read_csv(path, required):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit(f"{path}: no rows")
    missing = [c for c in required if c not in rows[0]]
    if missing:
        sys.exit(f"{path}: missing columns {missing}. Found {list(rows[0].keys())}")
    return [{k.strip(): (v or "").strip() for k, v in r.items()} for r in rows]


def num(s, what):
    try:
        return float(s.replace(",", ""))
    except ValueError:
        sys.exit(f"Not a number for {what}: '{s}'")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("quantities")
    ap.add_argument("factors")
    ap.add_argument("--gia", type=float, help="gross internal area in m2, for kgCO2e/m2")
    ap.add_argument("--benchmark", type=float, help="target in kgCO2e/m2 (a target, not a requirement)")
    ap.add_argument("--benchmark-source", default="")
    ap.add_argument("--out", help="write line results to CSV")
    a = ap.parse_args()

    qs = read_csv(a.quantities, ["element", "material", "quantity", "unit"])
    fs = read_csv(a.factors, ["material", "factor", "factor_unit", "stages", "source"])
    factors = {}
    for f in fs:
        key = f["material"].lower()
        if key in factors:
            sys.exit(f"Duplicate factor for material '{f['material']}'. Keep one, cited.")
        if not f["source"]:
            sys.exit(f"Factor for '{f['material']}' has no source. Every factor must be cited.")
        factors[key] = f

    stages = {f["stages"].replace(" ", "").upper() for f in fs}
    if len(stages) > 1:
        sys.exit(f"Factors cover different life-cycle stages: {sorted(stages)}. "
                 "Use factors with one consistent scope, or report scopes separately.")
    scope = stages.pop()

    errors, lines = [], []
    for q in qs:
        f = factors.get(q["material"].lower())
        if not f:
            errors.append(f"No factor for material '{q['material']}' (element '{q['element']}')")
            continue
        qty = num(q["quantity"], f"quantity of {q['element']}")
        qu, fu = norm_unit(q["unit"]), norm_unit(f["factor_unit"])
        fac = num(f["factor"], f"factor of {f['material']}")
        basis = ""
        if qu == fu:
            conv_qty = qty
        elif qu == "t" and fu == "kg":
            conv_qty, basis = qty * 1000, f"{qty:g} t x 1000 = {qty*1000:g} kg; "
        elif qu == "kg" and fu == "t":
            conv_qty, basis = qty / 1000, f"{qty:g} kg / 1000 = {qty/1000:g} t; "
        elif qu == "m3" and fu in ("kg", "t") and f.get("density_kg_m3"):
            if not f.get("density_source"):
                errors.append(f"Density for '{f['material']}' has no density_source")
                continue
            d = num(f["density_kg_m3"], f"density of {f['material']}")
            kg = qty * d
            conv_qty = kg if fu == "kg" else kg / 1000
            basis = f"{qty:g} m3 x {d:g} kg/m3 ({f['density_source']}) = {kg:g} kg; "
        else:
            errors.append(f"Unit mismatch for '{q['element']}': quantity in '{q['unit']}', "
                          f"factor per '{f['factor_unit']}'. Supply a matching factor or a cited density.")
            continue
        co2 = conv_qty * fac
        basis += f"{conv_qty:g} {fu} x {fac:g} kgCO2e/{fu} = {co2:,.0f} kgCO2e"
        lines.append({"element": q["element"], "material": q["material"], "quantity": qty,
                      "unit": q["unit"], "factor": fac, "factor_unit": fu, "kgco2e": round(co2, 1),
                      "basis": basis, "source": f["source"]})

    if errors:
        print("REFUSED: fix these before an estimate can be produced:")
        for e in errors:
            print(" - " + e)
        sys.exit(1)

    total = sum(l["kgco2e"] for l in lines)
    print(f"Scope: {scope} (all factors)")
    print(f"{'Element':28} {'Material':24} {'kgCO2e':>12}   Share")
    for l in sorted(lines, key=lambda x: -x["kgco2e"]):
        share = l["kgco2e"] / total * 100 if total else 0
        print(f"{l['element'][:28]:28} {l['material'][:24]:24} {l['kgco2e']:12,.0f}   {share:4.1f}%")
    print(f"{'TOTAL':53} {total:12,.0f}   ({total/1000:,.1f} tCO2e)")
    print("\nBasis per line:")
    for l in lines:
        print(f" - {l['element']}: {l['basis']}  [factor: {l['source']}]")
    if a.gia:
        per = total / a.gia
        print(f"\nIntensity: {total:,.0f} / {a.gia:,.0f} m2 GIA = {per:,.0f} kgCO2e/m2 ({scope})")
        if a.benchmark:
            src = a.benchmark_source or "SOURCE NOT GIVEN: cite it before using this comparison"
            diff = per - a.benchmark
            print(f"Target: {a.benchmark:,.0f} kgCO2e/m2 [{src}] -> "
                  f"{'above' if diff > 0 else 'below'} target by {abs(diff):,.0f} kgCO2e/m2. "
                  "Check the target covers the same scope and building elements before comparing.")
    print("\nCoverage: only the elements listed above are included. Missing elements lower the total.")
    if a.out:
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(lines[0].keys()))
            w.writeheader()
            w.writerows(lines)
        print(f"Line results written to {a.out}")


if __name__ == "__main__":
    main()
