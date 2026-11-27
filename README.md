# Crew SEO

Read-only Search Console collector for Crew projects. No Gemini key or service-account JSON key required.

## Activate P0

1. Set repository visibility to **private**.
2. Under Settings > Secrets and variables > Actions > Variables, create:
   - GCP_WIF_PROVIDER: full Google workload identity provider resource name
   - GCP_SERVICE_ACCOUNT: Google service account email
   - GSC_PROPERTY: Search Console property, e.g. sc-domain:koolo.app
   - SEO_ENABLED: true (only after making the repository private)
3. Merge the bootstrap PR, then run the "GSC daily" workflow on main manually. Verify the run and download its gsc-report artifact. Scheduled runs are at 23:00 UTC (07:00 Taipei next day), subject to GitHub scheduling delays.

The collection job is skipped unless the repository is private, main is selected and SEO_ENABLED is true. Do not change visibility back to public while reports exist. Disable collection and remove sensitive artifacts before changing visibility. Credentials and search data are never committed by the workflow. Reports are kept as private Actions artifacts for 7 days. Access is restricted to repository readers.

## Data

Final web search data: 7-day current and previous windows, ending four days before the current date in US Pacific time. Separate site totals, daily, query and page dimensions. Query/page rows are bounded and can omit anonymized/low-volume results; never sum them to derive site totals. Opportunity rules are hypotheses, not recommendations to automatically change a page. URL inspection, durable historical storage, additional SEO Coach modules, AI analysis and cross-repo Issue/PR creation are later phases.

Run offline tests: `python3 -m unittest discover -s tests -v`.

## Evidence cards

`analyze.py` converts a collected report into `reports/evidence.json`. It separates observed totals from unverified query opportunities, preserves date ranges, and does not propose automatic changes. Selected upstream SEO Coach reference documents and MIT license are in `knowledge/seo-coach/`. No upstream hooks are installed. Real reports remain private artifacts only.
