# Power BI Architecture — Delhi GRAP Analytics Platform

**Role of this document.** This is the semantic-model blueprint for the
Presentation & Product Layer. It defines *what gets built into the Power BI
data model* — tables, keys, relationships, measures, and formatting rules — for
a decision-support product aimed at policy analysts, government officials,
environmental researchers, and urban planning teams. **It contains no report
pages, no visuals, no layout, and no colour decisions.** Those are a separate,
later deliverable.

**Relationship to prior documents.** `docs/archive/powerbi_data_model.md` was written
earlier in the project (Phase 2) against a smaller event calendar and a
nullable, view-computed `active_stage` column. The pipeline has since moved on:
`grap_stage` is now populated for every calendar day (0 = no active GRAP, never
NULL), the event calendar carries **9** verified events across **three**
GRAP-season labels, and a fixed **±7-day** event-window table is now
materialized on disk rather than computed at query time. This document
supersedes `docs/archive/powerbi_data_model.md` for semantic-model purposes; the
earlier file is kept for historical context on the SQL-view design.

**Analytical phase status.** Frozen. Every number this model will ever surface
was already computed and validated in `notebooks/01`–`10`. This document adds no
analysis, changes no methodology, and introduces no new descriptive claim — it
only decides how the existing, validated outputs are structured for BI
consumption.

---

## 1. Source Data Inventory

The model is built from five files already on disk. Grain and row counts are
stated here so the model below can be checked against them after any refresh.

| File | Grain | Rows (current) | Role |
|---|---|---|---|
| `data/processed/station_daily.csv` | station × date | 5,840 (8 × 730) | Fact source — pure measurements |
| `data/processed/daily_grap_state.csv` | date | 730 | Date-dimension source — daily GRAP state |
| `data/processed/stations.csv` | station | 8 | Station-dimension source |
| `data/raw/grap/grap_events_manual.csv` (filtered `verified = 'Yes'`) | event | 9 | Event-dimension source |
| `data/processed/event_windows_master.csv` | event × station × relative day | 1,080 (9 × 8 × 15) | Second fact source — event-window study |

`data/processed/station_daily_grap.csv` (the flattened file used by the Python
notebooks) is **not** imported as-is. It denormalizes date- and GRAP-state
attributes (`season`, `grap_stage`, `is_event_day`, `days_since_last_change`,
`days_until_next_change`) onto every one of the 8 station rows for a given day,
repeating the same city-wide value eight times. Power BI should decompose this
back into fact + dimension (Section 2) rather than import the wide flat file —
smaller fact table, no repeated columns, and `grap_stage` becomes filterable
through one dimension instead of eight duplicated copies of the same value.

The SQLite warehouse (`data/processed/delhi_aqi_grap.db`, built by
`src/05_load_sqlite.py`) is optional. If used, import its base tables
(`station_daily`, `stations`, `grap_events`) and derived view
(`daily_grap_state`) rather than `v_station_daily_enriched` — the enriched view
re-introduces the same denormalization this section avoids. **Rebuild the
warehouse before pointing Power BI at it**; its `grap_events` table and
`event_windows` view predate the current 9-event calendar and the fixed ±7-day
window and will not match `event_windows_master.csv` until
`src/05_load_sqlite.py` is re-run.

---

## 2. Semantic Model

Two fact tables at two different grains, sharing conformed dimensions.

### 2.1 Fact tables

**`FactStationDaily`** — grain: one station × one calendar day.
Source: `station_daily.csv` (or `station_daily` table in the warehouse).

| Column | Type | Notes |
|---|---|---|
| `station_id` | Text | FK → `DimStation` |
| `date` | Date | FK → `DimDate` |
| `pm25_ugm3` | Decimal | Primary outcome; blank if missing, never imputed |
| `pm10_ugm3` | Decimal | Secondary outcome |
| `air_temp_c` | Decimal | Weather covariate |
| `rh_pct` | Decimal | Weather covariate |
| `wind_speed_ms` | Decimal | Weather covariate |
| `wind_dir_deg` | Decimal | Weather covariate |

