# Delhi Air Quality Under GRAP
### A Weather-Adjusted Analysis of Pollution Patterns Around Policy Escalations

## Central question

How did Delhi's air-pollution patterns change around GRAP (Graded Response
Action Plan) escalations after accounting for observable weather conditions, and
where were improvements weakest?

## Methodological position — this is NOT a causal-inference project

This project does **not** claim, and will not claim, that:

- GRAP *caused* pollution to decrease
- GRAP *succeeded* or *failed*
- weak improvement *proves* weak enforcement
- weather has been *fully* controlled
- one monitoring station represents an entire district or ward

It is a transparent, reproducible descriptive analysis:
real CPCB station data → cleaning & validation → SQL analytical model → GRAP
event-window analysis → *partial* weather adjustment → station/episode comparison
→ Power BI decision-oriented visualisation.

## Current scope

- 8 CPCB (DPCC-operated) monitoring stations in Delhi
- 2 calendar years: **2022** and **2023** (daily `1D` data)
- Primary outcome: **PM2.5**; secondary: PM10 and core weather variables
- AQI is not used in this phase

## Selected stations (locked before outcome analysis)

| station_id | station | geographic role |
|---|---|---|
| `narela` | Narela | northern edge |
| `bawana` | Bawana | outer north-west |
| `anand_vihar` | Anand Vihar | east |
| `punjabi_bagh` | Punjabi Bagh | west |
| `r_k_puram` | R K Puram | south |
| `okhla_phase_2` | Okhla Phase-2 | south-east |
| `najafgarh` | Najafgarh | south-west edge |
| `jawaharlal_nehru_stadium` | Jawaharlal Nehru Stadium | central |

*Alipur was excluded because its 2023 wind-speed field was missing for all 365 days.*

## Data source

Central Pollution Control Board (CPCB) daily station data, downloaded as 16
untouched CSV files (8 stations × 2 years) under `data/raw/cpcb/`. Each raw file
has 365 daily rows and an identical 25-column schema. Raw files are **never
modified** by this pipeline.

## Repository structure

```
delhi-aqi-grap/
├── data/
│   ├── raw/cpcb/           # 16 untouched CPCB CSVs (+ station list PDF)
│   ├── raw/grap/           # grap_events_manual.csv (human-entered; verified events)
│   ├── raw/weather/        # (future) supplementary weather data
│   └── processed/          # station_daily.csv, stations.csv, daily_grap_state.csv,
│       │                   # station_daily_grap.csv, delhi_aqi_grap.db (derived)
├── src/
│   ├── config.py                      # paths, station registry, column maps
│   ├── 01_inventory_raw_data.py       # raw-file inventory
│   ├── 02_audit_data_quality.py       # data-quality audit
│   ├── 03_build_station_daily.py      # canonical dataset + metadata
│   ├── 04_validate_grap_events.py     # validate the manual GRAP event calendar
│   ├── 05_load_sqlite.py              # build the SQLite warehouse (derived, disposable)
│   ├── 06_build_daily_grap_state.py   # build daily GRAP state table
│   ├── 07_validate_daily_grap_state.py# validate daily state continuity
│   ├── 08_merge_station_daily_grap.py # merge station data with GRAP state
│   └── 09_validate_merged_dataset.py  # validate merged dataset integrity
├── tests/                 # pytest checks on the processed dataset + GRAP validator
├── reports/data_quality/  # generated audit reports (data_quality_summary.md,
│                           # grap_daily_validation.md, merged_dataset_validation.md)
├── sql/                   # schema + 15 prepared analytical queries (sql/README.md)
├── notebooks/ powerbi/ figures/ docs/
├── requirements.txt
└── README.md
```

## How to reproduce (Phases 1 & 2)

```bash
python -m pip install -r requirements.txt

# Phase 1: Data engineering & validation
python src/01_inventory_raw_data.py          # inventory raw files
python src/02_audit_data_quality.py          # data-quality audit (writes reports/)
python src/03_build_station_daily.py         # build canonical dataset

# Tests
python -m pytest -q

# GRAP event calendar — validate the manual source file
python src/04_validate_grap_events.py

# Phase 2A: Build SQLite warehouse (derived, disposable; rebuild any time)
python src/05_load_sqlite.py

# Phase 2B: Analytical dataset construction
python src/06_build_daily_grap_state.py       # daily GRAP state table (730 rows)
python src/07_validate_daily_grap_state.py    # validate continuity & transitions
python src/08_merge_station_daily_grap.py     # merge station data + GRAP state (5840 rows)
python src/09_validate_merged_dataset.py      # validate merged dataset integrity
```

