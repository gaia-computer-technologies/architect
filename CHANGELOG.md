# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is [SemVer](https://semver.org/).

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
