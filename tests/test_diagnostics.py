import datetime as dt
import unittest
from urllib.error import HTTPError, URLError
from io import BytesIO
from diagnostics import (sitemap_urls,load_sitemap,SITEMAP,SitemapRedirectError,sample,inspect_sample,extended_windows,long_periods,new_query_candidates)

class DiagnosticsTests(unittest.TestCase):
    def test_sitemap_scope(self):
        xml = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://koolo.app/learn</loc></url><url><loc>https://other.example/</loc></url><url><loc>https://koolo.app/a?secret=1</loc></url></urlset>'
        self.assertEqual(sitemap_urls(xml),["https://koolo.app/learn"])
        with self.assertRaises(ValueError):
            sitemap_urls("<sitemapindex/>")

    def test_sampling(self):
        urls = [str(i) for i in range(41)]
        day = dt.date(2026,11,27)
        self.assertEqual(len(set(sample(urls,day))),20)
        self.assertFalse(set(sample(urls,day)) & set(sample(urls,day+dt.timedelta(days=1))))

    def test_inspection_stops_on_denied(self):
        def denied(*args):
            raise HTTPError("https://example.com",403,"denied",None,None)
        result = inspect_sample("fake","sc-domain:koolo.app",dt.date(2026,11,27),
                                load=lambda:["https://koolo.app/a","https://koolo.app/b"],inspect=denied)
        self.assertEqual(len(result["rows"]),1)
        self.assertEqual(result["rows"][0]["status"],"unknown")
        self.assertEqual(result["planned"],2)
        self.assertEqual(inspect_sample("fake","sc-domain:other.example",dt.date.today())["status"],"unsupported_property")

    def test_long_windows(self):
        periods = long_periods("fake","example",dt.date(2026,11,27),
                               lambda *args:{"rows":[],"possibly_truncated":False})
        for n in (28,90):
            a,b = periods[str(n)]
            self.assertEqual((dt.date.fromisoformat(a["end"])-dt.date.fromisoformat(a["start"])).days+1,n)
            self.assertEqual(dt.date.fromisoformat(a["start"])-dt.timedelta(days=1),dt.date.fromisoformat(b["end"]))

    def test_new_queries(self):
        def period(keys,truncated=False):
            return {"groups":{"query":{"rows":[{"keys":[k]} for k in keys],"possibly_truncated":truncated}}}
        self.assertEqual(new_query_candidates(period(["a","b"]),period(["a"])),[{"keys":["b"]}])
        self.assertIsNone(new_query_candidates(period(["b"]),period(["a"],True)))
        self.assertIsNone(new_query_candidates(period(["b"]),period([])))

    def test_sitemap_retry_and_user_agent(self):
        calls, pauses = [], []
        class Response(BytesIO):
            def geturl(self):
                return SITEMAP
        def opener(req, timeout):
            calls.append(req)
            self.assertEqual(req.get_header("User-agent"), "Crew-Production-SEO-Smoke/1.0")
            if len(calls) == 1:
                raise HTTPError(SITEMAP, 503, "temporary", None, None)
            return Response(b"<urlset><url><loc>https://koolo.app/</loc></url></urlset>")
        self.assertEqual(load_sitemap(opener, pauses.append), ["https://koolo.app/"])
        self.assertEqual(pauses, [1])

    def test_sitemap_failure_reason(self):
        for exc, reason in [(HTTPError(SITEMAP,403,"denied",None,None), "http_403"),
                            (URLError("private detail"), "network_error"),
                            (SitemapRedirectError("redirect"), "unexpected_redirect")]:
            def failed():
                raise exc
            result = inspect_sample("fake","sc-domain:koolo.app",dt.date(2026,11,28),load=failed)
            self.assertEqual(result["status"],"sitemap_unavailable")
            self.assertEqual(result["sitemap_error"],reason)
            self.assertEqual(result["rows"],[])
