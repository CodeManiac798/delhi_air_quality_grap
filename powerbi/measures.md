# Measure Catalogue — Delhi GRAP Analytics Platform

Every DAX measure approved across `docs/powerbi_architecture.md` §6,
`docs/dashboard_design_system.md` §2 (the `_Measures` → `Measures` rename and
folder amendment), and `docs/page1_executive_overview.md` §10 (one new
measure required for the Page 1 build). Nothing below is new design — this
document is a straight implementation transcription of already-approved DAX,
organized the way it should be typed into the **Measures** table in Power BI
Desktop.

**Table:** `Measures` — a disconnected table (no relationships), created via
**Modeling → New Table**, empty except for a single placeholder column
(hidden), used purely to host every measure below in one place in the field
list. Create the table first, then create every measure below *in* that
table (select `Measures` in the Fields pane before each **New Measure**), and
set the **Home table** and **Display folder** exactly as shown so the field
list matches this catalogue.

---

## Display folder: `KPIs`

Cross-domain "at a glance" counts — no pollutant- or weather-specific measure
lives here.

```DAX
Total Observations = COUNTROWS ( FactStationDaily )
```
One-line: counts every station-day row currently in filter context — the
"how much data" headline number.

```DAX
Monitoring Stations = DISTINCTCOUNT ( FactStationDaily[station_id] )
```
One-line: counts distinct stations contributing at least one row in the
current filter context (reacts to station/date filters, unlike a static row
count of `DimStation`).

```DAX
Verified GRAP Events = COUNTROWS ( DimGrapEvent )
```
One-line: a plain row count is already a *verified* count, because
`DimGrapEvent` is loaded pre-filtered to `verified = 'Yes'` at the Power Query
stage (see `docs/powerbi_architecture.md` §2.2).

```DAX
Active GRAP Days =
    CALCULATE ( COUNTROWS ( DimDate ), DimDate[grap_stage] > 0 )
```
One-line: counts calendar days with any active GRAP stage, independent of
which fact table or station is currently filtered.

```DAX
Data Completeness % =
    DIVIDE ( COUNT ( FactStationDaily[pm25_ugm3] ), COUNTROWS ( FactStationDaily ) )
```
One-line: the share of station-day rows in context that have a non-blank
PM2.5 reading — the model's core trust indicator, referenced by every guarded
measure below.

---

## Display folder: `Pollution`

```DAX
Average PM2.5 = AVERAGE ( FactStationDaily[pm25_ugm3] )
```
One-line: mean PM2.5 across the current filter context.

```DAX
Average PM2.5 (guarded) =
    IF ( [Data Completeness %] >= 0.5, [Average PM2.5], BLANK () )
```
One-line: same as above, but returns blank rather than a number if fewer than
half the in-context rows are observed — prevents a thinly-observed slice from
displaying as confidently as a well-observed one.

```DAX
Median PM2.5 = MEDIAN ( FactStationDaily[pm25_ugm3] )
```
One-line: median PM2.5 across the current filter context.

```DAX
Maximum PM2.5 = MAX ( FactStationDaily[pm25_ugm3] )
```
One-line: the single highest PM2.5 reading in the current filter context.

```DAX
Average PM10 = AVERAGE ( FactStationDaily[pm10_ugm3] )
```
One-line: mean PM10 across the current filter context.

```DAX
Average PM10 (guarded) =
    IF ( [Data Completeness %] >= 0.5, [Average PM10], BLANK () )
```
One-line: guarded counterpart to `Average PM10`, same 50%-coverage threshold
as the PM2.5 guard (uses the same `Data Completeness %`, which is defined on
PM2.5 non-blank rows — see the note under §"Known modelling nuance" below).

```DAX
Median PM10 = MEDIAN ( FactStationDaily[pm10_ugm3] )
```
One-line: median PM10 across the current filter context.

```DAX
Maximum PM10 = MAX ( FactStationDaily[pm10_ugm3] )
```
One-line: the single highest PM10 reading in the current filter context.

---

## Display folder: `Weather`

```DAX
Average Temperature = AVERAGE ( FactStationDaily[air_temp_c] )
```
One-line: mean air temperature across the current filter context.

```DAX
Average Humidity = AVERAGE ( FactStationDaily[rh_pct] )
```
One-line: mean relative humidity across the current filter context.

```DAX
Average Wind Speed = AVERAGE ( FactStationDaily[wind_speed_ms] )
```
One-line: mean wind speed across the current filter context.

---

## Display folder: `Events`

Absorbs both the GRAP-state measure (reads through `DimStage`/`DimDate`) and
the `FactEventWindow`-based Pre/Post pair — grouped together because, from a
report user's perspective, both are "the GRAP-event side of the model" (see
`docs/dashboard_design_system.md` §2 placement rationale).

