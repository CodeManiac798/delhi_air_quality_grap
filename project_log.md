# Project Log

## 2026-07-10
- Initialized project folder structure.
# Delhi Air Quality Under GRAP

## Central Question

How did Delhi's air-pollution patterns change around GRAP escalations after accounting for observable weather conditions, and where were improvements weakest?

## Current Proposed Scope

Time:
- October 2022 to February 2023
- October 2023 to February 2024

Grain:
- One monitoring station per day

Pollution:
- AQI
- PM2.5

Weather:
- Wind speed
- Temperature

Policy:
- GRAP stage escalation and de-escalation dates

## Claims I Will NOT Make

- GRAP caused pollution to decrease.
- GRAP succeeded or failed.
- Weak improvement proves weak enforcement.
- Weather has been fully controlled.
- One monitoring station represents an entire district or ward.

## Session 1 Goal

Test whether the proposed data sources and acquisition process actually work before committing to the full project.

## Station List Inspection

Downloaded successfully: Yes

Source: Official CPCB Delhi-NCR CAAQMS station list

Available fields:
- Serial number
- Station name
- Operating agency

Coordinates available: No
Opening date available: No
Official station type available: No
Active/inactive status available: Not clearly shown

Observation:
The official PDF is useful for verifying station names and operating agencies,
but it is insufficient for selecting the final eight stations by operating
history, coordinates, or station type. Those fields will require another source.

## CPCB Data Repository Test

Station: Anand Vihar, Delhi - DPCC
Year: 2023
Frequency selected: 24H
Actual file grain: One row per calendar day

Rows: 365
Columns: 25
Date coverage: 2023-01-01 to 2023-12-31
Duplicate dates: 0

Core variables confirmed:
- PM2.5
- PM10
- Air Temperature
- Relative Humidity
- Wind Speed
- Wind Direction

AQI included: No

Core missing values:
- PM2.5: 10 days
- PM10: 13 days
- Air Temperature: 10 days
- Relative Humidity: 10 days
- Wind Speed: 10 days
- Wind Direction: 10 days

Major finding:
The CPCB daily station file already contains local meteorological variables.
A separate weather dataset may therefore be unnecessary.

Decision:
Do not add an external weather source until station-level CPCB weather coverage
has been checked across the final station sample.

## CPCB Cross-Station Schema Test

Second station: Bawana, Delhi - DPCC
Year: 2023
Rows: 365
Columns: 25

Schema consistent with Anand Vihar: Yes

Core missing values:
- PM2.5: 10 days
- PM10: 8 days
- Air Temperature: 6 days
- Relative Humidity: 6 days
- Wind Speed: 6 days
- Wind Direction: 6 days

Conclusion:
The daily CPCB repository structure is consistent across the two tested stations.
Both pollution and local meteorological variables are available in the same file.
External weather data is not currently required.

## Eight-Station Data Quality Audit

All files:
- 365 daily rows
- 25-column schema
- Zero duplicate dates

Result:
Seven of eight proposed stations passed the core data-quality screen.

Failed station:
Alipur

Reason:
Wind Speed is missing for all 365 days in the 2023 daily file.

Decision:
Exclude Alipur before outcome analysis.
Test Narela as the geographically similar replacement candidate.

Important:
The exclusion is based only on missingness in a pre-declared core weather variable,
not on the station's pollution levels or analytical results.

## Gate 1 — Data Acquired: PASSED

Dataset:
- 8 pre-selected Delhi monitoring stations
- 2 complete calendar years: 2022 and 2023
- 16 raw CPCB daily files
- 5,840 potential station-day observations

Validation:
- 365 rows per file
- 25 columns per file
- Identical schema across all 16 files
- Complete Jan 1–Dec 31 date coverage
- Zero duplicate dates

Core variables confirmed:
- PM2.5
- PM10
- Air Temperature
- Relative Humidity
- Wind Speed
- Wind Direction

Decision:
The pollution and station-level weather dataset is sufficient to proceed.

Important limitation:
JLN Stadium has elevated PM10 missingness in 2023, but PM2.5 remains sufficiently complete and is the primary outcome.

Gate 1 Status: PASSED

## Phase 1 — Data-Engineering Pipeline (2026-07-10)

