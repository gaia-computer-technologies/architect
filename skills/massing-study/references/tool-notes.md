# Massing tool notes

_Last reviewed: 2026-11. MCP servers for CAD tools are young and change monthly. Check the project page before relying on any of this, and say so if it is stale._

## Library route (always available)

- `scripts/massing.py` uses shapely (geometry), trimesh with mapbox-earcut (extrusion and triangulation) and matplotlib (images). Outputs `.glb` (glTF binary, Y-up) and `.obj` (Z-up, metres). Both import into Rhino, Blender, SketchUp (via an importer), Revit (via conversion) and most web viewers.

## Rhino

- **McNeel RhinoAI** (official, `github.com/mcneel/RhinoAI`; "RhinoMCP" was its old repository name). Ships as a Claude Desktop connector that installs the Rhino plugin. It is young: users report setup rough edges, and early builds targeted Rhino WIP. Check its docs for the current Rhino version requirement.
- **rhinomcp** (community, `github.com/jingcheng-chen/rhinomcp`, PyPI `rhinomcp`). Rhino 8 on Windows and Mac. Install the plugin from the Rhino Package Manager, then register the server, for example `claude mcp add rhino -- uvx rhinomcp@latest`. Covers modelling commands and Grasshopper. At the time of review it was the most mature option.
- Guardrails: read the document units and tolerance before creating anything; create on a new named layer (for example `MASSING-option-a`); create in small batches and capture the viewport after each; never delete or modify existing objects unless asked.

## Blender

- **Blender Lab MCP** (official, from the Blender project; requires a recent Blender release, with a Claude connector). **mcp-for-blender** (community, `github.com/ahujasid/mcp-for-blender`, very widely used).
- Both execute Python inside Blender, and Blender's own listing warns that LLM-generated code runs without guards. Work in a new collection, save a copy first, and keep generated code short and readable.
- Bonsai (the IFC authoring add-on for Blender) has community MCP servers. They are experimental, so prefer IFC export and the `ifc-query` skill.

## SketchUp

- Trimble announced an official SketchUp connector in Claude's connector directory (April 2026). It requires a Trimble ID. `mhyrr/sketchup-mcp` is a community alternative. For massing, importing the `.obj` is often simpler and safer.
