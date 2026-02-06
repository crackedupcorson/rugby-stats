# URC Player Performance Extraction Tool (GraphQL-Based)

## Objective

Build a deterministic data extraction and analysis tool for **United Rugby Championship (URC)** player performance, focusing primarily on **unstructured play contribution**, with supporting **defensive** and **discipline** metrics.

The tool must:

- Query known URC GraphQL endpoints
- Extract **season-level player statistics**
- Normalize metrics into a structured dataset
- Compute **derived performance indicators**
- Support **API-level validation checkpoints**

**Initial pilot scope:** Leinster players only.

---

## Hard Constraints (Do Not Violate)

- ❌ Do NOT explore or crawl the website  
- ❌ Do NOT infer endpoints or schemas  
- ❌ Do NOT scrape the DOM  
- ✅ Use ONLY explicitly defined GraphQL endpoints and variables  
- ✅ URLs are consistent and manually defined  
- ✅ Assume authentication/cookies are handled externally if required  

---

## Known Teams (Theme IDs)

| Team      | Club ID |
|-----------|---------|
| Leinster  | 5356    |
| Munster   | 4377    |
| Connacht  | 5483    |
| Ulster    | 2129    |

**Pilot target:** Leinster (`5356`)

---

## GraphQL Endpoints

### 1. Player Season Stats

- **Endpoint:** `https://www.unitedrugby.com/graphql`  
- **Operation Name:** `GetPlayerSeasonStats1`  
- **Variables:**
    ```json
    {
      "player_id": [<player_ids>],
      "season_id": [202501]
    }
    ```
- **Persisted Query:**
    ```
    version: 1
    sha256Hash: 0a0022eeecff7bbdae5667322bd51a42cac3c9260bd116acd4e3e338b314ce28
    ```

### 2. Team Theme / Context (Optional – Phase 2)

- **Endpoint:** `https://www.unitedrugby.com/graphql`  
- **Operation Name:** `GetPlayerThemeSettingsById`  
- **Variables:**
    ```json
    {
      "currentClub": ["5356"]
    }
    ```
- **Persisted Query:**
    ```
    version: 1
    sha256Hash: e1b82de16fadff0637731c7e7ca176c6f304685eb2760ea391fc1ee5745636ab
    ```

---

## Inputs

- A manually supplied list of **Leinster player IDs**  
- No player discovery logic required  
- Tool must accept an **array of player IDs**

---

## Metrics to Extract

### Primary: Unstructured Play
- Carries  
- Metres Made  
- Offloads  
- Clean Breaks  
- Defenders Beaten  

### Secondary: Defensive Contribution
- Tackles Made  
- Missed Tackles  
- Turnovers Won  
- Breakdown Steals  
- Tackle Success Percentage  

### Discipline (Negative Impact)
- Penalties Conceded  
- Yellow Cards  
- Red Cards  

---

## Normalization Rules

- Normalize metrics **per 80 minutes** where minutes data exists  
- If minutes are unavailable, normalize **per appearance**  
- Handle **missing or null fields safely**  
- **No silent metric drops**

---

## Derived Metrics (Phase 1)

Compute the following using configurable weight constants:

- **Unstructured Impact Score**  
- **Defensive Reliability Score**  
- **Discipline Risk Index**  
- **Composite Player Contribution Score**

> Weights must be defined as **constants** and easily adjustable.

---

## Output Requirements

- **Primary output:** JSON  
- **Optional:** CSV export  
- **One record per player per season**  

**Required structure:**
    ```json
    {
      "player_id": 1234,
      "team": "Leinster",
      "season": 202501,
      "raw_metrics": {...},
      "derived_metrics": {...}
    }
    ```

---

## Validation Checkpoints

1. **Single Player Validation**
   - Fetch one known Leinster player  
   - Log the full raw GraphQL response  
   - Verify all expected metric fields exist  

2. **Metric Mapping Validation**
   - Explicitly map raw API fields to internal metric names  
   - Assert **zero unintended metric loss**  

3. **Batch Processing**
   - Process at least 5 Leinster players  
   - Partial failures **must not abort execution**  

4. **Scoring Sanity Check**
   - Non-zero values for active players  
   - Discipline metrics **must reduce composite score**  

---

## Non-Goals

- ❌ No UI  
- ❌ No prediction models  
- ❌ No betting or fantasy outputs  
- ❌ No real-time or live data  

---

## Success Criteria

- Deterministic outputs for identical inputs  
- Zero reliance on HTML structure  
- Clear separation of:
  - Data acquisition
  - Normalization
  - Scoring  
- Leinster rankings pass a rugby **“sniff test”**

---

## Implementation Guidance

- **Language:** Python (preferred)  
- **HTTP library:** `requests` or equivalent  
- **Code structure:** Modular, allowing future extension to other URC teams and data sources (use separate classes etc.)