Independent re-validation of the raw files and construction of the canonical
dataset. Raw files under data/raw/cpcb/ were not modified.

Environment:
- requirements.txt (pandas, numpy, pytest only — no ML/viz yet)
- .gitignore (Python cache, venvs, Office lock files; raw/processed data kept)
- src/config.py — paths, locked 8-station registry, filename parser, column maps

Raw-vintage differences found and handled by the loaders:
- Line endings: 2023 CRLF, 2022 LF (schema names byte-identical)
- Timestamp format: 2023 "YYYY-MM-DD", 2022 "YYYY-MM-DD HH:MM:SS"
- Missing token: 2023 blank, 2022 "NA"

Scripts (each run and verified):
- src/01_inventory_raw_data.py -> reports/data_quality/raw_file_inventory.csv
  16/16 structural pass, 1 schema signature, all 8x2 station-years present.
- src/02_audit_data_quality.py -> core_variable_missingness.csv,
  data_quality_flags.csv, data_quality_summary.md.
  Gate 1: PASS (re-confirmed). 0 impossible-value flags.
- src/03_build_station_daily.py -> data/processed/station_daily.csv
  (5,840 station-days; core 6 vars + date + source_file provenance) and
  data/processed/stations.csv (8 stations; lat/lon blank pending verification).

Tests:
- tests/test_station_daily.py — 9 pytest checks, all passing.

Decisions locked this session:
- station_id = slug; processed keeps core 6 + date only; coordinates deferred.

Docs:
- README.md and docs/data_dictionary.md updated with current facts only.

Not started: GRAP event windows, weather adjustment, SQL model, Power BI.
No analytical findings exist yet.

## Phase 2 — Preparation (2026-07-11)

GRAP event calendar now holds a **first batch of 5 human-verified events**
(E001–E005, season 2022-23 only, all `verified = Yes`, 0 contract errors) —
README was stale saying it was empty; corrected. No new events were entered or
invented this session; existing data was inspected only.

Built the complete Phase-2 SQL + BI scaffolding (no analysis performed):

- `src/config.py` — added SQL_DIR/SQLITE_DB/GRAP_EVENTS_CSV paths.
- `sql/00_schema.sql` — 3 base tables (stations, station_daily, grap_events) +
  4 derived views (v_calendar, daily_grap_state, v_station_daily_enriched,
  event_windows). No materialised redundancy by design.
- `src/05_load_sqlite.py` — builds data/processed/delhi_aqi_grap.db from the
  validated CSVs; re-runs the GRAP contract validator and refuses to load on
  any ERROR; loads only verified=Yes events. Verified: 8 stations, 5840
  station-days, 5 events loaded, 243 in-season date-rows, 2440 event-window
  rows — all reconcile.
- `sql/01`-`15_*.sql` — 15 documented analytical queries; every one smoke-tested
  against the built warehouse and confirmed to execute cleanly.
- `docs/sql_layer_design.md` — schema design rationale.
- `docs/powerbi_data_model.md` — star schema, relationships, DAX measures,
  hierarchies (design only, no .pbix built).
- `docs/phase2_analysis_checklist.md` — ordered Phase-2 task list with
  purpose/input/output/success-criteria per step.
- `docs/issue_tracker.md` — critical/medium/low issues, tech debt, assumptions,
  limitations (critical: GRAP calendar incomplete; 2023-24 season truncated at
  2023-12-31).
- `docs/project_status_report.md` — completion %, risks, hour estimate
  (32-40h), likely interview questions.
- `.gitignore` — added data/processed/*.db (derived, disposable warehouse).
- README.md — corrected GRAP status, documented SQL layer and warehouse build
  step.

Decisions locked this session:
- Warehouse is a derived artifact (git-ignored), always rebuilt from CSVs —
  never a second source of truth.
- daily_grap_state / event_windows are VIEWS, not tables, so derived state can
  never drift from the loaded events.
- Season 2023-24 is explicitly treated as truncated (data ends 2023-12-31);
  seasonal comparisons restrict to the Oct-Dec window both seasons share.

Not started: EDA, event-window analysis, weather adjustment, Power BI build,
report writing. No analytical findings exist yet.