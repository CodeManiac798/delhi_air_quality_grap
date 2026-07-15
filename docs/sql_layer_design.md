# SQL Layer Design (Phase B)

Design of the SQLite analytical model for the Delhi AQI / GRAP project. This
document is the *specification*; `sql/00_schema.sql` is the *implementation*.
It describes what exists and why — it does not run or interpret any analysis.

## Objectives

Support, with **no redundant storage**:

- rolling averages (window frames),
- window functions (rank, lead/lag, running state),
- GRAP event studies (per-event before/after and day-relative panels),
- station comparisons (station × stage, station × season),
- a clean star-ish model for Power BI.

## Storage strategy: 3 base tables, everything else a view

| Object | Kind | Grain | Why |
|---|---|---|---|
| `stations` | base table | 1 row / station | Dimension. Small, stable. |
| `station_daily` | base table | 1 row / station / day | The fact. Loaded verbatim from the processed CSV. |
| `grap_events` | base table | 1 row / verified event | The policy event calendar. Only `verified=Yes` rows. |
| `v_calendar` | view | 1 row / date | Date dimension derived from the dates present in the fact. |
| `daily_grap_state` | view | 1 row / in-season date | Derived active-stage step function. |
| `v_station_daily_enriched` | view | 1 row / station / day | Fact + station + calendar + active stage. BI feed. |
| `event_windows` | view | 1 row / event / station / day (±30d) | Event-study panel. |

**Why views for `daily_grap_state` and `event_windows`?** Both are *pure
functions* of the three base tables. Materialising them would create a second
copy of the truth that can silently drift when events are added. As views they
are always consistent by construction, and the datasets are tiny (243 and 2,440
rows), so there is no performance reason to materialise. If Power BI import mode
needs snapshots, materialise them **at load time** from these view definitions
rather than hand-maintaining them.

## Tables, keys, indexes

### `stations` (dimension)
- **PK:** `station_id` (slug).
- Columns: `station_name, display_name, operating_agency, geographic_role,
  selected, selection_reason, latitude, longitude`.
- `latitude`/`longitude` are `NULL` until coordinates are verified.

### `station_daily` (fact)
- **PK:** `(station_id, date)` — enforces the one-station-one-day grain.
- **FK:** `station_id → stations.station_id`.
- **Indexes:** `ix_station_daily_date` (cross-station date-range scans for event
  windows / daily-state joins), `ix_station_daily_station_year` (per-station-year
  aggregations).
- Measures: `pm25_ugm3` (primary), `pm10_ugm3`, `air_temp_c`, `rh_pct`,
  `wind_speed_ms`, `wind_dir_deg`. `NULL` = missing (never imputed).

### `grap_events` (event calendar)
- **PK:** `event_id`.
- **Indexes:** `ix_grap_events_effective` (anchor lookups),
  `ix_grap_events_season` (`season, effective_date` for the per-season step
  function).
- Analytical anchor is `effective_date`, per the data contract.

## Relationships

```
stations (1) ───< (many) station_daily
station_daily >──── v_calendar (on date)         [date dimension join]
grap_events  ──> daily_grap_state (per-season step function over v_calendar)
station_daily + daily_grap_state ──> v_station_daily_enriched
grap_events (1) ───< (many) event_windows >─── station_daily
```

`grap_events` has **no hard FK** to a date/station — it is Delhi-NCR-wide policy,
attached to `station_daily` through `effective_date` (event windows) and through
the derived `daily_grap_state` (which day carries which stage), not through a key.

## Derived logic

### `v_calendar`
Adds `year, month, year_month, day, dow, grap_season, is_grap_season`.
Season boundaries: `2022-23` = 2022-10-01 … 2023-02-28; `2023-24` = 2023-10-01 …
2024-02-29. **Data ends 2023-12-31, so 2023-24 is truncated** — encoded here once
so every downstream query inherits the correct season attribution.

### `daily_grap_state`
For each in-season date `D`:
`active_stage = stage_to of the latest event with effective_date ≤ D in the same
season, else 0`. Scoped per season so a prior season's stage cannot leak forward.
Expressed as a correlated subquery (portable; the table is tiny).

### `event_windows`
Cross-join of `grap_events` × `station_daily` where `|date − effective_date| ≤ 30`
days, exposing `rel_day` (signed offset, 0 = event day) and a `before/event_day/
after` bucket. Half-window is 30; narrow downstream (e.g. `rel_day BETWEEN -7 AND
7`). Windows may overlap adjacent events and may hit the data boundary — the
event queries flag this.

## Supporting the required capabilities

| Requirement | How the model supports it |
|---|---|
| Rolling averages | Complete daily grain ⇒ `ROWS BETWEEN n PRECEDING` = calendar days (`10_rolling_pm25.sql`). |
| Window functions | `RANK` (04), `LEAD` (12), windowed `AVG/COUNT` (10). |
| Event studies | `event_windows` view + queries 06 (day-relative) and 08 (before/after). |
| Station comparisons | `v_station_daily_enriched` groups by station × stage (07) / season (11). |
| Power BI | `v_station_daily_enriched` as the fact; `stations`, `v_calendar`, `daily_grap_state`, `grap_events` as dimensions. The dashboard actually built (`powerbi/`) sources from the processed CSVs directly rather than this SQL layer — see `docs/powerbi_architecture.md`. |
| No redundancy | Only 3 base tables; all state/windows are views. |

## Deliberate non-goals (SQLite limitations, handled elsewhere)

- **No median / stddev / percentiles in SQL** — SQLite lacks them. Distributional
  stats belong in the pandas EDA step; the SQL layer uses means, min/max, and
  robust threshold counts (`14_extreme_days.sql`) instead.
- **No imputation** — missingness is surfaced (02, 15), never filled.
- **No weather adjustment in SQL** — the SQL layer *describes* weather by stage
  (09) to motivate adjustment; the modelling itself is a Python step.
