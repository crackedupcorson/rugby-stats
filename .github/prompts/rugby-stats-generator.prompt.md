# 🏉 Rugby Data Exploration Assistant Prompt

**Goal:**  
Build a *lightweight*, **read-only** Python scraper to explore publicly available player and team stats
from RugbyPass and (where exposed) embedded Opta data.
This is *exploratory* only — no automation, no bypassing logins, and no commercial API scraping.

---

## 🎯 Objectives
1. Retrieve and parse **publicly visible tables** for:
   - Ireland national team
   - Leinster, Munster, Ulster, Connacht
2. Automatically detect **table headers + sample data rows**
   and output them to a `pandas.DataFrame`.
3. Log what fields are available (`headers`) to help shape a JSON schema later.
4. Write results to `/data/preview_<team>.csv` for inspection.

---

## ⚙️ Constraints
- Use only: `requests`, `beautifulsoup4`, `pandas`
- Add `time.sleep()` delays to stay polite to the site.
- No scraping behind login walls or dynamic JS endpoints.
- Keep code modular and readable: 
  - `fetch_page(url) -> str`
  - `extract_table(html) -> pd.DataFrame`
  - `save_to_csv(df, team_name)`
- Support basic error handling (status codes, missing table, etc.)

---

## 💡 Stretch Ideas (later, not now)
- Detect embedded `<script>` blocks with `"Opta"` or `"dataLayer"`, parse JSON payloads.
- Extend scraper to other competitions (URC, Six Nations, Champions Cup).
- Build a data reliability map comparing RugbyPass vs ESPN Scrum vs PlanetRugby.

---

## 🧠 Example Usage
```python
teams = ["ireland", "leinster", "munster", "ulster", "connacht"]
for team in teams:
    url = f"https://www.rugbypass.com/stats/team/{team}/"
    html = fetch_page(url)
    df = extract_table(html)
    save_to_csv(df, team)
