import datetime as dt
import unittest
from affiliate_collect import summary, SITE
class AffiliateTests(unittest.TestCase):
    def test_private_summary(self):
        seen = []
        def fetch(token, site, start, end, dims):
            self.assertEqual(site, SITE)
            seen.append(dims)
            row = {"clicks": 2, "impressions": 20, "position": 12, "ctr": .1}
            if dims == ["query"]:
                row["keys"] = ["充電器"]
            elif dims == ["date"]:
                row["keys"] = [str(start)]
            return {"rows": [row], "possibly_truncated": False}
        result = summary("test", dt.date(2026,11,27), fetch)
        self.assertEqual(result["property"], SITE)
        self.assertEqual(result["period"], {"start":"2026-11-17","end":"2026-11-23"})
        self.assertEqual(result["opportunities"][0]["query"], "充電器")
        self.assertEqual(len(seen), 3)
        self.assertNotIn("ctr", result["total"])
    def test_empty(self):
        result = summary("test", dt.date(2026,11,27), lambda *a: {"rows": [], "possibly_truncated": False})
        self.assertIsNone(result["total"])
        self.assertEqual(result["daily"], [])
if __name__ == "__main__":
    unittest.main()
