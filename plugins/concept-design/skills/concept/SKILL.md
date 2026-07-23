---
name: concept
description: Route a concept-phase task to the right skill, and show the toolkit menu. Use when an architect says "help me with a concept", "where do I start", "what can this do", or describes a project without naming a skill. Maps the request to the right concept-design skill (design-brief, site-context, programme-schedule, material-palette, space-feel, concept-parti, concept-narrative, render-prompt, precedent-study, or design-critique) and hands off, or lists the menu.
---

# Concept (router + menu)

The front door to the concept-design toolkit. Point a request at the right skill, or show what's available. For open-ended, multi-step work, prefer the **concept-architect** agent, which runs the whole arc; use this skill for a quick "which one do I want?"

## When to use

- The architect describes a project or task but hasn't named a skill.
- Someone asks "what can this do?" or "where do I start?"
- You need to hand off to a single specific skill.

## How to route

Read the request, name the one or two skills that fit, say why in a line, and hand off. If the work spans several, suggest the sequence (or the agent).

| The architect wants to… | Skill |
|---|---|
| Turn notes / a client meeting into a structured brief | `design-brief` |
| Read a site's opportunities and constraints from its facts | `site-context` |
| Build or check an area schedule / schedule of accommodation | `programme-schedule` |
| Find the organising idea / concept options for a blank page | `concept-parti` |
| Choose a cohesive, specifiable material palette | `material-palette` |
| Describe how a space *feels* (light, threshold, atmosphere) | `space-feel` |
| Write the design rationale / project statement for an audience | `concept-narrative` |
| Craft a prompt for an AI render | `render-prompt` |
| Gather verifiable precedents / case studies | `precedent-study` |
| Pressure-test a scheme before a pin-up | `design-critique` |

## A natural order (adapt — most projects use a subset)

`design-brief` → `site-context` → `programme-schedule` → `concept-parti` → `material-palette` → (`space-feel`) → `concept-narrative` → `render-prompt`, with `precedent-study` feeding in wherever references help and `design-critique` as the checkpoint before presenting.

## The house rules (apply to every skill here)

- Concept phase only — upstream of BIM, code, and specification.
- Never fabricate a precedent, citation, code, benchmark, or number. Flag what needs verifying.
- Show the basis of any figure. Say "appears consistent with," never "complies."
- One strong direction beats five weak ones.

## What you don't do

- Don't do the downstream work yourself — route to the skill, don't reinvent it inline.
- Don't route to more than two skills at once. If it's genuinely multi-step, name the sequence or hand to the agent.
