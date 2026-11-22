#!/usr/bin/env python3
"""Strict Agent Skills checks for every skills/<name>/SKILL.md.

Enforces the agentskills.io spec (so `npx skills`, skills-ref, Claude Code,
Codex, Cursor and Copilot all load every skill) plus this repo's house rules.
Requires: python3, pyyaml.   Run: python3 scripts/check_skills.py
"""
import json, os, re, sys
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
fails = []

def fail(msg):
    fails.append(msg)
    print("FAIL:", msg)

skills_dir = os.path.join(ROOT, "skills")
names = sorted(d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d)))

for n in names:
    d = os.path.join(skills_dir, n)
    p = os.path.join(d, "SKILL.md")
    if os.path.islink(d):
        fail(f"{n}: skill dir is a symlink (skipped by npx skills, blocked by the directory)")
    if not os.path.isfile(p):
        fail(f"{n}: missing SKILL.md"); continue
    text = open(p, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        fail(f"{n}: no YAML frontmatter"); continue
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        fail(f"{n}: frontmatter is not valid YAML ({str(e).splitlines()[0]}) -- quote the description"); continue
    if not isinstance(fm, dict):
        fail(f"{n}: frontmatter is not a mapping"); continue
    extra = set(fm) - ALLOWED
    if extra:
        fail(f"{n}: non-spec frontmatter keys {sorted(extra)}")
    name = fm.get("name")
    if name != n:
        fail(f"{n}: name '{name}' must equal directory '{n}'")
    if not isinstance(name, str) or not NAME_RE.match(name or "") or len(name) > 64:
        fail(f"{n}: name must be 1-64 chars of a-z0-9 and single hyphens")
    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        fail(f"{n}: description missing")
    elif len(desc) > 1024:
        fail(f"{n}: description is {len(desc)} chars (max 1024)")
    meta = fm.get("metadata", {})
    if not isinstance(meta, dict) or not all(isinstance(v, str) for v in meta.values()):
        fail(f"{n}: metadata must be a string-to-string map (quote versions)")
    lines = text.count("\n")
    if lines > 500:
        fail(f"{n}: SKILL.md is {lines} lines (spec recommends < 500)")
    # Self-contained: skills are installed one folder at a time.
    for root, _, files in os.walk(d):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.islink(fp):
                fail(f"{n}: symlinked file {os.path.relpath(fp, ROOT)}")
            if f.endswith(".md"):
                body = open(fp, encoding="utf-8").read()
                if re.search(r"\]\(\.\./|`\.\./rules", body):
                    fail(f"{n}: {os.path.relpath(fp, ROOT)} links outside its skill folder")
            if f == ".DS_Store":
                fail(f"{n}: .DS_Store committed")
    # Liability marker spelled right where used.
    if "requires-disclaimer" in text and "<!-- architect:requires-disclaimer -->" not in text:
        fail(f"{n}: disclaimer marker must be '<!-- architect:requires-disclaimer -->'")
    # No emojis.
    if re.search(r"[\U0001F300-\U0001FAFF☀-➿]", text):
        fail(f"{n}: contains emoji")
    print(f"ok:   skill {n}")

# Router lists every skill; skills.sh.json groups every skill exactly once.
router = open(os.path.join(skills_dir, "architect", "SKILL.md"), encoding="utf-8").read()
for n in names:
    if n != "architect" and f"`{n}`" not in router:
        fail(f"router skills/architect/SKILL.md does not list `{n}`")
cfg = json.load(open(os.path.join(ROOT, "skills.sh.json")))
grouped = [s for g in cfg["groupings"] for s in g["skills"]]
for n in names:
    if grouped.count(n) != 1:
        fail(f"skills.sh.json groups '{n}' {grouped.count(n)} times (want 1)")
for s in set(grouped) - set(names):
    fail(f"skills.sh.json names unknown skill '{s}'")

print("---")
print(f"{len(names)} skills checked, {len(fails)} problem(s).")
sys.exit(1 if fails else 0)