No natural single-column primary key; the grain key is the composite
(`station_id`, `date`). `year` and `source_file` from the source CSV are
dropped at load (`year` is derivable from `DimDate`; `source_file` is
provenance, not analytical — see Section 8, Field Catalogue).

**`FactEventWindow`** — grain: one event × one station × one relative day
(-7…+7). Source: `event_windows_master.csv`.

| Column | Type | Notes |
|---|---|---|
| `event_id` | Text | FK → `DimGrapEvent` |
| `station_id` | Text | FK → `DimStation` — **added at load**; see below |
| `calendar_date` | Date | FK → `DimDate` |
| `relative_day` | Whole number | -7…+7; 0 = event day |
| `pm25_ugm3` | Decimal | |
| `pm10_ugm3` | Decimal | |
| `air_temp_c` | Decimal | |
| `rh_pct` | Decimal | |
| `wind_speed_ms` | Decimal | |

`event_windows_master.csv` carries `station_name` (text), not `station_id`. At
load, merge in `station_id` from `stations.csv` (join on `station_name`) so the
relationship to `DimStation` uses the same short text key as
`FactStationDaily`, rather than a longer, mixed-case display string — see
Section 9 (Performance). `event_date`, `wind_dir_deg`, and `grap_stage` from
the source file are dropped at load: `event_date` duplicates information
already on `DimGrapEvent`; `grap_stage` on this fact is a copy of the same
city-wide value already on `DimDate` for `calendar_date` and should be read
through that relationship instead of stored twice. The three boolean flags
(`is_before_event`, `is_event_day`, `is_after_event`) are replaced by a single
`Period` calculated column (Section 5).

### 2.2 Dimension tables

**`DimStation`** — source: `stations.csv`. Key: `station_id`.

| Column | Type | Notes |
|---|---|---|
| `station_id` | Text | **Primary key** |
| `station_name` | Text | Display |
| `display_name` | Text | Dashboard label, if it differs from `station_name` |
| `geographic_role` | Text | e.g. "east", "central" — categorical hierarchy level |
| `latitude` / `longitude` | Decimal | Currently blank for all 8 rows; import for future map visuals, hide until populated |

`operating_agency` and `selection_reason` are dropped at load (all 8 rows share
the same agency; selection reasoning is project documentation, not a report
field — see Section 8).

**`DimDate`** — source: `daily_grap_state.csv`, extended with standard calendar
attributes. Key: `date`. One row per calendar day, 2022‑01‑01 to 2023‑12‑31
(730 rows), marked as the model's **official date table**.

| Column | Type | Notes |
|---|---|---|
| `date` | Date | **Primary key** |
| `year` | Whole number | Calendar year |
| `month` | Whole number | 1–12 |
| `month_name` | Text | Sort by `month` |
| `year_month` | Text | e.g. "2022-10" |
| `day_of_week` | Text | Sort by an added `day_of_week_number` |
| `grap_season` | Text | `2021-22` / `2022-23` / `2023-24` / blank |
| `is_grap_season` | Whole number (0/1) | 1 if `grap_season` is non-blank |
| `grap_stage` | Whole number (0–4) | FK → `DimStage`; daily city-wide state |
| `active_event_id` | Text | Populated only on the 9 event-effective dates; FK → `DimGrapEvent` (inactive relationship, see Section 3) |
| `is_event_day` | Whole number (0/1) | 1 on the 9 effective dates |
| `days_since_last_change` | Whole number | Blank outside a season or before the season's first event |
| `days_until_next_change` | Whole number | Blank after a season's last recorded event |

`DimDate` is a hybrid: mostly a conventional calendar dimension, but
`grap_stage`, `is_event_day`, and the day-counters are genuine daily-grain
*facts* about city-wide GRAP state, sourced from `daily_grap_state.csv` rather
than derived from the calendar itself. This is intentional — it is the single
place city-wide GRAP state lives, so it is never duplicated across 8 station
rows the way it is in `station_daily_grap.csv`.

