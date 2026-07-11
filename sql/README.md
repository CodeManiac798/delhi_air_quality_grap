# SQL layer

The analytical SQL layer for the Delhi AQI / GRAP project. It turns the
validated Phase-1 CSVs into a small SQLite warehouse and ships the queries the
project should eventually answer. **Nothing here performs or concludes analysis
— it is the machinery that tomorrow's analysis runs on.**

## Files

| File | What it is |
|---|---|
| `00_schema.sql` | DDL: 3 base tables + keys/indexes, then the derived views (`v_calendar`, `daily_grap_state`, `v_station_daily_enriched`, `event_windows`). |
| `01`–`15_*.sql` | 15 prepared analytical queries. Each has a header comment: business question, purpose, expected output, dependencies, caveats. **Read the caveats.** |

Design rationale (grain, keys, relationships, why views not tables) is in
[`../docs/sql_layer_design.md`](../docs/sql_layer_design.md).

## Build the warehouse

The warehouse `data/processed/delhi_aqi_grap.db` is a **derived, disposable**
artifact (git-ignored). Rebuild it any time:

```bash
python src/05_load_sqlite.py
```

This applies `00_schema.sql`, loads `stations` and `station_daily` (NaN → NULL),
and loads **only the `verified=Yes` GRAP events** — after re-running the Phase-1
contract validator and refusing to load if there is any ERROR. Expected output:

```
stations         : 8
station_daily    : 5840 (expected 5840)
grap_events      : 5 loaded (of 5 rows in file; verified only)
daily_grap_state : 243 in-season date-rows (view)
event_windows    : 2440 rows (view, +/-30 days x stations)
```

### Pure-SQLite alternative (no Python)

If you prefer the `sqlite3` CLI, load via staging tables so blank cells become
`NULL` rather than empty strings (this matters — empty strings break `AVG` on
`REAL` columns):

```sql
.mode csv
.import data/processed/stations.csv       stg_stations
.import data/processed/station_daily.csv  stg_station_daily
-- then: INSERT INTO station_daily SELECT ... NULLIF(pm25_ugm3,'') ... FROM stg_station_daily;
```

The Python loader is the recommended path because it also enforces the GRAP
contract gate. (`.import` would happily load unverified or malformed events.)

## Run a query

```bash
sqlite3 data/processed/delhi_aqi_grap.db < sql/01_station_summary.sql
# or interactively:  sqlite3 data/processed/delhi_aqi_grap.db  then  .read sql/05_stage_summary.sql
```

## Dependency order

```
stations ─┐
          ├─> station_daily ─┬─> v_calendar ─> daily_grap_state ─> v_station_daily_enriched
grap_events ─────────────────┴─> event_windows
```

Every query depends only on the base tables and/or these four views, so the
build order above is the only prerequisite. Load the data before running the
views (they are lazy, so creating them first is fine).

## Known data-shape facts the queries rely on

- `station_daily` has a row for **every** station-day (8 × 730 = 5,840), so
  ROWS-based window frames equal calendar-day frames (`10_rolling_pm25.sql`).
- The data spans **2022-01-01 … 2023-12-31**. Season **2023-24 is truncated** at
  2023-12-31 (no Jan/Feb 2024). Queries 04/11/12 handle this explicitly.
- Only **5 verified GRAP events** are loaded (season 2022-23, E001–E005). The
  season has no end-of-season revocation entered yet, so the derived state trails
  Stage III to season end — a completeness gap, not a finding.
