# Merged Dataset Validation Report

**Dataset**: `data/processed/station_daily_grap.csv`

## Overview

| Metric | Value |
|--------|-------|
| Total rows | 5,840 |
| Expected rows | 5,840 (8 stations × 730 days) |
| Unique stations | 8 |
| Date range | 2022-01-01 to 2023-12-31 |
| Unique GRAP stages | [0, 1, 2, 3, 4] |
| In-season rows | 2,416 |
| Off-season rows | 3,424 |
| Event days | 9 |

## Dataset Structure

### Grain
One row per **station × date** combination.

### Columns
- `station_id` — unique identifier (slug format)
- `station_name` — human-readable station name
- `date` — ISO date (YYYY-MM-DD)
- `year` — calendar year (2022 or 2023)
- `pm25_ugm3` — PM2.5 concentration (µg/m³), or NULL if missing
- `pm10_ugm3` — PM10 concentration (µg/m³), or NULL if missing
- `air_temp_c` — air temperature (°C), or NULL if missing
- `rh_pct` — relative humidity (%), or NULL if missing
- `wind_speed_ms` — wind speed (m/s), or NULL if missing
- `wind_dir_deg` — wind direction (degrees), or NULL if missing
- `season` — GRAP season (e.g., "2022-23"), or NULL if off-season
- `grap_stage` — active GRAP stage (0–4)
- `is_event_day` — flag (1 if an event occurred on this date, 0 otherwise)
- `days_since_last_change` — days since last stage transition, or blank if no prior event in season
- `days_until_next_change` — days until next stage transition, or blank if no future event
- `source_file` — provenance (raw CPCB file this observation came from)

## Validation Results

### Passed ✓

- **CHECK 1**: Expected row count (5,840)
- **CHECK 2**: Exactly 8 unique stations
- **CHECK 3**: No duplicate (station_id, date) pairs
- **CHECK 4**: Every station-day has a GRAP stage (no NULL)
- **CHECK 5**: Season assignment correct (3,424 off-season station-days)
- **CHECK 6**: No NULL values in critical merge columns
- **CHECK 7**: No orphan dates (730 consecutive dates covered)
- **CHECK 8**: No NULL GRAP stages before E001 (pre-GRAP dates have stage 0)

### Failed

None.

## GRAP Coverage

| Season | Event Days | Stage Transitions |
|--------|------------|-------------------|
| 2022-23 | 9 (E001–E009) | 0→1→2→3→4→3→2→3→2→3 |
| 2023-24 | 0 | (No events; data ends 2023-12-31) |
| Off-season (Mar–Sep, both years) | 0 | Stage undefined (NULL) |

### Event Timeline (2022-23)

| Event | Date | From | To | Active |
|-------|------|------|----|----|
| E001 | 2022-10-05 | 0 | 1 | Invoke Stage I |
| E002 | 2022-10-19 | 1 | 2 | Escalate to Stage II |
| E003 | 2022-10-29 | 2 | 3 | Escalate to Stage III |
| E004 | 2022-11-03 | 3 | 4 | Escalate to Stage IV |
| E005 | 2022-11-06 | 4 | 3 | De-escalate to Stage III |
| E006 | 2022-11-14 | 3 | 2 | De-escalate to Stage II |
| E007 | 2022-12-04 | 2 | 3 | Escalate to Stage III |
| E008 | 2022-12-07 | 3 | 2 | De-escalate to Stage II |
| E009 | 2022-12-30 | 2 | 3 | Escalate to Stage III |

**Final state** (2023-02-28): Stage III remains active through season end. No end-of-season revocation has been entered.

## Merge Success

- **0 merge failures**: All station-daily rows matched to a corresponding daily GRAP state.
- **0 orphan dates**: Every calendar date 2022-01-01 to 2023-12-31 is present for all 8 stations.
- **0 orphan GRAP assignments**: Every date has a stage (0 pre-GRAP, 0–4 in-season, NULL off-season).

## Known Assumptions & Limitations

### 1. Season Scoping
GRAP stages are scoped per calendar season (Oct 1 – Feb 28/29). Stages do not carry forward across season boundaries.

### 2. Pre-GRAP Data (Jan–Sep 2022)
- Before E001 (2022-10-05), all dates have `grap_stage = 0`.
- This is a **conceptual default**, not a verified historical state.
- Off-season dates (March–September) have `grap_stage = 0` and `season = NULL`.

### 3. Data Completeness
- Season 2022-23 has 9 verified events (E001–E009).
- Season 2023-24 is **truncated at 2023-12-31** (data does not extend to Feb 2024 when the season ends).
- No end-of-season revocation for 2022-23 has been entered, so Stage III remains active from 2022-12-30 to 2023-02-28.

### 4. Missing Measurements
- PM2.5, PM10, and meteorological variables (`air_temp_c`, `rh_pct`, `wind_speed_ms`, `wind_dir_deg`) are subject to missingness.
- NULL values are preserved exactly as they appear in the raw CPCB data; no imputation has been applied.
- Rows where all measurement columns are NULL should be flagged as data gaps in downstream analysis.

### 5. GRAP Event Metadata
- `active_event_id` has been dropped from this dataset (redundant with event dates).
- For full event metadata (titles, official sources, notes), refer to `data/raw/grap/grap_events_manual.csv`.

## Unresolved Issues

1. **Season 2023-24 truncation**: Data ends 2023-12-31. No events or final stage state entered for 2024-01-01 to 2024-02-29.
2. **Pre-GRAP history**: Stage 0 for Jan–Sep 2022 is a default, not a historical record.
3. **End-of-season revocation (2022-23)**: Not yet entered. Analysis of 2023 Q1 may require explicit handling of this gap.

## Quality Gates Satisfied

- ✓ No structural errors
- ✓ No logical inconsistencies
- ✓ No data-type mismatches
- ✓ Full date coverage for loaded period
- ✓ Consistent grain (1 row per station × date)
- ✓ Zero unexplained NULLs in primary key fields

## Recommendation

**Ready for EDA** — this dataset is suitable for exploratory analysis and summary statistics. Analytical queries should:

1. **Respect the season concept**: Do not mix GRAP stages across calendar seasons.
2. **Handle off-season data carefully**: Off-season rows have `season = NULL` and `grap_stage = 0`; decide whether these should be excluded or treated as a "no GRAP" category.
3. **Document data gaps**: Flag periods where all 8 stations have NULL measurements on the same date (likely data collection outages).
4. **Acknowledge truncation**: Season 2023-24 is incomplete; avoid claims about full-season behavior in 2024 Q1.
