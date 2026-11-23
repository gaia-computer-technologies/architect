# The README demo loop: three skill scripts run for real, each printing its
# inputs and arithmetic.
#   site-map       figure-ground of 150 m around a Rotterdam point, from OpenStreetMap
#   dxf-drawing    a three-room plan from demo/plan.json, areas checked
#   massing-study  feasibility yield from demo/massing.json
# Run from the repo root: vhs assets/tapes/demo.tape
# Needs uv and network. The hidden setup runs each script once off-camera so
# uv's environments and osmnx's Overpass cache are warm; a cold Overpass fetch
# can take a few minutes; the osmnx cache is kept in $OSM_CACHE (default
# ~/.cache/architect-demo/osm) so later recordings skip it. Nothing is written
# inside the repo.
Output assets/demo.gif
Require uv

Set Shell "bash"
Set FontSize 16
Set Width 1280
Set Height 680
Set Padding 24
Set Framerate 20
Set Theme { "name": "Architect", "background": "#000000", "foreground": "#f2f2f2", "cursor": "#f2f2f2", "selection": "#444444", "black": "#000000", "brightBlack": "#8c8c8c", "red": "#ff5f5f", "brightRed": "#ff8787", "green": "#d7d7d7", "brightGreen": "#ffffff", "yellow": "#ffd75f", "brightYellow": "#ffe08a", "blue": "#b0b0b0", "brightBlue": "#d0d0d0", "magenta": "#b0b0b0", "brightMagenta": "#d0d0d0", "cyan": "#b0b0b0", "brightCyan": "#d0d0d0", "white": "#d7d7d7", "brightWhite": "#ffffff" }
Set TypingSpeed 15ms
Set WindowBar Rings
Set WindowBarSize 36
Set BorderRadius 0
Set Margin 0
Set WaitTimeout 600s
Set WaitPattern /^\$ ?$/
Env BASH_SILENCE_DEPRECATION_WARNING "1"

# Private scratch folder with the demo specs and a link to the skills.
Hide
Type `export PS1='$ ' REPO="$PWD" DEMO="$(mktemp -d)" OSM_CACHE="${OSM_CACHE:-$HOME/.cache/architect-demo/osm}" && mkdir -p "$OSM_CACHE" && cp assets/tapes/demo/*.json "$DEMO" && cd "$DEMO" && ln -s "$REPO/skills" skills && ln -s "$OSM_CACHE" cache` Enter
Type `uv run -q skills/site-map/scripts/site_map.py --point 51.9225 4.4792 --radius 150 --out out/rdam >/dev/null 2>&1; uv run -q skills/dxf-drawing/scripts/plan_to_dxf.py plan.json --out out/plan.dxf >/dev/null 2>&1; uv run -q skills/massing-study/scripts/massing.py massing.json --out out/massing >/dev/null 2>&1; rm -rf out; clear; echo WA""RM` Enter
Wait+Screen /WARM/
Type "clear" Enter
Sleep 300ms
Show

Type "uv run skills/site-map/scripts/site_map.py --point 51.9225 4.4792 --radius 150 --out out/rdam" Sleep 300ms Enter
Wait
Sleep 1.5s

Type "uv run skills/dxf-drawing/scripts/plan_to_dxf.py plan.json --out out/plan.dxf" Sleep 300ms Enter
Wait
Sleep 1.5s

Type "clear && uv run skills/massing-study/scripts/massing.py massing.json --out out/massing" Sleep 300ms Enter
Wait
Sleep 4s

# Remove the private demo folder.
Hide
Type `cd / && rm -rf "$DEMO"` Enter
