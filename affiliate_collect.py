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

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def run():
    if os.environ.get("GITHUB_REPOSITORY") != "magic76/crew-seo" or os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise RuntimeError("Not authorized branch")
    token = os.environ["GSC_ACCESS_TOKEN"]
    if not token:
        raise RuntimeError("Missing Google token")
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(urllib.request.Request(ENDPOINT, method="HEAD"), timeout=20) as r:
        if r.status != 204:
            raise RuntimeError("Endpoint unavailable")
    report = summary(token, dt.datetime.now(ZoneInfo("America/Los_Angeles")).date())
    url = urllib.parse.urlsplit(os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"])
    if url.scheme != "https":
        raise RuntimeError("Invalid token endpoint")
    params = urllib.parse.parse_qsl(url.query, keep_blank_values=True)
    params = [(k, v) for k, v in params if k != "audience"] + [("audience", ENDPOINT)]
    auth_url = urllib.parse.urlunsplit(url._replace(query=urllib.parse.urlencode(params)))
    with opener.open(urllib.request.Request(auth_url, headers={"Authorization": "Bearer " + os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]}), timeout=20) as r:
        jwt = json.load(r)["value"]
    req = urllib.request.Request(ENDPOINT, data=json.dumps(report, ensure_ascii=False).encode(), method="POST",
                                 headers={"Authorization": "Bearer " + jwt, "Content-Type": "application/json"})
    with opener.open(req, timeout=30) as r:
        if r.status != 200 or json.load(r).get("ok") is not True:
            raise RuntimeError("Private upload failed")
    print("Affiliate GSC collection and private upload verified. No report data logged.")

if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print("Affiliate GSC collection failed: " + (f"HTTP {exc.code}" if isinstance(exc, urllib.error.HTTPError) else type(exc).__name__), file=sys.stderr)
        sys.exit(1)
