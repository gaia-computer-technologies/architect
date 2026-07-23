# Contributing

Thanks for helping build open concept-phase tools for architects. This repo is small and opinionated on purpose — additions should raise the floor, not widen the surface.

## Scope

Concept phase only — RIBA Stage 0–2 / AIA Pre-Design to Schematic Design, upstream of BIM, code, and specification. Downstream work (zoning, specs, EPDs, procurement, construction docs) is well covered by [ALPA's Architecture Studio](https://github.com/AlpacaLabsLLC/skills-for-architects); we complement it, we don't duplicate it.

## The house rules (every skill must hold these)

- **Discipline the model.** Show the basis of any number. Never fabricate a precedent, citation, code, benchmark, or standard. Flag what needs verifying.
- **Say it straight.** "Appears consistent with … (verify)," never "complies." No empty archispeak.
- **Stay in your lane.** No engineering, structural, fire, accessibility, or code rulings — flag them for a qualified professional.
- **One skill, one job.** If it does two things, it's two skills.

These are codified in [`plugins/concept-design/rules/`](plugins/concept-design/rules/).

## Adding a skill

1. Create `plugins/concept-design/skills/<name>/SKILL.md`. `<name>` is lowercase-hyphenated and must match the frontmatter `name`.
2. Start with YAML frontmatter — this is required, and the `description` is what makes the skill auto-trigger:
   ```yaml
   ---
   name: your-skill
   description: What it does, and WHEN to use it. Lead with trigger phrases ("Use when the architect wants …"). Third person, ≤1024 chars. Cross-reference sibling skills by name.
   ---
   ```
3. Follow the shared shape: `When to use` · `Input` · `Process` · `Domain knowledge` · `Output format` · `What you don't do`.
4. Keep the body tight (aim well under 500 lines). Move long reference material to a `references/` folder in the skill and link it — it loads on demand.
5. If the skill can assert regulated facts, have it emit the disclaimer block from `rules/professional-disclaimer.md`.
6. Update the README table and the `<!-- skill-count:N -->` marker.

## Before you open a PR

```bash
bash scripts/lint.sh
```

It validates the manifests (JSON, kebab-case marketplace name, `owner`), every skill's frontmatter and name↔directory match, agent frontmatter, the README skill count, and that hook scripts are executable. CI (`.github/workflows/validate.yml`) runs the same lint plus `shellcheck` on every push and PR.

## Style

Match the voice in [`rules/voice.md`](plugins/concept-design/rules/voice.md): direct, specific, architecturally literate, honest about gaps, brief. No emojis.