```DAX
Stage-wise Observation Count = COUNTROWS ( FactStationDaily )
```
One-line: no stage filter is written into the DAX — placed on a visual with
`DimStage[stage_label]` on rows/axis, the `DimStage → DimDate →
FactStationDaily` relationship chain does the stage split automatically.

```DAX
Event Window Observations = COUNTROWS ( FactEventWindow )
```
One-line: counts event-window rows (event × station × relative day) in the
current filter context.

```DAX
Pre-Event Avg PM2.5 =
    CALCULATE ( AVERAGE ( FactEventWindow[pm25_ugm3] ), FactEventWindow[Period] = "Pre" )
```
One-line: mean PM2.5 across the -7…-1 relative-day rows of the event window.

```DAX
Post-Event Avg PM2.5 =
    CALCULATE ( AVERAGE ( FactEventWindow[pm25_ugm3] ), FactEventWindow[Period] = "Post" )
```
One-line: mean PM2.5 across the +1…+7 relative-day rows of the event window.

```DAX
Pre-Event Avg PM10 =
    CALCULATE ( AVERAGE ( FactEventWindow[pm10_ugm3] ), FactEventWindow[Period] = "Pre" )
```
One-line: mean PM10 across the -7…-1 relative-day rows of the event window.

```DAX
Post-Event Avg PM10 =
    CALCULATE ( AVERAGE ( FactEventWindow[pm10_ugm3] ), FactEventWindow[Period] = "Post" )
```
One-line: mean PM10 across the +1…+7 relative-day rows of the event window.

**Deliberately not included:** a delta/percent-change measure subtracting
Post from Pre. The frozen analytical notebooks (`08_cross_event_analysis.ipynb`,
`09_sensitivity_analysis.ipynb`) found that number's sign and size vary by
event and by window width — see `docs/powerbi_architecture.md` §6.5 for the
full rationale. If a future page needs it, build it per-event next to the
underlying Pre/Post pair, not as a standalone always-on measure.

---

## Display folder: `Metadata`

Small text/utility measures. Never plotted on an axis — consumed only by the
footer caveat strip, KPI coverage captions, and the About panel's live
"Dataset" figures (`docs/dashboard_design_system.md` §2, §5,
`docs/page1_executive_overview.md` §10).

```DAX
Selected Season Label =
    SELECTEDVALUE ( DimDate[grap_season], "All Seasons" )
```
One-line: shows the selected GRAP season, or "All Seasons" when none is
singly selected — used in page/section subtitles that reference the current
filter.

```DAX
Data As Of =
    FORMAT ( MAX ( DimDate[date] ), "d MMMM yyyy" )
```
One-line: the latest date present in the current filter context, formatted
for a caption (e.g. "31 December 2023").

```DAX
Truncated Season Flag =
    IF (
        SELECTEDVALUE ( DimDate[grap_season] ) = "2023-24",
        "Season truncated — data ends 31 Dec 2023",
        BLANK ()
    )
```
One-line: returns a caveat string only when the truncated 2023-24 season is
the singly-selected season; blank otherwise — drives the footer strip.

```DAX
Coverage Caveat =
    IF (
        [Data Completeness %] < 0.8,
        "Coverage " & FORMAT ( [Data Completeness %], "0%" ) & " for this selection",
        BLANK ()
    )
```
One-line: returns a caveat string only when completeness for the current
filter context is below 80%; blank otherwise — drives both the footer strip
and the Average PM2.5 KPI card's subtitle.

```DAX
Date Coverage =
    FORMAT ( MIN ( DimDate[date] ), "MMM yyyy" ) & " – " &
    FORMAT ( MAX ( DimDate[date] ), "MMM yyyy" )
```
One-line: the study period as a compact range string (e.g. "Jan 2022 – Dec
2023") — **new in this implementation phase**, added in
`docs/page1_executive_overview.md` §10 for the Page 1 "Date Coverage" KPI
card; not present in the original `docs/powerbi_architecture.md` catalogue.

---

## Known modelling nuance (documented, not a defect)

`Data Completeness %` and both guarded measures are defined against
`FactStationDaily[pm25_ugm3]` specifically — there is one completeness
measure, not one per pollutant. `Average PM10 (guarded)` therefore blanks
based on **PM2.5** coverage, not PM10 coverage. In practice PM10 has slightly
*more* missing rows than PM2.5 across the full dataset (119 vs. 77, per
`docs/data_dictionary.md`-adjacent Phase 1 audit figures), so this guard is
directionally conservative rather than permissive — it will not overstate
PM10's reliability. If a future page needs a PM10-specific completeness guard,
add a parallel `PM10 Completeness %` measure rather than repurposing this one.

## Naming conventions (restated, unchanged from `docs/dashboard_design_system.md` §2)

Title Case for every measure name; unit implied by the format string, never
spelled out in the name; guarded variants append `(guarded)`; the table itself
is named `Measures` (no leading underscore).
