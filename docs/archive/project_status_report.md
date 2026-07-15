> **Archived.** Snapshot from the end of Phase 2 preparation (2026-07-11),
> reporting ~35% completion with analysis, weather context, and the dashboard
> not yet started. All of that work is now complete — see the
> [root README](../../README.md) for current project status.

# Project Status Report

As of **2026-07-11**, end of Phase 2 preparation. This report is a status
snapshot for planning purposes only — it contains no analytical findings.

## Current completion

**~35% of the full project** (Phase 1 data engineering + Phase 2 scaffolding done;
Phase 2 analysis, weather adjustment, Power BI build-out, and reporting remain).

| Phase | Status |
|---|---|
| Phase 1 — data engineering & validation | **Complete** |
| Phase 2 prep — SQL layer, warehouse, checklist, docs | **Complete** (this session) |
| Phase 2 — EDA, event study, weather adjustment | Not started |
| Phase 2 — Power BI build | Not started (model designed, not built) |
| Phase 2 — report & portfolio write-up | Not started |

## Completed

- 16/16 validated CPCB raw files; Gate 1: PASS.
- Canonical `station_daily.csv` (5,840 rows) + `stations.csv`.
- Automated data-quality pipeline (`01`–`02`) + reports.
- Automated tests (9 dataset tests + 15 GRAP-validator tests), all passing.
- GRAP event data contract + validator; **5 verified events loaded** (season
  2022-23, E001–E005).
- SQLite warehouse (`src/05_load_sqlite.py`) — 3 base tables + 4 derived views,
  built and smoke-tested; all 15 rebuilds cleanly from CSVs.
- 15 production-quality SQL query files, each executed successfully against the
  warehouse.
- Power BI data model spec (star schema, relationships, DAX measures).
- Phase 2 analysis checklist (ordered, with success criteria).
- Issue tracker (critical/medium/low, tech debt, assumptions, limitations).

## Blocked

- **2023-24 event analysis** — blocked on GRAP calendar acquisition (C-1);
  cannot proceed without human-verified CAQM orders for that season.
- **Full-season 2023-24 comparison** — blocked on data boundary (C-2); only
  Oct–Dec 2023 is in scope until/unless Jan–Feb 2024 files are acquired.
- Nothing else is blocked — EDA, SQL analysis, weather adjustment, and Power BI
  can all start immediately with the current 5-event, 2022-23 dataset.

## Next milestone

**Run the Phase 2 analysis checklist (`docs/phase2_analysis_checklist.md`)
end-to-end for the 2022-23 season**, producing: EDA summary, SQL result set,
event-window figures, a first weather-adjustment pass, and a Power BI draft
model loaded with real data.

## Risks

| Risk | Severity | Mitigation in place |
|---|---|---|
| Small event sample (n=5, one season) overstated as general finding | High | Hedging language mandated (README, checklist); issue LIM-5 documented |
| Weather-stage confounding read as a GRAP effect | High | 09/05/07 SQL carry explicit interpretation warnings; adjustment step planned |
| Overlapping event windows contaminate before/after deltas | Medium | Documented in query headers (M-2); shorter/cleaner windows possible once more events exist |
| Truncated 2023-24 season compared unfairly to full 2022-23 | Medium | Like-for-like Oct–Dec restriction already coded (`11_seasonal_comparison.sql`) |
| Units/aggregation method unverified against CPCB docs | Low-Medium | Flagged **(verify)** in data dictionary (M-3) |
| No CI; correctness depends on local test runs | Low | Tests exist and pass; CI is a future improvement (F-6) |

## Estimated remaining hours

| Work item | Hours |
|---|---|
| EDA (distributions, missingness, seasonality) | 3–4 |
| SQL analytical pass + result export | 2 |
| Event-window / before-after analysis | 3 |
| Weather adjustment (model + diagnostics) | 6–8 |
| Station comparison + summary stats | 2 |
| Power BI model build + core measures | 4–5 |
| Power BI pages (4 pages) | 4–6 |
| Report writing | 4 |
| README / docs / GitHub hygiene | 2 |
| Portfolio case study | 2 |
| **Total** | **32–40 hours** |

*(Excludes acquiring additional GRAP events or extending data scope — those are
separate, gated decisions, not estimated here.)*

## Estimated completion date

At ~4–6 focused hours/day, **32–40 hours ≈ 6–9 working days** from tomorrow
(2026-07-12) → **approximately 2026-07-21 to 2026-07-24**, assuming no scope
change (e.g., acquiring the 2023-24 GRAP calendar or extra stations would add
time on top of this estimate).

## Highest risk

**Overclaiming from a 5-event, single-season dataset.** The entire credibility of
this project rests on descriptive honesty; the biggest failure mode is not a bug,
it's a chart caption that implies more than 5 events in one season can support.
Every event-related output must carry its sample-size and confounding caveats
verbatim from `docs/issue_tracker.md`.

## Lowest risk

**Data engineering correctness.** Phase 1 is independently re-validated, tested,
and reproducible (Gate 1: PASS, 0 impossible values, 9/9 + 15/15 tests green).
The warehouse rebuilds deterministically from the same validated CSVs. This layer
is solid and unlikely to need revisiting.

## Most likely interview questions based on the repository today

1. **"Why is this not a causal-inference project, and how does the repo enforce
   that boundary?"** — point to the README's explicit non-claims list, the
   hedging built into every SQL query's caveats, and the stage-defined-by-AQI
   confound (issue LIM-1, queries 05/07).
2. **"Walk me through your data-quality gate. What would make Gate 1 fail?"** —
   `02_audit_data_quality.py`: structural checks, missingness, plausibility flags,
   all currently PASS with 0 impossible values.
3. **"Why did you exclude Alipur?"** — pre-declared missingness rule (wind speed
   100% missing in 2023), decided before looking at pollution levels — a
   selection-bias safeguard.
4. **"Why is the GRAP event calendar manually entered instead of scraped?"** — the
   data contract's golden rules: legal-order semantics (immediate vs. deferred
   effect, partial vs. full revocation) can't be reliably parsed automatically;
   auditability requires human verification against primary CAQM sources.
5. **"Why views instead of materialized tables for `daily_grap_state` and
   `event_windows`?"** — they're pure functions of 3 base tables; materializing
   would risk drift; dataset is small enough that view cost is negligible.
6. **"How do you handle the fact that your two GRAP seasons have unequal
   coverage?"** — explicit truncation handling in `11_seasonal_comparison.sql`
   (Oct–Dec-only comparison) rather than a naive full-season average.
7. **"What's the single biggest limitation of this analysis right now?"** — five
   verified events in one season; everything event-related is a first look, not
   a generalizable pattern (C-1).
8. **"How would you extend this to a full causal design?"** — would need a
   control (e.g., comparable non-GRAP city/period), more seasons, formal
   weather-adjustment with diagnostics, and ideally an identification strategy
   (e.g., regression discontinuity around thresholds) — explicitly out of scope
   here by design.
