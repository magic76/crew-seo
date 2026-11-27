"""Produce evidence cards from GSC reports without claiming causal results."""
import json
import sys
from pathlib import Path

def total(period):
    group = period["groups"]["total"]
    rows = group["rows"]
    if group["possibly_truncated"] or len(rows) != 1:
        return None
    return {k: rows[0][k] for k in ("clicks", "impressions", "ctr", "position")}

def analyze(report):
    current, previous = report["periods"]
    a, b = total(current), total(previous)
    cards = []
    if a is not None and b is not None:
        cards.append({
            "status": "observed",
            "source": "GSC Search Analytics, final web data, site totals",
            "scope": {"property": report["property"], "current": [current["start"], current["end"]],
                      "previous": [previous["start"], previous["end"]]},
            "observation": {"current": a, "previous": b, "delta": {
                k: a[k]-b[k] for k in ("clicks","impressions","ctr","position")}},
            "limitation": "Descriptive comparison only; CTR delta is a fraction, lower position is better. No causal attribution or significance claim.",
            "next_check": "Review daily trends, search demand and recent site changes."
        })
    else:
        cards.append({"status": "unknown", "source": "GSC site totals",
                      "limitation": "Missing or incomplete totals; no growth claim.",
                      "next_check": "Verify property, date range and final data availability."})
    for row in report["query_opportunities"]:
        cards.append({
            "status": "candidate",
            "source": "GSC query rows, current period",
            "scope": {"property": report["property"], "start": current["start"], "end": current["end"]},
            "observation": {k: row[k] for k in ("keys","clicks","impressions","ctr","position")},
            "limitation": "Average position is not live rank; top rows may omit queries. Thresholds only select review candidates.",
            "next_check": "Verify query-to-page mapping and search intent before suggesting a change.",
            "action": None
        })
    return {"property": report["property"], "evidence_cards": cards,
            "review_policy": "No automatic changes. Preserve baseline, confirm page fit, make one reversible change, recheck live, review at 14/28 days."}

if __name__ == "__main__":
    source, destination = map(Path, sys.argv[1:])
    report = analyze(json.loads(source.read_text(encoding="utf-8")))
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Evidence cards generated (data not printed).")
