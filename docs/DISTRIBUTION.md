# Distribution

Where Architect is listed, how each listing happens, and the copy to paste. Checked November 2026; venues change, so re-check a venue's rules before submitting.

## Status

| Venue | How it lists | Effort | Status |
|---|---|---|---|
| Claude plugin marketplace (this repo) | `claude plugin marketplace add gaia-computer-technologies/architect` | none | Live once `main` has v1.0 |
| skills.sh | Automatic, from install telemetry when someone runs `npx skills add gaia-computer-technologies/architect`. `skills.sh.json` groups the page | none | Appears after the first counted install |
| Anthropic plugin directory | Form at claude.ai/directory/manage (paid plan). Automated validation, a security scan, then human review. Listed plugins appear in Claude Code, Claude Desktop, claude.ai and Cowork | low | Not submitted: needs the icon first |
| claudemarketplaces.com | Crawled, or submit at its /submit page with GitHub sign-in | low | Not submitted |
| ComposioHQ/awesome-claude-skills (80k stars) | Pull request, one line under "Productivity & Organization" | low | Not submitted |
| hesreallyhim/awesome-claude-code (58k stars) | Web issue form only, one recommendation at a time; repo must be 14+ days old with ongoing commits, or 100+ stars | low | Eligible (repo created 2026-04; keep commits ongoing) |
| travisvn/awesome-claude-skills (16k stars) | Pull request; requires "social proof" (stars) | low | Wait for stars |
| VoltAgent/awesome-agent-skills (37k stars) | Pull request; "brand new skills are not accepted" | low | Wait |
| Codex, Cursor, Copilot | All read `npx skills` installs today. Their own plugin marketplaces need separate manifests (`.codex-plugin/`, `.cursor-plugin/`); Codex excludes plugins with lifecycle hooks | medium | Not planned yet |
| Gemini CLI extensions | `gemini-extension.json` plus the `gemini-cli-extension` topic. Gemini also reads `hooks/hooks.json` with its own schema, so the Claude hook must move first | medium | Skipped on purpose |

## Before the Anthropic directory submission

- [ ] Add a square PNG icon at `.claude-plugin/icon.png`, 512 to 2048 px, under 2 MB (no SVG or WebP). **The directory takes the icon once, at first submission; changing it later does not change the listing.**
- [ ] `claude plugin validate .` passes with no warnings (today the only warning is the missing icon).
- [ ] README of 40+ words and LICENSE at the plugin root (done), no symlinks or `.DS_Store` (lint enforces).
- [ ] Name check: a name made only of generic words is "held for a reviewer", and a name another organisation uses is blocked. If `architect` is refused, keep `displayName: "Architect"` and change `name` (note that the slash namespace follows `name`).

## Copy to paste

**Name:** `architect` · **Display name:** Architect · **Category:** architecture (or productivity) · **Repository:** https://github.com/gaia-computer-technologies/architect · **License:** MIT

**One line (under 100 characters):**
> Agent Skills for the architect's working week, concept to completion. Every number shows its basis.

**Short description:**
> 45 skills for the work architects do every week: briefs, planning research, code navigation, DXF drawings and diagrams, Rhino, Revit and IFC connectors, specifications, cost and carbon checks, minutes, RFIs, site reports, contract letters, bids and fee proposals. Every skill shows the basis of its numbers, never fabricates a precedent or code clause, and names the professional who must verify anything regulated.

**Awesome-list line (ComposioHQ format):**
```markdown
- [architect](https://github.com/gaia-computer-technologies/architect) - 45 skills for architects' day-to-day work: planning research, code navigation, DXF drawings and site maps from code, Rhino/Revit/IFC connectors, specs, cost and carbon, RFIs, site reports and fee proposals. Shows the basis of every number and never fabricates a citation.
```

**awesome-claude-code issue form:** use the one-line and short descriptions above; link the README and `skills/architect/SKILL.md`.

## After each release

- Bump `version` in `.claude-plugin/plugin.json` and `metadata.version` in `.claude-plugin/marketplace.json` together (lint checks they match), and add a CHANGELOG entry.
- The directory re-runs validation and the security scan on every new version.
- Re-check the dated `references/tool-notes.md` files; MCP servers change monthly.
