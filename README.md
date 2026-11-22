# Architect

Open-source Agent Skills for the architect's whole working week, from the first client conversation to the post-occupancy survey.

[![skills.sh](https://skills.sh/b/gaia-computer-technologies/architect)](https://skills.sh/gaia-computer-technologies/architect)
[![validate](https://github.com/gaia-computer-technologies/architect/actions/workflows/validate.yml/badge.svg)](https://github.com/gaia-computer-technologies/architect/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-black.svg)](LICENSE)

<!-- skill-count:45 -->
**45 skills. 2 agents. 1 plugin.** Works in Claude Code, Claude Desktop and Cowork, and, through `npx skills`, in Cursor, Codex, GitHub Copilot, Gemini CLI, Windsurf and about 70 other agents.

---

## What this is

An assistant that works the way a good senior colleague does: it writes the brief, reads the site, draws the diagram, checks the drawing set, chases the RFIs, drafts the instruction, prices the option, answers the objection, and tells you plainly what it cannot know.

It is built on one rule, taken from what architects say goes wrong with AI: **discipline the model, don't just prompt it.** Every skill shows the basis of its numbers, refuses to fabricate a precedent, code clause, product, appeal decision or citation, says "appears consistent with ... (verify)" instead of "complies", and names the professional who must check anything regulated. Where a number can be computed from your own file, a script computes it and prints its inputs.

Nothing assumes a home country. Skills ask for your jurisdiction, code edition and contract form and work with RIBA, AIA, HOAI and other stage systems, JCT, NEC, AIA, FIDIC and local forms, NBS, MasterFormat and NATSPEC.

## Install

**Claude Code (plugin, with agents and guardrail hook):**

```bash
claude plugin marketplace add gaia-computer-technologies/architect
claude plugin install architect@gaia
```

Skills then appear as `/architect:<skill>`, and Claude invokes them automatically when a request matches. Start with `/architect:architect` for the menu.

**Any agent (Cursor, Codex, Copilot, Gemini CLI, Windsurf, Claude Code and more):**

```bash
npx skills add gaia-computer-technologies/architect
```

Pick all skills or a few with `--skill <name>`. Installed this way, skills are un-namespaced (`/design-brief`, and `/architect` for the menu); agents and the hook are Claude-plugin features and don't come along.

**Claude Desktop and claude.ai:** Customize → Plugins → add marketplace from GitHub → `gaia-computer-technologies/architect`.

**Upgrading from `concept-design@gaia-ai-architect`:** the plugin is now `architect` in the `gaia` marketplace.

```bash
claude plugin marketplace remove gaia-ai-architect
claude plugin marketplace add gaia-computer-technologies/architect
claude plugin install architect@gaia
```

## The skills

Commands are shown in plugin form. "Script" means the skill ships tested Python that computes the result from your files (`uv run` installs its dependencies). "Flagged" means outputs that state regulated facts end with a verification disclaimer.

### Start here

| Skill | Command | What it does |
|---|---|---|
| Architect | `/architect:architect` | The menu: routes any task to the right skill, suggests a sequence for multi-step work |

### Concept

| Skill | Command | What it does | |
|---|---|---|---|
| Design brief | `/architect:design-brief` | Turns a client conversation or loose notes into a structured brief | |
| Site context | `/architect:site-context` | Turns supplied site facts into design moves; never invents site data | Flagged |
| Programme schedule | `/architect:programme-schedule` | Builds or checks a schedule of accommodation with net-to-gross shown | Flagged |
| Concept parti | `/architect:concept-parti` | Finds the organising idea, as two or three distinct directions | |
| Material palette | `/architect:material-palette` | A cohesive, specifiable 3-5 material palette with ageing and detailing notes | |
| Space feel | `/architect:space-feel` | Describes how a space feels: threshold, compression, light, sound | |
| Concept narrative | `/architect:concept-narrative` | The design argument for a client, jury or planning board | |
| Render prompt | `/architect:render-prompt` | Structured prompts for Midjourney, Nano Banana and ControlNet workflows | |
| Precedent study | `/architect:precedent-study` | Verifiable case studies; flags every attribution, invents nothing | |
| Design critique | `/architect:design-critique` | Red-teams a scheme against its own stated intent before a pin-up | |

### Research and regulation

| Skill | Command | What it does | |
|---|---|---|---|
| Planning research | `/architect:planning-research` | Planning history, designations and policy for a site, each item linked and dated | Flagged |
| Regulation navigator | `/architect:regulation-navigator` | Finds the governing clause by jurisdiction, edition and adoption date; never from memory | Flagged |
| Citation check | `/architect:citation-check` | Checks every reference in a document exists, says what is claimed, and is current | |
| Site map | `/architect:site-map` | Figure-ground and context maps from OpenStreetMap, areas in a projected CRS, optional DXF | Script |
| Sun study | `/architect:sun-study` | Sun path, altitude and azimuth, shadow lengths, EPW climate summary | Script, Flagged |

### Drawings, models and tools

| Skill | Command | What it does | |
|---|---|---|---|
| DXF drawing | `/architect:dxf-drawing` | Real layered, dimensioned DXF that opens in AutoCAD, Rhino or Vectorworks, plus a preview | Script |
| Design diagram | `/architect:design-diagram` | Adjacency and bubble diagrams sized by area, stacking, zoning and circulation, as SVG | Script |
| Massing study | `/architect:massing-study` | Feasibility massing and yield from setbacks, height, coverage and FAR; glTF/OBJ out | Script, Flagged |
| Area check | `/architect:area-check` | Measures areas from DXF polylines, IFC spaces or CSV and checks them against the brief | Script, Flagged |
| Rhino and Grasshopper | `/architect:rhino-grasshopper` | Models and scripts Rhino and Grasshopper via McNeel's RhinoAI or rhinomcp, units checked first | |
| Revit | `/architect:revit-mcp` | Queries schedules, rooms, parameters and warnings via Autodesk's Revit MCP; dry-run before any write | |
| IFC query | `/architect:ifc-query` | Read-only openBIM QA, schedules and quantities with IfcOpenShell; reports schema and query | Script, Flagged |
| Tool setup | `/architect:tool-setup` | Connects the practice's software over MCP, with install steps, risk class and what each unlocks | |

### Documents and QA

| Skill | Command | What it does | |
|---|---|---|---|
| Drawing register QA | `/architect:drawing-register-qa` | Reads title blocks from a PDF set and checks them against the register; flags sheets with no text layer | Script |
| Markup review | `/architect:markup-review` | Collates PDF or Bluebeam markups into a numbered comment-response schedule | Script |
| Spec writer | `/architect:spec-writer` | Outline clauses in NBS, MasterFormat, NATSPEC or your system; product comparisons with sources | Flagged |

### Cost and carbon

| Skill | Command | What it does | |
|---|---|---|---|
| Cost check | `/architect:cost-check` | Order-of-magnitude cost with the rate source, date, location and a low/likely/high range | Flagged |
| Carbon estimate | `/architect:carbon-estimate` | Early A1-A3 embodied carbon; refuses uncited factors, unit mismatches and mixed scopes | Script, Flagged |

### Coordination

| Skill | Command | What it does | |
|---|---|---|---|
| Meeting minutes | `/architect:meeting-minutes` | Transcript or notes into minutes and an owner-and-date action log | |
| Project email | `/architect:project-email` | Drafts and replies in the practice's tone, with a check for accidental commitments | |
| RFI | `/architect:rfi` | Drafts RFIs and responses tied to drawing references, keeps the log, spots hidden variations | Flagged |

### Construction

| Skill | Command | What it does | |
|---|---|---|---|
| Site visit report | `/architect:site-visit-report` | Photos and notes into a dated, numbered report that describes and never certifies | |
| Snag list | `/architect:snag-list` | Snagging / punch list by area and trade, with printable HTML and status tracking | Script |
| Contract admin letter | `/architect:contract-admin-letter` | Instructions, notices, EOT and variation letters against your contract form and clause; flags time-bars | Flagged |

### Winning work and presenting

| Skill | Command | What it does | |
|---|---|---|---|
| Fee proposal | `/architect:fee-proposal` | Scope by stage, deliverables matrix, fee built from hours and rates, cross-checked | Flagged |
| Bid response | `/architect:bid-response` | Answers tenders against their criteria with a compliance matrix; never invents projects | |
| Project description | `/architect:project-description` | Portfolio, award and press copy at 50, 150 and 400 words, from verified facts only | |
| Presentation deck | `/architect:presentation-deck` | Slide-by-slide storyline and board layout for a client, jury or committee | |

### Challenges

| Skill | Command | What it does | |
|---|---|---|---|
| Objection response | `/architect:objection-response` | Groups objections by theme, checks their citations, drafts policy-tied responses | Flagged |
| Value engineering | `/architect:value-engineering` | Weighs VE options on cost, quality, carbon, programme and intent; replies to the QS | Flagged |
| Client pushback | `/architect:client-pushback` | Prepares a hard client conversation: options, consequences, a script, the follow-up email | |

### Practice and in use

| Skill | Command | What it does | |
|---|---|---|---|
| Practice pulse | `/architect:practice-pulse` | Fee burn, earned value, utilisation and forecasts from timesheet exports | Script |
| AI policy | `/architect:ai-policy` | A practice AI-use policy and client disclosure note, with points for your lawyer and insurer | Flagged |
| POE study | `/architect:poe-study` | Post-occupancy survey and interview design, and analysis of what comes back | |

### Agents (Claude Code and Cowork)

- **project-architect**: runs whole-project and practice work, chains skills (an objection goes through `citation-check` before `objection-response`), and stops at anything that needs a qualified professional.
- **concept-architect**: runs the concept arc from vague idea to presentation-ready output, and knows when to stop.

## Connect your tools

Skills work on their own, and get sharper with your software connected over MCP. `/architect:tool-setup` checks what is connected and walks through the rest. As of November 2026:

| Software | Route | Notes |
|---|---|---|
| Rhino / Grasshopper | McNeel RhinoAI (official), or rhinomcp | Official is young; rhinomcp is the most mature |
| Revit | Autodesk Revit Public MCP (Revit 2027.2) | Use the Read server by default; Write is preview |
| Archicad | Archicad 30 MCP (beta), or Tapir MCP | Official needs a Collaborate or Max subscription |
| SketchUp | Trimble SketchUp connector | Needs a Trimble ID |
| IFC / openBIM | IfcOpenShell `ifcmcp` | Run with `--no-execute` |
| Bluebeam | Revu MCP | Revu 21.9+, Max plan |
| Miro, Figma | Official MCP servers | Read-only by default for client boards |
| Maps | Mapbox MCP, Google Maps Grounding Lite | Or OpenStreetMap from code via `site-map` |

No connection? `dxf-drawing`, `ifc-query`, `site-map`, `sun-study`, `area-check` and `massing-study` produce real files from code alone.

## Guardrails, by design

- **Rules** ([`rules/`](rules/)): voice, transparency and professional boundary. Each skill carries its own copy of what it needs, so it stays safe when installed on its own.
- **An advisory hook** ([`hooks/`](hooks/)) notices when a written file asserts a regulated fact (code, occupancy, ratings, cost, carbon, contract entitlement) without the disclaimer marker, and reminds you. It never blocks; remove `hooks/hooks.json` to turn it off.
- **Safe writes**: model connectors default to read-only and show a dry run of affected elements before any edit.

## Community

For deep US and New York City due diligence, FF&E and EPD workflows, see [Arch Studio](https://github.com/AlpacaLabsLLC/skills-for-architects) by [ALPA](https://alpa.llc), whose open work inspired ours. The two are complementary. Architecture needs more open tools.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Run `bash scripts/lint.sh` before opening a PR; CI runs it, `shellcheck`, and `npx skills add . --list` on every push.

## License

MIT, Gaia Computer Technologies, Inc. See [LICENSE](LICENSE).
