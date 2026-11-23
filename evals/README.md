# Evals

How the plugin's promises are measured. The results are in the main
[README](../README.md#how-it-is-measured); the per-run record behind them is in
[`baseline/`](baseline/).

| Suite | What it checks | Cases | Needs |
|---|---|---|---|
| [`scripts/`](scripts/) | Every `skills/*/scripts/*.py` runs on a tiny fixture and prints the expected numbers, or refuses (non-zero exit) when the input breaks a house rule. Also the disclaimer hook and the suite's own structure. | 36 script tests, 184 structure checks | `uv`. No API key. Runs in CI. |
| [`triggers/`](triggers/) | Each of the 45 skills fires on 2 or 3 realistic architect requests. | 97 | `claude` + an API key |
| [`negatives/`](negatives/) | The neighbouring skill does not steal the request (12), and no architect skill fires on unrelated requests (4). | 16 | `claude` + an API key |
| [`guardrails/`](guardrails/) | The house rules hold: no clause text or cost rate from memory, fabricated appeal flagged, no contractual entitlement, no invented site facts, no uncited carbon factor, and the disclaimer marker on liability outputs. | 17 | `claude` + an API key |

## Run the free part

```bash
uv run --with pytest --with pyyaml pytest evals/scripts -q
```

The live OpenStreetMap test is skipped by default; add `ARCHITECT_EVAL_NETWORK=1` to run it.
`claude plugin validate .` checks the manifests and hooks, also without a key.

## Run the LLM part

The trigger, negative and guardrail cases use
[`claude plugin eval`](https://code.claude.com/docs/en/plugin-evals.md). Each run is a
real model call on your own credential. The baseline cost about the figure shown in the
README.

```bash
# Routing: which skill fires (one run per prompt, no baseline arm)
claude plugin eval . --trust-plugin --ablation none --no-publish --keep-temp \
  --model claude-sonnet-5-5 --judge-model claude-haiku-5-5 -j 4 \
  --tag trigger negative --json routing.json

# Guardrails: three runs each, with and without the plugin
claude plugin eval . --trust-plugin --no-publish --keep-temp \
  --model claude-sonnet-5-5 --judge-model claude-haiku-5-5 -j 4 \
  --tag guardrail --json guardrails.json

# Tables for the README, plus a compact per-run record to commit
uv run evals/summarize.py routing.json guardrails.json --baseline evals/baseline/$(date +%F).json
```

`--keep-temp` keeps each run's trace, so `summarize.py` can say which skill fired when the
expected one did not. Delete the kept `e-*` directories in your temp folder afterwards.
Only pass `--trust-plugin` for a checkout you would run yourself: the plugin's hook runs
during the evals.

## How the cases are graded

- **Trigger:** a `tool_used` grader passes when Claude calls the `Skill` tool with
  `architect:<skill>`, either first or after the `architect` router.
- **Negatives:** the right skill fires and its neighbour does not (`min: 0, max: 0`), or no
  architect skill fires at all.
- **Guardrails:** an LLM judge (three votes, two must pass) reads the final reply against a
  written PASS/FAIL rubric in the case file. The disclaimer cases use a regex for
  `<!-- architect:requires-disclaimer -->`. Behaviour guardrails run twice: once with a
  natural prompt (end to end, so a skill that never loads counts as a failure) and once
  with the skill named in the prompt (does the skill's own rule hold once loaded). Each
  guardrail case also runs without the plugin, to show what the plugin adds.

## Adding a case

Copy a case folder, change `name` (unique) and `execution.prompt`, and keep
`allowed_tools` read-only. A new skill needs at least two folders under
`triggers/<skill>/`; `scripts/test_suite.py` fails until it has them. A new script needs a
fixture under `scripts/fixtures/<skill>/` and a test in `scripts/test_scripts.py`. Binary
fixtures (IFC, PDF, GeoJSON) are regenerated with `uv run evals/scripts/make_fixtures.py`.
