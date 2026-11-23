# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is [SemVer](https://semver.org/).

## [Unreleased]

### Added
- `evals/`: an eval suite for the plugin's promises. Script evals run every bundled script on a tiny checked-in fixture and check the expected numbers and refusals (no API key; in CI). `claude plugin eval` cases measure routing (97 trigger prompts across all 45 skills, 16 negatives) and the guardrails (no clause text, cost rate or carbon factor from memory; fabricated appeal flagged; no contractual entitlement; no invented site facts; the disclaimer marker), with and without the plugin. Baseline results are in the README under "How it is measured" and per run in `evals/baseline/`.
- CI job `evals`: script evals, suite structure checks and `claude plugin validate`.

### Fixed
- The disclaimer marker was often dropped from chat replies. Four skills (`client-pushback`, `contract-admin-letter`, `ifc-query`, `rfi`) had it as a bare HTML comment outside a code block. All 18 skills that carry it now keep it in a code block and say to copy it exactly.
- `hooks/hooks.json` quotes `${CLAUDE_PLUGIN_ROOT}`, so the hook runs when the plugin is installed under a path with spaces (reported by `claude plugin validate`).

## [1.0.0] — 2026-11-22

The concept toolkit becomes an assistant for the architect's whole working week, renamed **architect**, and distributable to any agent.

### Renamed
- Repository `gaia-ai-architect` → `architect`. GitHub redirects the old URL; never recreate a repo with the old name.
- Plugin `concept-design` → `architect` (commands are now `/architect:<skill>`); marketplace `gaia-ai-architect` → `gaia` (install with `architect@gaia`). `marketplace.json` carries `renames` so Claude Code can migrate the plugin name. To upgrade: `claude plugin marketplace remove gaia-ai-architect`, then add `gaia-computer-technologies/architect` and install `architect@gaia`.
- Router skill `concept` → `architect` (`/architect` when installed with `npx skills`).

### Changed (layout, for every marketplace)
- The repo root is now the plugin: `.claude-plugin/plugin.json`, `skills/`, `agents/`, `hooks/`, `rules/` at the top level; the marketplace entry uses `source: "./"`. One real `skills/` folder, no symlinks, so the same tree works for the Claude plugin marketplace, the Anthropic plugin directory, `npx skills` / skills.sh, Codex, Cursor and Copilot.
- Every skill is self-contained: no links outside its folder, the disclaimer block inline where needed, because `npx skills` installs one folder at a time.
- Frontmatter follows the Agent Skills spec only (`name`, `description`, `license`, `metadata`).
- Added `skills.sh.json` to group skills on the skills.sh repo page.
- Disclaimer marker is now `<!-- architect:requires-disclaimer -->`; the hook still accepts the old `concept-design:` marker and now also catches €/m² and contract-entitlement language.

### Fixed
- `concept-narrative` and `precedent-study` had descriptions that were not valid YAML (an unquoted `: `), so `npx skills` and strict parsers silently skipped them. Quoted; the lint now parses every frontmatter as strict YAML.
- Removed links to gaia.computer and Gaia Studio, which no longer serve those pages. `render-prompt` now points to ControlNet and in-CAD renderers for geometry-locked renders.
- License holder corrected to Gaia Computer Technologies, Inc.

### Added (11 → 45 skills)
- **Research and regulation:** `planning-research`, `regulation-navigator`, `citation-check`, `site-map` (script), `sun-study` (script).
- **Drawings, models and tools:** `dxf-drawing` (script), `design-diagram` (script), `massing-study` (script), `area-check` (script), `rhino-grasshopper`, `revit-mcp`, `ifc-query` (script), `tool-setup`.
- **Documents and QA:** `drawing-register-qa` (script), `markup-review` (script), `spec-writer`.
- **Cost and carbon:** `cost-check`, `carbon-estimate` (script).
- **Coordination:** `meeting-minutes`, `project-email`, `rfi`.
- **Construction:** `site-visit-report`, `snag-list` (script), `contract-admin-letter`.
- **Winning work and presenting:** `fee-proposal`, `bid-response`, `project-description`, `presentation-deck`.
- **Challenges:** `objection-response`, `value-engineering`, `client-pushback`.
- **Practice and in use:** `practice-pulse` (script), `ai-policy`, `poe-study`.
- **Agent:** `project-architect`, for whole-project and practice work; `concept-architect` keeps the concept arc.
- Scripts carry PEP 723 headers (`uv run` installs dependencies), print their inputs and basis, and refuse bad input rather than guess. Each was run against a fixture before release.

