"""Script evals: every skills/*/scripts/*.py runs on a tiny checked-in fixture
and must print the expected numbers, or refuse with a non-zero exit when the
input breaks a house rule (uncited factor, missing units, missing planning input).

Each script runs exactly as an agent would run it: `uv run <script> ...`, so its
PEP 723 dependencies are resolved by uv. No API key, no network (the live OSM
test is skipped unless ARCHITECT_EVAL_NETWORK=1).

Run:  uv run --with pytest pytest evals/scripts -q
"""
from __future__ import annotations

import csv
import json
import math
import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIX = Path(__file__).resolve().parent / "fixtures"
SKILLS = ROOT / "skills"


def run(script: str, *args, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """`uv run -q skills/<script> args`, returning stdout+stderr merged in .out."""
    p = subprocess.run(["uv", "run", "-q", str(SKILLS / script), *map(str, args)],
                       capture_output=True, text=True, cwd=cwd or ROOT, timeout=600)
    p.out = p.stdout + p.stderr  # type: ignore[attr-defined]
    return p


def ok(p):
    assert p.returncode == 0, p.out
    return p.out


# ---------------------------------------------------------------- carbon-estimate

CARBON = "carbon-estimate/scripts/carbon_estimate.py"


def test_carbon_totals_with_basis():
    out = ok(run(CARBON, FIX / "carbon-estimate/quantities.csv", FIX / "carbon-estimate/factors.csv",
                 "--gia", 100, "--benchmark", 50, "--benchmark-source", "TEST target"))
    # 10 m3 x 2400 kg/m3 x 0.1 = 2,400; 5 m3 x 100 = 500; 2 t -> 2000 kg x 1.5 = 3,000
    assert "Scope: A1-A3" in out
    assert re.search(r"TOTAL\s+5,900\s+\(5\.9 tCO2e\)", out)
    assert "10 m3 x 2400 kg/m3 (TEST FIXTURE density) = 24000 kg" in out
    assert "2 t x 1000 = 2000 kg" in out
    assert "= 59 kgCO2e/m2 (A1-A3)" in out
    assert "above target by 9 kgCO2e/m2" in out


@pytest.mark.parametrize("factors, reason", [
    ("factors_uncited.csv", "has no source"),
    ("factors_mixed_stages.csv", "different life-cycle stages"),
    ("factors_no_density.csv", "Unit mismatch"),
])
def test_carbon_refuses(factors, reason):
    p = run(CARBON, FIX / "carbon-estimate/quantities.csv", FIX / "carbon-estimate" / factors)
    assert p.returncode != 0, p.out
    assert reason in p.out
    assert "TOTAL" not in p.out


# ---------------------------------------------------------------- practice-pulse

PULSE = "practice-pulse/scripts/practice_pulse.py"


def test_practice_pulse_cpi_and_flags():
    d = FIX / "practice-pulse"
    out = ok(run(PULSE, d / "timesheets.csv", d / "fees.csv", d / "staff.csv"))
    # P1: 10h x 50 + 10h x 30 = 800 cost; EV 2000 x 50% = 1000; CPI 1.25; forecast 800/0.5 = 1600
    assert re.search(r"P1\s+20\.0\s+800\s+2,000\s+40%\s+50%\s+1,000\s+1\.25\s+1,600", out)
    # P2: 20h x 50 = 1000; EV 1500 x 40% = 600; CPI 0.60; forecast 2500 > fee by 1000
    assert re.search(r"P2\s+20\.0\s+1,000\s+1,500\s+67%\s+40%\s+600\s+0\.60\s+2,500\s+OVERRUNNING", out)
    assert "forecast exceeds fee by 1,000" in out
    assert "Flagged projects: P2" in out
    # Leave is not billable: Bob books 18 h in total, 10 h billable.
    assert re.search(r"Bob\s+10\.0\s+18\.0", out)


def test_practice_pulse_refuses_missing_rate():
    d = FIX / "practice-pulse"
    p = run(PULSE, d / "timesheets.csv", d / "fees.csv", d / "staff_missing.csv")
    assert p.returncode == 1
    assert "No cost rate / capacity for person 'Bob'" in p.out


# ---------------------------------------------------------------- snag-list

def test_snag_summary(tmp_path):
    html = tmp_path / "snags.html"
    out = ok(run("snag-list/scripts/snag_report.py", FIX / "snag-list/snags.csv", "-o", html))
    assert "Total items: 4" in out
    assert "Closed: 2/4 (50%)" in out
    assert "Not closed, by priority: high 2" in out
    page = html.read_text()
    assert page.count("<tr class=") == 4
    assert "does not relieve the contractor" in page  # records, never certifies


# ---------------------------------------------------------------- area-check

AREA = "area-check/scripts/area_check.py"


def test_area_csv_efficiency_and_brief_miss():
    d = FIX / "area-check"
    p = run(AREA, "--csv", d / "areas.csv", "--gross", 40, "--brief", d / "brief.csv")
    assert p.returncode == 3, p.out  # Kitchen 10 vs 12 is outside 5 %
    assert "Net-to-gross efficiency = 30.00 / 40.00 = 75.0%" in p.out
    assert "| Kitchen | 12.00 | 10.00 | -2.00 (-16.7%) | OUTSIDE +/-5% |" in p.out
    assert "| Living | 20.00 | 20.00 | +0.00 (+0.0%) | OK +/-5% |" in p.out


def test_area_csv_brief_met():
    d = FIX / "area-check"
    ok(run(AREA, "--csv", d / "areas.csv", "--brief", d / "brief_ok.csv"))


def test_area_ifc_counts_missing_quantities():
    out = ok(run(AREA, "--ifc", FIX / "ifc-query/model.ifc"))
    assert "IfcSpace: 3 | without area quantity: 1" in out
    assert "| **Sum of measured spaces** | **35.00** | 2 spaces |" in out
    assert "NO area quantity" in out


# ---------------------------------------------------------------- dxf-drawing (+ area-check on its output)

DXF = "dxf-drawing/scripts/plan_to_dxf.py"


def test_dxf_writes_and_area_check_measures_it(tmp_path):
    dxf = tmp_path / "plan.dxf"
    out = ok(run(DXF, FIX / "dxf-drawing/plan.json", "--out", dxf))
    assert "units: m ($INSUNITS=6)" in out
    assert "room 'Living': drawn area 20.000 m2 vs expected 20.000 -> OK" in out
    assert "audit errors: 0" in out
    for ext in (".dxf", ".png", ".svg"):
        assert dxf.with_suffix(ext).stat().st_size > 0
    # Round trip: measure the file we just wrote.
    out = ok(run(AREA, "--dxf", dxf, "--room-layer", "A-ROOM", "--gross-layer", "C-PROP"))
    assert "| Living | uncategorised | 20.00 |" in out
    assert "| Kitchen | uncategorised | 9.00 |" in out
    assert "Net-to-gross efficiency = 29.00 / 60.00 = 48.3%" in out


def test_dxf_area_assertion_fails(tmp_path):
    p = run(DXF, FIX / "dxf-drawing/plan_mismatch.json", "--out", tmp_path / "p.dxf")
    assert p.returncode == 3
    assert "drawn area 9.000 m2 vs expected 10.000 -> MISMATCH (10.0%)" in p.out


def test_dxf_refuses_without_units(tmp_path):
    p = run(DXF, FIX / "dxf-drawing/plan_no_units.json", "--out", tmp_path / "p.dxf")
    assert p.returncode == 1
    assert "Never assume units" in p.out


# ---------------------------------------------------------------- massing-study

MASS = "massing-study/scripts/massing.py"


def test_massing_yield(tmp_path):
    out = ok(run(MASS, FIX / "massing-study/spec.json", "--out", tmp_path / "m"))
    # 40 x 30 site; setbacks 6 / 3 / 3 / 3 -> 34 x 21 = 714 m2
    assert "Site area = 1,200.0 m2" in out
    assert "Buildable footprint after setbacks = 714.0 m2" in out
    # 1 + floor((21 - 4.5) / 3.15) = 6 storeys; FAR 3 caps GFA at 3,600 -> floor(3600 / 714) = 5
    assert "Storeys by height = 1 + floor((21 - 4.5) / 3.15) = 6" in out
    assert "storeys cut to 5" in out
    assert "Net area = GFA 3,570.0 x efficiency 80%" in out
    assert "= 2,856.0 m2" in out
    assert "Units = floor(2,856.0 / 65) = 43" in out
    assert "USER-SUPPLIED, TO VERIFY" in out
    for suffix in (".glb", ".obj"):
        assert (tmp_path / f"m{suffix}").stat().st_size > 0


def test_massing_refuses_missing_planning_input(tmp_path):
    p = run(MASS, FIX / "massing-study/spec_no_height.json", "--out", tmp_path / "m")
    assert p.returncode == 1
    assert "'max_height' is required" in p.out


# ---------------------------------------------------------------- design-diagram

DIAG = "design-diagram/scripts/adjacency_diagram.py"


def test_bubble_area_is_honest(tmp_path):
    svg = tmp_path / "b.svg"
    out = ok(run(DIAG, FIX / "design-diagram/spec.json", "--out", svg))
    assert "spaces: 4; adjacencies: 3; total area: 205 m2" in out
    radii = sorted(float(r) for r in re.findall(r'<circle [^>]*r="([0-9.]+)"', svg.read_text()))
    assert len(radii) == 4
    # Areas 16, 25, 64, 100 -> radii in ratio 4 : 5 : 8 : 10 (area-proportional bubbles).
    for r, k in zip(radii, (4, 5, 8, 10)):
        assert math.isclose(r / radii[0], k / 4, rel_tol=0.01)


def test_stack_totals(tmp_path):
    out = ok(run(DIAG, FIX / "design-diagram/spec.json", "--out", tmp_path / "s.svg", "--mode", "stack"))
    assert "level 1: 80 m2 across 2 spaces" in out
    assert "level 0: 125 m2 across 2 spaces" in out


def test_diagram_refuses_unknown_space(tmp_path):
    p = run(DIAG, FIX / "design-diagram/spec_bad_adjacency.json", "--out", tmp_path / "x.svg")
    assert p.returncode == 1
    assert "names a space that is not in 'spaces'" in p.out


# ---------------------------------------------------------------- ifc-query

IFC = "ifc-query/scripts/ifc_query.py"
MODEL = FIX / "ifc-query/model.ifc"


def test_ifc_summary():
    out = ok(run(IFC, MODEL, "summary"))
    assert "schema: IFC4" in out
    assert "| IfcDoor | 3 |" in out and "| IfcSpace | 3 |" in out and "| IfcWall | 2 |" in out
    assert "IfcSpace with Qto_SpaceBaseQuantities: 2 of 3" in out


def test_ifc_gaps_names_the_missing_door():
    out = ok(run(IFC, MODEL, "gaps", "IfcDoor", "--require", "Pset_DoorCommon.FireRating"))
    assert re.search(r"\| Pset_DoorCommon\.FireRating \| 2 \| 1 \| \S+ \(D03\) \|", out)


def test_ifc_qto_sum():
    out = ok(run(IFC, MODEL, "qto", "IfcWall", "--quantity", "Qto_WallBaseQuantities.NetSideArea"))
    assert "sum = 20.000 over 2 element(s) with the quantity; 0 element(s) have no value" in out


def test_ifc_schedule_csv(tmp_path):
    out = ok(run(IFC, MODEL, "schedule", "IfcDoor", "--props", "Name,Pset_DoorCommon.FireRating",
                 "--csv", tmp_path / "doors.csv"))
    assert "empty values: Name: 0/3, Pset_DoorCommon.FireRating: 1/3" in out
    rows = list(csv.reader((tmp_path / "doors.csv").open()))
    assert [r[1:] for r in rows[1:]] == [["D01", "FD30"], ["D02", "FD60"], ["D03", ""]]


# ---------------------------------------------------------------- drawing-register-qa

def test_register_qa_finds_every_issue(tmp_path):
    d = FIX / "drawing-register-qa"
    p = run("drawing-register-qa/scripts/register_qa.py", d / "set.pdf", "--out", tmp_path / "reg.csv",
            "--register", d / "issued.csv")
    assert p.returncode == 3, p.out
    assert "| A-100 | revision | P02 | P01 | MISMATCH" in p.out
    assert "| A-102 | - | listed | not in set | MISSING FROM SET |" in p.out
    assert "scale stated at A1 but sheet measures A3 landscape" in p.out
    assert "NO TEXT LAYER - needs OCR or manual entry; nothing guessed" in p.out
    assert "Issues: 4." in p.out
    rows = list(csv.DictReader((tmp_path / "reg.csv").open()))
    assert [r["number"] for r in rows] == ["A-100", "A-101", ""]  # page 3 left blank, not guessed


# ---------------------------------------------------------------- markup-review

def test_markups_extracted_without_guessing(tmp_path):
    out_csv = tmp_path / "markups.csv"
    out = ok(run("markup-review/scripts/extract_annotations.py", out_csv, FIX / "markup-review/markups.pdf"))
    assert "Markups extracted: 3" in out
    assert "By type: FreeText 1, Square 1, Text 1" in out
    assert "Markups with no comment text: 1" in out
    rows = list(csv.DictReader(out_csv.open()))
    assert {r["sheet_label"] for r in rows} == {"A-201"}
    assert {r["comment"] for r in rows} == {"Check door swing against corridor width", "Add fire rating note", ""}


# ---------------------------------------------------------------- sun-study

def test_sun_study_solstice_geometry(tmp_path):
    out = ok(run("sun-study/scripts/sun_study.py", "--lat", 52.37, "--lon", 4.90, "--tz", "Europe/Amsterdam",
                 "--year", 2026, "--height", 10, "--out", tmp_path / "sun"))
    assert out.startswith("# Sun study") and "NOT A COMPLIANCE CALCULATION" in out
    alt = {m.group(1): float(m.group(2)) for m in
           re.finditer(r"## (\w+) (?:equinox|solstice).*?max altitude ([0-9.]+) deg", out, re.S)}
    # Noon altitude ~ 90 - lat +/- 23.44 (plus < 0.1 deg refraction).
    assert abs(alt["June"] - (90 - 52.37 + 23.44)) < 0.3, alt
    assert abs(alt["December"] - (90 - 52.37 - 23.44)) < 0.3, alt
    # Solar noon in Amsterdam (4.9 E, CEST in June) falls around 13:40 local clock time.
    assert re.search(r"June solstice.*?solar noon ~13:[34]\d", out, re.S)
    # Every shadow row is height / tan(altitude).
    rows = re.findall(r"\| \d\d:\d\d \| ([0-9.]+) deg \| [^|]+\| ([0-9.]+) m towards", out)
    assert len(rows) > 30
    for a, L in rows:
        # Altitude is printed to 0.1 deg, so bound the shadow by that rounding interval.
        lo = 10 / math.tan(math.radians(float(a) + 0.05)) - 0.05
        hi = 10 / math.tan(math.radians(max(float(a) - 0.05, 1e-3))) + 0.05
        assert lo <= float(L) <= hi, (a, L)
    assert (tmp_path / "sun_sunpath.png").stat().st_size > 0


def test_sun_study_refuses_bad_height(tmp_path):
    p = run("sun-study/scripts/sun_study.py", "--lat", 52.37, "--lon", 4.90, "--tz", "Europe/Amsterdam",
            "--height", -1, "--out", tmp_path / "s")
    assert p.returncode == 1 and "--height must be > 0" in p.out


# ---------------------------------------------------------------- site-map

SITE = "site-map/scripts/site_map.py"


def test_site_map_offline_geojson(tmp_path):
    d = FIX / "site-map"
    out = ok(run(SITE, "--geojson", d / "context.geojson", "--site", d / "site.geojson",
                 "--out", tmp_path / "site", "--dxf"))
    assert "projected CRS for all measurements: EPSG:32631" in out
    assert "buildings: 3 | street segments: 1" in out
    assert "1 tagged 'height' | 1 ASSUMED from building:levels x 3.0 m | 1 UNKNOWN" in out
    assert "height range of tagged/assumed buildings: 9.0-12.0 m (not surveyed)" in out
    # 2e-4 deg lon x 1e-4 deg lat at 52 N ~ 13.7 m x 11.1 m ~ 152.6 m2
    m = re.search(r"site area: ([0-9.,]+) m2", out)
    assert m and abs(float(m.group(1).replace(",", "")) - 152.6) < 1.5
    assert "(c) OpenStreetMap contributors, ODbL 1.0" in out
    assert (tmp_path / "site.dxf").stat().st_size > 0


@pytest.mark.skipif(os.environ.get("ARCHITECT_EVAL_NETWORK") != "1",
                    reason="needs the public Overpass API; set ARCHITECT_EVAL_NETWORK=1 to run")
def test_site_map_live_osm(tmp_path):
    # cwd=tmp_path: osmnx writes its HTTP cache to ./cache
    out = ok(run(SITE, "--point", 51.9225, 4.4792, "--radius", 100, "--out", tmp_path / "live", cwd=tmp_path))
    assert "OpenStreetMap via Overpass" in out and "building coverage within 100 m radius" in out


# ---------------------------------------------------------------- house-rule wiring (static)

HOOK = ROOT / "hooks/check-disclaimer.sh"


def _hook(path: Path) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(path)}})
    return subprocess.run(["bash", str(HOOK)], input=payload, capture_output=True, text=True)


