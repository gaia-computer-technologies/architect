#!/usr/bin/env bash
# concept-design — advisory disclaimer check (PostToolUse, matcher Write|Edit).
#
# If a just-written .md file asserts REGULATED facts (building code, occupancy,
# fire/thermal ratings, flood/zoning, cost rates, carbon figures) but carries no
# disclaimer marker, print a gentle reminder. This is ADVISORY ONLY: it never
# blocks and always exits 0. To disable, remove this plugin's hooks/hooks.json.
set -u

input="$(cat 2>/dev/null || true)"

# Find the written file path in the hook's JSON payload (jq if present, else grep).
path=""
if command -v jq >/dev/null 2>&1; then
  path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)"
fi
if [ -z "$path" ]; then
  path="$(printf '%s' "$input" \
    | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n1 \
    | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//; s/"$//')"
fi

# Only markdown outputs that exist on disk.
case "$path" in
  *.md) ;;
  *) exit 0 ;;
esac
[ -f "$path" ] || exit 0

# Marker already present → nothing to do.
grep -q 'concept-design:requires-disclaimer' "$path" 2>/dev/null && exit 0

# Does it assert regulated facts? Kept specific to limit false positives.
if grep -Eiq '(building code|complies with|code[- ]compliant|occupancy load|means of egress|fire rating|fire-rated|U-value|flood zone|conservation area|listed building|kgCO2|£/m²|per m²|\$/(sf|ft2))' "$path" 2>/dev/null; then
  {
    echo "concept-design: '$path' names regulated facts (code / occupancy / ratings / cost / carbon) but has no disclaimer marker."
    echo "Consider ending it with the disclaimer block in plugins/concept-design/rules/professional-disclaimer.md,"
    echo "and prefer 'appears consistent with … (verify)' over 'complies'. (Advisory only — nothing was blocked.)"
  } >&2
fi
exit 0
