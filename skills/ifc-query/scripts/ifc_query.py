# /// script
# requires-python = ">=3.10"
# dependencies = ["ifcopenshell>=0.8"]
# ///
"""
ifc_query.py - read-only openBIM QA and schedules with IfcOpenShell. Every
answer states the schema, the query and counts taken from the model.

Deps:   ifcopenshell
Usage:
  uv run ifc_query.py model.ifc summary
  uv run ifc_query.py model.ifc schedule "IfcDoor" --props "Name,Pset_DoorCommon.FireRating,Qto_DoorBaseQuantities.Width" [--csv doors.csv]
  uv run ifc_query.py model.ifc schedule "IfcWall, Pset_WallCommon.IsExternal=TRUE" --props "Name,Qto_WallBaseQuantities.NetSideArea"
  uv run ifc_query.py model.ifc gaps "IfcWall" --require "Pset_WallCommon.FireRating,Pset_WallCommon.IsExternal"
  uv run ifc_query.py model.ifc qto "IfcWall" --quantity "Qto_WallBaseQuantities.NetSideArea"

The first argument after the command is an IfcOpenShell selector query
(ifcopenshell.util.selector syntax): a class, optionally with filters, e.g.
"IfcSpace", "IfcDoor, Name=D*", "IfcWall, Pset_WallCommon.LoadBearing=TRUE".
The model is opened read-only; nothing is ever written back.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter

import ifcopenshell
import ifcopenshell.util.element as ue
import ifcopenshell.util.selector as sel
import ifcopenshell.util.unit as uu


def die(msg: str) -> None:
    print(f"REFUSED: {msg}", file=sys.stderr)
    sys.exit(1)


def prop(el, path: str):
    """'Name' / 'GlobalId' / 'type' / 'storey' / 'Pset.Prop' / 'Qto.Quantity'."""
    if path == "storey":
        c = ue.get_container(el)
        return getattr(c, "Name", None)
    if path == "type":
        t = ue.get_type(el)
        return getattr(t, "Name", None)
    if "." not in path:
        return getattr(el, path, None)
    pset, name = path.split(".", 1)
    return ue.get_psets(el).get(pset, {}).get(name)


def select(f, query: str):
    try:
        return sorted(sel.filter_elements(f, query), key=lambda e: (e.Name or "", e.GlobalId))
    except Exception as e:
        die(f"selector query failed ({e}). Example: \"IfcWall, Pset_WallCommon.IsExternal=TRUE\"")


def header(f, path, query=None):
    proj = (f.by_type("IfcProject") or [None])[0]
    try:
        ls = uu.calculate_unit_scale(f)
    except Exception:
        ls = None
    print(f"file: {path} | schema: {f.schema} | project: {getattr(proj, 'Name', None)!r} | "
          f"length unit scale to metres: {ls}")
    if query:
        print(f"query: {query!r} (ifcopenshell.util.selector)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ifc")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("summary")
    s = sub.add_parser("schedule"); s.add_argument("query"); s.add_argument("--props", default="Name,type,storey")
    s.add_argument("--csv")
    g = sub.add_parser("gaps"); g.add_argument("query"); g.add_argument("--require", required=True)
    q = sub.add_parser("qto"); q.add_argument("query"); q.add_argument("--quantity", required=True)
    args = ap.parse_args()

    try:
        f = ifcopenshell.open(args.ifc)
    except Exception as e:
        die(f"cannot open IFC: {e}")

    if args.cmd == "summary":
        header(f, args.ifc)
        prods = f.by_type("IfcProduct")
        counts = Counter(p.is_a() for p in prods)
        print(f"IfcProduct instances: {len(prods)}")
        print("| Class | Count |\n|---|---|")
        for cls, n in counts.most_common():
            print(f"| {cls} | {n} |")
        print("\n| Storey | Elevation | Contained elements | Spaces |\n|---|---|---|---|")
        for st in sorted(f.by_type("IfcBuildingStorey"), key=lambda s: s.Elevation or 0):
            contained = ue.get_decomposition(st)
            n_sp = sum(1 for e in contained if e.is_a("IfcSpace"))
            print(f"| {st.Name} | {st.Elevation} | {len(contained)} | {n_sp} |")
        sp = f.by_type("IfcSpace")
        with_q = sum(1 for x in sp if "Qto_SpaceBaseQuantities" in ue.get_psets(x, qtos_only=True))
        print(f"\nIfcSpace with Qto_SpaceBaseQuantities: {with_q} of {len(sp)}")
        no_type = sum(1 for p in prods if p.is_a("IfcElement") and not ue.get_type(p))
        print(f"IfcElement without a type object: {no_type} of {sum(1 for p in prods if p.is_a('IfcElement'))}")
        return

    els = select(f, args.query)
    header(f, args.ifc, args.query)
    print(f"matched: {len(els)} element(s)")
    if not els:
        return

    if args.cmd == "schedule":
        cols = [c.strip() for c in args.props.split(",") if c.strip()]
        rows = [["GlobalId"] + cols] + [[e.GlobalId] + [prop(e, c) for c in cols] for e in els]
        print("| " + " | ".join(rows[0]) + " |\n|" + "---|" * len(rows[0]))
        for r in rows[1:]:
            print("| " + " | ".join("" if v is None else str(v) for v in r) + " |")
        empty = {c: sum(1 for e in els if prop(e, c) in (None, "")) for c in cols}
        print("empty values: " + ", ".join(f"{c}: {n}/{len(els)}" for c, n in empty.items()))
        if args.csv:
            with open(args.csv, "w", newline="") as fh:
                csv.writer(fh).writerows(rows)
            print(f"wrote: {args.csv}")

    elif args.cmd == "gaps":
        req = [r.strip() for r in args.require.split(",") if r.strip()]
        print("| Required property | Present | Missing | Missing GlobalIds (first 10) |\n|---|---|---|---|")
        for r in req:
            miss = [e for e in els if prop(e, r) in (None, "")]
            ids = ", ".join(f"{e.GlobalId} ({e.Name})" for e in miss[:10])
            print(f"| {r} | {len(els) - len(miss)} | {len(miss)} | {ids} |")

    elif args.cmd == "qto":
        vals = [(e, prop(e, args.quantity)) for e in els]
        have = [(e, float(v)) for e, v in vals if isinstance(v, (int, float))]
        missing = len(vals) - len(have)
        total = sum(v for _, v in have)
        print(f"{args.quantity}: sum = {total:,.3f} over {len(have)} element(s) with the quantity; "
              f"{missing} element(s) have no value and are NOT included")
        print("units: as exported in the project's unit for this quantity type (check the authoring tool's export settings)")
        by_storey = Counter()
        for e, v in have:
            by_storey[prop(e, "storey") or "(no container)"] += v
        print("| Storey | Sum |\n|---|---|")
        for k, v in sorted(by_storey.items()):
            print(f"| {k} | {v:,.3f} |")


if __name__ == "__main__":
    main()
