#  URC Player Performance Extraction Tool (GraphQL-Based)
# Role Based Analysis

## Objective
Introduce role-aware metric weighting:
* Forwards
* Backs
* Half-backs
* Front row / second row (optional refinement)

Each role defines:
* Relevant metrics
* Weighting model
* Scoring interpretation

No single “overall” score without role context

## Guiding Advice

* Start simple, don't try to be clever by introducing too much complexity. 
* In this phase, start with coarse buckets
* Build a system that explains rugby performance clearly before trying to rate it comparatively.

### Roles
- FRONT_5
  - Loosehead
  - Hooker
  - Tighthead
  - Lock

- BACK_ROW
  - 6 / 7 / 8

- HALF_BACKS
  - 9 / 10

- BACKS
  - 11/ 12 / 13/ 14 / 15

* You do not change raw metrics.
* You change weightings and expectations.

### Example:

| Metric | Front 5 | Back Row | Halfbacks | Backs |
|--------|---------|----------|-----------|------------|
| Carries | Medium | High | Low | Medium |
| Metres | Low | Medium | Low | High |
| Tackles | High | High | Medium | Low |
| Offloads | Low | Medium | Medium | High |
| Penalties | Very costly | Costly | Costly | Medium |


