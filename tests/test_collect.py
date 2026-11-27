import datetime as dt
import unittest
from unittest.mock import patch
import collect

class CollectorTests(unittest.TestCase):
    def test_windows(self):
        self.assertEqual(collect.windows(dt.date(2026, 11, 27)), [
            (dt.date(2026,11,17), dt.date(2026,11,23)),
            (dt.date(2026,11,10), dt.date(2026,11,16))])

    def test_opportunities(self):
        rows = [{"impressions": 20, "position": 10},
                {"impressions": 9, "position": 10},
                {"impressions": 30, "position": 21},
                {"impressions": 40, "position": 8}]
        self.assertEqual(collect.opportunities(rows), [rows[3], rows[0]])

    def test_collect(self):
        calls = []
        def fake(token, site, start, end, dims):
            calls.append(dims)
            return {"rows": [], "possibly_truncated": False}
        report = collect.collect("fake", "sc-domain:example.com", dt.date(2026,11,27), fake)
        self.assertEqual(len(calls), 8)
        self.assertEqual(calls[:4], [[], ["date"], ["query"], ["page"]])
        self.assertEqual(report["query_opportunities"], [])

    def test_disabled(self):
        with patch.dict("os.environ", {"SEO_ENABLED": "true", "REPO_PRIVATE": "false"}, clear=True):
            with self.assertRaises(SystemExit):
                collect.main()

    def test_public_pilot_policy(self):
        base = {"SEO_ENABLED": "true", "REPO_PRIVATE": "false",
                "ALLOW_PUBLIC_REPORTS": "true", "GSC_PROPERTY": "sc-domain:koolo.app"}
        self.assertTrue(collect.collection_allowed(base))
        for key, value in [("SEO_ENABLED", "false"), ("ALLOW_PUBLIC_REPORTS", "false"),
                           ("GSC_PROPERTY", "sc-domain:example.com"), ("REPO_PRIVATE", "")]:
            with self.subTest(key=key):
                self.assertFalse(collect.collection_allowed(dict(base, **{key: value})))
        self.assertTrue(collect.collection_allowed({"SEO_ENABLED": "true", "REPO_PRIVATE": "true"}))
        self.assertFalse(collect.collection_allowed({"SEO_ENABLED": "false", "REPO_PRIVATE": "true"}))
        self.assertFalse(collect.collection_allowed({"SEO_ENABLED": "true", "REPO_PRIVATE": "false"}))
