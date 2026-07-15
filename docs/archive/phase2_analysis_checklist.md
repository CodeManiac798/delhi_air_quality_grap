> **Archived.** A forward-looking task checklist written before Phase 2 began.
> Every item below has since been completed — see the
> [notebooks](../../notebooks/) and [root README](../../README.md) for the
> finished work. Kept for planning-process history only.

# Phase 2 Analysis Checklist

The exact order to work tomorrow. Each task lists **Purpose · Input · Output ·
Success criteria**. Do them top to bottom; later steps assume earlier outputs
exist. Nothing here changes Phase-1 methodology, raw data, or the station
selection. Check a box only when its success criteria are met.

> Ground rules that apply to every step: no imputation of the 6 core variables;
> no causal language; report completeness beside every number; keep 2023-24
> treated as truncated (ends 2023-12-31).

---

## 0. Environment & warehouse build

- [ ] **0.1 Rebuild the SQLite warehouse**
  - Purpose: get a clean analytical DB from validated inputs.
  - Input: `data/processed/*.csv`, `data/raw/grap/grap_events_manual.csv`, `sql/00_schema.sql`.
  - Output: `data/processed/delhi_aqi_grap.db`.
  - Success: `python src/05_load_sqlite.py` prints 8 / 5840 / 5 loaded and exits 0.
- [ ] **0.2 Re-run the Phase-1 gates**
  - Purpose: confirm the foundation still passes before building on it.
  - Input: pipeline scripts + tests.
  - Output: green `pytest`; `04_validate_grap_events.py` exits 0.
  - Success: `python -m pytest -q` all pass; GRAP validator reports 5 analysis-ready events, 0 errors.

## 1. Exploratory Data Analysis (Python / notebook)

- [ ] **1.1 Distribution & shape of PM2.5 (and PM10)**
  - Purpose: understand skew, spikes, plausible ranges before modelling.
  - Input: `station_daily.csv`.
  - Output: histograms / boxplots per station; a short notes cell.
  - Success: distributions described (heavy right tail expected); no value looks impossible beyond the Phase-1 flags (which were zero).
- [ ] **1.2 Missingness & coverage map**
  - Purpose: know which station-months can carry weight.
  - Input: `02_missingness.sql`, `15_data_coverage_matrix.sql`.
  - Output: coverage heatmap (station × month).
  - Success: every downstream chart can be checked against this map; JLN 2023 PM10 (~13%) and any <50% cells flagged.
- [ ] **1.3 Seasonality view**
  - Purpose: confirm winter is the pollution/GRAP season.
  - Input: `03_monthly_pm25.sql`.
  - Output: monthly PM2.5 line per station.
  - Success: visible Oct–Jan peak; GRAP season aligns with peaks.

## 2. SQL analytical pass

- [ ] **2.1 Run the descriptive queries 01, 04, 05, 07, 09**
  - Purpose: station profiles, rankings, stage/weather summaries.
  - Input: the warehouse + those SQL files.
  - Output: result tables saved (CSV) for the report.
  - Success: all run clean; row counts match the header comments; caveats copied into notes.
- [ ] **2.2 Build the daily state panel & validate the step function**
  - Purpose: confirm active-stage timeline matches E001–E005 exactly.
  - Input: `13_daily_state_panel.sql`, `12_stage_transitions.sql`.
  - Output: state timeline table/plot.
  - Success: transitions occur only on effective dates (0→1 05-Oct, …, 4→3 06-Nov) and the trailing Stage-III-to-season-end gap is explicitly noted.

## 3. Event windows / event study

- [ ] **3.1 Day-relative panels per event**
  - Purpose: see PM2.5 trajectory around each change.
  - Input: `06_event_window.sql`.
  - Output: one event-study line per event (x = rel_day −14…+14).
  - Success: each event plotted with `event_direction` labelled and overlapping-window caveat stated.
- [ ] **3.2 Before/after deltas**
  - Purpose: compact per-event, per-station Δ table.
  - Input: `08_before_after.sql`.
  - Output: delta table + diverging bar chart.
  - Success: deltas computed for all 5 events × 8 stations; “raw, not weather-adjusted, windows overlap” stated on the figure.

## 4. Weather adjustment (Python)

- [ ] **4.1 Quantify weather–stage confounding**
  - Purpose: show weather differs across stages (justifies adjustment).
  - Input: `09_weather_summary.sql`.
  - Output: wind/temp/RH by stage table.
  - Success: direction and size of weather differences documented.
- [ ] **4.2 Fit the partial weather adjustment**
  - Purpose: describe PM2.5 net of observable weather (wind, temp, RH; consider wind-direction).
  - Input: `station_daily` (join weather + PM2.5), model spec agreed first.
  - Output: adjusted PM2.5 / residual series per station-day; model diagnostics.
  - Success: model documented (form, variables, R², residual checks); output labelled **partial** adjustment; no claim weather is fully controlled.
- [ ] **4.3 Re-express event before/after on adjusted values**
  - Purpose: before/after that is less weather-confounded.
  - Input: adjusted series + `event_windows` logic.
  - Output: adjusted Δ table beside the raw one.
  - Success: raw vs adjusted shown side by side; differences discussed, not overclaimed.

## 5. Summary statistics & station comparison

- [ ] **5.1 Distributional stats in Python** (median, IQR, p90/p95)
  - Purpose: the stats SQLite can’t do.
  - Input: `station_daily.csv`.
  - Output: per-station / per-stage summary table.
  - Success: medians & percentiles reported alongside the SQL means.
- [ ] **5.2 “Where were improvements weakest?”**
  - Purpose: the central comparative question.
  - Input: `07_station_vs_stage.sql`, `11_seasonal_comparison.sql`, adjusted deltas.
  - Output: ranked station comparison with caveats.
  - Success: statement is comparative and hedged (weak ≠ enforcement failure), tied to coverage.

## 6. Power BI

- [ ] **6.1 Load model** per `docs/powerbi_data_model.md`
  - Input: warehouse views / CSVs.
  - Output: `.pbix` with fact + dims + relationships + `DimStage`.
  - Success: relationships single-direction, `DimDate` marked as date table, `DimStage` sorted; no ambiguous-relationship warnings.
- [ ] **6.2 Core measures**
  - Input: DAX from the model doc.
  - Output: measures created (Avg PM2.5, coverage %, rolling 7d, before/after, rank).
  - Success: a coverage % or guarded measure accompanies every headline number.
- [ ] **6.3 Pages** (station overview, seasonality, stage summary, event study)
  - Success: every page carries the relevant caveat caption (truncation / not-adjusted / stage-is-defined-by-AQI).

## 7. Documentation & delivery

- [ ] **7.1 Update README** to Phase-2 status (5 verified events, SQL layer, warehouse build step).
- [ ] **7.2 Update `project_log.md`** with the Phase-2 session decisions.
- [ ] **7.3 Write the analytical report** (methods, results, every limitation from `issue_tracker.md`).
- [ ] **7.4 GitHub hygiene** — commit structure, ensure `.db` is ignored, tests green in a clean clone.
- [ ] **7.5 Portfolio case study** — 1-pager: question → data → method → what can/can’t be said. Lead with the honesty of the caveats; that is the selling point.

---

### Definition of done for Phase 2

Every SQL result reproduced from a clean warehouse build; weather-adjusted
before/after produced beside the raw; Power BI model matches the spec; report and
README updated; all findings stated comparatively and hedged, each paired with a
completeness figure and its limitation.
