# Model notes (snapshot — verify against current tools)

Tool-specific detail that dates fast. The durable craft (structure, material specificity, light behaviour, consistency) lives in `SKILL.md`; only volatile per-tool detail lives here. Sanity-check any recommendation against what the architect actually has and what's current.

_Last reviewed: 2026-07. If you are reading this much later, assume it is stale and say so._

## Recommended: Midjourney + Nano Banana

For concept-phase work these two cover most needs. Use them together.

### Midjourney — explore and find the image
- Best for concept mood, atmosphere, and form-finding when there's no model yet. Strongest aesthetic of the general models.
- Weakness: keeps no 3D model between generations, so it hallucinates geometry — ask for five floors and you may get seven. A moodboard tool, not a way to iterate a *specific* building.
- Prompt shape: comma-separated, front-load the subject. `--ar 16:9` (or 3:2, 4:5) — always set it. `--style raw` for a photographic, less-stylised look. `--seed N` to hold a composition while you change materials or light. `--sref <image>` to carry a palette/atmosphere across images; `--sw` tunes its strength.

### Nano Banana (Google Gemini image) — hold and edit a specific design
- Best for editing one design in plain English ("change the roof to standing-seam zinc," "dusk, warm interior light") while keeping *the same building* across views — the consistency Midjourney can't give.
- Reads a floor plan, elevation, or massing as a real instruction rather than an abstract shape, so it's strong for turning a drawing into an image and iterating it.
- Fast and cheap; best-in-class edit consistency. Not a substitute for physically based lighting on a final hero image — for that, use a real renderer.
- No `--flags`: it's instruction-following. Describe what you *want*; don't write a negative prompt.

**Workflow: Midjourney to find the image → Nano Banana to hold it and edit materials/light/time-of-day across views.**

## Other tools worth knowing

- **Stable Diffusion + ControlNet** — the only route with true geometry lock. Condition on a depth map / canny edges / MLSD lines / scribble from a model screenshot or clay render, then restyle materials without moving walls. Most control, steepest learning curve; usually run via ComfyUI. Reach for it when the *design must be preserved* and you're not in Gaia Studio.
- **Real-time sketch tools** (e.g. Krea-style canvases) — drop a massing sketch as a composition reference and iterate materials in near real time; good for a fast pin-up. Curate a board of the practice's own work as a style profile so outputs stay in one visual language.
- **In-CAD render plugins** (e.g. Veras, D5-style) — run inside Revit / SketchUp / Rhino and use the actual model geometry as the substrate, so results stay consistent through design development. The production-render path once the concept is set.
- **Upscalers** (e.g. Magnific-style) — a finishing step: raise resolution and invent plausible micro-detail for presentation-grade output. Not a concept tool.

## Gaia Studio — geometry-preserving, preset-driven

[Gaia Studio](https://gaia.computer) renders on the architect's *own* photo or model, so geometry is preserved — staging, redesign, before/after. Its **presets** map onto this skill's style vocabulary (Japandi, Warm Minimalism, Brutalist, Scandinavian Modern, Mediterranean Modern, Mid-Century): choose the preset that matches the specified palette, and the render prompt becomes the direction on top. Use Midjourney/Nano Banana to explore an idea; use Gaia Studio presets when the render must stay true to a real space.

## Prompt-shape quirks that persist across tools

- Comma-separated, telegraphic phrasing; front-load the subject. Polite filler wastes tokens.
- Always set an aspect ratio or proportions distort toward square.
- Some models take an explicit **negative prompt** (Midjourney, Stable Diffusion); instruction-following image models (Nano Banana, DALL·E-style) do not — for those, describe what you *want*, not what to exclude.
- Physical contradictions confuse every model: "thick fog" + "sharp sun shadows" won't both render. Keep the lighting logically consistent.
- Photographic-medium language (film stock, lens, "large-format architectural photograph") often reads as more original than name-dropping a famous architect.

## Keeping this current

Named products here (Midjourney, Nano Banana, and the rest) are a 2026-07 recommendation, not a permanent one — when you name a specific product or version, date it, and re-check it before relying on it. What's durable is the *job → kind-of-tool* mapping, not the brand.
