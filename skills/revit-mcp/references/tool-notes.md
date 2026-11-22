# Revit MCP servers: tool notes

_Last reviewed: 2026-11. If you are reading this much later, assume it is stale and say so._

## Official

**Autodesk Revit Public MCP Server (Tech Preview)**
- Revit 2027.2 only. Runs locally over stdio.
- Three add-ons: **Read**, **Write** (adds model edits), **Experimental**.
- Downloaded through Autodesk account entitlements.
- Docs: https://help.autodesk.com/cloudhelp/ENU/ADSKMCP-RevitMcp/files/ADSKMCP_RevitMcp_revit_mcp_server_html.html
- Announcement: https://www.autodesk.com/blogs/aec/2026/06/17/revit-public-mcp-server/
- Recommendation: install **Read** by default. Treat Write as preview and use it only on detached copies until it matures.

**Autodesk Platform Services (cloud models)**
- `autodesk-platform-services/aps-aecdm-mcp-dotnet`: queries the AEC Data Model GraphQL API for models in Autodesk Construction Cloud. Sample-grade.

## Community (older Revit versions)

The ecosystem is fragmented. Check the repo's last commit before installing.

| Repo | Note |
|---|---|
| mcp-servers-for-revit/revit-mcp | Archived 2026-02. Don't start new setups on it. |
| mcp-servers-for-revit/mcp-servers-for-revit | Active to Apr 2026; describes itself as a fork. |
| mcp-servers-for-revit/mcp-server-for-revit-python | Active (Oct 2026). |
| LuDattilo/revit-mcp-server | "80+ tools", Revit 2023 to 2026. |
| oakplank/RevitMCP | Active (Oct 2026). |

## Scripting without an MCP

- pyRevit: https://github.com/pyrevitlabs/pyRevit
- Dynamo: https://dynamobim.org
- API index: https://www.revitapidocs.com
