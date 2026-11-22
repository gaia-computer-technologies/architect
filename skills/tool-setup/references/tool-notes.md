# Connector table

_Last reviewed: 2026-11. Connectors change monthly. If you are reading this much later, assume it is stale, say so, and check each repo's last commit before recommending it._

Legend: **Official** = from the software vendor. **Community** = third party; check activity. **Risk**: R = reads, W = writes to the model, X = can run arbitrary code, C = cloud / data leaves the machine.

| Software | Recommended | Status | Install | Risk | Needs / caveat |
|---|---|---|---|---|---|
| Rhino 8 | jingcheng-chen/rhinomcp | Community, most mature | Rhino Package Manager: "RhinoMCP"; then `claude mcp add rhino -- uvx rhinomcp@latest` | R W | Rhino 8.20+ (.NET 8), Win/Mac. Includes Grasshopper control. |
| Rhino (official) | mcneel/RhinoAI | Official, young | Claude Desktop connector / `.mcpb`; docs mcneel.github.io/RhinoAI/docs/ | R W | Early setup rough per McNeel forum; Rhino 9 WIP focus. |
| Revit 2027.2 | Autodesk Revit Public MCP (Read add-on) | Official, tech preview | Autodesk account entitlements download; local stdio | R (W with Write add-on) | 2027.2 only. Keep Write off until trusted. |
| Revit 2023 to 2026 | mcp-servers-for-revit/mcp-server-for-revit-python, LuDattilo/revit-mcp-server | Community, fragmented | Per repo README | R W | Check last commit; original revit-mcp is archived. |
| Archicad 30 | Public Archicad MCP Server (Beta) | Official, beta | Archicad AI Assistant settings | R W | Needs Collaborate or Max subscription. |
| Archicad (any) | SzamosiMate/tapir-archicad-MCP on the Tapir add-on | Community, active | Install Tapir add-on, then per README | R W | |
| SketchUp | Trimble SketchUp connector | Official | Claude connector directory; Trimble ID | R W C | Free accounts limited to 30 saved models. |
| Blender | Blender Lab MCP (projects.blender.org/lab/blender_mcp) | Official | Claude connector directory | R W X | Blender 5.1+. Blender warns it runs LLM code without guards. |
| Blender | ahujasid/mcp-for-blender | Community, very popular | Per README | R W X | Arbitrary Python execution. |
| IFC (any) | IfcOpenShell `ifcmcp` (PyPI `ifcopenshell-mcp`) | Official to IfcOpenShell project | `claude mcp add --transport stdio ifc -- ifcmcp --no-execute` | R W (X without flag) | Use `--no-execute` to disable arbitrary Python. |
| Bonsai (IFC in Blender) | JotaDeRodriguez/Bonsai_mcp | Community | Per README | R W X | Experimental. |
| AutoCAD LT / DXF | puran-water/autocad-mcp | Community, active | Per README; has a headless ezdxf backend for Mac/Linux | R W | No official Autodesk AutoCAD MCP. For plain DXF output, no MCP is needed (ezdxf). |
| Bluebeam Revu | Bluebeam Revu MCP | Official | support.bluebeam.com/revu/resources/revu-mcp.html | R W | Revu 21.9+, Bluebeam Max plan, desktop only. |
| Miro | Miro MCP (hosted) | Official, public beta | `claude mcp add --transport http miro https://mcp.miro.com` | R W C | Disabled by default on Enterprise plans. |
| Figma | Figma MCP | Official | See github.com/figma/mcp-server-guide | R W C | |
| QGIS | nkarasiak/qgis-mcp | Community, active | Per README | R W X | The older jjsantos01/qgis_mcp is stale. |
| Mapbox | mapbox/mcp-server | Official | Per README; Mapbox token | R C | |
| Google Maps | Maps Grounding Lite | Official | `https://mapstools.googleapis.com/mcp` (HTTP); GCP key or OAuth | R C | search_places, compute_routes, lookup_weather. |
| V-Ray (SketchUp, Rhino) | Chaos V-Ray MCP | Official, announced 2026-11 | Per Chaos docs | R W | Very new; verify availability. |

## No good connector yet (use files or APIs instead)

- **Vectorworks, Speckle, Autodesk Forma, Twinmotion, Enscape, D5:** no official MCP found; community ones are tiny or stale. Use exports (IFC, DXF, PDF) or the vendor API.
- **OpenStreetMap / Overpass, Ladybug / Honeybee:** community MCPs are stale or tiny. Call the libraries from code (OSMnx, ladybug-core).
- **Planning data:** UK planning.data.gov.uk has an official keyless API (planning.data.gov.uk/docs); NYC uses Socrata SODA. Call them directly.
- **Embodied carbon:** no EC3 MCP. The EC3 API needs notice to Building Transparency and attribution.
