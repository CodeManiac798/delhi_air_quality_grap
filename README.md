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
│   ├── raw/grap/           # grap_events_manual.csv (human-entered; not yet populated)
│   ├── raw/weather/        # (future) supplementary weather data
│   └── processed/          # station_daily.csv, stations.csv
├── src/
│   ├── config.py                 # paths, station registry, column maps
│   ├── 01_inventory_raw_data.py  # raw-file inventory
│   ├── 02_audit_data_quality.py  # data-quality audit
│   ├── 03_build_station_daily.py # canonical dataset + metadata
│   ├── 04_validate_grap_events.py# validate the manual GRAP event calendar
│   └── 05_load_sqlite.py         # build the SQLite warehouse (derived, disposable)
├── tests/                 # pytest checks on the processed dataset + GRAP validator
├── reports/data_quality/  # generated audit reports
├── sql/                   # schema + 15 prepared analytical queries (sql/README.md)
├── notebooks/ powerbi/ figures/ docs/
├── requirements.txt
└── README.md
```

## How to reproduce (Phase 1)

```bash
python -m pip install -r requirements.txt

# Phase 2 — inventory the raw files
python src/01_inventory_raw_data.py

# Phase 3 — data-quality audit (writes reports/data_quality/)
python src/02_audit_data_quality.py

# Phase 4/5 — build canonical dataset + station metadata
python src/03_build_station_daily.py

# Tests
python -m pytest -q

# GRAP event calendar — validate the manual source file
python src/04_validate_grap_events.py

# Build the SQLite analytical warehouse (derived, disposable; rebuild any time)
python src/05_load_sqlite.py
```

## Current status

**Phase 1 (data engineering & validation) complete. Phase 2 preparation
(SQL layer, warehouse, analysis checklist) complete. Phase 2 analysis not yet
started — no analytical findings exist yet.**

- All 16 expected station-year files present; schema consistent; date coverage
  complete (365/yr); no duplicate dates; no impossible values detected.
- **Gate 1: PASS** (independently re-validated from the raw files).
- Canonical `data/processed/station_daily.csv` built: 5,840 station-days
  (8 stations × 730 days), core 6 variables + date, full provenance.

### GRAP event calendar — first batch acquired, NOT complete

This project's rule is that **every GRAP event must be entered by a human from
an official CAQM order** — no scraping, no web search, no recall from memory.

- Source file: `data/raw/grap/grap_events_manual.csv` — **5 verified events
  loaded** (E001–E005, season 2022-23: invoke → Stage I → II → III → IV, then
  de-escalate to Stage III on 2022-11-06). All `verified = Yes`, 0 contract errors.
- Schema and rules: `docs/grap_event_data_contract.md` (the data contract).
- Validator: `python src/04_validate_grap_events.py` checks the file against the
  contract and reports errors, review flags, and how many rows are analysis-ready.
- **Only rows with `verified = Yes` (and no errors) may enter analysis.**
- **This is a first batch, not a complete calendar** — season 2022-23 has no
  closing revocation yet, and season 2023-24 has zero events entered. See
  `docs/issue_tracker.md` (C-1, C-2) before drawing any event-based conclusion.

### SQL analytical layer (Phase 2 prep)

- `sql/00_schema.sql` — SQLite schema: 3 base tables (`stations`,
  `station_daily`, `grap_events`) + 4 derived views (`v_calendar`,
  `daily_grap_state`, `v_station_daily_enriched`, `event_windows`). No
  redundant storage — see `docs/sql_layer_design.md`.
- `src/05_load_sqlite.py` — builds `data/processed/delhi_aqi_grap.db` from the
  validated CSVs; refuses to load if the GRAP file has contract errors.
- `sql/01`–`15_*.sql` — 15 prepared, documented queries (station summaries,
  missingness, monthly trends, rankings, stage summaries, event windows,
  before/after, weather summaries, rolling averages, seasonal comparison, stage
  transitions, daily state panel, extreme days, coverage matrix). See
  `sql/README.md`.
- Power BI data model designed (not yet built): `docs/powerbi_data_model.md`.

### What's next

`docs/phase2_analysis_checklist.md` has the exact, ordered task list for Phase 2
(EDA → SQL pass → event windows → weather adjustment → summary stats → Power BI
→ documentation). `docs/issue_tracker.md` and `docs/project_status_report.md`
track open issues, assumptions, limitations, and overall project status.

See `docs/data_dictionary.md` for processed-field definitions,
`docs/grap_event_data_contract.md` for the GRAP event contract, and
`reports/data_quality/data_quality_summary.md` for the audit summary.
