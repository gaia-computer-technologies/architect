# /// script
# requires-python = ">=3.10"
# dependencies = ["ezdxf>=1.3", "shapely>=2.0", "ifcopenshell>=0.8"]
# ///
"""
area_check.py - measure space areas from a DXF, an IFC or a CSV, total them by
category, compute net-to-gross efficiency, and compare against a brief. Every
figure is printed with the inputs it came from.

Deps:   ezdxf, shapely (DXF);  ifcopenshell (IFC only)
Usage:
  uv run area_check.py --dxf plan.dxf --room-layer A-ROOM [--gross-layer A-AREA-GROS] [--units m]
  uv run area_check.py --ifc model.ifc
  uv run area_check.py --csv areas.csv              # columns: name,area[,category,level]
  ...any of the above plus:  --brief brief.csv     # columns: name,target_area[,tolerance_pct]
                             --categories cats.csv # columns: name,category (net|circulation|core|plant|...)
                             --md report.md

Areas are reported in m2 and sq ft. DXF areas are the area enclosed by each closed
polyline on the given layer, so the result depends on which face the outlines were
drawn to (internal face, centreline, external face). The measurement STANDARD
(IPMS, RICS, BOMA, local codes) is the architect's choice; this script measures,
it does not decide what counts.

Exit codes: 0 ok; 1 refused (bad input); 3 measured but a brief target was missed.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

TO_M = {1: 0.0254, 2: 0.3048, 4: 0.001, 5: 0.01, 6: 1.0}
UNIT_CODE = {"in": 1, "ft": 2, "mm": 4, "cm": 5, "m": 6}
SQFT = 10.7639104
AREA_TEXT = re.compile(r"^\s*[0-9.,]+\s*(m2|m²|sq ?ft|ft2|sf)?\s*$", re.I)


def die(msg: str) -> None:
    print(f"REFUSED: {msg}", file=sys.stderr)
    sys.exit(1)


def from_dxf(path: str, room_layer: str, gross_layer: str | None, units: str | None):
    import ezdxf
    from ezdxf import path as ezpath
    from shapely.geometry import Point, Polygon

    try:
        doc = ezdxf.readfile(path)
    except (OSError, ezdxf.DXFStructureError) as e:
        die(f"cannot read DXF: {e}")
    code = doc.header.get("$INSUNITS", 0)
    if units:
        if code and UNIT_CODE[units] != code:
            print(f"note: --units {units} overrides header $INSUNITS={code}")
        code = UNIT_CODE[units]
    if code not in TO_M:
        die(f"drawing units unknown ($INSUNITS={code}). Pass --units m|cm|mm|ft|in - never assume.")
    k = TO_M[code]
    msp = doc.modelspace()
    layers = {e.dxf.layer for e in msp}
    for lay in [room_layer] + ([gross_layer] if gross_layer else []):
        if lay not in layers:
            die(f"layer {lay!r} has no entities. Layers present: {sorted(layers)}")

    texts = []
    for t in msp.query("TEXT MTEXT"):
        s = t.plain_text() if t.dxftype() == "MTEXT" else t.dxf.text
        if s and not AREA_TEXT.match(s):
            texts.append((Point(t.dxf.insert.x, t.dxf.insert.y), s.strip()))

    def polys(layer):
        out, skipped = [], 0
        for e in msp.query(f'LWPOLYLINE POLYLINE[layer=="{layer}"]'):
            closed = e.closed if e.dxftype() == "LWPOLYLINE" else e.is_closed
            if not closed:
                skipped += 1
                continue
            pts = [(v.x, v.y) for v in ezpath.make_path(e).flattening(0.01 / k)]  # arcs to 10 mm chords
            p = Polygon(pts)
            if not p.is_valid or p.area == 0:
                skipped += 1
                continue
            out.append(p)
        return out, skipped

    rooms, skipped = polys(room_layer)
    if not rooms:
        die(f"no closed, valid polylines on {room_layer!r} ({skipped} open or invalid skipped)")
    rows = []
    for i, p in enumerate(rooms, 1):
        names = [s for pt, s in texts if p.contains(pt)]
        rows.append({"name": " / ".join(names) if names else f"Unlabelled {i}",
                     "area_m2": p.area * k * k, "source": f"closed polyline on {room_layer}, shoelace area x {k}^2"})
    gross = None
    if gross_layer:
        g, gs = polys(gross_layer)
        gross = sum(p.area for p in g) * k * k
        print(f"gross outline(s) on {gross_layer}: {len(g)} closed ({gs} skipped) -> {gross:,.2f} m2")
    unit_name = {v: n for n, v in UNIT_CODE.items()}[code]
    print(f"source: {path} | units: {unit_name} | room outlines: {len(rooms)} closed ({skipped} open/invalid skipped)")
    return rows, gross


def from_ifc(path: str):
    import ifcopenshell
    import ifcopenshell.util.element as ue
    import ifcopenshell.util.unit as uu

    try:
        f = ifcopenshell.open(path)
    except Exception as e:
        die(f"cannot open IFC: {e}")
    spaces = f.by_type("IfcSpace")
    if not spaces:
        die("no IfcSpace entities in the model - spaces must be modelled to measure them")
    try:
        ascale = uu.calculate_unit_scale(f, "AREAUNIT")  # project area unit -> m2
    except Exception:
        ascale = 1.0
    rows, missing = [], 0
    for s in spaces:
        q = ue.get_psets(s, qtos_only=True)
        base = q.get("Qto_SpaceBaseQuantities", {})
        a = base.get("NetFloorArea") or base.get("GrossFloorArea")
        which = "NetFloorArea" if base.get("NetFloorArea") else ("GrossFloorArea" if a else None)
        if not a:
            missing += 1
        storey = ue.get_container(s) or ue.get_aggregate(s)
        rows.append({"name": f"{s.Name or ''} {s.LongName or ''}".strip() or s.GlobalId,
                     "area_m2": float(a) * ascale if a else None, "level": getattr(storey, "Name", None),
                     "source": f"IfcSpace {s.GlobalId} Qto_SpaceBaseQuantities.{which}" if which else
                     f"IfcSpace {s.GlobalId}: NO area quantity"})
    print(f"source: {path} | schema: {f.schema} | IfcSpace: {len(spaces)} | without area quantity: {missing} "
          f"| area unit scale to m2: {ascale:g}")
    if missing:
        print("note: spaces without Qto areas are listed but not totalled. Export quantities from the authoring tool.")
    return rows, None


def from_csv(path: str):
    rows = []
    try:
        with open(path, newline="") as fh:
            for i, r in enumerate(csv.DictReader(fh), 2):
                try:
                    a = float(str(r["area"]).replace(",", ""))
                except (KeyError, ValueError):
                    die(f"{path} line {i}: needs a numeric 'area' column (m2)")
                rows.append({"name": r.get("name") or f"Row {i}", "area_m2": a,
                             "category": r.get("category") or None, "level": r.get("level") or None,
                             "source": f"{path} line {i} (as supplied)"})
    except OSError as e:
        die(f"cannot read CSV: {e}")
    print(f"source: {path} | rows: {len(rows)} (areas as supplied, assumed m2)")
    return rows, None


def main() -> None:
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--dxf"); src.add_argument("--ifc"); src.add_argument("--csv")
    ap.add_argument("--room-layer", default="A-ROOM")
    ap.add_argument("--gross-layer")
    ap.add_argument("--units", choices=sorted(UNIT_CODE))
    ap.add_argument("--gross", type=float, help="gross area in m2 if not measured here")
    ap.add_argument("--brief"); ap.add_argument("--categories"); ap.add_argument("--md")
    args = ap.parse_args()

    if args.dxf:
        rows, gross = from_dxf(args.dxf, args.room_layer, args.gross_layer, args.units)
    elif args.ifc:
        rows, gross = from_ifc(args.ifc)
    else:
        rows, gross = from_csv(args.csv)
    if args.gross:
        gross = args.gross
        print(f"gross area supplied: {gross:,.2f} m2")

    if args.categories:
        with open(args.categories, newline="") as fh:
            cmap = {r["name"].strip().lower(): r["category"].strip() for r in csv.DictReader(fh)}
        for r in rows:
            r["category"] = cmap.get(r["name"].strip().lower(), r.get("category"))
    for r in rows:
        r.setdefault("category", None)
        r["category"] = r["category"] or "uncategorised"

    out = ["| Space | Category | Area m2 | Area sq ft | Basis |", "|---|---|---|---|---|"]
    for r in rows:
        a = r["area_m2"]
        out.append(f"| {r['name']} | {r['category']} | {a:,.2f} | {a * SQFT:,.0f} | {r['source']} |" if a is not None
                   else f"| {r['name']} | {r['category']} | - | - | {r['source']} |")
    by = defaultdict(float)
    for r in rows:
        if r["area_m2"] is not None:
            by[r["category"]] += r["area_m2"]
    total = sum(by.values())
    out += ["", "| Category | Total m2 | Share of measured |", "|---|---|---|"]
    for c, a in sorted(by.items()):
        out.append(f"| {c} | {a:,.2f} | {a / total:.1%} |")
    out.append(f"| **Sum of measured spaces** | **{total:,.2f}** | {len([r for r in rows if r['area_m2'] is not None])} spaces |")

    if gross:
        net = by.get("net", total if set(by) == {"uncategorised"} else 0.0)
        basis = "category 'net'" if "net" in by else "all measured spaces (no categories given)"
        out += ["", f"Gross: {gross:,.2f} m2 | Net ({basis}): {net:,.2f} m2",
                f"Net-to-gross efficiency = {net:,.2f} / {gross:,.2f} = {net / gross:.1%}",
                f"Gross minus measured spaces = {gross - total:,.2f} m2 (walls, unmeasured areas, voids, or outline mismatch)"]

    failures = 0
    if args.brief:
        out += ["", "| Brief item | Target m2 | Measured m2 | Difference | Check |", "|---|---|---|---|---|"]
        meas = defaultdict(float)
        for r in rows:
            if r["area_m2"] is not None:
                meas[r["name"].strip().lower()] += r["area_m2"]
        with open(args.brief, newline="") as fh:
            for b in csv.DictReader(fh):
                name, tgt = b["name"].strip(), float(b["target_area"])
                tol = float(b.get("tolerance_pct") or 5) / 100
                m = meas.get(name.lower())
                if m is None:
                    out.append(f"| {name} | {tgt:,.2f} | not found | - | MISSING |"); failures += 1
                    continue
                d = (m - tgt) / tgt
                ok = abs(d) <= tol
                failures += 0 if ok else 1
                out.append(f"| {name} | {tgt:,.2f} | {m:,.2f} | {m - tgt:+,.2f} ({d:+.1%}) | {'OK' if ok else 'OUTSIDE'} +/-{tol:.0%} |")

    report = "\n".join(out)
    print(report)
    if args.md:
        Path(args.md).write_text(report + "\n")
        print(f"wrote: {args.md}")
    if failures:
        print(f"{failures} brief item(s) outside tolerance or missing.", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
