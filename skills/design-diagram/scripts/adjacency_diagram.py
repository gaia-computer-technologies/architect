# /// script
# requires-python = ">=3.10"
# dependencies = ["networkx>=3.0", "scipy>=1.10"]
# ///
"""
adjacency_diagram.py - bubble (adjacency) and stacking diagrams as plain SVG.

Deps:   networkx + scipy (layout only; the SVG is written by hand)
Usage:  uv run adjacency_diagram.py spec.json --out bubble.svg [--mode bubble|stack] [--seed 7]

Spec:
{
  "title": "Primary school - adjacency",
  "area_unit": "m2",
  "spaces": [{"name": "Hall", "area": 180, "zone": "Shared", "level": 0}, ...],
  "adjacencies": [{"a": "Hall", "b": "Kitchen", "strength": "required"},
                  {"a": "Hall", "b": "Entrance", "strength": "desired"},
                  {"a": "Plant", "b": "Library", "strength": "avoid"}]
}
strength: required | desired | avoid.   level is only needed for --mode stack.

Bubble area is proportional to space area (radius = sqrt(area / pi) * k), so the
diagram is honest about relative size. Layout is Kamada-Kawai with a target distance
per pair (same input + seed = same picture), then overlaps are pushed apart. The script reports
which "required" pairs ended up far apart and which "avoid" pairs ended up close,
because a layout cannot always satisfy every constraint at once.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from html import escape
from pathlib import Path

import networkx as nx

PALETTE = ["#d9d4c7", "#b9c4c9", "#c9b9a6", "#a9b8a0", "#c4b4c4", "#e0c9a6", "#b0b0b0", "#a6bcd0"]
EDGE = {"required": ("#111", 3.0, ""), "desired": ("#555", 1.5, "6 4"), "avoid": ("#b3261e", 1.5, "2 4")}


def die(msg: str) -> None:
    print(f"REFUSED: {msg}", file=sys.stderr)
    sys.exit(1)


def load(path: str) -> dict:
    try:
        spec = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as e:
        die(f"cannot read spec: {e}")
    spaces = spec.get("spaces") or die("spec needs a non-empty 'spaces' list")
    names = [s.get("name") for s in spaces]
    if len(set(names)) != len(names) or None in names:
        die("every space needs a unique 'name'")
    for s in spaces:
        try:
            if float(s["area"]) <= 0:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            die(f"space {s.get('name')!r}: 'area' must be a positive number")
    for a in spec.get("adjacencies", []):
        if a.get("a") not in names or a.get("b") not in names:
            die(f"adjacency {a} names a space that is not in 'spaces'")
        if a.get("strength") not in EDGE:
            die(f"adjacency {a}: strength must be one of {list(EDGE)}")
    return spec


def hash_order(name: str, seed: int) -> int:
    """Deterministic pseudo-random order from the seed (no Python hash randomisation)."""
    h = seed
    for ch in name:
        h = (h * 131 + ord(ch)) % 1_000_003
    return h


def zone_colours(spaces) -> dict:
    zones = sorted({s.get("zone", "Unzoned") for s in spaces})
    return {z: PALETTE[i % len(PALETTE)] for i, z in enumerate(zones)}


def bubble(spec: dict, seed: int) -> tuple[str, list[str]]:
    spaces, adj = spec["spaces"], spec.get("adjacencies", [])
    unit = spec.get("area_unit", "m2")
    total = sum(float(s["area"]) for s in spaces)
    k = 260 / math.sqrt(total / math.pi)  # largest plausible cluster ~ 520 px across
    r = {s["name"]: math.sqrt(float(s["area"]) / math.pi) * k for s in spaces}

    # Kamada-Kawai with an explicit target distance for every pair (centre to
    # centre, px): required = touching, desired = close, unrelated = loose,
    # avoid = far. Seeded circular start keeps it deterministic.
    names = sorted(r)
    strength = {}
    for a in adj:
        strength[frozenset((a["a"], a["b"]))] = a["strength"]
    extra = {"required": 10, "desired": 70, None: 160, "avoid": 420}
    dist = {m: {} for m in names}
    for m in names:
        for n in names:
            if m != n:
                dist[m][n] = r[m] + r[n] + extra[strength.get(frozenset((m, n)))]
    g = nx.complete_graph(names)
    start = nx.circular_layout(sorted(names, key=lambda n: (hash_order(n, seed))))
    pos = nx.kamada_kawai_layout(g, dist=dist, pos=start, weight=None)
    ratios = sorted(dist[m][n] / max(1e-9, math.dist(pos[m], pos[n])) for m in names for n in names if m < n)
    s = ratios[len(ratios) // 2]
    p = {n: [pos[n][0] * s, pos[n][1] * s] for n in names}

    # Push apart overlapping bubbles (deterministic order), keep 8 px gap,
    # and keep "avoid" pairs at least 80 px apart edge to edge.
    for _ in range(400):
        moved = False
        for i, m in enumerate(names):
            for n in names[i + 1:]:
                dx, dy = p[n][0] - p[m][0], p[n][1] - p[m][1]
                d = math.hypot(dx, dy) or 1e-6
                need = r[m] + r[n] + (80 if strength.get(frozenset((m, n))) == "avoid" else 8)
                if d < need:
                    push = (need - d) / 2
                    ux, uy = dx / d, dy / d
                    p[m][0] -= ux * push; p[m][1] -= uy * push
                    p[n][0] += ux * push; p[n][1] += uy * push
                    moved = True
        if not moved:
            break

    notes = []
    for a in adj:
        gap = math.dist(p[a["a"]], p[a["b"]]) - r[a["a"]] - r[a["b"]]
        if a["strength"] == "required" and gap > 40:
            notes.append(f"required adjacency not achieved in layout: {a['a']} - {a['b']} (gap {gap:.0f} px)")
        if a["strength"] == "avoid" and gap < 20:
            notes.append(f"avoid pair ended up touching: {a['a']} - {a['b']}")

    xs = [p[n][0] - r[n] for n in p] + [p[n][0] + r[n] for n in p]
    ys = [p[n][1] - r[n] for n in p] + [p[n][1] + r[n] for n in p]
    pad, top = 40, 70
    minx, miny = min(xs) - pad, min(ys) - pad - top
    col = zone_colours(spaces)
    legend_w = 520 + len(col) * 130 + 2 * pad
    content_w = max(xs) - minx + pad
    w, h = max(content_w, legend_w), max(ys) - miny + pad + 60
    # When the legend is wider than the bubbles, centre the bubbles in the canvas.
    minx -= (w - content_w) / 2

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{minx:.0f} {miny:.0f} {w:.0f} {h:.0f}" '
           f'font-family="Helvetica, Arial, sans-serif">',
           f'<rect x="{minx:.0f}" y="{miny:.0f}" width="{w:.0f}" height="{h:.0f}" fill="#fff"/>',
           f'<text x="{minx + pad:.0f}" y="{miny + 40:.0f}" font-size="22" font-weight="600">'
           f'{escape(spec.get("title", "Adjacency diagram"))}</text>']
    for a in sorted(adj, key=lambda e: ["avoid", "desired", "required"].index(e["strength"])):
        c, sw, dash = EDGE[a["strength"]]
        (x1, y1), (x2, y2) = p[a["a"]], p[a["b"]]
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c}" '
                   f'stroke-width="{sw}"' + (f' stroke-dasharray="{dash}"' if dash else "") + "/>")
    for s in spaces:
        n = s["name"]; x, y = p[n]
        fs = max(10, min(18, r[n] / 3.2))
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r[n]:.1f}" fill="{col[s.get("zone", "Unzoned")]}" '
                   f'stroke="#111" stroke-width="1"/>')
        out.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{fs:.0f}" text-anchor="middle">{escape(n)}</text>')
        out.append(f'<text x="{x:.1f}" y="{y + fs * 1.2:.1f}" font-size="{fs * 0.8:.0f}" text-anchor="middle" '
                   f'fill="#333">{float(s["area"]):g} {escape(unit)}</text>')
    lx, ly = minx + pad, miny + h - 30
    for i, (label, (c, sw, dash)) in enumerate(EDGE.items()):
        x0 = lx + i * 170
        out.append(f'<line x1="{x0}" y1="{ly}" x2="{x0 + 40}" y2="{ly}" stroke="{c}" stroke-width="{sw}"'
                   + (f' stroke-dasharray="{dash}"' if dash else "") + "/>")
        out.append(f'<text x="{x0 + 48}" y="{ly + 5}" font-size="13">{label}</text>')
    for i, (z, c) in enumerate(col.items()):
        x0 = lx + 520 + i * 130
        out.append(f'<rect x="{x0}" y="{ly - 9}" width="16" height="16" fill="{c}" stroke="#111"/>'
                   f'<text x="{x0 + 22}" y="{ly + 5}" font-size="13">{escape(z)}</text>')
    out.append("</svg>")
    return "\n".join(out), notes


def stack(spec: dict) -> tuple[str, list[str]]:
    spaces, unit = spec["spaces"], spec.get("area_unit", "m2")
    if any("level" not in s for s in spaces):
        die("--mode stack needs a 'level' on every space")
    levels = sorted({int(s["level"]) for s in spaces}, reverse=True)
    per = {lv: [s for s in spaces if int(s["level"]) == lv] for lv in levels}
    tot = {lv: sum(float(s["area"]) for s in per[lv]) for lv in levels}
    scale = 800 / max(tot.values())
    col = zone_colours(spaces)
    bar, gap, left, top = 54, 14, 120, 80
    h = top + len(levels) * (bar + gap) + 60
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 {h}" font-family="Helvetica, Arial, sans-serif">',
           f'<rect width="1000" height="{h}" fill="#fff"/>',
           f'<text x="20" y="40" font-size="22" font-weight="600">{escape(spec.get("title", "Programme stacking"))}</text>']
    for i, lv in enumerate(levels):
        y = top + i * (bar + gap)
        out.append(f'<text x="20" y="{y + bar / 2 + 5}" font-size="14">Level {lv}</text>')
        x = left
        for s in sorted(per[lv], key=lambda s: (s.get("zone", ""), s["name"])):
            wdt = float(s["area"]) * scale
            out.append(f'<rect x="{x:.1f}" y="{y}" width="{wdt:.1f}" height="{bar}" '
                       f'fill="{col[s.get("zone", "Unzoned")]}" stroke="#111"/>')
            if wdt > 46:
                out.append(f'<text x="{x + 5:.1f}" y="{y + 22}" font-size="12">{escape(s["name"])}</text>'
                           f'<text x="{x + 5:.1f}" y="{y + 40}" font-size="11" fill="#333">{float(s["area"]):g}</text>')
            x += wdt
        out.append(f'<text x="{x + 8:.1f}" y="{y + bar / 2 + 5}" font-size="13">{tot[lv]:g} {escape(unit)}</text>')
    out.append("</svg>")
    notes = [f"level {lv}: {tot[lv]:g} {unit} across {len(per[lv])} spaces" for lv in levels]
    return "\n".join(out), notes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", choices=["bubble", "stack"], default="bubble")
    ap.add_argument("--seed", type=int, default=7, help="layout seed; change it to try another arrangement")
    args = ap.parse_args()
    spec = load(args.spec)
    svg, notes = bubble(spec, args.seed) if args.mode == "bubble" else stack(spec)
    Path(args.out).write_text(svg)
    total = sum(float(s["area"]) for s in spec["spaces"])
    print(f"mode: {args.mode}; spaces: {len(spec['spaces'])}; adjacencies: {len(spec.get('adjacencies', []))}; "
          f"total area: {total:g} {spec.get('area_unit', 'm2')} (sum of inputs)")
    if args.mode == "bubble":
        print(f"seed: {args.seed}; bubble area proportional to space area")
    for n in notes:
        print(f"- {n}")
    print(f"wrote: {args.out}")


if __name__ == "__main__":
    main()
