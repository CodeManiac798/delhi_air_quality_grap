# Visual Inventory — Delhi GRAP Analytics Platform

Every visual on every page, transcribed from the approved implementation
specs. **Page 1 is fully detailed** (it is the only page with a complete,
pixel-level implementation spec — `docs/page1_executive_overview.md`).
**Pages 2–5 are listed at the level of detail currently approved** — the
high-level visual list from `docs/dashboard_design_system.md` §3 — because no
implementation spec exists for them yet. Inventing exact fields/positions for
those four pages now would be designing UX beyond what has been approved;
this document only transcribes what already has a design decision behind it.

---

## Page 1 — Executive Overview *(fully specified — build from this table)*

### Top Navigation Bar

| Visual Name | Power BI Visual Type | Fields | Measures | Formatting | Interactions |
|---|---|---|---|---|---|
| Nav Bar Background | Rectangle (shape) | — | — | Fill `#FFFFFF`; 1px bottom border `rgba(23,33,43,0.10)`; no radius; no shadow; `x0,y0,w1280,h56` | Non-interactive |
| Project Title | Text box | — | — | "Delhi GRAP Analytics Platform"; Segoe UI Semibold 16px; `#17212B`; `x24,y8,w360,h40` | Non-interactive |
| Global Navigation | Page Navigator | Report page list | — | Horizontal; 5 entries; only *Executive Overview* enabled, other 4 in disabled/muted styling; `x400,y8,w480,h40` | Click → navigate (enabled entry only) |
| Filters button | Button (icon+label) | — | — | Funnel icon + "Filters"; secondary/icon style (§1.10); `x896,y8,w74,h40` | On click → apply "Filters panel open" bookmark |
| Reset button | Button (icon+label) | — | — | Circular-arrow icon + "Reset"; `x978,y8,w84,h40` | On click → apply "Default state" bookmark |
| About button | Button (icon+label) | — | — | Info-circle icon + "About"; `x1170,y8,w86,h40` | On click → apply "About panel open" bookmark |

### KPI Row

| Visual Name | Power BI Visual Type | Fields | Measures | Formatting | Interactions |
|---|---|---|---|---|---|
| KPI — Monitoring Stations | Card | — | `Measures[Monitoring Stations]` | Whole number; label "Monitoring Stations"; station-pin icon; no delta; `x24,y64,w192,h120` | Edit interactions → all in-page visuals = **None** (never cross-filtered by a click) |
| KPI — Total Observations | Card | — | `Measures[Total Observations]` | Whole number, thousands-separated; database icon; no delta; `x232,y64,w192,h120` | Same as above |
| KPI — Verified GRAP Events | Card | — | `Measures[Verified GRAP Events]` | Whole number; calendar-check icon; no delta; `x440,y64,w192,h120` | Same as above |
| KPI — Date Coverage | Card | — | `Measures[Date Coverage]` | Text value (e.g. "Jan 2022 – Dec 2023"); calendar-range icon; no delta; `x648,y64,w192,h120` | Same as above |
| KPI — Average PM2.5 | Card | — | `Measures[Average PM2.5 (guarded)]`; subtitle `Measures[Coverage Caveat]` | `0.0 "µg/m³"`; no icon (deliberately neutral — §1.10 rationale); no delta | Same as above |
| KPI — Data Completeness | Card | — | `Measures[Data Completeness %]` | `0.0%`; shield-check icon; conditional font color (rules): ≥80% good `#0ca30c`, 50–79% warning `#fab219`, <50% critical `#d03b3b`; no delta arrow | Same as above |

### Main Body — Left

| Visual Name | Power BI Visual Type | Fields | Measures | Formatting | Interactions |
|---|---|---|---|---|---|
| Monitoring Station Overview | Table | `DimStation[station_name]`, `DimStation[geographic_role]`; sort by `DimStation[station_sort]`; leading blank column | — | Conditional formatting → background color → Rules, one rule per `station_name` mapping to the 8 `dataColors` hexes; 1px hairline row dividers; header muted ink; 10px body; `x24,y200,w280,h380` | Edit interactions → KPI row = **None** (§8) |

### Main Body — Center

