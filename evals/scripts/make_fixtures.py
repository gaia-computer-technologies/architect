# /// script
# requires-python = ">=3.10"
# dependencies = ["ifcopenshell>=0.8", "pymupdf>=1.24"]
# ///
"""Regenerate the binary and geographic script-eval fixtures.

The CSV and JSON fixtures are written by hand. The IFC model, the PDFs and the
GeoJSON are generated here so they stay tiny, reproducible and reviewable.
Every value is a round test number, not real project data.

Usage: uv run evals/scripts/make_fixtures.py
"""
from __future__ import annotations

import json
from pathlib import Path

import ifcopenshell
import ifcopenshell.api as api
import pymupdf

HERE = Path(__file__).parent / "fixtures"
A3 = (420 / 25.4 * 72, 297 / 25.4 * 72)  # landscape, PDF points


def ifc_model() -> None:
    f = api.run("project.create_file", version="IFC4")
    project = api.run("root.create_entity", f, ifc_class="IfcProject", name="Eval model")
    api.run("unit.assign_unit", f)
    api.run("context.add_context", f, context_type="Model")
    site = api.run("root.create_entity", f, ifc_class="IfcSite", name="Site")
    building = api.run("root.create_entity", f, ifc_class="IfcBuilding", name="Building")
    storey = api.run("root.create_entity", f, ifc_class="IfcBuildingStorey", name="Ground")
    storey.Elevation = 0.0
    api.run("aggregate.assign_object", f, products=[site], relating_object=project)
    api.run("aggregate.assign_object", f, products=[building], relating_object=site)
    api.run("aggregate.assign_object", f, products=[storey], relating_object=building)

    # Three spaces: two with a net floor area quantity (20 + 15 m2), one without.
    for name, area in (("Living", 20.0), ("Kitchen", 15.0), ("Store", None)):
        sp = api.run("root.create_entity", f, ifc_class="IfcSpace", name=name)
        api.run("aggregate.assign_object", f, products=[sp], relating_object=storey)
        if area is not None:
            q = api.run("pset.add_qto", f, product=sp, name="Qto_SpaceBaseQuantities")
            api.run("pset.edit_qto", f, qto=q, properties={"NetFloorArea": area})

    # Three doors: two carry a fire rating, one does not.
    for name, rating in (("D01", "FD30"), ("D02", "FD60"), ("D03", None)):
        d = api.run("root.create_entity", f, ifc_class="IfcDoor", name=name)
        api.run("spatial.assign_container", f, products=[d], relating_structure=storey)
        p = api.run("pset.add_pset", f, product=d, name="Pset_DoorCommon")
        props = {"IsExternal": False}
        if rating:
            props["FireRating"] = rating
        api.run("pset.edit_pset", f, pset=p, properties=props)

    # Two walls with net side areas 12.5 + 7.5 = 20.0.
    for name, a in (("W01", 12.5), ("W02", 7.5)):
        w = api.run("root.create_entity", f, ifc_class="IfcWall", name=name)
        api.run("spatial.assign_container", f, products=[w], relating_structure=storey)
        q = api.run("pset.add_qto", f, product=w, name="Qto_WallBaseQuantities")
        api.run("pset.edit_qto", f, qto=q, properties={"NetSideArea": a})

    out = HERE / "ifc-query" / "model.ifc"
    f.write(str(out))
    print(f"wrote {out}")


def title_block(page, lines: list[str]) -> None:
    w, h = page.rect.width, page.rect.height
    page.draw_rect(pymupdf.Rect(w * 0.70, h * 0.78, w - 20, h - 20), color=(0, 0, 0), width=0.8)
    y = h * 0.78 + 18
    for ln in lines:
        page.insert_text((w * 0.70 + 8, y), ln, fontsize=9)
        y += 12


def drawing_set() -> None:
    doc = pymupdf.open()
    # Sheet 1: revision differs from the register (P01 vs P02) and the scale is
    # stated at A1 on an A3 sheet.
    p = doc.new_page(width=A3[0], height=A3[1])
    title_block(p, ["Drawing No: A-100", "Title: Ground Floor Plan", "Rev: P01", "Status: S2",
                    "Date: 2026-11-02", "Scale: 1:100 @ A1"])
    # Sheet 2: matches the register.
    p = doc.new_page(width=A3[0], height=A3[1])
    title_block(p, ["Drawing No: A-101", "Title: First Floor Plan", "Rev: P01", "Status: S2",
                    "Date: 2026-11-02", "Scale: 1:100 @ A3"])
    # Sheet 3: a scan with no text layer. Must be flagged, never guessed.
    p = doc.new_page(width=A3[0], height=A3[1])
    p.draw_rect(pymupdf.Rect(40, 40, A3[0] - 40, A3[1] - 40), color=(0, 0, 0), width=2)
    out = HERE / "drawing-register-qa" / "set.pdf"
    doc.save(str(out), garbage=4, deflate=True)
    print(f"wrote {out}")


def markups() -> None:
    doc = pymupdf.open()
    p = doc.new_page(width=A3[0], height=A3[1])
    p.insert_text((200, 200), "Door D01", fontsize=12)
    title_block(p, ["Drawing No: A-201", "Title: Door Details"])
    a = p.add_text_annot((210, 190), "Check door swing against corridor width")
    a.set_info(title="Client", subject="Comment")
    a.update()
    a = p.add_freetext_annot(pymupdf.Rect(300, 300, 520, 330), "Add fire rating note", fontsize=10)
    a.set_info(title="Consultant")
    a.update()
    a = p.add_rect_annot(pymupdf.Rect(180, 180, 280, 210))  # graphic-only, no comment
    a.set_info(title="Client")
    a.update()
    out = HERE / "markup-review" / "markups.pdf"
    doc.save(str(out), garbage=4, deflate=True)
    print(f"wrote {out}")


def geojson() -> None:
    # A small block near 52.0 N, 4.0 E. 1e-4 deg ~ 11.1 m north, ~6.9 m east.
    def rect(x0, y0, x1, y1):
        return [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]

    lon, lat = 4.0, 52.0
    feats = [
        {"type": "Feature", "properties": {"building": "yes", "height": "12"},
         "geometry": {"type": "Polygon", "coordinates": rect(lon, lat, lon + 2e-4, lat + 1e-4)}},
        {"type": "Feature", "properties": {"building": "yes", "building:levels": "3"},
         "geometry": {"type": "Polygon", "coordinates": rect(lon + 3e-4, lat, lon + 5e-4, lat + 1e-4)}},
        {"type": "Feature", "properties": {"building": "yes"},
         "geometry": {"type": "Polygon", "coordinates": rect(lon, lat + 2e-4, lon + 2e-4, lat + 3e-4)}},
        {"type": "Feature", "properties": {"highway": "residential"},
         "geometry": {"type": "LineString", "coordinates": [[lon - 1e-4, lat + 1.5e-4], [lon + 6e-4, lat + 1.5e-4]]}},
    ]
    (HERE / "site-map" / "context.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, indent=1))
    site = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"name": "site"},
         "geometry": {"type": "Polygon", "coordinates": rect(lon + 3e-4, lat + 2e-4, lon + 5e-4, lat + 3e-4)}}]}
    (HERE / "site-map" / "site.geojson").write_text(json.dumps(site, indent=1))
    print("wrote site-map/context.geojson, site-map/site.geojson")


if __name__ == "__main__":
    ifc_model()
    drawing_set()
    markups()
    geojson()
