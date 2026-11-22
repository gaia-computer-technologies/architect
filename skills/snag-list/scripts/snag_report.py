# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Turn a snag-list CSV into a printable HTML list plus a status summary.

Usage:
    python snag_report.py snags.csv -o snag-list.html [--project "Name"] [--issue "Rev A, 12 Mar"]

CSV columns (header row required; names are case-insensitive, extra columns are kept in Notes):
    ref, area, room, element, trade, description, priority, status, raised, reinspected, photo, notes

Only ref, area and description are required. Priority values: high / medium / low (anything
else is shown as given). Status values: open / in progress / closed / disputed / not accessible.

Standard library only. Prints a plain-text summary to stdout and writes the HTML file.
"""
from __future__ import annotations

import argparse
import csv
import html
import sys
from collections import Counter, OrderedDict
from datetime import date

FIELDS = ["ref", "area", "room", "element", "trade", "description",
          "priority", "status", "raised", "reinspected", "photo", "notes"]
REQUIRED = ["ref", "area", "description"]
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
STATUS_ORDER = ["open", "in progress", "disputed", "not accessible", "closed"]


def load(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            sys.exit("CSV has no header row.")
        header = {h: h.strip().lower() for h in reader.fieldnames}
        missing = [f for f in REQUIRED if f not in header.values()]
        if missing:
            sys.exit(f"CSV is missing required column(s): {', '.join(missing)}")
        rows = []
        for i, raw in enumerate(reader, start=2):
            row = {f: "" for f in FIELDS}
            extras = []
            for k, v in raw.items():
                if k is None:
                    continue
                key = header[k]
                val = (v or "").strip()
                if key in row:
                    row[key] = val
                elif val:
                    extras.append(f"{k.strip()}: {val}")
            if not any(row.values()):
                continue
            if not row["ref"] or not row["description"]:
                print(f"warning: line {i} has no ref or description; kept but flagged", file=sys.stderr)
                row["ref"] = row["ref"] or f"[line {i}]"
            if extras:
                row["notes"] = "; ".join([row["notes"]] + extras if row["notes"] else extras)
            row["status"] = (row["status"] or "open").lower()
            row["priority"] = row["priority"].lower()
            rows.append(row)
    return rows


def summarise(rows: list[dict]) -> str:
    total = len(rows)
    by_status = Counter(r["status"] for r in rows)
    open_rows = [r for r in rows if r["status"] != "closed"]
    by_trade = Counter((r["trade"] or "unassigned") for r in open_rows)
    by_area = Counter((r["area"] or "unassigned") for r in open_rows)
    by_pri = Counter((r["priority"] or "unset") for r in open_rows)
    lines = [f"Total items: {total}"]
    lines.append("By status: " + ", ".join(
        f"{s} {by_status[s]}" for s in STATUS_ORDER + sorted(set(by_status) - set(STATUS_ORDER)) if by_status[s]))
    closed = by_status.get("closed", 0)
    if total:
        lines.append(f"Closed: {closed}/{total} ({closed * 100 / total:.0f}%)  [basis: count of rows with status 'closed']")
    lines.append("Not closed, by priority: " + (", ".join(f"{k} {v}" for k, v in sorted(by_pri.items(), key=lambda kv: PRIORITY_ORDER.get(kv[0], 9))) or "none"))
    lines.append("Not closed, by trade: " + (", ".join(f"{k} {v}" for k, v in by_trade.most_common()) or "none"))
    lines.append("Not closed, by area: " + (", ".join(f"{k} {v}" for k, v in by_area.most_common()) or "none"))
    return "\n".join(lines)


def sort_key(r: dict):
    return (PRIORITY_ORDER.get(r["priority"], 9), r["room"], r["ref"])


def render(rows: list[dict], project: str, issue: str, summary: str) -> str:
    e = html.escape
    groups: "OrderedDict[str, list[dict]]" = OrderedDict()
    for r in sorted(rows, key=lambda r: (r["area"] or "zz")):
        groups.setdefault(r["area"] or "Unassigned area", []).append(r)
    out = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        f"<title>{e(project)} snag list</title>",
        "<style>",
        "body{font:11pt/1.35 system-ui,-apple-system,Segoe UI,Helvetica,Arial,sans-serif;color:#111;background:#fff;margin:24px}",
        "h1{font-size:16pt;margin:0 0 4px}h2{font-size:12pt;margin:24px 0 6px;border-bottom:2px solid #111;padding-bottom:2px}",
        ".meta{color:#444;margin-bottom:12px}pre{background:#f4f4f4;padding:8px;white-space:pre-wrap;font-size:9.5pt}",
        "table{width:100%;border-collapse:collapse;font-size:9.5pt}th,td{border:1px solid #999;padding:4px 6px;vertical-align:top;text-align:left}",
        "th{background:#eee}.closed td{color:#777;text-decoration:line-through}.high td:first-child{border-left:4px solid #111}",
        "td.chk{width:22px}@media print{body{margin:10mm}h2{break-after:avoid}tr{break-inside:avoid}}",
        "</style></head><body>",
        f"<h1>{e(project)} — Snag list</h1>",
        f"<div class='meta'>{e(issue)} · Generated {date.today().isoformat()} · {len(rows)} items</div>",
        f"<pre>{e(summary)}</pre>",
    ]
    cols = ["Ref", "Room", "Element", "Trade", "Description", "Pri.", "Status", "Raised", "Re-inspected", "Photo", "Notes", "OK"]
    for area, items in groups.items():
        out.append(f"<h2>{e(area)} ({len(items)})</h2><table><thead><tr>")
        out.extend(f"<th>{c}</th>" for c in cols)
        out.append("</tr></thead><tbody>")
        for r in sorted(items, key=sort_key):
            cls = " ".join(c for c in [("closed" if r["status"] == "closed" else ""), ("high" if r["priority"] == "high" else "")] if c)
            out.append(f"<tr class='{cls}'>" + "".join(
                f"<td>{e(r[k])}</td>" for k in ["ref", "room", "element", "trade", "description", "priority", "status", "raised", "reinspected", "photo", "notes"]
            ) + "<td class='chk'>&#9744;</td></tr>")
        out.append("</tbody></table>")
    out.append("<p class='meta'>Items listed are those observed on the inspections recorded. The list is not exhaustive and does not relieve the contractor of its obligations to complete the works in accordance with the contract.</p>")
    out.append("</body></html>")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("-o", "--out", default="snag-list.html")
    ap.add_argument("--project", default="Project")
    ap.add_argument("--issue", default="Issue")
    a = ap.parse_args()
    rows = load(a.csv)
    if not rows:
        sys.exit("No snag rows found.")
    summary = summarise(rows)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(render(rows, a.project, a.issue, summary))
    print(summary)
    print(f"Wrote {a.out}")


if __name__ == "__main__":
    main()
