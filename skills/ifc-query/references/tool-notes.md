# IFC tool notes

_Last reviewed: 2026-11. Tool details date quickly. If you are reading this much later, assume it is stale, check the project pages, and say so._

## IfcOpenShell (library)

- Python package `ifcopenshell` (0.8 / 0.9 series at time of review). Open source (LGPL), the reference open toolkit for IFC.
- Used by `scripts/ifc_query.py` with `ifcopenshell.util.element` (psets, types, containers), `ifcopenshell.util.selector` (query syntax) and `ifcopenshell.util.unit` (unit scale).
- Install: `uv run` resolves it from the script header, or `pip install ifcopenshell`.

## IfcOpenShell MCP server (`ifcmcp`)

- Lives in the official IfcOpenShell repository under `src/ifcmcp`, published on PyPI as `ifcopenshell-mcp`.
- Example registration with Claude Code: `claude mcp add --transport stdio ifc -- ifcmcp --no-execute`
- Wraps IfcOpenShell's query and edit tools and keeps the model in memory between calls. It also exposes a tool that executes arbitrary Python. **Start it with `--no-execute`** to disable that, and use it read-only unless an edit is explicitly requested, on a copy of the file.

## Viewing a model

- Free viewers to check findings visually: Bonsai (Blender add-on, the IfcOpenShell project's own authoring tool) and BIMvision, plus the IFC import or viewer built into most authoring tools (Revit, Archicad, Vectorworks). Other free viewers come and go; check availability and licensing before recommending one.

## Not recommended at time of review

- Small or unmaintained community IFC MCP servers. Prefer the official `ifcmcp` or the library directly.