The final analytical dataset is `data/processed/station_daily_grap.csv` (5,840 rows, all validations passed).

## Current status

**Phase 1 complete. Phase 2 analytical dataset construction complete. Phase 2 EDA not yet started — no analytical findings exist yet.**

### Phase 1 — Data engineering & validation

- All 16 expected station-year files present; schema consistent; date coverage complete (365/yr); no duplicate dates; no impossible values.
- **Gate 1: PASS** (independently re-validated from raw files).
- Canonical `data/processed/station_daily.csv` built: 5,840 station-days (8 stations × 730 days), core 6 variables + date, full provenance.

### Phase 2A — GRAP event calendar (human-entered, verified)

This project's rule: **every GRAP event must be entered by a human from an official CAQM order** — no scraping, no web search, no memory.

- Source file: `data/raw/grap/grap_events_manual.csv` — **9 verified events** (E001–E009, season 2022-23).
  - E001–E005: Oct–Nov 2022 (escalation sequence 0→1→2→3→4→3)
  - E006–E009: Nov–Dec 2022 (de-escalations and re-escalations; final state = Stage III)
  - All rows: `verified = Yes`, 0 contract errors.
- Validator: `python src/04_validate_grap_events.py` — reports 9 analysis-ready events, 0 errors.
- **Only rows with `verified = Yes` (and no errors) may enter analysis.**
- **Known limitation**: No end-of-season revocation yet entered for 2022-23. Stage III remains active through 2023-02-28. Season 2023-24 has zero events (data ends 2023-12-31).

### Phase 2B — Analytical dataset construction (completed)

- **Daily GRAP state table** (`data/processed/daily_grap_state.csv`):
  - 730 rows (2022-01-01 to 2023-12-31), one per calendar date.
  - Fields: date, grap_stage, season, active_event_id, is_event_day, days_since_last_change, days_until_next_change.
  - Validation: 6 checks passed (no duplicates, no gaps, correct chronology, event-date correctness, stage continuity).
  
- **Merged analytical dataset** (`data/processed/station_daily_grap.csv`):
  - 5,840 rows (8 stations × 730 days), grain = station × date.
  - Joins: station_daily + daily_grap_state.
  - Fields: all 10 measurement variables + season + 5 GRAP state fields.
  - Validation: 8 checks passed (expected row count, 8 stations, no duplicates, no merge failures, complete date coverage, correct GRAP stage assignment).
  - **Ready for EDA**: dataset is structurally sound, fully validated.

### Phase 2C — SQL analytical layer

- `sql/00_schema.sql` — SQLite schema: 3 base tables (`stations`, `station_daily`, `grap_events`) + 4 derived views (`v_calendar`, `daily_grap_state`, `v_station_daily_enriched`, `event_windows`). No redundant storage — see `docs/sql_layer_design.md`.
- `src/05_load_sqlite.py` — builds `data/processed/delhi_aqi_grap.db` from validated CSVs; refuses to load if GRAP file has errors. Rebuild with: `python src/05_load_sqlite.py`.
- `sql/01`–`15_*.sql` — 15 prepared, documented analytical queries. See `sql/README.md`.
- Power BI data model designed (not yet built): `docs/powerbi_data_model.md`.

### What's next — Phase 2 Analysis

**EDA has not yet started. No analytical findings, comparisons, or conclusions have been drawn.**

- Rebuild SQLite warehouse with new GRAP events: `python src/05_load_sqlite.py` (now loads 9 events instead of 5).
- Reference: `docs/phase2_analysis_checklist.md` for ordered task list.
- Open issues tracked in `docs/issue_tracker.md` and `docs/project_status_report.md`.

### Data documentation

- `docs/data_dictionary.md` — processed dataset field definitions
- `docs/grap_event_data_contract.md` — GRAP event schema & validation rules
- `reports/data_quality/data_quality_summary.md` — Phase 1 audit summary
- `reports/data_quality/grap_daily_validation.md` — daily state table validation
- `reports/data_quality/merged_dataset_validation.md` — merged dataset validation
