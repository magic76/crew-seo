"""Bounded, read-only diagnostics. Public pilot is limited to Koolo."""
import datetime as dt
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

PROPERTY = "sc-domain:koolo.app"
SITEMAP = "https://koolo.app/sitemap.xml"
INSPECT = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
CAP = 20

def extended_windows(end, length):
    start = end - dt.timedelta(days=length-1)
    return [(start,end),(start-dt.timedelta(days=length),start-dt.timedelta(days=1))]

def long_periods(token, site, today, query):
    end = today - dt.timedelta(days=4)
    result = {}
    for length in (28,90):
        periods = []
        for start, stop in extended_windows(end,length):
            groups = {}
            for name, dims in (("total",[]),("date",["date"])):
                groups[name] = query(token,site,start,stop,dims)
            periods.append({"start":str(start),"end":str(stop),"groups":groups})
        result[str(length)] = periods
    return result

def koolo_url(value):
    try:
        url = urlsplit(value)
        return (url.scheme == "https" and url.netloc == "koolo.app"
                and not url.fragment and not url.query)
    except ValueError:
        return False

def sitemap_urls(xml):
    root = ET.fromstring(xml)
    if root.tag.split("}")[-1] != "urlset":
        raise ValueError("Expected sitemap urlset")
    urls = []
    for entry in root:
        if entry.tag.split("}")[-1] != "url":
            continue
        for child in entry:
            if child.tag.split("}")[-1] == "loc":
                loc = (child.text or "").strip()
                if koolo_url(loc):
                    urls.append(loc)
    return sorted(set(urls))

def load_sitemap():
    with urlopen(SITEMAP,timeout=12) as response:
        if response.geturl() != SITEMAP:
            raise ValueError("Unexpected sitemap redirect")
        payload = response.read(2_000_001)
    if len(payload) > 2_000_000:
        raise ValueError("Sitemap too large")
    return sitemap_urls(payload)

def sample(urls,today,cap=CAP):
    if not urls:
        return []
    offset = today.toordinal()*cap % len(urls)
    return [urls[(offset+i)%len(urls)] for i in range(min(cap,len(urls)))]

def inspect_url(token,site,url):
    body = {"inspectionUrl":url,"siteUrl":site,"languageCode":"en-US"}
    req = Request(INSPECT,data=json.dumps(body).encode(),method="POST",
                  headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"})
    with urlopen(req,timeout=12) as response:
        result = json.load(response).get("inspectionResult",{}).get("indexStatusResult",{})
    if not result:
        return {"url":url,"status":"unknown"}
    return {"url":url,"status":"observed","verdict":result.get("verdict","VERDICT_UNSPECIFIED"),
            "coverage":result.get("coverageState"),"last_crawl":result.get("lastCrawlTime"),
            "canonical_matches": (result["googleCanonical"] == url) if result.get("googleCanonical") else None}

def inspect_sample(token,site,today,load=load_sitemap,inspect=inspect_url):
    if site != PROPERTY:
        return {"status":"unsupported_property","rows":[]}
    try:
        urls = load()
    except (OSError,ValueError,ET.ParseError):
        return {"status":"sitemap_unavailable","rows":[]}
    rows = []
    targets = sample(urls,today)
    for url in targets:
        try:
            rows.append(inspect(token,site,url))
        except HTTPError as exc:
            rows.append({"url":url,"status":"unknown","http_status":exc.code})
            if exc.code in (401,403,429):
                break
        except (OSError,ValueError):
            rows.append({"url":url,"status":"unknown"})
    return {"status":"sampled" if rows else "no_urls","date":str(today),
            "eligible":len(urls),"planned":len(targets),"rows":rows,
            "limitation":"Rotating sample, not full coverage or live test."}

def new_query_candidates(current,previous):
    a = current["groups"]["query"]
    b = previous["groups"]["query"]
    if a["possibly_truncated"] or b["possibly_truncated"] or not b["rows"]:
        return None
    prior = {tuple(r["keys"]) for r in b["rows"]}
    return [r for r in a["rows"] if tuple(r["keys"]) not in prior]
