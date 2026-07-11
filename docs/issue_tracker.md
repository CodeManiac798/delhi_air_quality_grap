# Issue Tracker

Professional issue log for the Delhi AQI / GRAP repository, as of **2026-07-11**
(start of Phase 2 prep). IDs are stable. Status ∈ {OPEN, IN PROGRESS, RESOLVED}.
Nothing here asserts an analytical finding — these are engineering/data-quality
items and documented assumptions.

Legend: **C** critical · **M** medium · **L** low.

---

## Critical

### C-1 · GRAP calendar is a first batch, not complete · OPEN
Only **5 verified events** are loaded, all in season **2022-23** (E001–E005,
invoke → Stage IV → de-escalate to III on 2022-11-06). There is **no
end-of-season revocation** entered and **no 2023-24 event at all**.
- Impact: `daily_grap_state` trails **Stage III to season end** (2023-02-28) as a
  data artifact; event analysis currently rests on one season / five events; any
  2023-24 GRAP analysis is impossible until events are entered.
- Action: enter remaining 2022-23 events (incl. the closing revocation) and the
  2023-24 season from official CAQM orders, per the data contract; re-validate;
  reload. **Do not** invent or recall events.

### C-2 · Season 2023-24 is truncated at the data boundary · OPEN
Data spans **2022-01-01 … 2023-12-31**; the 2023-24 GRAP season (Oct 1 → Feb 29)
is missing **Jan–Feb 2024**.
- Impact: full-season season-over-season comparison is biased; late-season 2023-24
  event windows would spill past the data edge.
- Action: either acquire Jan–Feb 2024 daily files (would extend scope) or keep the
  Oct–Dec like-for-like restriction already coded in `11_seasonal_comparison.sql`
  and label 2023-24 as partial everywhere. Decision to be recorded in `project_log.md`.

### C-3 · README is stale about GRAP status · IN PROGRESS
`README.md` still says the GRAP file "exists but is empty (headers only)". It now
holds 5 verified events, and the README omits the SQL layer / warehouse build.
- Impact: a reader is misinformed about project state on first contact.
- Action: correct the "Current status" section and add the `src/05_load_sqlite.py`
  build step. (Being addressed as part of this prep.)

---

## Medium

### M-1 · Station coordinates missing · OPEN
`stations.latitude/longitude` are blank/NULL (never verified).
- Impact: no map visuals in Power BI; no spatial (edge-vs-central) analysis.
- Action: source verified coordinates for the 8 DPCC stations, fill `stations.csv`,
  reload. Until then, `geographic_role` is the only spatial handle.

### M-2 · Event windows overlap · OPEN
E001–E005 are only 3–14 days apart, so ±7-day before/after windows straddle
neighbouring events (`08_before_after.sql`, `06_event_window.sql`).
- Impact: a "before" window can contain another event; before/after deltas are
  contaminated and must not be read as clean effects.
- Action: caveat on every event figure; consider shorter windows or restricting to
  events with clean neighbourhoods once more events exist.

### M-3 · Units / aggregation method unconfirmed · OPEN
`docs/data_dictionary.md` marks units **(verify)**; CPCB's daily aggregation
method (mean of sub-daily?) is assumed, not confirmed.
- Impact: axis labels and any standard-threshold comparison depend on it.
- Action: confirm against official CPCB metadata before publishing figures.

### M-4 · Residual missingness in a few station-years · OPEN (accepted)
JLN Stadium 2023 PM10 ≈ 13% missing; several station-years ≈ 1.6–2.7% PM2.5
missing (see `reports/data_quality/core_variable_missingness.csv`).
- Impact: thin months can distort means.
- Action: no imputation (by policy); surface via `15_data_coverage_matrix.sql` and
  the guarded DAX measures; exclude/annotate low-coverage cells in the report.

### M-5 · No distributional stats in the SQL layer · OPEN (by design)
SQLite has no MEDIAN/STDDEV/percentile.
- Impact: SQL gives means only; medians/IQR/p90 must come from Python.
- Action: cover in EDA step 5.1; documented in `docs/sql_layer_design.md`.

---

## Low

### L-1 · `project_log.md` structure is messy · OPEN
The log mixes an initial header block with session notes and a duplicated title.
- Impact: cosmetic; slightly harder to skim.
- Action: tidy into dated sections during the Phase-2 doc pass (7.2).

### L-2 · `source_file` is partially redundant · OPEN (accepted)
`station_daily.source_file` is derivable from `station_id`+`year`.
- Impact: negligible; kept intentionally for provenance/auditability.
- Action: none.

### L-3 · AQI intentionally excluded · OPEN (scope)
Documented scope decision; noted so it is not mistaken for an omission.
- Action: none this phase.

---

## Future improvements

- **F-1** Populate the full GRAP calendar (both seasons, all transitions incl.
  revocations) — unblocks C-1/C-2.
- **F-2** Add verified station coordinates → maps + spatial analysis (M-1).
- **F-3** Add control/placebo windows (non-event periods) to benchmark event-study
  deltas.
- **F-4** Broaden scope later: more stations, more winters, possibly hourly data
  for finer event timing (explicit scope change, new gate).
- **F-5** Formalise the weather-adjustment model (spec, diagnostics, sensitivity).
- **F-6** Add CI (run `pytest` + a headless warehouse build) on push.

## Technical debt

- **TD-1** `src/05_load_sqlite.py` imports the validator via path-based import
  because the module filename starts with a digit (same pattern as the test).
  Works and is tested, but is a smell; a `grap_validator.py` re-export could
  clean it up.
- **TD-2** GRAP CSV path is defined both in `src/config.py` (new) and inside
  `src/04_validate_grap_events.py` (self-contained constant). Keep in sync or
  consolidate.
- **TD-3** No CI yet; correctness relies on running tests locally.
- **TD-4** `event_windows` half-window (±30) is hard-coded in the view; changing
  it means editing DDL. Acceptable given downstream `rel_day` filtering.

## Known assumptions (documented, not defects)

- **A-1** `station_daily` grain is complete (every station has all 730 days) —
  verified in Phase 1; the rolling-average queries depend on it.
- **A-2** ROWS-based window frames equal calendar-day frames (follows from A-1).
- **A-3** GRAP season = Oct 1 → Feb 28/29; events attributed to the season they
  fall in (matches the validator's allowed seasons).
- **A-4** Active stage on day D = `stage_to` of the latest event ≤ D within the
  same season; a stage persists until the next event. No inter-season carryover.
- **A-5** de-escalation/revocation semantics follow `grap_event_data_contract.md`
  (revoking a higher stage may leave a lower stage active).

## Known limitations (carry into every report)

- **LIM-1** Descriptive, **not causal** — no claim GRAP caused any change.
- **LIM-2** Weather adjustment is **partial**; weather is not fully controlled.
- **LIM-3** One monitoring station does **not** represent a ward/district.
- **LIM-4** Scope is 8 DPCC stations × 2 calendar years; not all of Delhi-NCR.
- **LIM-5** Event evidence is currently **5 events in one season**.
- **LIM-6** **AQI is not used** this phase; PM2.5 is the primary outcome.
- **LIM-7** Units/aggregation **(verify)** pending CPCB metadata confirmation (M-3).