### Infrastructure
- `scripts/check_skills.py`: strict spec checks (YAML, name rules, 1024-char descriptions, allowed keys, string metadata), self-containment, emoji ban, and that the router, `skills.sh.json` and README list every skill.
- CI adds `npx skills add . --list` and fails if any skill would be skipped.

### Docs
- README rebuilt around real output: a hero image and gallery made by the skills' own scripts (`assets/`), mermaid diagrams for what it does, how a skill answers, the project arc, and tool connections, and a linked table of all 45 skills.

## [0.2.0] — 2026-07-23

A structural and content overhaul: make the plugin actually load and install to spec,
then double the toolkit.

### Fixed (it now works as a plugin)
- **Added YAML frontmatter (`name`, `description`) to all skills and the agent.** Without it, skills loaded with empty metadata and never auto-triggered. Skill `name`s are lowercase-hyphenated and match their directory (no `/` — a `/design-brief` name was invalid).
- **Wired up the orchestrating agent.** It lived at repo-root `agents/` (discovered by nothing) and had no frontmatter. Moved into the plugin at `plugins/concept-design/agents/` with frontmatter.
- **Rehabilitated the governance rules.** `professional-disclaimer`, `transparency`, and `voice` were orphaned files that loaded nowhere. They are now folded into the agent and skills, and enforced by an advisory hook.
- **Fixed the marketplace manifest and install command.** `marketplace.json` `name` had spaces (invalid — now `gaia-ai-architect`) and no `owner`; the documented install command didn't match. Skill commands are namespaced `/concept-design:<skill>`.
- **Flattened the plugin layout** from `plugins/00-concept-design/` to `plugins/concept-design/`.

### Added (new skills — 5 → 11)
- `site-context` — supplied site facts → design implications; never invents site data.
- `programme-schedule` — schedule of accommodation with explicit net-to-gross; shows every calculation.
- `concept-parti` — the organising idea, as two or three distinct directions.
- `precedent-study` — verifiable case studies; flags every attribution, fabricates nothing.
- `design-critique` — red-team a scheme against its own stated intent.
- `concept` — a router / menu skill.

### Added (infrastructure)
- `version`, `author`, `homepage`, `repository`, `license`, `keywords` in `plugin.json`; `owner` + `metadata.version` in `marketplace.json`.
- An advisory `PostToolUse` hook (`plugins/concept-design/hooks/`) that reminds when an output asserts a regulated fact without a disclaimer marker. Non-blocking.
- Structural lint (`scripts/lint.sh`) + CI (`.github/workflows/validate.yml`): validates manifests, frontmatter, naming, and the README skill count.
- `CHANGELOG.md`, `CONTRIBUTING.md`.

### Changed (content)
- `render-prompt` — reworked: recommends **Midjourney** (explore/mood) + **Nano Banana** (edit and hold a specific design), maps the style vocabulary to **Gaia Studio presets** ([gaia.computer](https://gaia.computer)), and teaches cross-tool prompting; added cross-view consistency (seed / style reference / ControlNet), a "target real defects" negative-prompt discipline, techniques for masking image-quality problems (inpaint/local-edit to fix; atmosphere / shallow DoF / foreground occlusion / tight crop / night-glow / film grain / upscale to hide), a worked example, and an IP note. Volatile tool detail lives in a dated `references/model-notes.md`.
- `material-palette` — moved the large material-families reference to `references/material-families.md` (progressive disclosure).
- `design-brief` — flagged programme benchmarks as convention-to-verify, not requirements; added phase awareness and hand-offs.
- `concept-narrative` / `space-feel` — sharpened the boundary between them; added an explicit anti-archispeak guardrail.
- `README.md` — corrected install and commands; replaced the unsourced "70% of rework" claim with a defensible statement; documented the governance model.

### Repository
- Renamed `ai-for-architects` → `gaia-ai-architect`.

## [0.1.0]
- Initial release: five concept-phase skills (render-prompt, design-brief, material-palette, concept-narrative, space-feel), one agent, three rules. (Pre-frontmatter; superseded by 0.2.0.)
