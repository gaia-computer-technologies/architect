#!/usr/bin/env bash
# Structural lint for the architect plugin (repo root = plugin root).
# Validates manifests, agents, hooks, README count, and runs the strict
# Agent Skills checks in scripts/check_skills.py.
# Run: bash scripts/lint.sh   (requires: bash, jq, python3 + pyyaml)
set -euo pipefail
cd "$(dirname "$0")/.."

fail=0
err() { printf 'FAIL: %s\n' "$*" >&2; fail=1; }
ok()  { printf 'ok:   %s\n' "$*"; }

command -v jq >/dev/null 2>&1 || { echo "jq is required" >&2; exit 2; }

# --- 1. JSON manifests parse -------------------------------------------------
for f in .claude-plugin/marketplace.json .claude-plugin/plugin.json skills.sh.json; do
  if jq -e . "$f" >/dev/null 2>&1; then ok "valid JSON: $f"; else err "invalid JSON: $f"; fi
done

# --- 2. marketplace: kebab-case name, owner, plugin sources exist -----------
mname="$(jq -r '.name // empty' .claude-plugin/marketplace.json)"
case "$mname" in
  ""|*[!a-z0-9-]*) err "marketplace name not kebab-case: '$mname'" ;;
  *) ok "marketplace name: $mname" ;;
esac
[ -n "$(jq -r '.owner.name // empty' .claude-plugin/marketplace.json)" ] \
  || err "marketplace missing owner.name"
while IFS= read -r src; do
  case "$src" in ./*) ;; *) err "plugin source must start with ./ : $src" ;; esac
  [ -d "$src" ] || err "plugin source path missing: $src"
done < <(jq -r '.plugins[].source' .claude-plugin/marketplace.json)

# --- 3. plugin.json: required fields; name matches marketplace entry --------
pj=.claude-plugin/plugin.json
for key in name version description license; do
  [ -n "$(jq -r ".$key // empty" "$pj")" ] || err "$pj missing '$key'"
done
[ -n "$(jq -r '.author.name // empty' "$pj")" ] || err "$pj missing author.name"
[ "$(jq -r .name "$pj")" = "$(jq -r '.plugins[0].name' .claude-plugin/marketplace.json)" ] \
  || err "plugin.json name differs from marketplace entry name"
[ "$(jq -r .version "$pj")" = "$(jq -r '.metadata.version' .claude-plugin/marketplace.json)" ] \
  || err "plugin.json version differs from marketplace metadata.version"
ok "plugin: $(jq -r .name "$pj") $(jq -r .version "$pj")"

# --- 4. skills (strict spec + house rules) -----------------------------------
python3 scripts/check_skills.py || fail=1
skill_count="$(find skills -mindepth 2 -maxdepth 2 -name SKILL.md | wc -l | tr -d ' ')"

# --- 5. agents: frontmatter with name+description ----------------------------
while IFS= read -r ag; do
  if [ "$(head -n1 "$ag")" != "---" ]; then err "no frontmatter: $ag"; continue; fi
  fm="$(awk 'NR>1 && $0=="---"{exit} NR>1{print}' "$ag")"
  printf '%s\n' "$fm" | grep -q '^name:' || err "agent missing name: $ag"
  printf '%s\n' "$fm" | grep -q '^description:' || err "agent missing description: $ag"
  ok "agent: $(basename "$ag" .md)"
done < <(find agents -name '*.md' | sort)

# --- 6. README skill-count marker matches reality ----------------------------
claimed="$(sed -n 's/.*skill-count:\([0-9][0-9]*\).*/\1/p' README.md | head -n1)"
if [ "$claimed" = "$skill_count" ]; then ok "README skill-count: $claimed"
else err "README says skill-count:$claimed but found $skill_count skills"; fi
for d in skills/*/; do
  n="$(basename "$d")"
  grep -q "\`$n\`\|/architect:$n" README.md || err "README does not mention skill '$n'"
done

# --- 7. hooks executable; no stray symlinks or .DS_Store ---------------------
while IFS= read -r sh; do
  [ -x "$sh" ] || err "hook script not executable (chmod +x): $sh"
done < <(find hooks -name '*.sh')
if [ -n "$(find . -path ./.git -prune -o -type l -print)" ]; then err "symlinks present (blocked by the plugin directory)"; fi
if [ -n "$(find . -name .DS_Store -not -path './.git/*')" ]; then err ".DS_Store present"; fi

echo "---"
if [ "$fail" -eq 0 ]; then echo "All checks passed ($skill_count skills)."; else echo "Lint failed."; exit 1; fi
