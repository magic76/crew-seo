# Crew SEO

Read-only Search Console collector for Crew projects. No Gemini key or service-account JSON key required.

## Activate P0

1. Prefer **private** visibility for ongoing operation. The owner has approved a temporary public pilot for repository ID 1473953409 and property `sc-domain:koolo.app` only.
2. Under Settings > Secrets and variables > Actions > Variables, create:
   - GCP_WIF_PROVIDER: full Google workload identity provider resource name
   - GCP_SERVICE_ACCOUNT: Google service account email
   - GSC_PROPERTY: Search Console property, e.g. sc-domain:koolo.app
   - SEO_ENABLED: true (explicitly enables collection)
   - SEO_ALLOW_PUBLIC_REPORTS: optional; set to false to stop the temporary public pilot without changing private collection.
3. Run the "GSC daily" workflow on main manually. Verify the run and download its gsc-report artifact. Scheduled runs are at 23:00 UTC (07:00 Taipei next day), subject to GitHub scheduling delays.

Collection requires main and SEO_ENABLED=true. Private repositories are supported by default. Public collection is allowed only for the approved repository ID and Koolo property unless SEO_ALLOW_PUBLIC_REPORTS=false. Both workflow and collector enforce the policy. Reports are Actions artifacts for seven days. **On a public repository, signed-in GitHub users may download these reports, including real queries and page metrics.** Changing to private later cannot retract downloaded copies. Do not upload tokens, credentials, or report files to git or print report data to logs. To end the pilot, set SEO_ALLOW_PUBLIC_REPORTS=false or disable SEO_ENABLED, delete old public artifacts if desired, and change repository visibility to private. Do not change a private repository back to public while private reports exist.

## Data

Final web search data: 7-day current and previous windows, ending four days before the current date in US Pacific time. Separate site totals, daily, query and page dimensions. Query/page rows are bounded and can omit anonymized/low-volume results; never sum them to derive site totals. Opportunity rules are hypotheses, not recommendations to automatically change a page. URL inspection, durable historical storage, additional SEO Coach modules, AI analysis and cross-repo Issue/PR creation are later phases.

Run offline tests: `python3 -m unittest discover -s tests -v`.

## Evidence cards

`analyze.py` converts a collected report into `reports/evidence.json`. It separates observed totals from unverified query opportunities, preserves date ranges, and does not propose automatic changes. Selected upstream SEO Coach reference documents and MIT license are in `knowledge/seo-coach/`. No upstream hooks are installed. Real reports remain Actions artifacts only; visibility follows the repository, including the approved public pilot.
