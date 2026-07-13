# Power BI Build Manual — Delhi GRAP Analytics Platform

This is the step-by-step build manual for the `.pbix`. It assumes the reader
has `docs/powerbi_architecture.md` (semantic model), `docs/dashboard_design_system.md`
(design system), and `docs/page1_executive_overview.md` (Page 1 spec) open for
reference — this document sequences the *order of operations*, it does not
re-explain design decisions already made in those three files.

**Scope of this build pass.** Only Page 1 (Executive Overview) has an
approved implementation spec. Follow this manual through §7 (Page 1) and
stop — do not build Pages 2–5 until their own implementation specs exist
(see `powerbi/visual_inventory.md` for what's pending).

---

## 1. Import Order

Import in this exact order — later steps assume earlier tables already exist,
and Power Query's dependency graph is easier to debug when built in the
sequence the model was designed in (`docs/powerbi_architecture.md` §2).

1. **`data/processed/stations.csv`** → `DimStation`.
   In Power Query: keep `station_id`, `station_name`, `display_name`,
   `geographic_role`, `latitude`, `longitude`. Drop `operating_agency`,
   `selection_reason` (architecture §2.2). Add calculated column
   `station_sort` (design system-approved, architecture §5) once loaded.
2. **`data/processed/daily_grap_state.csv`** → `DimDate` (base rows).
   Keep all 7 source columns. This is the *base* of `DimDate` — the daily
   GRAP-state file, not a generated calendar — because `grap_stage`,
   `is_event_day`, `active_event_id`, and the two day-counters are genuine
   daily-grain facts sourced from here, not derived (architecture §2.2).
3. **Extend `DimDate`** with standard calendar columns in Power Query
   (`year`, `month`, `month_name`, `year_month`, `day_of_week`,
   `day_of_week_number`) — see §3 below for the exact steps.
4. **`data/raw/grap/grap_events_manual.csv`**, filtered to `verified = 'Yes'`
   at the Power Query step → `DimGrapEvent`. Keep `event_id`,
   `effective_date`, `order_date`, `season`, `action_type`, `stage_from`,
   `stage_to`, `event_direction`, `official_order_title`. Drop
   `immediate_effect`, `official_source`, `notes`, `verified` (architecture
   §2.2 — `verified` becomes constant once filtered, so it carries no
   information as a column).
5. **`DimStage`** — create as an entered/static table (Power Query → Enter
   Data), 5 rows, exactly as specified in `docs/powerbi_architecture.md` §2.2
   (`stage_code`, `stage_label`, `stage_short`, `stage_sort`).
6. **`data/processed/station_daily.csv`** → `FactStationDaily`.
   Keep `station_id`, `date`, `pm25_ugm3`, `pm10_ugm3`, `air_temp_c`,
   `rh_pct`, `wind_speed_ms`, `wind_dir_deg`. Drop `year`, `source_file`
   (architecture §2.1). **Do not import `station_daily_grap.csv`** — it
   denormalizes date/GRAP-state attributes across 8 rows per day; the whole
   point of steps 2–5 above is to avoid that (architecture §1).
7. **`data/processed/event_windows_master.csv`** → `FactEventWindow`.
   In Power Query: **merge in `station_id`** from `stations.csv` (join on
   `station_name`) — the source file only carries `station_name`, and every
   other relationship in this model uses the short `station_id` key
   (architecture §2.1, performance §9.5). Keep `event_id`, the new
   `station_id`, `calendar_date`, `relative_day`, `pm25_ugm3`, `pm10_ugm3`,
   `air_temp_c`, `rh_pct`, `wind_speed_ms`. Drop `event_date`,
   `wind_dir_deg`, `grap_stage`, `station_name` (now redundant with
   `station_id`), and the three boolean flags (`is_before_event`,
   `is_event_day`, `is_after_event`) — replaced by the `Period` calculated
   column in step 8.
8. **Add calculated columns** — `FactEventWindow[Period]`,
   `DimGrapEvent[stage_transition_label]` — per architecture §5. Prefer doing
   `Period` in Power Query (a conditional column on `relative_day`); do
   `stage_transition_label` either in Power Query (string concatenation) or
   as a DAX calculated column — both are equivalent for this static,
   per-row logic.
9. **Create the `Measures` table** (Modeling → New Table, one hidden
   placeholder column) and populate it per `powerbi/measures.md`, in
   folder order (KPIs → Pollution → Weather → Events → Metadata).

Do **not** import `data/processed/delhi_aqi_grap.db` for this build — per
`docs/powerbi_architecture.md` §1, its `grap_events`/`event_windows` tables
predate the current 9-event, ±7-day dataset and would need
`src/05_load_sqlite.py` re-run first. The CSV import path above is
self-consistent and current.

---

## 2. Relationship Setup

Build in **Model view**, in this order (architecture §4):

| # | From (many) | To (one) | On | Cross-filter | Active |
|---|---|---|---|---|---|
| 1 | `FactStationDaily[station_id]` | `DimStation[station_id]` | text | Single | Yes |
| 2 | `FactStationDaily[date]` | `DimDate[date]` | date | Single | Yes |
| 3 | `FactEventWindow[station_id]` | `DimStation[station_id]` | text | Single | Yes |
| 4 | `FactEventWindow[calendar_date]` | `DimDate[date]` | date | Single | Yes |
| 5 | `FactEventWindow[event_id]` | `DimGrapEvent[event_id]` | text | Single | Yes |
| 6 | `DimDate[grap_stage]` | `DimStage[stage_code]` | whole number | Single | Yes |
| 7 | `DimDate[active_event_id]` | `DimGrapEvent[event_id]` | text | Single | **No — leave inactive** |
| 8 | `DimGrapEvent[effective_date]` | `DimDate[date]` | date | Single | Yes |

After creating relationship 8, Power BI will refuse to also activate
relationship 7 automatically (two relationships between the same table
pair) — this is expected and correct; leave 7 inactive as designed
(architecture §4 explains why: it exists only as a documented alternate path
for a future `USERELATIONSHIP`-scoped measure, not for model-wide use).

**Mark `DimDate` as the official date table**: select `DimDate` →
**Table tools → Mark as date table** → key column `date`.

Verify no relationship shows as bidirectional in the relationship view —
every arrow should point one way (dimension → fact, or the smaller/lookup
side → `DimDate` for the two Dim–Dim relationships).

---

## 3. Calendar Columns on `DimDate`

Add in Power Query (preferred, cheaper than DAX calculated columns —
performance §9.6) on the `DimDate` query, after loading
`daily_grap_state.csv`:

- `year` = `Date.Year([date])`
- `month` = `Date.Month([date])`
- `month_name` = `Date.MonthName([date])` (then set **Sort by column** = `month` once loaded into the model)
- `year_month` = `Text.From([year]) & "-" & Text.PadStart(Text.From([month]), 2, "0")`
- `day_of_week` = `Date.DayOfWeekName([date])`
- `day_of_week_number` = `Date.DayOfWeek([date])` (then set **Sort by column** = `day_of_week_number`)

Set `DimDate[grap_season]`'s custom sort (2021-22 → 2022-23 → 2023-24) via a
small manual sort-key column (`grap_season_sort`: 1/2/3) if the report needs
it ordered outside alphabetical — alphabetical already happens to be correct
for these three specific labels, so this is optional, not required.

---

## 4. Theme Import

**Schema note.** `theme.json` and `theme-dark.json` use only the twelve
top-level properties Microsoft's report-theme schema has supported since
Power BI Desktop's earliest custom-theme releases and continues to support
today: `name`, `dataColors`, `background`, `foreground`, `tableAccent`,
`good`/`neutral`/`bad`, `minimum`/`center`/`maximum`, `textClasses`. An
earlier draft of this file added a `$schema` URL, custom `_comment_*`
metadata keys, and a `visualStyles` block with hand-guessed per-visual
property names — Power BI Desktop's theme validator rejected that file
outright rather than ignoring the parts it didn't recognize. Nothing below
depends on `visualStyles`; every corner-radius/shadow/border rule from the
design system is applied by hand per visual instead (step 3).

1. **Report → View → Themes → Browse for themes** → select
   `powerbi/theme.json`. Confirm the field list's default colors now show the
   8 station hues in `dataColors` order, and that the import completes
   without an error dialog.
2. Import `powerbi/theme-dark.json` as a **second** theme (Power BI Desktop
   keeps the currently-applied theme; switching between the two at report
   *runtime* — not just at author-time — is done via the bookmark mechanism
   in `docs/dashboard_design_system.md` §1.11, not by re-importing the JSON
   file live. For the author-time step: apply `theme.json` first, build
   every page against it, then separately verify `theme-dark.json` looks
   correct by applying it temporarily and reviewing each page, before
   reverting to `theme.json` as the shipped default).
3. **Apply card/table/chart formatting by hand, per visual**, since it is not
   carried by the theme file:
   - **General → Effects → Border**: on, color = ink token (`#17212B` light /
     `#F4F6F8` dark), radius 8 — apply to every Card, Table, and chart
     container.
   - **General → Effects → Shadow**: on, `rgba(23,33,43,0.08)` light /
     `rgba(0,0,0,0.30)` dark, blur 4, distance 1, position Outside.
   - **General → Effects → Background**: solid, surface token (`#FFFFFF`
     light / `#141A21` dark).
   - **Line chart → Lines**: stroke width 2, style solid, markers off (per
     design system §1.1 — no dual-axis, no marker clutter on the daily
     lines).
   - **Line chart → Y-axis gridlines**: solid, `#E2E6EA` light /
     `#232B33` dark, 1px — never dashed (see the Project Timeline's 9
     event-marker reference lines for the one deliberate, semantically
     justified exception, `docs/page1_executive_overview.md` §4).
   - **Table → Column headers**: font color `#47576B` light / `#B9C2CB`
     dark; background `#F5F7F9` light / `#0B0F14` dark.
   - **Table → Values**: font color `#17212B` light / `#F4F6F8` dark; grid
     — vertical off, horizontal `#E2E6EA` light / `#232B33` dark.
   - **Slicer**: background `#F5F7F9` light / `#0B0F14` dark; border on,
     radius 8.
   - **Card**: callout value font `#17212B` light / `#F4F6F8` dark, 28px
     Segoe UI Semibold; category label `#47576B` light / `#B9C2CB` dark,
     11px Segoe UI.

   Once a first visual of each type (Card, Table, Line chart, Slicer) is
   formatted this way, use **Format painter** (Home ribbon) to copy the
   formatting onto the remaining visuals of the same type, rather than
   repeating all of the above by hand for all 6 KPI cards etc.
4. **Provenance, kept here rather than as JSON comments** (removing the
   rationale from the JSON file is what fixed the import — Power BI's
   validator does not tolerate unrecognized keys anywhere in the document,
   including custom metadata):
   - **Station color mapping** (`dataColors`, fixed order, never cycled):
     1 Navy `#1E5FA0`=Anand Vihar, 2 Emerald `#0E7C4A`=Bawana, 3 Bronze/Gold
     `#B8860B`=Jawaharlal Nehru Stadium, 4 Teal `#0090A5`=Najafgarh, 5 Plum
     `#8A3F7A`=Narela, 6 Brick Red `#B03A2E`=Okhla Phase-2, 7 Mauve
     `#A65378`=Punjabi Bagh, 8 Terracotta `#C1622D`=R K Puram (dark-mode
     hexes in `theme-dark.json`, same order/assignment).
   - **`good`/`neutral`/`bad`** are the GRAP-stage status colors, deliberately
     **not** re-themed to navy/emerald — per the data-viz skill's fixed rule
     ("status never follows the theme"), these are the same steps already
     approved in `docs/dashboard_design_system.md` §1.1 (Stage 0 = good,
     Stage I = warning/neutral, Stage II/III/IV = critical/bad). Power BI's
     theme schema exposes only 3 named status slots for 5 GRAP stages — the
     4th distinct visual state (Stage IV vs. Stage III) is carried by icon
     weight and label text, not a 4th color, exactly as documented in
     `docs/dashboard_design_system.md` §1.1.
   - **`minimum`/`center`/`maximum`** are the diverging scale for the one
     diverging visual in the approved design (GRAP Event Explorer's
     Pre/Event/Post paired bar): Navy tint (below baseline) ↔ neutral gray
     midpoint ↔ Brick Red (above baseline).
   - **Sequential navy ramp** (one hue, light→dark — for the Page 5
     completeness heatmap, station × month), not a top-level theme property
     but applied manually as a custom conditional-formatting color scale on
     that visual: step 100 `#DDE7F1` · 200 `#B7CCE1` · 300 `#8FAFD0` · 400
     `#628FBD` · 500 `#1E5FA0` (base) · 600 `#184C80` · 700 `#133B63`.
     Configure via **Conditional formatting → Background color → Format
     style: Gradient**, minimum = step 100, maximum = step 700.
5. Confirm the categorical color validation log (recorded here for audit,
   computed via the project's data-viz skill validator, not eyeballed):

   ```
   LIGHT — node scripts/validate_palette.js "#1E5FA0,#0E7C4A,#B8860B,#0090A5,#8A3F7A,#B03A2E,#A65378,#C1622D" --mode light
     Lightness band   PASS (all 8 inside L 0.43–0.77)
     Chroma floor     PASS (all 8 >= 0.10)
     CVD separation   PASS — worst adjacent ΔE 14.6; worst all-pairs ΔE 12.6 (both >= 12 target)
     Contrast         PASS (all 8 >= 3:1 vs #FFFFFF)

   DARK — node scripts/validate_palette.js "#3A7AC0,#1D9E63,#B08010,#00A6B8,#9D4A9A,#C93A2E,#C56D93,#CB8038" --mode dark --surface "#1a1a19"
     Lightness band   PASS (all 8 inside L 0.48–0.67)
     Chroma floor     PASS (all 8 >= 0.10)
     CVD separation   PASS — worst adjacent ΔE 13.5; worst all-pairs ΔE 8.6 (floor band — legal because every
                       station is always directly labeled: table swatch + name, chart legend/direct label —
                       never color-only identity)
     Contrast         PASS (all 8 >= 3:1 vs #1a1a19)

   Text/chrome contrast (computed via the validator's exported contrast() function, not eyeballed):
     Primary ink #17212B on white #FFFFFF        16.29:1
     Secondary ink #47576B on white #FFFFFF       7.39:1
     Muted ink #7C8896 on white #FFFFFF           3.61:1  (>= 3:1 large-text/graphical floor)
     Primary ink #F4F6F8 on dark surface #141A21 16.16:1
     Secondary ink #B9C2CB on dark surface        9.71:1
     Muted ink #7C8896 on dark surface            4.85:1
   ```

   Do not alter `dataColors` in either theme file without re-running the
   validator — see the data-viz skill's `references/color-formula.md`
   ("snap-to-passing" procedure) if a future rebrand changes any hue.

---

## 5. Icon Assets

`powerbi/assets/*.svg` (6 files) are simple, single-color outline icons at
24×24, stroke `#47576B` (muted ink, matches the nav bar's at-rest icon
color per design system §1.8). Each maps to one nav destination:

| File | Used for |
|---|---|
| `icon-executive.svg` | Page Navigator entry / Executive Overview |
| `icon-air-quality.svg` | Page Navigator entry / Air Quality Explorer |
| `icon-grap.svg` | Page Navigator entry / GRAP Event Explorer |
| `icon-research.svg` | Page Navigator entry / Research Findings |
| `icon-methodology.svg` | Page Navigator entry / Methodology & Trust |
| `icon-about.svg` | Nav bar "About" button |

**To use as a Button icon:** select the button → **Format → Icon → Image →
Custom** → browse to the SVG. Power BI buttons support separate images per
interaction state (Default / On Hover / On Press / Disabled); these SVGs are
provided as the **Default** state only. For the hover state (per design
system §1.8, "icon shifts from muted to primary ink"), duplicate the SVG and
recolor the `stroke` (and any `fill="#47576B"` accent dot) from `#47576B` to
`#17212B`, saved as e.g. `icon-about-hover.svg` — not pre-generated here
since it is a one-line find/replace on an already-provided file, not a new
design decision.

**To use on the Page Navigator visual:** the Page Navigator visual generates
its own entries from the report's page list and does not accept custom SVG
icons per entry in most Power BI Desktop versions — if the build's version
supports custom page icons, assign these files there; otherwise, build the
nav bar as 5 individual Buttons (icon + page-navigation action set via
**Action → Type: Page navigation**) instead of the Page Navigator visual, and
apply the SVGs there. Note this as a build-time judgment call depending on
the exact Power BI Desktop version in use — not a design ambiguity, a tooling
one.

---

## 6. Measure Creation

Create the `Measures` table first (§1, step 9), then create every measure in
`powerbi/measures.md`, **in folder order**, setting each measure's **Home
table** = `Measures` and **Display folder** = the folder name from the
catalogue (`KPIs`, `Pollution`, `Weather`, `Events`, `Metadata`) before moving
to the next. Creating them in this order means every measure a later one
depends on (`Data Completeness %` is referenced by both guarded measures and
`Coverage Caveat`) already exists when needed:

1. `KPIs` — all 5 (Total Observations, Monitoring Stations, Verified GRAP
   Events, Active GRAP Days, **Data Completeness %** last in this folder,
   since later folders depend on it).
2. `Pollution` — all 8, in the order listed in `measures.md`.
3. `Weather` — all 3.
4. `Events` — all 6.
5. `Metadata` — all 5, including the new `Date Coverage` measure.

After creating all 23 measures, set each one's format string individually:
whole-number counts plain thousands-separated, PM2.5/PM10 measures
`0.0 "µg/m³"`, temperature `0.0 "°C"`, humidity `0.0 "%"`, wind speed
`0.00 "m/s"`, `Data Completeness %` as `0.0%`. Text measures (`Selected
Season Label`, `Data As Of`, `Truncated Season Flag`, `Coverage Caveat`,
`Date Coverage`) need no numeric format.

---

## 7. Visual Creation Order (Page 1 — Executive Overview)

Build in this order — background-to-foreground, matching the Selection Pane
z-order target in `docs/page1_executive_overview.md` §9, so later visuals
never need to be manually sent behind earlier ones:

1. **Page setup.** New page, canvas size 1280×720 (**Format page → Canvas
   settings → Type: Custom, 1280×720**). Rename the page "Executive
   Overview". Apply page background = page-plane token (`#F5F7F9` light /
   `#0B0F14` dark — set via **Format page → Canvas background**).
2. **Background layer** — footer strip background (if any) and any full-page
   guide rectangles.
3. **KPI row** — all 6 Card visuals, left to right, per `visual_inventory.md`
   positions. Bind measures, set icons, set the Data Completeness card's
   conditional formatting rules.
4. **Primary content**:
   a. Left — Monitoring Station table (build the conditional-formatting
      color rules after the base table renders correctly).
   b. Center — Timeline line chart (build the plain line first, confirm it
      renders correctly against `DimStage` via tooltip, *then* add the 9
      Analytics-pane reference lines one at a time — easier to debug 9 lines
      against a working base chart than to add all 9 before confirming the
      chart itself is correct).
   c. Right — Project Summary card background + text box.
5. **Bottom section** — pipeline title/subtitle, then the 8 chips left to
   right, then the 7 chevrons between them (chips before chevrons, so
   chevron z-order sits visibly on top in the gaps).
6. **Filters panel** — background rectangle + 2 slicers, built off-canvas or
   in place, then wired to the bookmark in step 8.
7. **About panel** — scrim rectangle, panel rectangle, text content, close
   button, built off-canvas (e.g., positioned below the visible canvas at
   design time) then wired to its bookmark.
8. **Bookmarks** (View → Bookmarks pane): capture **Default state** first
   (everything at its resting position/visibility), then toggle the Filters
   panel visible and capture **Filters panel open**, then toggle it back off
   and the About panel visible and capture **About panel open**. Bind each
   nav-bar button's **Action** to the corresponding bookmark.
9. **Navigation bar** — background, title, Page Navigator (or 5 buttons, per
   §5 note), Filters/Reset/About buttons — built last so it visually sits on
   top of everything beneath it (highest z-order on the page, matching the
   Selection Pane target order).
10. **Footer caveat strip** — bind to `Truncated Season Flag` and
    `Coverage Caveat`; confirm both go blank under default (unfiltered)
    conditions and reappear correctly when the 2023-24 season or a
    low-coverage filter is selected.
11. **Tooltip page** — create the separate "Timeline tooltip" page (**Format
    page → Page information → Tooltip = On**), set its canvas to 320×240,
    build the Card/Text content, then on the Timeline line chart set
    **Format visual → Tooltips → Type: Report page → Page: Timeline
    tooltip**.
12. **Edit interactions pass.** With the KPI row visuals selected one at a
    time, use **Format → Edit interactions** to confirm the Left table and
    the Center chart both show **None** against every KPI card (they default
    to Filter/Highlight — this step must be done explicitly, it does not
    happen automatically).
13. **Selection Pane cleanup.** Rename every shape/text box from its Power
    BI default name to a descriptive one, and confirm group order matches
    `docs/page1_executive_overview.md` §9.
14. **Accessibility pass.** Set **Tab Order** (View → Tab Order) to: nav bar
    → filters button → reset → about → KPI row (left to right) → left table
    → center chart → right summary. Add Alt Text to every visual (Format
    visual → General → Alt text) describing its content, not just its type.
15. **Performance Analyzer pass** (per `docs/dashboard_design_system.md`
    §8): View → Performance Analyzer → Start Recording → refresh the page →
    open the Filters panel → open the About panel → hover the timeline →
    Stop. Review per-visual load time; investigate any visual consistently
    over ~1 second (almost always a DAX issue at this data volume, not a
    genuine performance ceiling).

**Stop here.** Do not begin Page 2 until `docs/page2_air_quality_explorer.md`
exists, per this prompt's scope.
