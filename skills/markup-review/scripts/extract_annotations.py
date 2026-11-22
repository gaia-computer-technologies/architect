# /// script
# requires-python = ">=3.9"
# dependencies = ["pymupdf>=1.24"]
# ///
"""Extract markups (annotations) from one or more PDFs into a CSV comment log.

Deps:  pymupdf  (pip install pymupdf, or run with `uv run`)
Usage: uv run extract_annotations.py OUT.csv a.pdf [b.pdf ...]
       uv run extract_annotations.py OUT.csv --dir ./markups

Writes one row per annotation with: id, file, page, sheet_label, type, author,
created, modified, comment, subject, text_under (the drawing text the markup
covers, when there is a text layer), x0, y0, x1, y1 (PDF points, origin top-left).

It never guesses. If a markup has no comment text, the comment column stays empty
and the row is still listed. If the PDF has no text layer, sheet_label stays empty.
Pages with no annotations are reported in the summary, not invented.
"""
import csv
import re
import sys
from pathlib import Path

try:
    import pymupdf  # PyMuPDF >= 1.24
except ImportError:  # older installs expose `fitz`
    try:
        import fitz as pymupdf  # type: ignore
    except ImportError:
        sys.exit("PyMuPDF is required: pip install pymupdf  (or: uv run extract_annotations.py ...)")

# Sheet numbers like A-101, A101, 01-GA-100, S2.01. Taken from the page's own text,
# bottom-right quadrant first (where title blocks usually are). Reported, not inferred.
SHEET_RE = re.compile(r"\b([A-Z]{1,3}[-_.]?\d{2,4}(?:[-_.]\d{1,3})?)\b")

SKIP_TYPES = {"Link", "Widget", "Popup"}  # not markups


def sheet_label(page):
    text = page.get_text("text") or ""
    if not text.strip():
        return ""
    r = page.rect
    corner = pymupdf.Rect(r.x0 + r.width * 0.5, r.y0 + r.height * 0.6, r.x1, r.y1)
    for chunk in (page.get_textbox(corner) or "", text):
        m = SHEET_RE.search(chunk)
        if m:
            return m.group(1)
    return ""


def text_under(page, rect):
    try:
        t = page.get_textbox(rect) or ""
    except Exception:
        return ""
    return " ".join(t.split())[:200]


def main(argv):
    if len(argv) < 3:
        sys.exit(__doc__)
    out = Path(argv[1])
    if argv[2] == "--dir":
        pdfs = sorted(Path(argv[3]).glob("*.pdf"))
    else:
        pdfs = [Path(p) for p in argv[2:]]
    if not pdfs:
        sys.exit("No PDFs given.")

    rows, empty_pages, no_text = [], [], []
    n = 0
    for pdf in pdfs:
        if not pdf.exists():
            sys.exit(f"Not found: {pdf}")
        doc = pymupdf.open(pdf)
        for pno, page in enumerate(doc, start=1):
            label = sheet_label(page)
            if not (page.get_text("text") or "").strip():
                no_text.append(f"{pdf.name} p{pno}")
            found = False
            for a in page.annots() or []:
                atype = a.type[1]
                if atype in SKIP_TYPES:
                    continue
                found = True
                n += 1
                info = a.info or {}
                rect = a.rect
                rows.append({
                    "id": n,
                    "file": pdf.name,
                    "page": pno,
                    "sheet_label": label,
                    "type": atype,
                    "author": info.get("title", ""),
                    "created": info.get("creationDate", ""),
                    "modified": info.get("modDate", ""),
                    "comment": " ".join((info.get("content", "") or "").split()),
                    "subject": info.get("subject", ""),
                    "text_under": text_under(page, rect),
                    "x0": round(rect.x0, 1), "y0": round(rect.y0, 1),
                    "x1": round(rect.x1, 1), "y1": round(rect.y1, 1),
                })
            if not found:
                empty_pages.append(f"{pdf.name} p{pno}")
        doc.close()

    fields = ["id", "file", "page", "sheet_label", "type", "author", "created", "modified",
              "comment", "subject", "text_under", "x0", "y0", "x1", "y1"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print(f"Files read: {len(pdfs)}")
    print(f"Markups extracted: {len(rows)} -> {out}")
    by_type = {}
    for r in rows:
        by_type[r["type"]] = by_type.get(r["type"], 0) + 1
    print("By type: " + (", ".join(f"{k} {v}" for k, v in sorted(by_type.items())) or "none"))
    blank = sum(1 for r in rows if not r["comment"])
    if blank:
        print(f"Markups with no comment text: {blank} (graphic-only; review visually)")
    if empty_pages:
        print(f"Pages with no markups: {len(empty_pages)}")
    if no_text:
        print(f"Pages with no text layer (sheet label not read): {', '.join(no_text)}")


if __name__ == "__main__":
    main(sys.argv)
