#!/usr/bin/env bash
# Structural lint for the gaia-ai-architect marketplace.
# Validates manifests, skill/agent frontmatter, naming, and doc/skill count.
# Run: bash scripts/lint.sh   (requires: bash, jq)
set -euo pipefail
cd "$(dirname "$0")/.."

fail=0
err() { printf 'FAIL: %s\n' "$*" >&2; fail=1; }
ok()  { printf 'ok:   %s\n' "$*"; }

command -v jq >/dev/null 2>&1 || { echo "jq is required" >&2; exit 2; }

# --- 1. JSON manifests parse -------------------------------------------------
for f in .claude-plugin/marketplace.json plugins/*/.claude-plugin/plugin.json; do
  if jq -e . "$f" >/dev/null 2>&1; then ok "valid JSON: $f"; else err "invalid JSON: $f"; fi
done

# --- 2. marketplace: kebab-case name + owner.name + plugin sources exist ------
mname="$(jq -r '.name // empty' .claude-plugin/marketplace.json)"
case "$mname" in
  ""|*[!a-z0-9-]*) err "marketplace name not kebab-case: '$mname'" ;;
  *) ok "marketplace name: $mname" ;;
esac
[ -n "$(jq -r '.owner.name // empty' .claude-plugin/marketplace.json)" ] \
  || err "marketplace missing owner.name"
while IFS= read -r src; do
  [ -d "$src" ] || err "plugin source path missing: $src"
done < <(jq -r '.plugins[].source' .claude-plugin/marketplace.json)

# --- 3. plugin.json: required fields -----------------------------------------
for pj in plugins/*/.claude-plugin/plugin.json; do
  for key in name version description; do
    [ -n "$(jq -r ".$key // empty" "$pj")" ] || err "$pj missing '$key'"
  done
  [ -n "$(jq -r '.author.name // empty' "$pj")" ] || err "$pj missing author.name"
done

# --- 4. every SKILL.md: frontmatter with name+description; name == dir --------
skill_count=0
while IFS= read -r skill; do
  skill_count=$((skill_count + 1))
  dir="$(basename "$(dirname "$skill")")"
  if [ "$(head -n1 "$skill")" != "---" ]; then err "no YAML frontmatter: $skill"; continue; fi
  fm="$(awk 'NR>1 && $0=="---"{exit} NR>1{print}' "$skill")"
  printf '%s\n' "$fm" | grep -Eq '^name:[[:space:]]*[a-z0-9-]+[[:space:]]*$' || err "bad/missing name: $skill"
  printf '%s\n' "$fm" | grep -q '^description:[[:space:]]*.' || err "missing description: $skill"
  nm="$(printf '%s\n' "$fm" | sed -n 's/^name:[[:space:]]*//p' | head -n1 | tr -d '[:space:]')"
  if [ "$nm" = "$dir" ]; then ok "skill: $nm"; else err "name '$nm' != directory '$dir' ($skill)"; fi
done < <(find plugins -path '*/skills/*/SKILL.md' | sort)

# --- 5. agents: frontmatter with name+description ----------------------------
while IFS= read -r ag; do
  if [ "$(head -n1 "$ag")" != "---" ]; then err "no frontmatter: $ag"; continue; fi
  fm="$(awk 'NR>1 && $0=="---"{exit} NR>1{print}' "$ag")"
  printf '%s\n' "$fm" | grep -q '^name:' || err "agent missing name: $ag"
  printf '%s\n' "$fm" | grep -q '^description:' || err "agent missing description: $ag"
  ok "agent: $(basename "$ag" .md)"
done < <(find plugins -path '*/agents/*.md' | sort)

# --- 6. README skill-count marker matches reality ----------------------------
if grep -q 'skill-count:' README.md; then
  claimed="$(sed -n 's/.*skill-count:\([0-9][0-9]*\).*/\1/p' README.md | head -n1)"
  if [ "$claimed" = "$skill_count" ]; then ok "README skill-count: $claimed"
  else err "README says skill-count:$claimed but found $skill_count SKILL.md files"; fi
else
  echo "note: add '<!-- skill-count:$skill_count -->' to README.md to lock the count"
fi

# --- 7. hook scripts are executable -----------------------------------------
while IFS= read -r sh; do
  [ -x "$sh" ] || err "hook script not executable (chmod +x): $sh"
done < <(find plugins -path '*/hooks/*.sh' 2>/dev/null || true)

echo "---"
if [ "$fail" -eq 0 ]; then echo "All checks passed ($skill_count skills)."; else echo "Lint failed."; exit 1; fi
