# README artwork

The hero and gallery follow Gaia's design system: paper `#FDFDFA`, Gaia Black `#1A1A1A`, True Black `#0A0A0A`, and neon `#DEFF00` used only on dark surfaces. Type is ITC Garamond Narrow Light for the display line, Basis Grotesque for body text, and Routed Gothic (uppercase, wide letter-spacing) for labels.

- `../gallery/*.png`: real skill outputs (`site-map`, `dxf-drawing`, `sun-study`, `massing-study`, `design-diagram`), made into tiles with `uv run assets/src/paper_tiles.py <output.png> ../gallery/<name>.png`.
- `../hero.png`: a screenshot of `hero.html` at 1680x840.

## Rebuilding the hero

The brand fonts are commercially licensed and are **not** in this repository. Put `garamond-itc-light-narrow.woff2`, `basis-grotesque-regular.woff2` and `routed-gothic.woff2` in `assets/src/fonts/` (gitignored), then:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --hide-scrollbars \
  --allow-file-access-from-files --force-device-scale-factor=1 --window-size=1680,840 \
  --virtual-time-budget=3000 --screenshot="$PWD/assets/hero.png" "file://$PWD/assets/src/hero.html"
```

Without the fonts the page falls back to system fonts, so don't commit a hero rendered that way.