**`DimStage`** — small static/entered table, 5 rows. Key: `stage_code`.

| stage_code | stage_label | stage_short | stage_sort |
|---|---|---|---|
| 0 | No Active GRAP | — | 0 |
| 1 | Stage I (Poor) | I | 1 |
| 2 | Stage II (Very Poor) | II | 2 |
| 3 | Stage III (Severe) | III | 3 |
| 4 | Stage IV (Severe+) | IV | 4 |

**`DimGrapEvent`** — source: `grap_events_manual.csv`, **filtered to
`verified = 'Yes'` at load** (per `docs/grap_event_data_contract.md`; currently
9 rows). Key: `event_id`.

| Column | Type | Notes |
|---|---|---|
| `event_id` | Text | **Primary key** |
| `effective_date` | Date | FK → `DimDate` |
| `order_date` | Date | Kept for reference/drillthrough only |
| `season` | Text | `2022-23` etc. |
| `action_type` | Text | invoke / escalate / de_escalate / revoke / other |
| `stage_from` | Whole number | 0–4 |
| `stage_to` | Whole number | 0–4 |
| `event_direction` | Text | activation / escalation / de_escalation / full_revocation / other |
| `official_order_title` | Text | Long string — drillthrough/tooltip field, not a slicer |

`immediate_effect`, `official_source`, `notes`, and `verified` are dropped at
load: `verified` is enforced by the load filter itself (every loaded row is
already verified, so the column would be constant); the rest are documentation
fields, not report fields (see Section 8).

**`_Measures`** — an empty, disconnected table used only to host DAX measures
(Section 6). No relationships, no source data. Standard practice for keeping
measures out of the physical fact/dimension tables and easy to find in one
place in the field list.

---

## 3. Star Schema

```
                                   ┌───────────────┐
                                   │   DimStage    │
                                   │  stage_code PK│
                                   └───────┬───────┘
                                           │ (1)
                                           │ grap_stage
                                           │ (many rows share 1 stage)
                                           ▼
┌───────────────┐   station_id     ┌───────────────┐    date        ┌───────────────┐
│  DimStation    │◄──────(1)───────│FactStationDaily│──────(many)──►│    DimDate     │
│ station_id  PK │      (many)     │  station_id FK │               │   date      PK │
└───────┬────────┘                 │  date       FK │               │  grap_stage    │
        │ (1)                      └───────────────┘               │  is_event_day  │
        │ station_id                                                │  active_event_id│
        │ (many)                                                    └───────┬────────┘
        ▼                                                                   │ (1)
┌───────────────┐                                                           │ effective_date
│FactEventWindow │       event_id        ┌───────────────┐                  │ (many, in practice 1:1 —
│ station_id  FK │──────────(many)───────►  DimGrapEvent │◄─────────────────┘  9 distinct dates)
│ event_id    FK │        (1)            │  event_id  PK │
│ calendar_date FK│                      └───────────────┘
└───────┬────────┘
        │ (many)
        │ calendar_date
        ▼ (1)
   [ same DimDate as above ]

                              ┌───────────────┐
                              │  _Measures    │   (disconnected — no relationships)
                              └───────────────┘
```

Both fact tables connect to the same `DimDate` and the same `DimStation` —
this is what makes it a true (if slightly extended) star schema rather than two
unrelated models: a report page can slice `FactStationDaily` by
`DimStation[geographic_role]` and a separate page can slice `FactEventWindow`
by the same field, and both will behave identically.

---

## 4. Relationships

