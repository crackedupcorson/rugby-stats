# rugby-stats
contains rugby union player and team stats

## Live run observations (automated preview)

I ran a small, read-only preview scraper that attempted to fetch the public team stat pages listed in the prompt spec and save any HTML tables it could find to CSV files under `data/`.

Summary of what happened:

- Targets: `ireland`, `leinster`, `munster`, `ulster`, `connacht`
- Request throttle: random delays between 10 and 20 seconds between requests to be polite.
- Libraries used: `requests`, `beautifulsoup4`, `pandas` (only).

Result (2025-11-03):

- All five pages returned HTTP 404 when fetched from this environment. No direct HTML `<table>`s were found on the returned content.
- The scraper does a heuristic search for embedded JSON (looking for script blocks mentioning "Opta" or "dataLayer"). It detected script blocks and wrote one `preview_<team>_embedded.json` per team into `data/`, but the parsed JSON blobs were empty objects with the current heuristics.

Files created by the run (in `data/`):

- `preview_ireland_embedded.json` (empty object)
- `preview_leinster_embedded.json` (empty object)
- `preview_munster_embedded.json` (empty object)
- `preview_ulster_embedded.json` (empty object)
- `preview_connacht_embedded.json` (empty object)
- `preview_summary.csv` (summary of fetch status and saved artifacts)

Notes & next steps:

- The 404 responses suggest the requested URL paths may have changed, are blocked for programmatic agents, or require a different user-agent/referrer or different endpoint. Do not attempt login bypasses or scraping behind authentication.
- Next steps I can take (pick one):
	- Try the pages in a browser to confirm the current canonical URLs and, if needed, adapt the target URLs used by the scraper.
	- Expand the embedded-JSON extraction to capture more patterns (e.g., JSON inside `window.__INITIAL_STATE__`, or use regex to extract larger script payloads then apply JS->JSON cleaning heuristics).
	- Add a small test harness that runs against saved HTML snapshots so development doesn't require live requests.

If you'd like, I can now try one of the next steps above — tell me which and I'll proceed.
