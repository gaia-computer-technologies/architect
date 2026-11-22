# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf>=1.24"]
# ///
"""
register_qa.py - build a drawing register from a PDF set by reading title blocks,
then check it against the issued register. Flags sheets it cannot read instead
of guessing.

Deps:   pymupdf
Usage:
  uv run register_qa.py SET.pdf [MORE.pdf | folder/] --out register.csv [--register issued.csv]
        [--tb 0.55,0.70,1.0,1.0]          # title-block region as page fractions x0,y0,x1,y1 (default bottom-right)
        [--number-regex "PRJ-[A-Z0-9-]+"] # your office/ISO 19650 sheet-number pattern
        [--md report.md]

Register CSV columns (case-insensitive): number,title,revision,status,date[,scale,size]
Extraction: labelled fields first ("Drawing No", "Rev", "Status", "Date", "Scale",
"Title"...), then patterns. A field the script cannot find is left blank and flagged;
two different candidates for one field are flagged AMBIGUOUS. Sheet size is
measured from the page, not read from text.

Exit codes: 0 clean; 1 refused (bad input); 3 issues found.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import re
import sys
from pathlib import Path

import pymupdf

PT_MM = 25.4 / 72
SIZES = {  # name: (short, long) in mm
    "A0": (841, 1189), "A1": (594, 841), "A2": (420, 594), "A3": (297, 420), "A4": (210, 297),
    "B1": (707, 1000), "B2": (500, 707),
    "ANSI A": (215.9, 279.4), "ANSI B": (279.4, 431.8), "ANSI C": (431.8, 558.8),
    "ANSI D": (558.8, 863.6), "ANSI E": (863.6, 1117.6),
    "ARCH C": (457.2, 609.6), "ARCH D": (609.6, 914.4), "ARCH E": (914.4, 1219.2), "ARCH E1": (762, 1066.8),
}
LABELS = {
    "number": r"(?:drawing|dwg|sheet)\s*(?:no\.?|number|nr\.?|#)",
    "revision": r"(?:rev(?:ision)?\.?)",
    "status": r"(?:status|suitability)",
    "date": r"(?:date)",
    "scale": r"(?:scale)",
    "title": r"(?:drawing\s+title|title)",
}
PATTERNS = {
    "revision": r"\b(?:[PCA]\d{2}(?:\.\d+)?|[A-Z]\d?|\d{1,2})\b",
    "status": r"\b(?:S[0-7]|A[1-9]|B[1-9]|CR|PRELIMINARY|FOR (?:INFORMATION|COMMENT|APPROVAL|PLANNING|TENDER|CONSTRUCTION)|"
              r"ISSUED FOR [A-Z ]+|DRAFT|AS[- ]BUILT|RECORD)\b",
    "date": r"\b(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}-\d{2}-\d{2}|\d{1,2}\s+[A-Za-z]{3,9}\.?\s+\d{4})\b",
    "scale": r"\b(?:1\s*:\s*\d{1,5}(?:\s*@\s*A\d)?|NTS|N\.T\.S\.?|AS SHOWN|\d+/\d+\"?\s*=\s*1'-0\")",
}
DEFAULT_NUMBER = r"\b[A-Z0-9]{2,6}(?:-[A-Z0-9]{1,6}){2,7}\b|\b[A-Z]{1,3}[-_.]?\d{2,4}(?:[-_.]\d{1,4})?\b"


def die(msg: str) -> None:
    print(f"REFUSED: {msg}", file=sys.stderr)
    sys.exit(1)


def sheet_size(page) -> str:
    w, h = page.rect.width * PT_MM, page.rect.height * PT_MM
    s, l = sorted((w, h))
    orient = "landscape" if w > h else "portrait"
    best = min(SIZES.items(), key=lambda kv: abs(kv[1][0] - s) + abs(kv[1][1] - l))
    if abs(best[1][0] - s) + abs(best[1][1] - l) <= 8:
        return f"{best[0]} {orient}"
    return f"non-standard {w:.0f}x{h:.0f} mm"


def labelled(lines: list[str], key: str) -> list[str]:
    """Value on the same line after the label, else the next non-empty line."""
    out = []
    lab = re.compile(rf"^\s*{LABELS[key]}\s*[:.\-]?\s*(.*)$", re.I)
    for i, ln in enumerate(lines):
        m = lab.match(ln)
        if not m:
            continue
        val = m.group(1).strip()
        if not val and i + 1 < len(lines):
            val = lines[i + 1].strip()
        if val and not any(re.match(rf"^\s*{p}\b", val, re.I) for p in LABELS.values()):
            out.append(val)
    return out


def extract(page, tb, number_re) -> dict:
    r = page.rect
    clip = pymupdf.Rect(r.x0 + tb[0] * r.width, r.y0 + tb[1] * r.height, r.x0 + tb[2] * r.width, r.y0 + tb[3] * r.height)
    full = page.get_text("text").strip()
    rec = {"size": sheet_size(page), "flags": []}
    if not full:
        has_img = bool(page.get_images())
        rec["flags"].append("NO TEXT LAYER" + (" (scanned image?)" if has_img else "") + " - needs OCR or manual entry; nothing guessed")
        return rec
    text = page.get_text("text", clip=clip)
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        rec["flags"].append("no text in title-block region - check --tb")
        return rec
    for key in ("number", "title", "revision", "status", "date", "scale"):
        cands = labelled(lines, key)
        if not cands and key == "number":
            cands = re.findall(number_re, text)
        elif not cands and key in PATTERNS:
            cands = [m.group(0) for m in re.finditer(PATTERNS[key], text, re.I)] if key != "revision" else []
        uniq = list(dict.fromkeys(c.strip() for c in cands))
        if key == "number":
            uniq = [u for u in uniq if re.search(number_re, u)] or uniq
        if len(uniq) == 1:
            rec[key] = uniq[0]
        elif len(uniq) > 1:
            rec[key] = uniq[0]
            rec["flags"].append(f"AMBIGUOUS {key}: {uniq[:4]}")
        else:
            rec[key] = ""
            rec["flags"].append(f"{key} not found")
    m = re.search(r"@\s*(A\d)", rec.get("scale", ""), re.I)
    if m and not rec["size"].upper().startswith(m.group(1).upper() + " "):
        rec["flags"].append(f"scale stated at {m.group(1).upper()} but sheet measures {rec['size']}")
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--register")
    ap.add_argument("--tb", default="0.55,0.70,1.0,1.0")
    ap.add_argument("--number-regex", default=DEFAULT_NUMBER)
    ap.add_argument("--md")
    args = ap.parse_args()

    try:
        tb = [float(x) for x in args.tb.split(",")]
        assert len(tb) == 4 and 0 <= tb[0] < tb[2] <= 1 and 0 <= tb[1] < tb[3] <= 1
    except (ValueError, AssertionError):
        die("--tb must be four fractions x0,y0,x1,y1 with x0<x1, y0<y1, all within 0..1")
    try:
        number_re = re.compile(args.number_regex)
    except re.error as e:
        die(f"bad --number-regex: {e}")

    pdfs = []
    for i in args.inputs:
        p = Path(i)
        pdfs += sorted(p.glob("*.pdf")) if p.is_dir() else [p]
    if not pdfs:
        die("no PDFs found")

    found = []
    for pdf in pdfs:
        try:
            doc = pymupdf.open(pdf)
        except Exception as e:
            die(f"cannot open {pdf}: {e}")
        for n, page in enumerate(doc, 1):
            rec = extract(page, tb, number_re)
            rec.update(file=pdf.name, page=n)
            found.append(rec)

    cols = ["file", "page", "number", "title", "revision", "status", "date", "scale", "size", "flags"]
    with open(args.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in found:
            w.writerow({**{c: r.get(c, "") for c in cols}, "flags": "; ".join(r["flags"])})

    out = [f"Read {len(found)} sheet(s) from {len(pdfs)} PDF(s); title-block region {tb} (page fractions).", "",
           "| File | Page | Number | Title | Rev | Status | Date | Scale | Size | Flags |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for r in found:
        out.append("| " + " | ".join(str(r.get(c, "")) for c in cols[:-1]) + " | " + "; ".join(r["flags"]) + " |")
    issues = sum(1 for r in found if r["flags"])

    nums = [r.get("number") for r in found if r.get("number")]
    dups = sorted({n for n in nums if nums.count(n) > 1})
    if dups:
        out.append(f"\nDUPLICATE sheet numbers in the set: {dups}")
        issues += len(dups)

    if args.register:
        with open(args.register, newline="") as fh:
            reg = [{k.strip().lower(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(fh)]
        if not reg or "number" not in reg[0]:
            die("register CSV needs a 'number' column")
        by_num = {r["number"]: r for r in found if r.get("number")}
        out += ["", "| Register number | Field | Register | Title block | Check |", "|---|---|---|---|---|"]
        for row in reg:
            sh = by_num.get(row["number"])
            if not sh:
                out.append(f"| {row['number']} | - | listed | not in set | MISSING FROM SET |"); issues += 1
                continue
            for fld in ("title", "revision", "status", "date", "scale", "size"):
                if not row.get(fld):
                    continue
                a, b = row[fld], sh.get(fld, "")
                if fld == "title":
                    ratio = difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
                    ok = ratio >= 0.9
                    note = f"similarity {ratio:.0%}"
                elif fld == "size":
                    ok = b.lower().startswith(a.lower()); note = ""
                else:
                    ok = a.replace(" ", "").lower() == b.replace(" ", "").lower(); note = ""
                if not ok:
                    issues += 1
                    out.append(f"| {row['number']} | {fld} | {a} | {b or '(not read)'} | MISMATCH {note} |")
        listed = {r["number"] for r in reg}
        for n in sorted(set(by_num) - listed):
            out.append(f"| {n} | - | not listed | in set | NOT IN REGISTER |"); issues += 1

    out.append(f"\nIssues: {issues}. CSV register written to {args.out}.")
    report = "\n".join(out)
    print(report)
    if args.md:
        Path(args.md).write_text(report + "\n")
    sys.exit(3 if issues else 0)


if __name__ == "__main__":
    main()