def test_disclaimer_hook_flags_unmarked_regulated_output(tmp_path):
    md = tmp_path / "note.md"
    md.write_text("The stair complies with the building code. Rate: £2,400/m².\n")
    p = _hook(md)
    assert p.returncode == 0  # advisory, never blocks
    assert "no disclaimer marker" in p.stderr


def test_disclaimer_hook_quiet_when_marked(tmp_path):
    md = tmp_path / "note.md"
    md.write_text("Appears consistent with the building code (verify).\n\n<!-- architect:requires-disclaimer -->\n")
    p = _hook(md)
    assert p.returncode == 0 and p.stderr == ""


GUARDED = ["regulation-navigator", "cost-check", "contract-admin-letter", "site-context", "carbon-estimate"]


@pytest.mark.parametrize("skill", GUARDED)
def test_guarded_skills_ship_the_marker(skill):
    # npx skills installs one folder at a time, so the marker must be inline in each SKILL.md.
    assert "<!-- architect:requires-disclaimer -->" in (SKILLS / skill / "SKILL.md").read_text()


MARKED = sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md") if "architect:requires-disclaimer" in p.read_text())


@pytest.mark.parametrize("skill", MARKED)
def test_marker_is_fenced_and_copied_verbatim(skill):
    # Baseline 2026-11-22: a bare HTML comment in SKILL.md reads as an authoring note and the
    # model dropped it from chat replies. Keep it inside a code block, with the copy instruction.
    lines = (SKILLS / skill / "SKILL.md").read_text().splitlines()
    i = next(n for n, l in enumerate(lines) if "<!-- architect:requires-disclaimer -->" in l)
    assert sum(l.strip().startswith("```") for l in lines[:i]) % 2 == 1, "marker is not inside a fenced block"
    assert any("Copy the disclaimer exactly as shown" in l for l in lines[i:i + 12])


def test_every_script_has_an_eval():
    scripts = sorted(p.relative_to(SKILLS).as_posix() for p in SKILLS.glob("*/scripts/*.py"))
    src = Path(__file__).read_text()
    missing = [s for s in scripts if s not in src]
    assert not missing, f"scripts with no eval: {missing}"
