# Data Dictionary

Documents the fields in the processed Phase 1 datasets. Units marked
**(verify)** are inferred from raw CPCB column headers and should be confirmed
against the official CPCB metadata before analytical use.

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

## Reports (audit outputs, not analytical data)

- `reports/data_quality/raw_file_inventory.csv` — per-file structural inventory.
- `reports/data_quality/core_variable_missingness.csv` — per station-year × core
  variable: counts, null %, coercion failures, min/max/median.
- `reports/data_quality/data_quality_flags.csv` — flagged implausible values
  (empty when none found).
- `reports/data_quality/data_quality_summary.md` — human-readable Gate 1 summary.
