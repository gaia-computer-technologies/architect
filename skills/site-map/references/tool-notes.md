# Site map tool notes

_Last reviewed: 2026-11. If you are reading this much later, assume it is stale and check._

- **OSMnx** (`github.com/gboeing/osmnx`, 2.x at review) queries the public Overpass API and caches responses in `./cache`. Public Overpass servers have usage limits: keep radii small, reuse the cache, and don't loop requests.
- **Overpass/OSM MCP servers** existed at review but were small or stale. Calling Overpass through OSMnx from the script is more reliable.
- **Geocoding.** Use a geocoder you actually have, such as the official Mapbox MCP server (`github.com/mapbox/mcp-server`) or Google's Maps Grounding Lite remote MCP (needs a Google Cloud key). Nominatim (OSM's geocoder) has a strict usage policy. Always show the resulting coordinates to the architect.
- **QGIS.** For heavier GIS work, `nkarasiak/qgis-mcp` was the actively maintained QGIS MCP server at review. The script's outputs (GeoJSON in, PNG/SVG/DXF out) also move easily into QGIS.
- **Authoritative alternatives** to OSM vary by country: national mapping agencies, cadastral services and city open-data portals. Check availability and licence for the specific place before recommending one.
