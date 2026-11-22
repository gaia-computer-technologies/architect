# DXF tool notes

_Last reviewed: 2026-11. If you are reading this much later, assume it is stale and check._

- **ezdxf** (`github.com/mozman/ezdxf`, MIT, 1.4.x at review). Used by `scripts/plan_to_dxf.py` for the DXF and for previews (`ezdxf.addons.drawing`, matplotlib and SVG backends). Also reads DXF, which `area-check` uses.
- **DWG.** ezdxf writes DXF only. To deliver DWG, open the DXF in the CAD package and save as DWG, or use the free ODA File Converter (check its licence terms).
- **AutoCAD via MCP.** `puran-water/autocad-mcp` (community) drives AutoCAD LT through AutoLISP and also has a headless ezdxf backend for macOS and Linux. It is useful when the architect wants the drawing created inside their live AutoCAD session. Treat it as community software: review what it will draw, and work on a new layer. Autodesk had no official AutoCAD MCP server at the time of review.
- **Checking a DXF without CAD.** QCAD Community Edition, LibreCAD, or the ezdxf `view` command (`ezdxf view plan.dxf`) all open DXF for a visual check.
