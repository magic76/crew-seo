import unittest
import json
from agent_report import allowed,build,group
from test_dashboard import fixture

class AgentReportTests(unittest.TestCase):
    def test_gate(self):
        env={"GITHUB_REPOSITORY_ID":"1473953409","GITHUB_REF":"refs/heads/main",
             "REPO_PRIVATE":"false","SEO_ENABLED":"true","GSC_PROPERTY":"sc-domain:koolo.app"}
        self.assertTrue(allowed(env))
        for k,v in [("GITHUB_REPOSITORY_ID","other"),("GITHUB_REF","refs/heads/test"),
                    ("REPO_PRIVATE","true"),("SEO_ENABLED","false"),
                    ("GSC_PROPERTY","sc-domain:other.example"),("SEO_ALLOW_PUBLIC_REPORTS","false"),
                    ("SEO_PUBLISH_AGENT_REPORT","false")]:
            self.assertFalse(allowed(dict(env,**{k:v})))

    def test_projection(self):
        report=fixture()
        report["token"]="DO_NOT_PUBLISH"
        report["periods"][0]["groups"]["query"]["rows"][0]["secret"]="DO_NOT_PUBLISH"
        report["inspection"]={"rows":[{"url":"https://koolo.app/learn","status":"observed",
                                        "referringUrls":["DO_NOT_PUBLISH"]}]}
        out=build(report,"2026-11-27T05:00:00+00:00","123","abc")
        self.assertNotIn("DO_NOT_PUBLISH",json.dumps(out))
        self.assertEqual(out["property"],"sc-domain:koolo.app")
        self.assertEqual(out["source_run_id"],"123")
        self.assertEqual(out["periods"][0]["groups"]["total"]["rows"][0]["clicks"],2)
        self.assertIsNone(out["query_page"])
        self.assertIsNone(out["new_query_candidates"])

    def test_scope_and_limit(self):
        rows=[{"keys":["https://koolo.app/"+str(i)],"impressions":i} for i in range(45)]
        rows.extend([{"keys":["https://other.example/"]},{"keys":["https://koolo.app/?token=secret"]}])
        out=group({"rows":rows,"possibly_truncated":True},["page"],40)
        self.assertEqual(len(out["rows"]),40)
        self.assertEqual(out["omitted_rows"],7)
        self.assertEqual(out["rows"][0]["impressions"],44)
        self.assertTrue(out["possibly_truncated"])
        self.assertNotIn("secret",json.dumps(out))
        report=fixture()
        report["property"]="sc-domain:other.example"
        with self.assertRaises(ValueError):
            build(report,"now","1","sha")