| Visual Name | Power BI Visual Type | Fields | Measures | Formatting | Interactions |
|---|---|---|---|---|---|
| Project Timeline | Line chart | X: `DimDate[date]`; Y: `DimDate[grap_stage]` (Max) | — (no measure; direct column aggregation) | Single line, 2px, slot-1 navy `#1E5FA0`; no legend (one series); Y-axis ticks 0–4, axis title "GRAP Stage (0 = None · IV = Severe+)"; solid hairline gridlines; `x320,y200,w560,h380` | Hover → "Timeline tooltip" report page; Edit interactions → KPI row = **None** (§8) |
| Timeline event markers (×9) | Analytics-pane constant/reference lines (part of the Line chart above, not separate visual objects) | `DimGrapEvent[effective_date]` (manually entered per line), `DimGrapEvent[event_direction]`, `DimGrapEvent[stage_transition_label]` (manually entered as each line's Label text) | — | Vertical, 1px, dashed; color by direction: escalation/activation `#d03b3b`, de-escalation `#0ca30c`; label = e.g. "E004: III→IV" | Static (no click action); label always visible |

### Main Body — Right

| Visual Name | Power BI Visual Type | Fields | Measures | Formatting | Interactions |
|---|---|---|---|---|---|
| Project Summary card background | Rectangle | — | — | Card surface `#FFFFFF`; 8px radius; hairline border; soft shadow; `x896,y200,w360,h380` | Non-interactive |
| Project Summary text | Text box | — | — | 4 sub-headed paragraphs (Research Objective / Data Sources / Study Scope / Methodology Summary); headers Segoe UI Semibold 11px `#17212B`; body Segoe UI Regular 10px `#47576B`; 16px padding | Non-interactive; static content |

### Bottom Section — Pipeline Overview

| Visual Name | Power BI Visual Type | Fields | Measures | Formatting | Interactions |
|---|---|---|---|---|---|
| Pipeline title/subtitle | Text box | — | — | "Pipeline Overview" (13px semibold) + subtitle (10px muted); `x24,y588,w1232,h24` | Non-interactive |
| Pipeline chips (×8) | Rectangle (shape), one per stage: Raw Data, Validation, Engineering, EDA, Event Analysis, Sensitivity Analysis, Weather Context, Power BI | — | — | Rounded rect, 8px radius, 6%-primary-ink wash fill, 1px hairline border, centered 10px semibold label; last chip ("Power BI") gets a 2px navy bottom border ("you are here"); ~130px wide, 40px tall, `y=620` | Non-interactive; native hover title only |
| Pipeline chevrons (×7) | Text box or Icon shape (`›`) | — | — | Muted ink `#7C8896`, vertically centered between chips | Non-interactive |

### Footer & Overlays

| Visual Name | Power BI Visual Type | Fields | Measures | Formatting | Interactions |
|---|---|---|---|---|---|
| Footer caveat strip | Text box (dynamic) | — | `Measures[Truncated Season Flag]`, `Measures[Coverage Caveat]` | Muted ink `#7C8896`, 9px; blank unless true for current context; static trailing clause "Descriptive analysis only — not causal inference. See Methodology & Trust."; `x24,y688,w1232,h32` | Trailing clause links to Page 5 (inert until built) |
| Filters flyout panel | Rectangle (background) + 2 Slicer visuals | `DimDate[grap_season]`, `DimStation[station_name]`/`geographic_role` | — | Card surface, 8px radius, shadow; slide-down overlay | Bookmark-toggled by nav bar Filters button; slicers are members of the cross-page Sync Slicers group |
| About overlay panel | Rectangle (scrim, full canvas, 40% opacity) + Rectangle (panel, 720×480 centered) + Text box(es) + Close button | — | `Measures[Monitoring Stations]`, `Measures[Total Observations]`, `Measures[Verified GRAP Events]`, `Measures[Date Coverage]` (live "Dataset" section only — rest is static text) | Card surface, 8px radius, shadow, centered | Bookmark-toggled by nav bar About button; "Read full methodology →" link navigates to Page 5 (inert until built) and closes panel |
| Timeline tooltip (separate report page, Page type = Tooltip) | Card ×2–3 + Text box | `DimStage[stage_label]`, `DimGrapEvent[action_type]`, `DimGrapEvent[official_order_title]` (populated only on event dates) | — | 320×240px canvas; card surface, 8px radius, shadow | Triggered by hovering the Project Timeline line |

---

## Page 2 — Air Quality Analysis *(built — planned as "Air Quality Explorer" in `docs/dashboard_design_system.md` §3)*

Built directly in Power BI Desktop rather than from a written implementation
spec (the approach `docs/page1_executive_overview.md` used for Page 1). As
shipped: a pollution trend line chart, three slicers (station/season filters),
and three text panels, under the display name "Air Quality Analysis." The
original approved visual list (station box plot, weather small multiples,
monthly variability box plot) describes the design intent; the built page is a
streamlined version of it, not a literal match — this file has not been
updated to a full visual-by-visual inventory for the as-built page.

## Page 3 — GRAP Intervention Analysis *(built — planned as "GRAP Event Explorer," the flagship page)*

Built directly in Power BI Desktop. As shipped: an event-relative pollution
trend line chart with three slicers, under the display name "GRAP Intervention
Analysis." As with Page 2, this is a streamlined build against the approved
design intent rather than a page matching the original visual list
line-for-line.

## Page 4 — Weather Context Analysis *(built — a different page than the "Research Findings" originally planned for this slot)*

The dashboard as built substitutes a dedicated **Weather Context Analysis**
page (three weather line charts, three slicers, three text panels) in place
of the "Research Findings" page sketched in `docs/dashboard_design_system.md`
§3 — a legitimate build-time decision to give weather its own page rather than
a separate findings page. `docs/dashboard_design_system.md` has not been
updated to reflect this substitution.

## Page 5 — Methodology & About *(built — planned as "Methodology & Trust")*

Built directly in Power BI Desktop as a text-only page (6 text boxes, no
filters), under the display name "Methodology & About." Matches the design
intent of a static, citable page; the specific sub-sections (pipeline diagram,
completeness heatmap, claim lists, glossary) were not verified visual-by-visual
against this inventory.

---

## Cross-page assets (not page-specific)

| Asset | Power BI Object Type | Notes |
|---|---|---|
| `Measures` table | Disconnected table | See `powerbi/measures.md` |
| Report theme | Theme file | `powerbi/theme.json` (default), `powerbi/theme-dark.json` (dark-mode bookmark target) |
| Nav/section icons | Image (uploaded SVG) or button icon | `powerbi/assets/*.svg` — see README §5 for exact upload steps |
