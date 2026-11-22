# Contributing

Thanks for helping build open tools for architects. Additions should raise the floor for every architect, in every country, not widen the surface for its own sake.

## Scope

The architect's whole working week, concept to completion: briefing, site and planning research, drawings and models, BIM/CAD connectors, specification, cost and carbon, coordination, construction administration, winning work, practice management, and the hard conversations.

For deep US- and NYC-specific due diligence, FF&E and EPD workflows, [ALPA's Arch Studio](https://github.com/AlpacaLabsLLC/skills-for-architects) already goes further than we would; we complement it rather than duplicate it.

## The house rules (every skill must hold these)

- **Discipline the model.** Show the basis of any number. Never fabricate a precedent, citation, code clause, product, benchmark, standard, person, or project. Flag what needs verifying.
- **Say it straight.** "Appears consistent with ... (verify)", never "complies". No empty archispeak.
- **Stay in your lane.** No engineering, structural, fire, accessibility, code, or contractual rulings: flag them for a qualified professional.
- **No home country.** If it depends on jurisdiction, ask for it and give examples from more than one. Metric first, imperial supported.
- **Compute, don't estimate.** If a number can come from a file (areas, counts, sheet lists, sun angles), ship a script and show the input.
- **Write safely to live models.** Default to read-only and dry-run first; never write unreviewed to a shared model or board.
- **One skill, one job.** If it does two things, it's two skills.

The canonical text lives in [`rules/`](rules/).

## Adding a skill

1. Create `skills/<name>/SKILL.md`. `<name>` is 1-64 chars of lowercase letters, digits, and single hyphens, and must match the frontmatter `name`.
2. Frontmatter uses only Agent Skills spec keys, so the skill loads everywhere (Claude Code, Codex, Cursor, Copilot, Gemini, and `npx skills`):
   ```yaml
   ---
   name: your-skill
   description: "What it does, then when to use it: lead with trigger phrases (Use when the architect wants ...). Third person, at most 1024 chars. Name sibling skills it hands to. Quote it if it contains a colon."
   license: MIT
   metadata:
     author: Gaia Computer Technologies, Inc.
     version: "1.0.0"
   ---
   ```
3. Follow the shared shape: `When to use` / `Input` / `Process` / `Domain knowledge` / `Output format` / `What you don't do`.
4. **Keep it self-contained.** `npx skills add` installs one skill folder at a time, without `rules/`, `agents/`, or `hooks/`. Never link outside the skill folder. If the skill can assert a regulated fact, put the disclaimer block (from [`rules/professional-disclaimer.md`](rules/professional-disclaimer.md)) inline in its Output format.
5. Keep `SKILL.md` well under 500 lines. Long material goes in `references/`, code in `scripts/`. Scripts carry a PEP 723 header so `uv run scripts/x.py` installs their dependencies, and print their inputs and basis.
6. Volatile tool detail (MCP servers, product versions) goes in a dated `references/tool-notes.md`.
7. Add the skill to the router table in `skills/architect/SKILL.md`, to a group in `skills.sh.json`, and to the README table; bump the `<!-- skill-count:N -->` marker.

## Before you open a PR

```bash
pip install pyyaml
bash scripts/lint.sh
```

The lint parses every frontmatter as strict YAML, enforces the spec's name and description limits and allowed keys, checks that skills are self-contained, that the router, `skills.sh.json`, and README list every skill, and validates the manifests and hooks. CI also runs `shellcheck` and `npx skills add . --list`, which fails if any skill would be skipped.

## Style

Match [`rules/voice.md`](rules/voice.md): direct, specific, architecturally literate, honest about gaps, brief. No emojis.
