# Rhino MCP servers: tool notes

_Last reviewed: 2026-11. These change fast. If you are reading this much later, assume it is stale and say so._

| Server | Who | Status | Install | Notes |
|---|---|---|---|---|
| RhinoAI ("Rhino MCP") | McNeel (official), github.com/mcneel/RhinoAI | Young, actively developed | Claude Desktop connector (`.mcpb`) that installs the Rhino plugin; docs at mcneel.github.io/RhinoAI/docs/ | Forum reports rough setup early on (stdio config lost, Apple-Silicon-only binary at first). Targets Rhino 9 WIP / Grasshopper 2 use. The old repo name `mcneel/RhinoMCP` now redirects here. |
| rhinomcp | Community (jingcheng-chen/rhinomcp), PyPI `rhinomcp` | Most mature community option | Install the RhinoMCP plugin from Rhino's Package Manager, then `claude mcp add rhino -- uvx rhinomcp@latest` | Rhino 8.20+ on .NET 8, Windows and Mac. Modelling (loft, extrude, sweep, booleans) and Grasshopper (find components, wire, set sliders, solve). |
| grasshopper-mcp | Community (alfredatnycu) | Stale since Mar 2025 | Not recommended | Avoid. |

## Safety

- Both live servers can change the open model. Ask the architect to save, or work on a copy, before a session that modifies geometry.
- Some servers expose a "run arbitrary script" tool. Treat it like running code on their machine: show the script first.

## Docs

- RhinoCommon API: https://developer.rhino3d.com/api/rhinocommon/
- rhinoscriptsyntax: https://developer.rhino3d.com/api/RhinoScriptSyntax/
- Grasshopper: https://developer.rhino3d.com/guides/grasshopper/
