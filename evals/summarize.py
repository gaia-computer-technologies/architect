# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Summarise `claude plugin eval --json` output into the README tables.

Usage:
  uv run evals/summarize.py ROUTING.json GUARDRAILS.json [--baseline evals/baseline/DATE.json]

ROUTING.json is a run of the trigger and negative cases (--ablation none, --keep-temp).
GUARDRAILS.json is a run of the guardrail cases (default --ablation with-without).
With --keep-temp the run traces are still on disk, and the Skill calls in each one
are recorded, so a missed route shows which skill fired instead. Prints Markdown;
--baseline also writes a compact per-run record (no transcripts) to commit.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def rate(k: int, n: int) -> str:
    lo, hi = wilson(k, n)
    return f"{k}/{n} ({k / n:.0%}, 95% CI {lo:.0%} to {hi:.0%})" if n else "n/a"


def skills_fired(run: dict) -> list[str] | None:
    """Skill names called in this run, in order, read from its trace (None if the trace is gone)."""
    p = run.get("tracePath")
    if not p or not Path(p).exists():
        return None
    out = []
    for line in Path(p).read_text().splitlines():
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = o.get("message") if isinstance(o, dict) else None
        content = msg.get("content") if isinstance(msg, dict) else None
        for c in content if isinstance(content, list) else []:
            if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Skill":
                out.append(str((c.get("input") or {}).get("skill", "")).split(":")[-1])
    return out


def models(d: dict) -> set[str]:
    """Agent models seen in the kept traces (the JSON report does not record them)."""
    seen = set()
    for c in d["cases"]:
        for arm in (c.get("arms") or {}).values():
            for r in arm:
                p = r.get("tracePath")
                if p and Path(p).exists():
                    for line in Path(p).read_text().splitlines():
                        try:
                            msg = json.loads(line).get("message")
                        except (json.JSONDecodeError, AttributeError):
                            continue
                        m = msg.get("model") if isinstance(msg, dict) else None
                        if m:
                            seen.add(m)
    return seen


def runs(case: dict, arm: str = "with") -> list[dict]:
    return (case.get("arms") or {}).get(arm) or []


def grader(run: dict, prefix: str) -> dict | None:
    return next((g for g in run.get("graders", []) if g["name"].startswith(prefix)), None)


def tag_value(case: dict, key: str) -> str | None:
    for t in case.get("tags") or []:
        if t.startswith(key + ":"):
            return t.split(":", 1)[1]
    return None


def load(path: str) -> dict:
    d = json.loads(Path(path).read_text())
    # tags are in the case files, not always in the JSON: read them back.
    root = Path(d["suite"]["root"])
    for c in d["cases"]:
        f = root / c["dir"] / "case.yaml"
        tags = []
        if f.exists():
            lines = f.read_text().splitlines()
            if "tags:" in lines:
                i = lines.index("tags:") + 1
                while i < len(lines) and lines[i].startswith("- "):
                    tags.append(lines[i][2:].strip()); i += 1
        c["tags"] = c.get("tags") or tags
    return d


def routing(d: dict, record: list) -> list[str]:
    out = []
    trig = [c for c in d["cases"] if c["name"].startswith("trigger-")]
    neg = [c for c in d["cases"] if c["name"].startswith("negative-")]
    hits = n = direct = via_router = 0
    per_skill = defaultdict(lambda: [0, 0])
    misses = []
    for c in trig:
        skill = tag_value(c, "skill")
        for r in runs(c):
            n += 1
            ok = bool(r.get("passed"))
            fired = skills_fired(r)
            hits += ok
            per_skill[skill][0] += ok
            per_skill[skill][1] += 1
            if ok and fired:
                if fired[0] == skill:
                    direct += 1
                elif "architect" in fired[:1]:
                    via_router += 1
            if not ok:
                misses.append((c["name"], skill, fired, r.get("error")))
            record.append({"case": c["name"], "kind": "trigger", "expected": skill, "passed": ok,
                           "skills_fired": fired, "error": r.get("error")})
    nb = [c for c in neg if "neighbour" in c["tags"]]
    ns = [c for c in neg if "no-skill" in c["tags"]]

    def count(cs):
        k = m = 0
        for c in cs:
            for r in runs(c):
                m += 1; k += bool(r.get("passed"))
                record.append({"case": c["name"], "kind": "negative", "expected": tag_value(c, "skill"),
                               "passed": bool(r.get("passed")), "skills_fired": skills_fired(r),
                               "graders": {g["name"]: g["passed"] for g in r.get("graders", [])},
                               "error": r.get("error")})
        return k, m

    kb, mb = count(nb)
    ks, ms = count(ns)
    full = sum(1 for s, (k, m) in per_skill.items() if k == m)
    out += ["| Measure | Result |", "|---|---|",
            f"| Trigger: the expected skill fired | {rate(hits, n)} |",
            f"| of which it was the first skill called | {direct} (the rest went through the `architect` router: {via_router}) |",
            f"| Skills that fired on every one of their prompts | {full} of {len(per_skill)} |",
            f"| Neighbour negatives: right skill, and not its neighbour | {rate(kb, mb)} |",
            f"| No-skill negatives: no architect skill fired | {rate(ks, ms)} |", ""]
    if misses:
        out += ["Missed routes:", "", "| Case | Expected | Skills that fired instead |", "|---|---|---|"]
        for name, skill, fired, err in misses:
            f = ", ".join(fired) if fired else ("none" if fired is not None else "(trace not kept)")
            out.append(f"| `{name}` | `{skill}` | {f}{' (run error: ' + str(err) + ')' if err else ''} |")
        out.append("")
    bad = [r for r in record if r["kind"] == "negative" and not r["passed"]]
    if bad:
        out += ["Failed negatives:", "", "| Case | Skills that fired |", "|---|---|"]
        for r in bad:
            out.append(f"| `{r['case']}` | {', '.join(r['skills_fired'] or []) or 'none'} |")
        out.append("")
    return out


