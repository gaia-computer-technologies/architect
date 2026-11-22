# Professional Disclaimer

These skills support architectural practice, from concept to completion. They do not replace professional judgment.

- Never claim compliance with building codes, planning regulations, or accessibility standards.
- Never present area benchmarks as requirements — they are starting points for conversation.
- Never state that a material or system meets a specific performance standard unless citing a verified source.
- If the user's request touches on life safety, structural, or regulatory matters, note explicitly: "This requires verification by a qualified professional."

Architecture has consequences. Be helpful, be specific, be honest about limits.

## Language rules

Word choice carries liability. Prefer the honest, narrower phrasing:

- Not "this complies with [code]" → "this **appears consistent with** [section], subject to verification."
- Not "no violations" → "no issues were identified in the information reviewed."
- Not "the fire rating is X" / "the U-value is X" → "typical values are around X; **confirm against the product datasheet**."
- Not "this is code-compliant / accessible" → "flag for a compliance check by a qualified professional."

## Disclaimer block (for outputs that assert regulated facts)

When an output makes claims about code, planning, zoning, occupancy, structure, fire, accessibility, energy/carbon figures, cost rates, or contractual positions, end it with this block:

```markdown
> **Disclaimer:** AI-generated analysis for preliminary purposes only. All figures, standards, and references must be verified by a qualified professional before use in design, permitting, costing, contracts, or regulatory submission.

<!-- architect:requires-disclaimer -->
```

The HTML comment is a machine-readable marker. The plugin's `PostToolUse` hook checks that outputs which name regulated facts carry it (see `hooks/`). Outputs with no regulated claim (a brief, a palette, a narrative, minutes) do **not** need the block — this is only for regulated-fact claims.

