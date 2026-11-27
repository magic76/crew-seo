"""Private affiliate GSC collector; no raw query logs, public artifacts or files."""
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo
from collect import query, windows
SITE = "sc-domain:hicrewapps.com"
ENDPOINT = "https://hicrewapps.com/api/private-gsc"

def summary(token, today, fetch=query):
    start, end = windows(today)[0]
    groups = {name: fetch(token, SITE, start, end, dims)
              for name, dims in [("total", []), ("date", ["date"]), ("query", ["query"])]}
    def values(r):
        return {k: r[k] for k in ["clicks", "impressions", "position"]}
    total = groups["total"]["rows"]
    daily = [{"date": r["keys"][0], **values(r)} for r in groups["date"]["rows"]]
    opportunities = sorted(
        [r for r in groups["query"]["rows"] if r["impressions"] >= 10 and 8 <= r["position"] <= 20 and len(r["keys"][0]) <= 512],
        key=lambda r: (-r["impressions"], r["position"])
    )[:20]
    return {"version": 1, "property": SITE,
            "period": {"start": str(start), "end": str(end)},
            "total": values(total[0]) if total else None,
            "daily": daily,
            "opportunities": [{"query": r["keys"][0], **values(r)} for r in opportunities],
            "possiblyTruncated": any(g["possibly_truncated"] for g in groups.values())}

def run():
    if os.environ.get("GITHUB_REPOSITORY") != "magic76/crew-seo" or os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise RuntimeError("Not authorized branch")
    token = os.environ["GSC_ACCESS_TOKEN"]
    if not token:
        raise RuntimeError("Missing Google token")
    report = summary(token, dt.datetime.now(ZoneInfo("America/Los_Angeles")).date())
    path = os.path.join(os.environ["RUNNER_TEMP"], "affiliate-gsc.json")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        json.dump(report, output, ensure_ascii=False)
    print("Affiliate Google query verified. Temporary private file created.")

if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        import re
        status = re.fullmatch(r"GSC query failed: HTTP (\d{3})", str(exc))
        print("Affiliate Google query failed: " + ("HTTP " + status.group(1) if status else type(exc).__name__), file=sys.stderr)
        sys.exit(1)
