"""Read-only GSC collector; never log tokens or raw search rows."""
import datetime as dt
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
from diagnostics import long_periods, inspect_sample, new_query_candidates

API = "https://www.googleapis.com/webmasters/v3/sites/"
LIMIT = 1000

def windows(today):
    end = today - dt.timedelta(days=4)
    start = end - dt.timedelta(days=6)
    return [(start, end), (start-dt.timedelta(days=7), start-dt.timedelta(days=1))]

def query(token, site, start, end, dimensions):
    body = {"startDate": str(start), "endDate": str(end),
            "dimensions": dimensions, "type": "web", "dataState": "final",
            "rowLimit": LIMIT}
    req = Request(API + quote(site, safe="") + "/searchAnalytics/query",
                  data=json.dumps(body).encode(), method="POST",
                  headers={"Authorization": "Bearer " + token,
                           "Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=30) as response:
            result = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"GSC query failed: HTTP {exc.code}") from None
    except URLError:
        raise RuntimeError("GSC network request failed") from None
    rows = result.get("rows", [])
    if not isinstance(rows, list):
        raise ValueError("Invalid GSC rows")
    return {"rows": rows, "possibly_truncated": len(rows) >= LIMIT}

def opportunities(rows):
    return sorted(
        [r for r in rows if r["impressions"] >= 10 and 8 <= r["position"] <= 20],
        key=lambda r: (-r["impressions"], r["position"])
    )[:20]

def collect(token, site, today, fetch=query):
    periods = []
    for start, end in windows(today):
        groups = {name: fetch(token, site, start, end, dims)
                  for name, dims in [("total", []), ("date", ["date"]),
                                     ("query", ["query"]), ("page", ["page"])]}
        periods.append({"start": str(start), "end": str(end), "groups": groups})
    return {"property": site, "periods": periods,
            "query_opportunities": opportunities(periods[0]["groups"]["query"]["rows"]),
            "limitations": "Final web data, top rows only; query/page rows may omit data. Small samples are exploratory."}

def collection_allowed(env):
    if env.get("SEO_ENABLED") != "true":
        return False
    if env.get("REPO_PRIVATE") == "true":
        return True
    return (env.get("REPO_PRIVATE") == "false"
            and env.get("ALLOW_PUBLIC_REPORTS") == "true"
            and env.get("GSC_PROPERTY") == "sc-domain:koolo.app")

def main():
    if not collection_allowed(os.environ):
        raise SystemExit("Collection disabled")
    token = os.environ["GSC_ACCESS_TOKEN"]
    site = os.environ["GSC_PROPERTY"]
    if not token or not site:
        raise SystemExit("Missing configuration")
    today = dt.datetime.now(ZoneInfo("America/Los_Angeles")).date()
    report = collect(token, site, today)
    try:
        report["long_periods"] = long_periods(token, site, today, query)
    except (RuntimeError, ValueError):
        report["long_periods"] = {}
    report["new_query_candidates"] = new_query_candidates(*report["periods"])
    current = report["periods"][0]
    try:
        report["query_page"] = query(token,site,dt.date.fromisoformat(current["start"]),dt.date.fromisoformat(current["end"]),["query","page"])
    except (RuntimeError, ValueError):
        report["query_page"] = None
    report["inspection"] = inspect_sample(token,site,today)
    out = Path("reports")
    out.mkdir(exist_ok=True)
    (out / "gsc.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("GSC report generated successfully (data not printed).")

if __name__ == "__main__":
    main()
