"""Static checks on the LLM eval suite itself (no API key, no model calls).

Keeps the suite honest as skills are added: every skill must have trigger
prompts, case names must be unique, and every case must load in the
`claude plugin eval` case.yaml 1.1 format.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
EVALS = ROOT / "evals"
SKILLS = sorted(p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md"))
CASES = sorted(EVALS.glob("**/case.yaml"))
GRADERS = {"regex", "tool_used", "tool_order", "file_exists", "llm", "baseline"}


def load(p: Path) -> dict:
    return yaml.safe_load(p.read_text())


def test_suite_has_cases():
    assert len(CASES) >= 100


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.parent.name)
def test_case_shape(path):
    c = load(path)
    assert c["schema_version"] == "1.1"
    assert c["name"] and c["execution"]["prompt"].strip()
    assert c["graders"], "every case needs at least one grader"
    for g in c["graders"]:
        assert g["type"] in GRADERS, g
        if g["type"] == "regex":
            re.compile(g["pattern"])
        if g["type"] == "tool_used" and g.get("input_match"):
            re.compile(g["input_match"])
    # Cases stay read-only: no Bash/Write, so they run without a shell sandbox.
    assert set(c["execution"]["allowed_tools"]) <= {"Read", "Glob", "Grep", "Skill"}


def test_case_names_unique():
    dupes = [n for n, k in Counter(load(p)["name"] for p in CASES).items() if k > 1]
    assert not dupes


@pytest.mark.parametrize("skill", SKILLS)
def test_every_skill_has_trigger_prompts(skill):
    cases = list((EVALS / "triggers" / skill).glob("*/case.yaml"))
    assert len(cases) >= 2, f"add at least two trigger prompts for {skill} under evals/triggers/{skill}/"
    for p in cases:
        g = load(p)["graders"][0]
        assert g["type"] == "tool_used" and g["tool"] == "Skill"
        assert re.search(g["input_match"], f'{{"skill": "architect:{skill}"}}')


def test_negatives_cover_neighbours_and_no_skill():
    tags = [t for p in (EVALS / "negatives").glob("*/case.yaml") for t in load(p)["tags"]]
    assert tags.count("neighbour") >= 10 and tags.count("no-skill") >= 3


@pytest.mark.parametrize("skill", ["regulation-navigator", "citation-check", "cost-check",
                                   "contract-admin-letter", "site-context", "carbon-estimate"])
def test_guardrail_per_promise(skill):
    tagged = [load(p) for p in (EVALS / "guardrails").glob("*/case.yaml")]
    mine = [c for c in tagged if f"skill:{skill}" in c["tags"]]
    assert any("natural" in c["tags"] for c in mine), f"no natural-prompt guardrail for {skill}"
