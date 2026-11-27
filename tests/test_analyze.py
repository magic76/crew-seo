import unittest
from analyze import analyze

def fixture():
    row = {"clicks": 2, "impressions": 20, "ctr": .1, "position": 12}
    return {"property": "sc-domain:example.com",
            "periods": [{"start": "2026-11-17", "end": "2026-11-23",
                         "groups": {"total": {"rows": [row], "possibly_truncated": False}}},
                        {"start": "2026-11-10", "end": "2026-11-16",
                         "groups": {"total": {"rows": [dict(row, clicks=1)], "possibly_truncated": False}}}],
            "query_opportunities": [dict(row, keys=["example"])]}

class AnalyzeTests(unittest.TestCase):
    def test_comparison(self):
        cards = analyze(fixture())["evidence_cards"]
        self.assertEqual(cards[0]["status"], "observed")
        self.assertEqual(cards[0]["observation"]["delta"]["clicks"], 1)
        self.assertEqual(cards[1]["status"], "candidate")
        self.assertIsNone(cards[1]["action"])

    def test_missing_totals(self):
        r = fixture()
        r["periods"][1]["groups"]["total"]["rows"] = []
        card = analyze(r)["evidence_cards"][0]
        self.assertEqual(card["status"], "unknown")
        self.assertNotIn("observation", card)