| From (many side) | To (one side) | Key | Cross-filter direction | Active |
|---|---|---|---|---|
| `FactStationDaily[station_id]` | `DimStation[station_id]` | `station_id` | Single (Dim → Fact) | Yes |
| `FactStationDaily[date]` | `DimDate[date]` | `date` | Single (Dim → Fact) | Yes |
| `FactEventWindow[station_id]` | `DimStation[station_id]` | `station_id` | Single (Dim → Fact) | Yes |
| `FactEventWindow[calendar_date]` | `DimDate[date]` | `date` | Single (Dim → Fact) | Yes |
| `FactEventWindow[event_id]` | `DimGrapEvent[event_id]` | `event_id` | Single (Dim → Fact) | Yes |
| `DimDate[grap_stage]` | `DimStage[stage_code]` | `grap_stage` / `stage_code` | Single (Dim → Dim) | Yes |
| `DimDate[active_event_id]` | `DimGrapEvent[event_id]` | `event_id` | Single (Dim → Dim) | **No** (inactive) |
| `DimGrapEvent[effective_date]` | `DimDate[date]` | `date` | Single (Dim → Dim) | Yes |

**Why `DimDate[active_event_id] → DimGrapEvent` is left inactive.** Activating
it would create a second relationship path between `DimDate` and
`DimGrapEvent` (the first being `DimGrapEvent[effective_date] → DimDate[date]`
above), which Power BI does not allow as two simultaneously active
relationships between the same table pair. The active path
(`effective_date → date`) is the one used for "what event fired on this date"
lookups; if the inactive path is ever needed (e.g. "which event is currently in
force on a non-event date"), invoke it explicitly with `USERELATIONSHIP` inside
a specific measure rather than activating it model-wide.

**No bi-directional relationships anywhere in this model.** Every
relationship filters from the dimension side toward the fact side (or, for the
two Dim–Dim relationships, from the smaller/lookup side toward `DimDate`). This
is deliberate: with two fact tables sharing `DimStation` and `DimDate`,
bi-directional filtering would let a selection on `FactEventWindow` reach back
through `DimStation` and filter `FactStationDaily` (or vice versa) in ways that
are easy to set up and hard to reason about later. If a report page genuinely
needs "select an event, see the whole-year `FactStationDaily` trend for that
event's station," implement it with a measure using `TREATAS` or
`CROSSFILTER(..., BOTH)` scoped to that one visual/measure — not with a
model-level bi-directional relationship.

---

## 5. Recommended Calculated Columns

Kept deliberately short — most of what a calculated column could do here is
better done once in Power Query at load time (cheaper to compute, cheaper to
store, and versioned alongside the load logic rather than hidden in the model).
Listed here because a reviewer needs to know they exist regardless of which
layer implements them.

| Table | Column | Logic | Why a column, not a measure |
|---|---|---|---|
| `FactEventWindow` | `Period` | `"Pre"` if `relative_day < 0`, `"Event"` if `= 0`, `"Post"` if `> 0` | Used as a slicer/axis/legend value, which requires a column, not a measure |
| `DimDate` | `month_name` | Text name of `month`, sorted by the numeric `month` column | Needed for a human-readable month axis with correct chronological sort |
| `DimDate` | `day_of_week` / `day_of_week_number` | Weekday name + numeric sort helper | Same reason as `month_name` |
| `DimGrapEvent` | `stage_transition_label` | `"Stage " & stage_from & " → Stage " & stage_to`, e.g. from `action_type`/`stage_from`/`stage_to` | Static per-row string for drillthrough/tooltip display; no aggregation involved |
| `DimStation` | `station_sort` | Rank string for `geographic_role → station_name` hierarchy ordering, if alphabetical default is not wanted | Only needed if the default alphabetical sort within a geographic role is undesirable |

Everything in Section 2's fact tables (`pm25_ugm3`, `air_temp_c`, etc.) stays
as plain imported columns — no derived columns on the fact tables themselves
beyond `Period` above. Do not add a calculated "PM2.5 category" or similar
bucketing column unless a specific report page is confirmed to need it; an
unused calculated column is pure model bloat.

---

## 6. Measure Catalogue

All measures live in `_Measures`. Grouped by theme; each states which fact
table it reads.

### 6.1 Volume & metadata

```DAX
Total Observations       = COUNTROWS ( FactStationDaily )

Monitoring Stations      = DISTINCTCOUNT ( FactStationDaily[station_id] )

Verified GRAP Events     = COUNTROWS ( DimGrapEvent )
-- Every row in DimGrapEvent is already verified = 'Yes' by the load filter,
-- so a plain row count IS the verified-event count; no further filter needed.

Active GRAP Days         = CALCULATE ( COUNTROWS ( DimDate ), DimDate[grap_stage] > 0 )
-- Counts calendar days with any active stage, independent of station/fact filters.

Data Completeness %      =
    DIVIDE ( COUNT ( FactStationDaily[pm25_ugm3] ), COUNTROWS ( FactStationDaily ) )
-- Non-blank PM2.5 rows over all station-day rows in the current filter context.
```

### 6.2 Pollutant measures (`FactStationDaily`)

```DAX
Average PM2.5   = AVERAGE ( FactStationDaily[pm25_ugm3] )
Median PM2.5    = MEDIAN ( FactStationDaily[pm25_ugm3] )
Maximum PM2.5   = MAX ( FactStationDaily[pm25_ugm3] )

Average PM10    = AVERAGE ( FactStationDaily[pm10_ugm3] )
Median PM10     = MEDIAN ( FactStationDaily[pm10_ugm3] )
Maximum PM10    = MAX ( FactStationDaily[pm10_ugm3] )
```

### 6.3 Weather measures (`FactStationDaily`)

```DAX
Average Temperature = AVERAGE ( FactStationDaily[air_temp_c] )
Average Humidity     = AVERAGE ( FactStationDaily[rh_pct] )
Average Wind Speed   = AVERAGE ( FactStationDaily[wind_speed_ms] )
```

### 6.4 GRAP-state measures (`DimDate` / `FactStationDaily`)

```DAX
Stage-wise Observation Count = COUNTROWS ( FactStationDaily )
-- No stage filter is written into the DAX itself. Placed on a visual with
-- DimStage[stage_label] on rows/axis, the DimStage -> DimDate -> FactStationDaily
-- relationship chain does the "stage-wise" split automatically.
```

### 6.5 Event-window measures (`FactEventWindow`)

These mirror, as reusable measures, the exact Pre/Post descriptive comparison
already computed and validated in `08_cross_event_analysis.ipynb` Section 5 —
no new computation, only a BI-layer restatement of a finding already on record.
Kept strictly descriptive, per `docs/analysis_plan.md` Section 9 (Allowed
Claims): a plain average of a labelled period, nothing else.

```DAX
Pre-Event Avg PM2.5  = CALCULATE ( AVERAGE ( FactEventWindow[pm25_ugm3] ), FactEventWindow[Period] = "Pre" )
Post-Event Avg PM2.5 = CALCULATE ( AVERAGE ( FactEventWindow[pm25_ugm3] ), FactEventWindow[Period] = "Post" )

Pre-Event Avg PM10   = CALCULATE ( AVERAGE ( FactEventWindow[pm10_ugm3] ), FactEventWindow[Period] = "Pre" )
Post-Event Avg PM10  = CALCULATE ( AVERAGE ( FactEventWindow[pm10_ugm3] ), FactEventWindow[Period] = "Post" )

Event Window Observations = COUNTROWS ( FactEventWindow )
```

**Deliberately not included:** a "PM2.5 Delta" or "% change" measure subtracting
Post from Pre. `08_cross_event_analysis.ipynb` and
`09_sensitivity_analysis.ipynb` both found the sign and size of that
difference to vary by event and by window width — collapsing it into one
always-on delta measure would present a single number as more settled than the
analysis behind it supports. If a future report page needs it, build it
per-event, next to the underlying Pre/Post pair, not as a standalone KPI.

### 6.6 Guarded variants

Every headline pollutant measure gets one guarded sibling, so a chart never
implies more precision than the underlying coverage supports:

```DAX
Average PM2.5 (guarded) =
    IF ( [Data Completeness %] >= 0.5, [Average PM2.5], BLANK () )
```

Apply the same pattern to `Average PM10` if it is ever surfaced as a standalone
KPI card rather than alongside its own coverage figure.

---

## 7. Slicers, Drillthrough, Tooltips, Interactions

**Slicers (model-level recommendations — not page layout):**
- `DimDate[grap_season]` — with a visible caveat that `2023-24` is truncated
  (ends 2023‑12‑31) and `2021-22` is partial (starts 2022‑01‑01, mid-season).
- `DimDate[is_grap_season]` — quick in-season/off-season toggle.
- `DimStation[geographic_role]` and `DimStation[station_name]` (station name
  filtered/nested under role — see Section 8 hierarchy).
- `DimStage[stage_label]` (sorted by `stage_sort`, not alphabetically).
- `DimGrapEvent[event_direction]` and `DimGrapEvent[action_type]` — for
  event-window pages only (they only meaningfully filter `FactEventWindow`).

**Drillthrough fields:**
- A station drillthrough page keyed on `DimStation[station_name]`, receiving
  `DimDate[date]` (or `year_month`) as the filter context — for "show me this
  one station in detail."
- An event drillthrough page keyed on `DimGrapEvent[event_id]`, surfacing
  `official_order_title`, `stage_transition_label`, `action_type`, and the full
  `FactEventWindow` slice for that event — mirrors the per-event subsections in
  `07_event_profile_analysis.ipynb`.

**Tooltip pages:**
- A small tooltip page for point-hover on any daily PM2.5 line, showing
  `Average PM2.5`, `Average PM10`, `Average Temperature`, `Average Humidity`,
  `Average Wind Speed`, and `Data Completeness %` for that single date —
  keeps the base visual uncluttered while still surfacing the weather context
  the project's own analysis (`10_weather_context_analysis.ipynb`) treats as
  essential background.
- A tooltip page for `DimGrapEvent` rows showing `official_order_title` and the
  stage transition, so a report page's event markers do not need to display a
  long title string inline.

**Cross-filtering behaviour:**
- All dimension slicers filter both fact tables where a relationship exists
  (`DimStation`, `DimDate`) — single-direction, as fixed in Section 4.
- `DimGrapEvent` slicers only affect `FactEventWindow` directly. If a page
  wants a `DimGrapEvent` selection to also highlight `FactStationDaily` (via
  `effective_date`), that is the one active Dim–Dim relationship already in
  place (Section 4) — it will work without any bidirectional setting.
- Disable "Edit interactions" default (all-filter) only where a page
  specifically wants one visual to highlight rather than filter another; leave
  the Power BI default (filter) everywhere else rather than customising
  per-visual as a matter of habit.

---

## 8. Field Catalogue — Data Types, Formatting, Sorting, Hierarchies

| Field | Data type | Format string | Sort by |
|---|---|---|---|
| `FactStationDaily[pm25_ugm3]` | Decimal | `0.0 "µg/m³"` | — |
| `FactStationDaily[pm10_ugm3]` | Decimal | `0.0 "µg/m³"` | — |
| `FactStationDaily[air_temp_c]` | Decimal | `0.0 "°C"` | — |
| `FactStationDaily[rh_pct]` | Decimal | `0.0 "%"` | — |
| `FactStationDaily[wind_speed_ms]` | Decimal | `0.00 "m/s"` | — |
| `DimDate[date]` | Date | `yyyy-mm-dd` | — |
| `DimDate[month_name]` | Text | — | `month` (numeric) |
| `DimDate[day_of_week]` | Text | — | `day_of_week_number` |
| `DimDate[grap_season]` | Text | — | custom: `2021-22` → `2022-23` → `2023-24` |
| `DimStage[stage_label]` | Text | — | `stage_sort` |
| `DimGrapEvent[stage_transition_label]` | Text | — | `stage_from` then `stage_to` |
| `_Measures[Data Completeness %]` | Decimal | `0.0%` | — |
| All `*_id` / key columns | Text | — | — (hidden; see below) |

**Date hierarchy.** Build an explicit hierarchy on `DimDate`:
`grap_season → year → month_name → date`. Because a GRAP season spans two
calendar years (Oct–Feb), do **not** nest `grap_season` under `year` — keep it
as a separate top-level slicer/hierarchy branch, exactly as
`docs/archive/powerbi_data_model.md` already noted. **Turn off Power BI's automatic
Date/Time hierarchy** (see Section 9) so this explicit hierarchy is the only
one users see.

**Categorical hierarchy.** `DimStation`: `geographic_role → station_name`.
`DimStage` is intentionally flat (5 rows, sorted, no further nesting).

---

## 9. Fields to Hide from Report Users

Hidden ≠ deleted — these stay in the model for relationships, sorting, or
drillthrough, but are marked **Hide in Report View** so they do not clutter the
field list or slicer pane.

| Field | Reason hidden |
|---|---|
| `FactStationDaily[station_id]`, `FactEventWindow[station_id]`, `FactEventWindow[event_id]` | Join keys; users filter by `station_name` / event attributes instead |
| `DimDate[grap_stage]` (raw 0–4 code) | Superseded for display by `DimStage[stage_label]`; keep the code column for the relationship, hide it from the field list |
| `DimDate[active_event_id]` | Join key for the inactive relationship only |
| `DimDate[month]`, `DimDate[day_of_week_number]` | Sort-by helper columns, not meant to be browsed directly |
| `DimGrapEvent[order_date]` | Reference-only field (see `docs/grap_event_data_contract.md` on order vs. effective date); available on drillthrough, not as a slicer |
| `DimStation[latitude]`, `DimStation[longitude]` | Blank for all 8 rows currently; unhide once populated for a future map visual |
| `FactEventWindow[relative_day]` | Kept visible *only* on event-window axis visuals; hide from the general field list / slicer pane if a page does not use it as an axis |
| `_Measures` table's own placeholder column (if Power BI requires one to create the table) | Not a real field |

Fields dropped entirely at load (Section 2) — `source_file`,
`operating_agency`, `selection_reason`, `immediate_effect`, `official_source`,
`notes`, `verified` — are not "hidden," they are simply never imported, which
is preferable to importing and hiding wherever the field serves no report
purpose at all (smaller model, nothing to accidentally re-expose later).

---

## 10. Performance Recommendations

1. **Star schema, not snowflake.** Both facts relate directly to `DimStation`
   and `DimDate`; no chained dimension-of-a-dimension beyond `DimDate → DimStage`
   and `DimGrapEvent → DimDate`, both of which are single-hop and already
   accounted for in Section 4.
2. **Disable Auto Date/Time** (File → Options → Data Load, both Global and
   Current File). With it left on, Power BI silently creates a hidden
   auto-generated date table for every date column across both fact tables —
   for this model that means hidden tables behind `FactStationDaily[date]`,
   `FactEventWindow[calendar_date]`, `DimGrapEvent[effective_date]`, and
   `DimGrapEvent[order_date]`, quadrupling the model's date-table footprint for
   no benefit once `DimDate` is marked as the official date table.
3. **No bi-directional or many-to-many relationships anywhere** (Section 4)
   — every relationship in this model is single-direction and many-to-one.
4. **Import mode, not DirectQuery.** Total data volume here is small (5,840 +
   1,080 fact rows plus small dimensions); Import gives full VertiPaq
   compression and lets every measure in Section 6 run instantly, with no
   round-trip to a live source.
5. **Text keys are fine at this scale, but align them.** `station_id` is a
   short slug (`anand_vihar`, etc.) already used consistently in
   `FactStationDaily` and `DimStation`; Section 2 explicitly adds the same key
   to `FactEventWindow` at load instead of relating on the longer
   `station_name` display string, keeping every station relationship on the
   same short, low-cardinality text column.
6. **Prefer measures over calculated columns.** Section 5's calculated-column
   list is intentionally short; every aggregation in this document is a
   measure (Section 6), computed at query time over compressed columns rather
   than materialized and stored per row.
7. **Use variables (`VAR`) in any measure more complex than a single
   aggregation** (e.g. the guarded measures in 6.6) to avoid recomputing the
   same `CALCULATE` twice within one measure.
8. **Trim unused columns at the source, not in Power BI.** Section 2 already
   drops `source_file`, `notes`, `official_source`, etc. before they reach the
   model — smaller Power Query output compresses better than importing
   everything and hiding it.
9. **Keep `_Measures` as a genuinely empty table** (no rows, no source query)
   — it costs nothing at refresh time and gives every measure one obvious home.

---

## 11. Power BI Best Practices Applied Here

- **One source of truth per fact:** `grap_stage` lives once, on `DimDate`; no
  fact table stores its own copy.
- **Verification enforced at load, not in DAX:** `DimGrapEvent` is filtered to
  `verified = 'Yes'` in Power Query, so no measure ever needs to re-check that
  condition (contrast with `Verified GRAP Events` in Section 6.1, which is a
  plain row count precisely because the filtering already happened upstream).
- **Every headline pollutant measure has a completeness-guarded sibling**
  (Section 6.6), so the model cannot present a thinly-observed average as if it
  were as reliable as a well-observed one.
- **No measure claims more than the frozen analysis supports** — Section 6.5
  explicitly declines to add a delta/percent-change measure where the
  underlying notebooks found that number to be sensitive to event and window
  choice; the model's measure catalogue stays inside the "Allowed Claims" drawn
  in `docs/analysis_plan.md`.
- **Two fact tables, two grains, never merged.** `FactStationDaily` and
  `FactEventWindow` answer different questions (city-wide daily trend vs.
  event-relative comparison) and are kept as separate tables rather than
  forced into one, echoing the same separation `docs/archive/powerbi_data_model.md`
  established and that `06_event_window_construction.ipynb` /
  `08_cross_event_analysis.ipynb` rely on structurally.

---

## 12. Naming Conventions

- **Tables:** `Fact<Grain>` / `Dim<Entity>` in PascalCase (`FactStationDaily`,
  `DimStation`); the measure table is `_Measures` (leading underscore sorts it
  to the top of the field-list pane).
- **Measures:** Title Case, unit implied by format string rather than spelled
  out in the name (`Average PM2.5`, not `Average PM2.5 (ug/m3) Measure`).
  Guarded variants append `(guarded)`.
- **Calculated columns:** `snake_case` to visually distinguish them at a glance
  from PascalCase measures and Title Case display columns pulled straight from
  source (matches the convention already used in the underlying CSVs, e.g.
  `stage_transition_label`, `month_name`).
- **Hidden key columns:** keep the source's own key name (`station_id`,
  `event_id`) rather than renaming — hidden fields are for relationships and
  drillthrough plumbing, not for a user-facing vocabulary that needs polish.
