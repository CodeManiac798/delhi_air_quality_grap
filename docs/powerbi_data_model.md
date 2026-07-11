# Power BI Data Model (Phase D)

The **data model** for the Delhi AQI / GRAP Power BI file — fact/dimension
tables, relationships, measures, hierarchies, and filters. This is a modelling
spec, **not** a set of dashboards or visuals, and it produces no findings.

Source: import from `data/processed/delhi_aqi_grap.db` (built by
`src/05_load_sqlite.py`) or directly from the processed CSVs. Prefer importing
the SQL **views**, which already encode season and active-stage logic once.

## Star schema

```
                 ┌──────────────┐
                 │  DimStation  │
                 └──────┬───────┘
                        │ station_id (1)
                        │
   ┌──────────────┐     ▼ (many)      ┌──────────────┐
   │   DimDate    │──(1)───► FactStationDaily ◄──(many)│  DimStage    │
   └──────────────┘  date            └──────┬───────┘   └──────────────┘
                                            │ active_stage (many→1)
                 ┌──────────────┐           │
                 │ DimGrapEvent │ (event study, related on effective_date via DimDate)
                 └──────────────┘
```

### Fact table

**`FactStationDaily`** — from `v_station_daily_enriched` (grain: station × day,
5,840 rows). Columns kept: `station_id`, `date`, `season`, `is_grap_season`,
`active_stage`, `pm25_ugm3`, `pm10_ugm3`, `air_temp_c`, `rh_pct`,
`wind_speed_ms`, `wind_dir_deg`. This is the only fact most pages need.

> Optional second fact **`FactEventWindow`** from `event_windows` for dedicated
> event-study pages (grain: event × station × day, `rel_day`). Keep it separate
> from `FactStationDaily`; do not try to make one fact serve both roles.

### Dimension tables

| Dimension | Source | Key | Notable columns |
|---|---|---|---|
| `DimStation` | `stations` | `station_id` | `station_name`, `display_name`, `geographic_role`, `latitude`, `longitude` |
| `DimDate` | mark a **date table**; source `v_calendar` (or let PBI generate one over 2022-01-01…2023-12-31) | `date` | `year`, `month`, `year_month`, `dow`, `grap_season`, `is_grap_season` |
| `DimStage` | small static table (see below) | `active_stage` | `stage_label`, `stage_short`, `stage_sort` |
| `DimGrapEvent` | `grap_events` | `event_id` | `effective_date`, `stage_from`, `stage_to`, `event_direction`, `action_type`, `season`, `official_order_title` |

**`DimStage`** (create as an entered/static table — 5 rows):

| active_stage | stage_short | stage_label | stage_sort |
|---|---|---|---|
| 0 | None | No active GRAP | 0 |
| 1 | I | Stage I (Poor) | 1 |
| 2 | II | Stage II (Very Poor) | 2 |
| 3 | III | Stage III (Severe) | 3 |
| 4 | IV | Stage IV (Severe+) | 4 |

Set `stage_label`'s **Sort By Column** = `stage_sort`.

## Relationships

| From (many) | To (one) | Key | Cross-filter | Active? |
|---|---|---|---|---|
| `FactStationDaily[station_id]` | `DimStation[station_id]` | station_id | single | yes |
| `FactStationDaily[date]` | `DimDate[date]` | date | single | yes |
| `FactStationDaily[active_stage]` | `DimStage[active_stage]` | active_stage | single | yes |
| `DimGrapEvent[effective_date]` | `DimDate[date]` | date | single | yes |
| `FactEventWindow[station_id]` | `DimStation[station_id]` | station_id | single | yes |
| `FactEventWindow[event_id]` | `DimGrapEvent[event_id]` | event_id | single | yes |

Notes:
- `active_stage` is **NULL off-season** — the blank member in `DimStage` is
  correct behaviour (no GRAP concept off-season); consider filtering pages to
  `is_grap_season = 1`.
