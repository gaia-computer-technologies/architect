# /// script
# requires-python = ">=3.10"
# dependencies = ["shapely>=2.0", "trimesh>=4.0", "mapbox-earcut>=1.0", "matplotlib>=3.7", "numpy>=1.24"]
# ///
"""
massing.py - feasibility massing and yield from a site boundary and envelope
rules. Every number is printed with its basis; every planning/zoning input is
echoed back as USER-SUPPLIED, TO VERIFY.

Deps:   shapely, trimesh + mapbox-earcut (triangulation), matplotlib, numpy
Usage:  uv run massing.py spec.json --out out/massing
Writes: <out>.glb and <out>.obj (stacked floor plates, metres, Y-up for glTF),
        <out>_plan.png, <out>_axo.png, <out>_report.md

Spec (metres; site vertices in local coordinates, listed in order around the site):
{
  "name": "Option A",
  "site": [[0,0],[40,0],[40,30],[0,30]],
  "setbacks": {"default": 3.0, "edges": {"0": 6.0}},   # edge i runs from vertex i to i+1
  "max_height": 21.0,
  "floor_to_floor": {"ground": 4.5, "typical": 3.15},
  "max_storeys": null,
  "coverage_max": 0.6,          # optional: footprint / site area
  "far_max": 3.0,               # optional: GFA / site area (FAR, plot ratio, FSI, GFZ...)
  "efficiency": 0.80,           # net / gross, the architect's assumption
  "unit_net_area": 65           # optional: average net area per unit for a unit count
}
Exit codes: 0 ok; 1 refused.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from shapely.geometry import Polygon  # noqa: E402


def die(msg: str) -> None:
    print(f"REFUSED: {msg}", file=sys.stderr)
    sys.exit(1)


def num(spec, key, lo=None, hi=None, required=True):
    v = spec.get(key)
    if v is None:
        if required:
            die(f"'{key}' is required - it is a planning/brief input, so it must come from the architect")
        return None
    try:
        v = float(v)
    except (TypeError, ValueError):
        die(f"'{key}' must be a number")
    if (lo is not None and v < lo) or (hi is not None and v > hi):
        die(f"'{key}'={v} outside plausible range {lo}..{hi}")
    return v


def buildable(site: Polygon, setbacks: dict) -> tuple[Polygon, list[float]]:
    # Keep the user's vertex order (edge i = vertex i -> i+1) so per-edge
    # setbacks land where they were specified; pick the inward side per winding.
    pts = list(site.exterior.coords)[:-1]
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    side = 1.0 if site.exterior.is_ccw else -1.0
    default = float(setbacks.get("default", 0))
    per = {int(k): float(v) for k, v in (setbacks.get("edges") or {}).items()}
    big = 10 * max(site.bounds[2] - site.bounds[0], site.bounds[3] - site.bounds[1])
    region, used = site, []
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        d = per.get(i, default)
        used.append(d)
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        nx, ny = -uy * side, ux * side  # inward normal
        a = (p[0] + nx * d - ux * big, p[1] + ny * d - uy * big)
        b = (q[0] + nx * d + ux * big, q[1] + ny * d + uy * big)
        half = Polygon([a, b, (b[0] + nx * big, b[1] + ny * big), (a[0] + nx * big, a[1] + ny * big)])
        region = region.intersection(half)
    if region.is_empty or region.area <= 0:
        die("setbacks leave no buildable area")
    if region.geom_type != "Polygon":
        region = max(region.geoms, key=lambda g: g.area)
    return region, used


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    try:
        spec = json.loads(Path(args.spec).read_text())
    except (OSError, json.JSONDecodeError) as e:
        die(f"cannot read spec: {e}")

    try:
        site = Polygon([(float(x), float(y)) for x, y in spec["site"]])
    except (KeyError, TypeError, ValueError):
        die("'site' must be a list of [x, y] vertices in metres")
    if not site.is_valid or site.area <= 0:
        die("site polygon is self-intersecting or has zero area")
    H = num(spec, "max_height", 2, 1000)
    ftf = spec.get("floor_to_floor") or die("'floor_to_floor' {ground, typical} is required")
    g, t = num(ftf, "ground", 2, 10), num(ftf, "typical", 2, 10)
    eff = num(spec, "efficiency", 0.3, 1.0)
    cov = num(spec, "coverage_max", 0.01, 1.0, required=False)
    far = num(spec, "far_max", 0.05, 50, required=False)
    max_st = num(spec, "max_storeys", 1, 300, required=False)
    unit = num(spec, "unit_net_area", 5, 10000, required=False)

    A = site.area
    fp, used = buildable(site, spec.get("setbacks") or {})
    log = [f"Site area = {A:,.1f} m2 (shoelace area of {len(site.exterior.coords) - 1} supplied vertices)",
           f"Setbacks applied per edge (m): {used}",
           f"Buildable footprint after setbacks = {fp.area:,.1f} m2 ({fp.area / A:.1%} of site)"]
    governs = ["setbacks (footprint)"]

    if cov is not None and fp.area > cov * A:
        target = cov * A
        lo, hi = 0.0, math.sqrt(fp.area)
        for _ in range(60):  # uniform inward offset until coverage cap is met
            mid = (lo + hi) / 2
            a = fp.buffer(-mid, join_style="mitre").area
            lo, hi = (mid, hi) if a > target else (lo, mid)
        shrunk = fp.buffer(-hi, join_style="mitre")
        if shrunk.geom_type != "Polygon":
            shrunk = max(shrunk.geoms, key=lambda x: x.area)
        log.append(f"Coverage cap {cov:.0%} x {A:,.1f} = {target:,.1f} m2 < buildable {fp.area:,.1f} m2 "
                   f"-> footprint pulled in uniformly by {hi:.2f} m to {shrunk.area:,.1f} m2")
        fp = shrunk
        governs = ["site coverage (footprint)"]

    n_h = 1 + math.floor((H - g) / t + 1e-9) if H >= g else 0
    if n_h < 1:
        die(f"max_height {H} m is below the ground floor-to-floor {g} m")
    log.append(f"Storeys by height = 1 + floor(({H:g} - {g:g}) / {t:g}) = {n_h} "
               f"(top of structure ~{g + (n_h - 1) * t:.2f} m, before roof build-up and plant)")
    n = n_h
    governs.append("height")
    if max_st is not None and max_st < n:
        n = int(max_st); governs[-1] = "max storeys"
        log.append(f"Storey cap {int(max_st)} < {n_h} -> {n} storeys")
    gfa = fp.area * n
    log.append(f"GFA = footprint {fp.area:,.1f} x {n} storeys = {gfa:,.1f} m2 (footprint repeated on every floor)")
    if far is not None and gfa > far * A:
        n_far = math.floor(far * A / fp.area)
        if n_far < 1:
            die(f"FAR {far} allows less than one full floor of this footprint - reduce the footprint first")
        log.append(f"FAR cap {far:g} x {A:,.1f} = {far * A:,.1f} m2 < {gfa:,.1f} m2 -> storeys cut to {n_far}")
        n, gfa = n_far, fp.area * n_far
        governs[-1] = "FAR / plot ratio"
    nia = gfa * eff
    log.append(f"Net area = GFA {gfa:,.1f} x efficiency {eff:.0%} (architect's assumption) = {nia:,.1f} m2")
    log.append(f"Achieved FAR = {gfa:,.1f} / {A:,.1f} = {gfa / A:.2f} | coverage = {fp.area / A:.1%} | "
               f"height ~{g + (n - 1) * t:.2f} m")
    if unit:
        log.append(f"Units = floor({nia:,.1f} / {unit:g}) = {math.floor(nia / unit)} (average unit net area as supplied)")
    log.append(f"Governing constraints: footprint by {governs[0]}; height by {governs[-1]}")

    # 3D: stacked plates with a 0.3 m slab gap so floors read.
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    meshes, z = [], 0.0
    for i in range(n):
        h = g if i == 0 else t
        m = trimesh.creation.extrude_polygon(fp, h - 0.3)
        m.apply_translation([0, 0, z])
        meshes.append(m)
        z += h
    mass = trimesh.util.concatenate(meshes)
    mass.export(out.with_suffix(".obj"))
    yup = mass.copy()
    yup.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]))
    yup.export(out.with_suffix(".glb"))

    # Plan
    fig, ax = plt.subplots(figsize=(8, 8), dpi=180)
    sx, sy = site.exterior.xy
    ax.fill(sx, sy, color="#f2f2f2", edgecolor="#000", linewidth=1.2)
    bx, by = fp.exterior.xy
    ax.fill(bx, by, color="#9a9a9a", edgecolor="#000", linewidth=1)
    for i, (p, d) in enumerate(zip(list(site.exterior.coords)[:-1], used)):
        q = list(site.exterior.coords)[(i + 1) % (len(site.exterior.coords) - 1)]
        ax.annotate(f"e{i}: {d:g} m", ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2), fontsize=7, color="#b3261e",
                    ha="center")
    c = fp.representative_point()
    ax.text(c.x, c.y, f"{fp.area:,.0f} m2\nx {n} storeys", ha="center", va="center", fontsize=9)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"{spec.get('name', 'Massing')} - plan (setbacks in red)", loc="left", fontsize=10)
    fig.savefig(out.with_name(out.name + "_plan.png"), bbox_inches="tight", facecolor="#fff")
    plt.close(fig)

    # Axonometric
    fig = plt.figure(figsize=(8, 7), dpi=180)
    ax = fig.add_subplot(projection="3d")
    ax.plot_trisurf(mass.vertices[:, 0], mass.vertices[:, 1], mass.vertices[:, 2], triangles=mass.faces,
                    color="#bdbdbd", edgecolor="#555", linewidth=0.15)
    ax.plot(*site.exterior.xy, zs=0, color="#000")
    span = max(site.bounds[2] - site.bounds[0], site.bounds[3] - site.bounds[1], z)
    ax.set_xlim(site.bounds[0], site.bounds[0] + span); ax.set_ylim(site.bounds[1], site.bounds[1] + span)
    ax.set_zlim(0, span); ax.view_init(elev=30, azim=-60); ax.set_axis_off()
    ax.set_title(f"{spec.get('name', 'Massing')} - {n} storeys, GFA {gfa:,.0f} m2", fontsize=10)
    fig.savefig(out.with_name(out.name + "_axo.png"), bbox_inches="tight", facecolor="#fff")
    plt.close(fig)

    inputs = ["max_height", "floor_to_floor", "setbacks", "coverage_max", "far_max", "max_storeys"]
    echo = [f"- {k}: {json.dumps(spec.get(k))}" for k in inputs if spec.get(k) is not None]
    report = "\n".join([f"# Massing: {spec.get('name', 'Option')}", "",
                        "## Planning / zoning inputs - USER-SUPPLIED, TO VERIFY with the planning authority", *echo,
                        f"- efficiency (brief/architect assumption): {eff}", "",
                        "## Calculation", *[f"- {line}" for line in log], "",
                        "## Not modelled",
                        "- Daylight angles, separation distances, rights of light, stepped or angled envelopes, "
                        "sky exposure planes, building-separation and fire access rules",
                        "- Cores, structure, roof plant zones, basements, amenity space requirements",
                        "", f"Files: {out}.glb, {out}.obj, {out}_plan.png, {out}_axo.png"])
    out.with_name(out.name + "_report.md").write_text(report + "\n")
    print(report)


if __name__ == "__main__":
    main()