def held(run: dict) -> bool:
    """Every behaviour and marker grader passed. The fires-<skill> grader is a routing
    indicator, unscored with the default ablation but scored under --ablation none, so it
    is left out here to keep runs with and without a baseline arm comparable."""
    gs = [g for g in run.get("graders", []) if not g["name"].startswith("fires-")]
    return bool(gs) and all(g.get("passed") for g in gs) and not run.get("error")


def guardrails(d: dict, record: list) -> list[str]:
    out = ["| Guardrail case | With plugin | Without plugin | Skill loaded (with plugin) |", "|---|---|---|---|"]
    tot = defaultdict(lambda: [0, 0, 0, 0])  # with k, with n, without k, without n
    for c in d["cases"]:
        w, wo = runs(c, "with"), runs(c, "without")
        kw = sum(held(r) for r in w)
        kwo = sum(held(r) for r in wo)
        loaded = 0
        for r in w:
            g = grader(r, "fires-")
            loaded += bool(g and g.get("passed"))
            record.append({"case": c["name"], "kind": "guardrail", "arm": "with", "passed": held(r),
                           "graders": {g["name"]: g["passed"] for g in r.get("graders", [])},
                           "skills_fired": skills_fired(r), "error": r.get("error")})
        for r in wo:
            record.append({"case": c["name"], "kind": "guardrail", "arm": "without", "passed": held(r),
                           "graders": {g["name"]: g["passed"] for g in r.get("graders", [])}, "error": r.get("error")})
        group = ("disclaimer marker" if "disclaimer" in c["tags"] else
                 "behaviour, skill named in the prompt" if "invoked" in c["tags"] else "behaviour, natural prompt")
        t = tot[group]
        t[0] += kw; t[1] += len(w); t[2] += kwo; t[3] += len(wo)
        out.append(f"| `{c['name'].removeprefix('guardrail-')}` | {kw}/{len(w)} | "
                   f"{f'{kwo}/{len(wo)}' if wo else 'n/a'} | {loaded}/{len(w)} |")
    out += ["", "| Group | With plugin | Without plugin |", "|---|---|---|"]
    for g, (a, b, c_, e) in tot.items():
        out.append(f"| {g} | {rate(a, b)} | {rate(c_, e) if e else 'n/a'} |")
    return out + [""]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("routing", help="routing JSON, or - to skip")
    ap.add_argument("guardrails")
    ap.add_argument("--baseline")
    a = ap.parse_args()
    gd = load(a.guardrails)
    rd = load(a.routing) if a.routing != "-" else {"cases": [], **{k: gd.get(k) for k in ("claudeVersion", "startedAt")}}
    record: list = []
    lines = (["## Routing", ""] + routing(rd, record) if rd["cases"] else []) + ["## Guardrails", ""] + guardrails(gd, record)
    meta = {k: rd.get(k) for k in ("claudeVersion", "startedAt")}
    meta["models"] = sorted(models(rd) | models(gd))
    cost = (rd.get("costUsd") or 0) + (gd.get("costUsd") or 0)
    lines.append(f"Model {', '.join(meta['models']) or 'unknown'}; Claude Code {meta['claudeVersion']}, "
                 f"run {meta['startedAt'][:10]}, "
                 f"total cost about ${cost:.2f} (list price, as reported by the harness).")
    print("\n".join(lines))
    if a.baseline:
        Path(a.baseline).parent.mkdir(parents=True, exist_ok=True)
        Path(a.baseline).write_text(json.dumps({**meta, "costUsd": round(cost, 2), "runs": record}, indent=1) + "\n")


if __name__ == "__main__":
    main()