- **Display labels users actually see** (`station_name`, `stage_label`,
  `grap_season`) get the polished, human-readable names; the underlying key
  stays technical and hidden.

---

## 13. Folder Organization

**Within the Power BI model** (display folders in the field list):

```
FactStationDaily
├── Pollutants        (pm25_ugm3, pm10_ugm3)
└── Weather           (air_temp_c, rh_pct, wind_speed_ms, wind_dir_deg)

FactEventWindow
├── Pollutants
├── Weather
└── Window Position   (relative_day, Period)

_Measures
├── Volume & Metadata
├── Pollutants
├── Weather
├── GRAP State
└── Event Window
```

**Within the repository** (`powerbi/`, currently empty per the project's
Phase-plan folder listing in `README.md`):

```
powerbi/
├── delhi_grap_analytics.pbix     # the Power BI file itself
├── model/
│   ├── measures.md               # measure catalogue kept in sync with this doc
│   └── relationships.md          # relationship diagram kept in sync with Section 4
└── exports/                      # any exported PDFs/images of the eventual report
```

Keep `powerbi/model/measures.md` and `powerbi/model/relationships.md` as living
mirrors of Sections 4 and 6 above once the `.pbix` is built — if the model
drifts from this document, one of the two is out of date, and the `.pbix`
should be assumed authoritative for *current* state while this document
remains the authoritative *design rationale*.
