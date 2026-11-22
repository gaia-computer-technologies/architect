# /// script
# requires-python = ">=3.10"
# dependencies = ["osmnx>=2.0", "geopandas>=0.14", "shapely>=2.0", "matplotlib>=3.7", "ezdxf>=1.3"]
# ///
"""
site_map.py - figure-ground and context map from OpenStreetMap or local GeoJSON.

Deps:   osmnx, geopandas, shapely, matplotlib, ezdxf (DXF export only)
Usage:
  # live OSM (needs internet; uses the Overpass API - be polite, results are cached by osmnx)
  uv run site_map.py --point 51.9225 4.4792 --radius 250 --out out/site [--site site.geojson] [--dxf]
  # offline: a GeoJSON FeatureCollection you already have (any CRS with .crs or WGS84)
  uv run site_map.py --geojson context.geojson --out out/site [--site site.geojson] [--dxf]

Writes: <out>_figure_ground.png/.svg, <out>_context.png/.svg, optional <out>.dxf, and a
printed report. All areas and distances are computed in a projected (UTM) CRS, never in
degrees. OSM data: (c) OpenStreetMap contributors, ODbL 1.0 - attribution is drawn on
every output and must be kept.

Heights: 'height' tag is used as tagged; 'building:levels' x --floor-height (default 3.0 m)
is labelled ASSUMED; anything else is UNKNOWN. Never present OSM heights as surveyed.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from shapely.geometry import Point, box  # noqa: E402

ATTRIB = "(c) OpenStreetMap contributors, ODbL 1.0"
GREEN = {"leisure": ["park", "garden", "pitch", "playground"],
         "landuse": ["grass", "forest", "meadow", "recreation_ground", "cemetery", "allotments"],
         "natural": ["wood", "scrub", "grassland"]}


def die(msg: str) -> None:
    print(f"REFUSED: {msg}", file=sys.stderr)
    sys.exit(1)


def num(v):
    if v is None or (isinstance(v, float) and v != v):
        return None
    m = re.match(r"^\s*([0-9]+(?:\.[0-9]+)?)", str(v))
    return float(m.group(1)) if m else None


def classify(gdf: gpd.GeoDataFrame):
    cols = gdf.columns

    def has(col, vals=None):
        if col not in cols:
            return gpd.pd.Series(False, index=gdf.index)
        s = gdf[col]
        return s.notna() if vals is None else s.isin(vals)

    poly = gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
    line = gdf.geometry.geom_type.isin(["LineString", "MultiLineString"])
    buildings = gdf[has("building") & poly]
    streets = gdf[has("highway") & line]
    green = gdf[(has("leisure", GREEN["leisure"]) | has("landuse", GREEN["landuse"])
                 | has("natural", GREEN["natural"])) & poly & ~has("building")]
    water = gdf[(has("natural", ["water"]) | has("waterway")) & (poly | line)]
    return buildings, streets, green, water


def heights(b: gpd.GeoDataFrame, floor_h: float):
    tagged = levels = unknown = 0
    hs = []
    for _, row in b.iterrows():
        h = num(row.get("height")) if "height" in b.columns else None
        if h is not None:
            tagged += 1; hs.append((h, "tagged"))
            continue
        lv = num(row.get("building:levels")) if "building:levels" in b.columns else None
        if lv is not None:
            levels += 1; hs.append((lv * floor_h, "assumed"))
        else:
            unknown += 1; hs.append((None, "unknown"))
    return hs, tagged, levels, unknown


def plot(layers, site, out: Path, figure_ground: bool, title: str):
    buildings, streets, green, water = layers
    fig, ax = plt.subplots(figsize=(10, 10), dpi=200)
    ax.set_facecolor("#ffffff")
    if figure_ground:
        buildings.plot(ax=ax, color="#000000", linewidth=0)
    else:
        if len(green):
            green.plot(ax=ax, color="#cfd8c4", linewidth=0)
        if len(water):
            water.plot(ax=ax, color="#c4d4dc", linewidth=0.6, edgecolor="#9fb6c2")
        if len(streets):
            streets.plot(ax=ax, color="#9a9a9a", linewidth=0.7)
        buildings.plot(ax=ax, color="#3a3a3a", linewidth=0)
    if site is not None:
        site.boundary.plot(ax=ax, color="#d0021b", linewidth=1.8)
    ax.set_axis_off()
    ax.set_aspect("equal")
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    # Scale bar and north arrow sit in a strip BELOW the map (axes coords,
    # clip_on=False) so buildings never draw over them. Projected CRS is
    # north-up, so the arrow is vertical.
    span = (x1 - x0) / 5
    bar = next(v for v in (10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000) if v >= span * 0.6)
    frac = bar / (x1 - x0)
    tr = ax.transAxes
    ax.plot([0.0, frac], [-0.035, -0.035], transform=tr, clip_on=False,
            color="#000", linewidth=3, solid_capstyle="butt")
    ax.text(0.0, -0.025, f"{bar} m", transform=tr, fontsize=9, va="bottom")
    ax.annotate("", xy=(0.98, -0.015), xytext=(0.98, -0.075), xycoords=tr, textcoords=tr,
                annotation_clip=False, arrowprops=dict(arrowstyle="-|>", color="#000", lw=1.2))
    ax.text(0.955, -0.045, "N", transform=tr, fontsize=12, fontweight="bold",
            ha="right", va="center")
    ax.set_title(title, loc="left", fontsize=12)
    fig.text(0.99, 0.01, ATTRIB, ha="right", fontsize=7, color="#444")
    for ext in (".png", ".svg"):
        fig.savefig(out.with_name(out.name + ext), bbox_inches="tight", facecolor="#fff")
    plt.close(fig)


def to_dxf(layers, site, path: Path, origin):
    import ezdxf
    buildings, streets, green, water = layers
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 6
    msp = doc.modelspace()
    for name, col in (("C-BLDG", 7), ("C-ROAD", 8), ("C-GREEN", 3), ("C-WATR", 5), ("C-PROP", 1), ("C-ANNO", 7)):
        doc.layers.add(name, color=col)
    ox_, oy_ = origin

    def rings(g):
        geoms = getattr(g, "geoms", [g])
        for p in geoms:
            if p.geom_type == "Polygon":
                yield [(x - ox_, y - oy_) for x, y in p.exterior.coords]
            elif p.geom_type == "LineString":
                yield [(x - ox_, y - oy_) for x, y in p.coords]

    for gdf, layer, closed in ((buildings, "C-BLDG", True), (green, "C-GREEN", True),
                               (streets, "C-ROAD", False), (water, "C-WATR", False)):
        for g in gdf.geometry:
            for r in rings(g):
                msp.add_lwpolyline(r[:-1] if closed else r, close=closed, dxfattribs={"layer": layer})
    if site is not None:
        for g in site.geometry:
            for r in rings(g):
                msp.add_lwpolyline(r[:-1], close=True, dxfattribs={"layer": "C-PROP"})
    msp.add_text(f"{ATTRIB}. Local origin = UTM ({ox_:.2f}, {oy_:.2f})", height=2.0,
                 dxfattribs={"layer": "C-ANNO"}).set_placement((0, -10))
    doc.saveas(path)


def main() -> None:
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--point", nargs=2, type=float, metavar=("LAT", "LON"))
    src.add_argument("--geojson", help="local GeoJSON with OSM-style tag columns")
    ap.add_argument("--radius", type=float, default=250, help="metres around --point (max 1500)")
    ap.add_argument("--site", help="GeoJSON polygon of the site boundary")
    ap.add_argument("--out", required=True, help="output path prefix")
    ap.add_argument("--floor-height", type=float, default=3.0, help="m per storey for levels-derived heights")
    ap.add_argument("--dxf", action="store_true", help="also write a DXF in local metres")
    args = ap.parse_args()

    if args.point:
        lat, lon = args.point
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            die("--point must be LAT LON in decimal degrees")
        if not 20 <= args.radius <= 1500:
            die("--radius must be between 20 and 1500 m (be kind to the public Overpass servers)")
        import osmnx as ox
        tags = {"building": True, "highway": True, "natural": ["water", "wood", "scrub", "grassland"],
                "waterway": True, **{k: v for k, v in GREEN.items() if k != "natural"}}
        try:
            gdf = ox.features_from_point((lat, lon), tags=tags, dist=args.radius)
        except Exception as e:  # network, rate limit, empty result
            die(f"OSM fetch failed ({type(e).__name__}: {e}). Retry later or pass --geojson.")
        source = f"OpenStreetMap via Overpass, {args.radius:.0f} m around {lat:.5f}, {lon:.5f}"
    else:
        try:
            gdf = gpd.read_file(args.geojson)
        except Exception as e:
            die(f"cannot read {args.geojson}: {e}")
        if gdf.crs is None:
            gdf = gdf.set_crs(4326)
        source = f"local file {args.geojson}"
    if gdf.empty:
        die("no features found - check the location or the file")

    utm = gdf.estimate_utm_crs()
    gdf = gdf.to_crs(utm)
    if args.point:
        # Overpass returns whole ways; clip to a square of the requested radius.
        c = gpd.GeoSeries([Point(args.point[1], args.point[0])], crs=4326).to_crs(utm).iloc[0]
        gdf = gdf.clip(box(c.x - args.radius, c.y - args.radius, c.x + args.radius, c.y + args.radius))
    site = None
    if args.site:
        site = gpd.read_file(args.site)
        site = (site.set_crs(4326) if site.crs is None else site).to_crs(utm)
        if not site.geometry.geom_type.isin(["Polygon", "MultiPolygon"]).all():
            die("--site must contain polygon(s)")

    layers = classify(gdf)
    buildings = layers[0]
    hs, tagged, lv, unknown = heights(buildings, args.floor_height)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    title = Path(args.out).name.replace("_", " ")
    plot(layers, site, out.with_name(out.name + "_figure_ground"), True, f"{title} - figure-ground")
    plot(layers, site, out.with_name(out.name + "_context"), False, f"{title} - context")

    minx, miny, _, _ = gdf.total_bounds
    if args.dxf:
        to_dxf(layers, site, out.with_suffix(".dxf"), (minx, miny))

    print(f"source: {source}")
    print(f"projected CRS for all measurements: {utm.to_string()}")
    print(f"buildings: {len(buildings)} | street segments: {len(layers[1])} | green areas: {len(layers[2])} | water: {len(layers[3])}")
    print(f"building heights: {tagged} tagged 'height' | {lv} ASSUMED from building:levels x {args.floor_height} m | {unknown} UNKNOWN")
    known = [h for h, _ in hs if h is not None]
    if known:
        print(f"height range of tagged/assumed buildings: {min(known):.1f}-{max(known):.1f} m (not surveyed)")
    if args.point:
        circle = gpd.GeoSeries([Point(args.point[1], args.point[0])], crs=4326).to_crs(utm).buffer(args.radius)
        cover = buildings.geometry.union_all().intersection(circle.iloc[0]).area
        print(f"building coverage within {args.radius:.0f} m radius: {cover:,.0f} m2 of {circle.area.iloc[0]:,.0f} m2 "
              f"= {cover / circle.area.iloc[0]:.1%} (OSM footprints; completeness varies by area)")
    if site is not None:
        a = site.geometry.area.sum()
        print(f"site area: {a:,.1f} m2 ({a / 10000:.4f} ha, {a * 10.7639:,.0f} sq ft) | perimeter {site.geometry.length.sum():,.1f} m"
              " - from the supplied boundary, projected; not a survey")
    print(f"wrote: {out}_figure_ground.png/.svg, {out}_context.png/.svg" + (f", {out.with_suffix('.dxf')}" if args.dxf else ""))
    print(f"attribution (keep on every use): {ATTRIB}")


if __name__ == "__main__":
    main()
