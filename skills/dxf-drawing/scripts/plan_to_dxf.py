# /// script
# requires-python = ">=3.10"
# dependencies = ["ezdxf>=1.3", "matplotlib>=3.7", "shapely>=2.0"]
# ///
"""
plan_to_dxf.py - write a layered, dimensioned DXF from a simple JSON spec,
then render a PNG + SVG preview so the drawing can be checked visually.

Deps:   ezdxf, matplotlib, shapely
Usage:  uv run plan_to_dxf.py spec.json --out plan.dxf [--tolerance 0.01]
        (writes plan.dxf, plan.png, plan.svg next to --out)

Spec (all coordinates in the spec's "units"):
{
  "units": "m",                       # m | cm | mm | ft | in   (required)
  "title": "Ground floor - option A",
  "boundary": [[x, y], ...],          # optional site/plot boundary (closed)
  "rooms": [{"name": "Living", "polygon": [[x,y],...], "expected_area": 20.0}],
  "walls": [{"from": [x,y], "to": [x,y], "thickness": 0.2}],
  "openings": [{"type": "door", "at": [x,y], "width": 0.9, "angle": 0},
               {"type": "window", "at": [x,y], "width": 1.2, "angle": 90}],
  "dimensions": [{"from": [x,y], "to": [x,y], "offset": 0.6}],
  "polylines": [{"layer": "A-SECT", "points": [[x,y],...], "closed": false}],
  "texts": [{"text": "N", "at": [x,y], "height": 0.3}]
}

Exit codes: 0 ok, 1 bad input (refused), 3 written but an area assertion failed.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext, layout, svg
from ezdxf.addons.drawing import matplotlib as ezmpl
from shapely.geometry import Polygon

INSUNITS = {"in": 1, "ft": 2, "mm": 4, "cm": 5, "m": 6}
TEXT_H = {"m": 0.2, "cm": 20.0, "mm": 200.0, "ft": 0.6, "in": 7.0}
AREA_UNIT = {"m": "m2", "cm": "cm2", "mm": "mm2", "ft": "sq ft", "in": "sq in"}

# Layer names follow the US National CAD Standard / AIA pattern. Rename to
# ISO 13567 / your office standard if required.
LAYERS = {
    "A-WALL": 7, "A-ROOM": 8, "A-ROOM-IDEN": 7, "A-DOOR": 3, "A-GLAZ": 4,
    "A-ANNO-DIMS": 1, "A-ANNO-TEXT": 7, "C-PROP": 6, "A-SECT": 7,
}


def die(msg: str) -> None:
    print(f"REFUSED: {msg}", file=sys.stderr)
    sys.exit(1)


def pts(raw, what: str, min_n: int = 2) -> list[tuple[float, float]]:
    try:
        out = [(float(p[0]), float(p[1])) for p in raw]
    except (TypeError, ValueError, IndexError):
        die(f"{what}: points must be [x, y] number pairs")
    if len(out) < min_n:
        die(f"{what}: needs at least {min_n} points, got {len(out)}")
    if len(out) > 1 and out[0] == out[-1]:
        out = out[:-1]  # closing point is implicit
    return out


def checked_polygon(raw, what: str) -> Polygon:
    p = pts(raw, what, 3)
    poly = Polygon(p)
    if not poly.is_valid or poly.area <= 0:
        die(f"{what}: polygon is self-intersecting or has zero area")
    return poly


def wall_outline(a, b, t):
    (x1, y1), (x2, y2) = a, b
    length = math.hypot(x2 - x1, y2 - y1)
    if length == 0:
        die(f"wall from {a} to {b} has zero length")
    nx, ny = -(y2 - y1) / length * t / 2, (x2 - x1) / length * t / 2
    return [(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("spec")
    ap.add_argument("--out", required=True, help="output .dxf path")
    ap.add_argument("--tolerance", type=float, default=0.01,
                    help="relative tolerance for expected_area checks (default 1%%)")
    args = ap.parse_args()

    try:
        spec = json.loads(Path(args.spec).read_text())
    except (OSError, json.JSONDecodeError) as e:
        die(f"cannot read spec: {e}")

    units = spec.get("units")
    if units not in INSUNITS:
        die(f"'units' must be one of {sorted(INSUNITS)} - got {units!r}. Never assume units.")
    th = TEXT_H[units]

    doc = ezdxf.new("R2018", setup=True)
    doc.header["$INSUNITS"] = INSUNITS[units]
    doc.header["$MEASUREMENT"] = 0 if units in ("ft", "in") else 1
    for name, color in LAYERS.items():
        if name not in doc.layers:
            doc.layers.add(name, color=color)
    msp = doc.modelspace()
    # dimlfac=1: ezdxf's stock EZDXF style multiplies measurements by 100.
    dim_override = {"dimlfac": 1.0, "dimtxt": th * 0.8, "dimasz": th * 0.6, "dimtsz": th * 0.4,
                    "dimexe": th * 0.5, "dimexo": th * 0.4, "dimgap": th * 0.25,
                    "dimdec": 2 if units in ("m", "ft") else 0}

    report = [f"units: {units} ($INSUNITS={INSUNITS[units]})"]
    failures = 0

    if "boundary" in spec:
        b = checked_polygon(spec["boundary"], "boundary")
        msp.add_lwpolyline(list(b.exterior.coords)[:-1], close=True, dxfattribs={"layer": "C-PROP"})
        report.append(f"boundary: area {b.area:.2f} {AREA_UNIT[units]} (shoelace of {len(b.exterior.coords)-1} vertices)")

    for i, room in enumerate(spec.get("rooms", [])):
        name = str(room.get("name") or f"Room {i+1}")
        poly = checked_polygon(room.get("polygon"), f"room '{name}'")
        msp.add_lwpolyline(list(poly.exterior.coords)[:-1], close=True, dxfattribs={"layer": "A-ROOM"})
        c = poly.representative_point()
        msp.add_text(name, height=th, dxfattribs={"layer": "A-ROOM-IDEN"}).set_placement(
            (c.x, c.y + th * 0.7), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
        msp.add_text(f"{poly.area:.2f} {AREA_UNIT[units]}", height=th * 0.8,
                     dxfattribs={"layer": "A-ROOM-IDEN"}).set_placement(
            (c.x, c.y - th * 0.7), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
        line = f"room '{name}': drawn area {poly.area:.3f} {AREA_UNIT[units]}"
        exp = room.get("expected_area")
        if exp is not None:
            diff = abs(poly.area - float(exp)) / float(exp)
            ok = diff <= args.tolerance
            failures += 0 if ok else 1
            line += f" vs expected {float(exp):.3f} -> {'OK' if ok else 'MISMATCH'} ({diff:.1%})"
        report.append(line)

    for w in spec.get("walls", []):
        t = float(w.get("thickness", 0))
        if t <= 0:
            die(f"wall {w}: thickness must be > 0")
        a, b = pts([w.get("from"), w.get("to")], "wall")
        msp.add_lwpolyline(wall_outline(a, b, t), close=True, dxfattribs={"layer": "A-WALL"})
    report.append(f"walls: {len(spec.get('walls', []))}")

    for o in spec.get("openings", []):
        (x, y), = pts([o.get("at")], "opening", 1)
        wdt, ang = float(o.get("width", 0)), math.radians(float(o.get("angle", 0)))
        if wdt <= 0:
            die(f"opening {o}: width must be > 0")
        if o.get("type") == "door":
            # leaf drawn open at 90 degrees from the hinge, plus the swing arc
            lx, ly = x + wdt * math.cos(ang + math.pi / 2), y + wdt * math.sin(ang + math.pi / 2)
            msp.add_line((x, y), (lx, ly), dxfattribs={"layer": "A-DOOR"})
            msp.add_arc((x, y), wdt, math.degrees(ang), math.degrees(ang) + 90, dxfattribs={"layer": "A-DOOR"})
        elif o.get("type") == "window":
            dx, dy = math.cos(ang) * wdt / 2, math.sin(ang) * wdt / 2
            msp.add_line((x - dx, y - dy), (x + dx, y + dy), dxfattribs={"layer": "A-GLAZ"})
        else:
            die(f"opening type must be 'door' or 'window': {o}")
    report.append(f"openings: {len(spec.get('openings', []))}")

    for d in spec.get("dimensions", []):
        a, b = pts([d.get("from"), d.get("to")], "dimension")
        dim = msp.add_aligned_dim(p1=a, p2=b, distance=float(d.get("offset", th * 3)),
                                  dimstyle="EZDXF", override=dim_override,
                                  dxfattribs={"layer": "A-ANNO-DIMS"})
        dim.render()
        report.append(f"dimension {a} -> {b}: {math.dist(a, b):.3f} {units}")

    for pl in spec.get("polylines", []):
        layer = pl.get("layer", "A-SECT")
        if layer not in doc.layers:
            doc.layers.add(layer)
        msp.add_lwpolyline(pts(pl.get("points"), "polyline"), close=bool(pl.get("closed")),
                           dxfattribs={"layer": layer})

    for t in spec.get("texts", []):
        (x, y), = pts([t.get("at")], "text", 1)
        msp.add_text(str(t.get("text", "")), height=float(t.get("height", th)),
                     dxfattribs={"layer": "A-ANNO-TEXT"}).set_placement((x, y))

    if spec.get("title"):
        ext = ezdxf.bbox.extents(msp)
        if ext.has_data:
            msp.add_text(spec["title"], height=th * 1.5, dxfattribs={"layer": "A-ANNO-TEXT"}).set_placement(
                (ext.extmin.x, ext.extmin.y - th * 4))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(out)

    # Previews: PNG (matplotlib) and SVG (native backend), white background.
    ezmpl.qsave(msp, str(out.with_suffix(".png")), bg="#FFFFFF", dpi=200)
    ctx = RenderContext(doc)
    backend = svg.SVGBackend()
    Frontend(ctx, backend).draw_layout(msp)
    page = layout.Page(0, 0, layout.Units.mm, margins=layout.Margins.all(10))
    out.with_suffix(".svg").write_text(backend.get_string(page))

    # Re-open and audit what was written, rather than trusting the writer.
    check = ezdxf.readfile(out)
    auditor = check.audit()
    counts = {}
    for e in check.modelspace():
        counts[e.dxf.layer] = counts.get(e.dxf.layer, 0) + 1
    report.append(f"audit errors: {len(auditor.errors)}; entities by layer: {dict(sorted(counts.items()))}")
    report.append(f"wrote: {out}, {out.with_suffix('.png')}, {out.with_suffix('.svg')}")
    print("\n".join(report))
    if failures:
        print(f"{failures} area assertion(s) failed - fix the geometry before issuing.", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
