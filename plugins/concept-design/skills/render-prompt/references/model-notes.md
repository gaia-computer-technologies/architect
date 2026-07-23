# Model notes (snapshot — verify against current tools)

This file changes fast. It is a **snapshot of tool strengths, not a ranking to trust blindly.** Model names, versions, and capabilities move month to month — sanity-check any recommendation against what the user actually has and what's current. The durable craft (structure, material specificity, light behaviour, consistency techniques) lives in `SKILL.md`; only volatile tool-specific detail lives here.

_Last reviewed: 2026-07. If you are reading this much later, assume it is stale and say so._

## How to match a tool to the job

- **Concept mood / atmosphere, no CAD model yet** → a general text-to-image model. Best for exploring form and vibe; will hallucinate geometry, so don't expect a specific building to hold.
- **Iterating a specific design you've already modelled** → a geometry-locked route: an in-CAD plugin, or a base model driven by ControlNet / a reference image. Condition on your massing or clay render so walls don't move.
- **Editing one design across many views by plain-English instructions** → a multimodal image-editing model that preserves scene identity between edits.
- **Final hero images with real light physics** → not AI. Use a physically based renderer. AI is a concept and design-development aid, not a substitute for production visualisation.

## Prompt-shape quirks that persist across tools

- Comma-separated, telegraphic phrasing; front-load the subject. Polite filler wastes tokens.
- Always set an aspect ratio or proportions distort toward square.
- Some models take an explicit **negative prompt**; others (instruction-following image models) do not — for those, describe what you *want*, not what to exclude.
- Photographic-medium language (film stock, lens, "large-format architectural photograph") often reads as more original than name-dropping a famous architect.

## What not to encode here

Don't hard-code "X is the best model." Encode *what each kind of tool is good at* so the guidance survives the next release. If you name a specific product, date it.