- Keep all cross-filtering **single-direction** from dimension → fact. Do not
  enable bidirectional filtering (it invites ambiguity with two facts sharing
  `DimStation`/`DimDate`).

## Hierarchies

- **Date hierarchy** (`DimDate`): `year → month (year_month) → date`. Add
  `grap_season` as a separate field for season slicers (it does not nest cleanly
  under calendar year because a season spans two years).
- **Station hierarchy** (`DimStation`): `geographic_role → station_name`.
- **Stage hierarchy** (`DimStage`): `active_stage / stage_label` (flat, sorted by
  `stage_sort`).

## Recommended DAX measures

Base measures — **average of daily values, never a sum of concentrations**:

```DAX
Avg PM2.5      = AVERAGE ( FactStationDaily[pm25_ugm3] )
Avg PM10       = AVERAGE ( FactStationDaily[pm10_ugm3] )
Avg Wind Speed = AVERAGE ( FactStationDaily[wind_speed_ms] )
Avg Temp       = AVERAGE ( FactStationDaily[air_temp_c] )
Avg RH         = AVERAGE ( FactStationDaily[rh_pct] )

Observed Days  = COUNT ( FactStationDaily[pm25_ugm3] )      -- non-blank only
Station-Days   = COUNTROWS ( FactStationDaily )
PM2.5 Coverage % =
    DIVIDE ( [Observed Days], [Station-Days] )
```

Completeness guard (blank the number when coverage is too thin to trust):

```DAX
Avg PM2.5 (guarded) =
    IF ( [PM2.5 Coverage %] >= 0.5, [Avg PM2.5], BLANK () )
```

Event before/after (uses `FactEventWindow`, ±7 day windows excluding day 0):

```DAX
PM2.5 Before =
    CALCULATE ( AVERAGE ( FactEventWindow[pm25_ugm3] ),
        FactEventWindow[rel_day] >= -7, FactEventWindow[rel_day] <= -1 )

PM2.5 After =
    CALCULATE ( AVERAGE ( FactEventWindow[pm25_ugm3] ),
        FactEventWindow[rel_day] >= 1, FactEventWindow[rel_day] <= 7 )

PM2.5 Delta (After - Before) = [PM2.5 After] - [PM2.5 Before]
```

Ranking (for "dirtiest station this season"):

```DAX
Station PM2.5 Rank =
    RANKX ( ALLSELECTED ( DimStation[station_name] ), [Avg PM2.5],, DESC, DENSE )
```

Rolling average (calendar-day trailing 7):

```DAX
Avg PM2.5 (7d roll) =
    AVERAGEX (
        DATESINPERIOD ( DimDate[date], MAX ( DimDate[date] ), -7, DAY ),
        [Avg PM2.5]
    )
```

> Keep these as measures, not calculated columns — they must respect slicer
> context. Every headline measure should have a `… (guarded)` sibling or a
> visible `PM2.5 Coverage %` beside it, so no chart implies precision the data
> does not have.

## Standard filters / slicers

- `DimDate[grap_season]` (2022-23 / 2023-24) — with the **2023-24 = truncated**
  caveat noted on the page.
- `DimDate[is_grap_season]` (default many pages to = 1).
- `DimStation[station_name]` (and `geographic_role`).
- `DimStage[stage_label]`.
- `DimGrapEvent[event_direction]` for event pages.

## Model-level cautions to carry onto the report

1. **2023-24 is truncated** (ends 2023-12-31) — never compare full seasons; use
   the Oct–Dec like-for-like window (mirrors `11_seasonal_comparison.sql`).
2. **Stage is defined by air quality**, so a stage→PM2.5 gradient is not a GRAP
   effect. Any stage visual needs this caption.
3. **Not weather-adjusted** — Power BI shows raw descriptives; the weather-
   adjusted numbers come from the Python step and should be a clearly separate,
   labelled measure/table when added.
4. **5 events, one season only** — the event pages are a first batch; design the
   model so adding rows to `grap_events` and reloading “just works” (it does:
   everything keys off `effective_date` / `active_stage`).
