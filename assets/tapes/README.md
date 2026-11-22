# Demo tapes

[VHS](https://github.com/charmbracelet/vhs) scripts for the GIF in `assets/`.
From the repo root:

```bash
vhs assets/tapes/demo.tape
```

| Tape | Output | Shows |
|------|--------|-------|
| `demo.tape` | `assets/demo.gif` | `site-map`, `dxf-drawing` and `massing-study` run for real, each printing its inputs and arithmetic |

The inputs are `demo/plan.json` (three rooms with expected areas) and
`demo/massing.json` (a 40 x 30 m site with setbacks, a height limit, a
coverage cap and a FAR cap). The site map is 150 m around 51.9225 N, 4.4792 E
in Rotterdam, live from OpenStreetMap.

The tape needs `uv` and network. Its hidden setup copies the specs to a
private temporary folder, runs each script once off-camera so uv's
environments and the osmnx Overpass cache are warm, then records the runs.
A cold Overpass fetch can take a few minutes. Nothing is written inside the
repo. OpenStreetMap data changes, so the site-map counts can differ between
recordings; update the README alt text when they do.
