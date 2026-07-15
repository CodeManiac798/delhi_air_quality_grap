# Data Dictionary

Documents the fields in every processed dataset under `data/processed/`. Units
marked **(verify)** are inferred from raw CPCB column headers and should be
confirmed against the official CPCB metadata before analytical use.

## `data/processed/station_daily.csv`

Grain: **one monitoring station × one calendar day**. Expected max 5,840 rows
(8 stations × 730 days). Missing values are left as-is (empty) — no imputation.

| field | meaning | unit | source | raw/derived | missingness treatment |
|---|---|---|---|---|---|
| `station_id` | Slug identifier for the station | — | derived from filename, validated vs registry | derived | never null |
| `station_name` | Human-readable station name | — | station registry (`src/config.py`) | derived | never null |
| `year` | Calendar year of the observation | year | parsed from `Timestamp` | derived | never null |
| `date` | Observation date (ISO `YYYY-MM-DD`) | date | raw `Timestamp` (normalised) | raw (parsed) | never null |
| `pm25_ugm3` | PM2.5 concentration | µg/m³ | CPCB `PM2.5 (µg/m³)` | raw | left blank if missing |
| `pm10_ugm3` | PM10 concentration | µg/m³ | CPCB `PM10 (µg/m³)` | raw | left blank if missing |
| `air_temp_c` | Air temperature | °C | CPCB `AT (°C)` | raw | left blank if missing |
| `rh_pct` | Relative humidity | % | CPCB `RH (%)` | raw | left blank if missing |
| `wind_speed_ms` | Wind speed | m/s | CPCB `WS (m/s)` | raw | left blank if missing |
| `wind_dir_deg` | Wind direction | degrees (0–360) | CPCB `WD (deg)` | raw | left blank if missing |
| `source_file` | Originating raw CSV filename | — | filesystem | derived (provenance) | never null |

**Notes**
- Daily values are CPCB station daily aggregates (`1D` files). The underlying
  aggregation method (mean of sub-daily readings) is **(verify)** against CPCB docs.
- Other raw columns (NO, NO₂, NOx, NH₃, SO₂, CO, Ozone, Benzene, Toluene,
  Xylene family, RF, TOT-RF, SR, BP, VWS) exist in the raw files but are **not**
  carried into the processed dataset per project scope. They remain available in
  `data/raw/cpcb/` and are covered by the audit reports.

## `data/processed/stations.csv`

One row per selected station.

| field | meaning | unit | source | raw/derived | notes |
|---|---|---|---|---|---|
| `station_id` | Slug identifier | — | registry | derived | primary key |
| `station_name` | Station name | — | registry | derived | |
| `display_name` | Label for dashboards/figures | — | registry | derived | |
| `operating_agency` | Operating agency | — | raw filename (`dpcc`) | derived | all DPCC |
| `geographic_role` | Locked geographic role | — | project (locked) | derived | e.g. "east", "central" |
| `selected` | Whether in the final 8-station sample | bool | project | derived | all `True` here |
| `selection_reason` | Why the station was selected | — | project | derived | |
| `latitude` | Station latitude | deg | — | — | **blank — not yet verified** |
| `longitude` | Station longitude | deg | — | — | **blank — not yet verified** |

## `data/processed/daily_grap_state.csv`

Grain: **one calendar day**. 730 rows, 2022-01-01 to 2023-12-31. Built by
`src/06_build_daily_grap_state.py` from the verified GRAP event calendar — the
single source of truth for "what GRAP stage was active on day D."

| field | meaning | unit | source | raw/derived | missingness treatment |
|---|---|---|---|---|---|
| `date` | Calendar date (ISO `YYYY-MM-DD`) | date | derived | derived | never null |
| `grap_stage` | Active GRAP stage on this date (0 = no active GRAP) | integer 0–4 | derived from `grap_events_manual.csv` | derived | never null (0 by default) |
| `season` | GRAP season the date falls in (e.g. `2022-23`), blank off-season | — | derived | derived | blank by design outside a GRAP season |
| `active_event_id` | ID of the event currently in force, if any | — | derived | derived | blank on non-transition days |
| `is_event_day` | 1 if this date is a verified event's effective date | 0/1 | derived | derived | never null |
| `days_since_last_change` | Days since the most recent stage change | integer | derived | derived | blank before a season's first event |
| `days_until_next_change` | Days until the next recorded stage change | integer | derived | derived | blank after a season's last recorded event |

## `data/processed/station_daily_grap.csv`

Grain: **one monitoring station × one calendar day**. 5,840 rows (8 stations ×
730 days) — the primary analytical dataset used by every notebook. Built by
`src/08_merge_station_daily_grap.py` as `station_daily.csv` joined with
`daily_grap_state.csv` on `date`.

| field | meaning | unit | source | raw/derived |
|---|---|---|---|---|
| `station_id`, `station_name`, `year`, `date` | Same as `station_daily.csv` | — | `station_daily.csv` | carried through |
| `pm25_ugm3`, `pm10_ugm3`, `air_temp_c`, `rh_pct`, `wind_speed_ms`, `wind_dir_deg` | Same as `station_daily.csv` | see above | `station_daily.csv` | carried through |
| `source_file` | Originating raw CSV filename | — | `station_daily.csv` | carried through |
| `season`, `grap_stage`, `is_event_day`, `days_since_last_change`, `days_until_next_change` | Same as `daily_grap_state.csv`, joined onto every station row for that date | see above | `daily_grap_state.csv` | joined |

## `data/processed/event_windows_master.csv`

Grain: **one verified event × one station × one relative day**. 1,080 rows
(9 events × 8 stations × 15 relative days). Built by
`notebooks/06_event_window_construction.ipynb` as a fixed ±7-day window around
each verified event's effective date — the input to every event-window
notebook (`07`–`10`).

| field | meaning | unit | notes |
|---|---|---|---|
| `event_id` | Verified event identifier (`E001`–`E009`) | — | matches `grap_events_manual.csv` |
| `event_date` | The event's effective date | date | constant within an event |
| `relative_day` | Signed offset from the event date | integer, −7…+7 | 0 = the event day itself |
| `calendar_date` | `event_date + relative_day` | date | |
| `station_name` | Monitoring station | — | matches `stations.csv` |
| `pm25_ugm3`, `pm10_ugm3`, `air_temp_c`, `rh_pct`, `wind_speed_ms`, `wind_dir_deg` | Same as `station_daily.csv`, for `(station_name, calendar_date)` | see above | left blank where the source row is missing — no imputation |
| `grap_stage` | Active GRAP stage on `calendar_date` | integer 0–4 | |
| `is_before_event`, `is_event_day`, `is_after_event` | Period flags derived from `relative_day` | boolean | exactly one is `True` per row |

## Reports (audit outputs, not analytical data)

- `reports/data_quality/raw_file_inventory.csv` — per-file structural inventory.
- `reports/data_quality/core_variable_missingness.csv` — per station-year × core
  variable: counts, null %, coercion failures, min/max/median.
- `reports/data_quality/data_quality_flags.csv` — flagged implausible values
  (empty when none found).
- `reports/data_quality/data_quality_summary.md` — human-readable Gate 1 summary.
