import unittest
from analyze import analyze
from dashboard import render

def fixture():
    row = {"impressions": 20, "clicks": 2, "ctr": .1, "position": 12}
    def period(start,end):
        return {"start":start,"end":end,"groups":{
            "total":{"rows":[row],"possibly_truncated":False},
            "date":{"rows":[dict(row,keys=[start])]},
            "query":{"rows":[dict(row,keys=['<script>alert("x")</script>'])]},
            "page":{"rows":[dict(row,keys=["https://koolo.app/learn"])]}
        }}
    return {"property":"sc-domain:koolo.app",
            "periods":[period("2026-11-17","2026-11-23"),period("2026-11-10","2026-11-16")],
            "query_opportunities":[dict(row,keys=["English practice"])]}

class DashboardTests(unittest.TestCase):
    def test_real_structure_and_escape(self):
        report = fixture()
        output = render(report,analyze(report),generated="test",public=True)
        self.assertIn("10.00%",output)
        self.assertIn("English practice",output)
        self.assertIn("https://koolo.app/learn",output)
        self.assertIn("&lt;script&gt;",output)
        self.assertNotIn('<script>alert("x")</script>',output)
        self.assertIn("任何人均可查看",output)
        self.assertIn("noindex,nofollow",output)

    def test_missing_rows(self):
        report = fixture()
        for period in report["periods"]:
            for group in period["groups"].values():
                group["rows"] = []
        report["query_opportunities"] = []
        output = render(report,analyze(report))
        self.assertIn("資料不足",output)
        self.assertIn("尚無每日資料",output)
        self.assertIn("目前沒有可顯示",output)
        self.assertNotIn("0.00%",output)

    def test_public_scope(self):
        report = fixture()
        report["property"] = "sc-domain:other.example"
        with self.assertRaises(ValueError):
            render(report,analyze(report),public=True)
        self.assertIn("other.example",render(report,analyze(report)))
