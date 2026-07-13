# Page 1 — Executive Overview: Implementation Specification

**Scope.** This document is the buildable implementation spec for exactly one
report page, per this prompt's instruction to implement Page 1 only. It uses
the finalized semantic model (`docs/powerbi_architecture.md`) and the
finalized design system (`docs/dashboard_design_system.md`) without altering
either — the two additions flagged below (one new measure, one map→list
substitution) are implementation necessities, called out explicitly rather
than silently introduced, not redesigns.

**Page objective (the one question this page answers):** *"What is this
project and what does it contain?"* Every visual below exists to answer that
orientation question. None of them perform the station-level, time-series, or
event-level analysis that Pages 2–4 own — this page tells a first-time viewer
what the platform is, not what it has found.

**Canvas.** 1280 × 720, matching every other page (design system §1.5).

**Two flagged additions, stated up front:**

1. **New measure required:** `Measures[Date Coverage]` (Metadata folder) did
   not exist in the finalized measure catalogue. It is a small text measure,
   in the same style already established for `Data As Of` — see "New DAX
   Required" below.
2. **Map → list substitution:** `docs/powerbi_architecture.md` §2.2 notes
   `DimStation[latitude]`/`[longitude]` are **currently blank for all 8
   rows**. A Map visual would render 8 unplotted points or an empty canvas.
   Per this prompt's own fallback instruction, the LEFT panel is built as a
   **station list**, not a map. Revisit a Map visual once coordinates are
   verified and populated (tracked already as a hidden-until-populated field
   in the design system, §1 Field Catalogue).

---

## Layout Overview (region map)

```
y=0    ┌──────────────────────────────────────────────────────────────────┐
       │  TOP NAVIGATION BAR                                    h=56      │
y=56   ├──────────────────────────────────────────────────────────────────┤
y=64   │  KPI ROW  (6 cards)                                     h=120    │
y=184  ├───────────────┬──────────────────────────────┬───────────────────┤
       │  LEFT          │  CENTER                       │  RIGHT           │
y=200  │  Monitoring    │  Project Timeline              │  Project        │
       │  Station       │  (GRAP stage + 9 verified      │  Summary        │
       │  Overview      │  events, 2022–2023)            │                 │
       │  w=280         │  w=560                         │  w=360          │
y=580  ├───────────────┴──────────────────────────────┴───────────────────┤
y=588  │  PIPELINE OVERVIEW  (8-stage process strip)             h=92     │
y=680  ├──────────────────────────────────────────────────────────────────┤
y=688  │  FOOTER CAVEAT STRIP                                     h=32     │
y=720  └──────────────────────────────────────────────────────────────────┘
```

All x-positions use the 24px outer margin / 16px gutter grid from design
system §1.5. Region widths recap: LEFT `x=24,w=280`; CENTER `x=320,w=560`;
RIGHT `x=896,w=360` (896+360 = 1256 = 1280−24, flush with the right margin).

---

## 1. Top Navigation Bar

| Attribute | Spec |
|---|---|
| **Visual placement** | Rectangle background `x=0,y=0,w=1280,h=56` |
| **Exact visual types** | 1 background Rectangle shape · 1 Text box (title) · 1 Page Navigator visual · 1 Button (Filters) · 1 Button (Reset) · 1 Button (About This Analysis) |
| **Required fields** | Page Navigator: bound to the report's page list (no data fields — it reads the page collection) |
| **Formatting** | Background rectangle: fill = card surface `#fcfcfb` (dark: `#1a1a19`), 1px bottom hairline border (`rgba(11,11,11,0.10)`), no corner radius (full-bleed bar), no shadow |
| **Titles** | Title text box, `x=24,y=8,w=360,h=40`: **"Delhi GRAP Analytics Platform"**, Segoe UI Semibold 16px, primary ink, vertically centered, left-aligned |
| **Subtitles** | None on the nav bar itself |
| **Interactions** | See §8 (Interactions) below |

**Sub-element placements:**

| Element | x | y | w | h | Detail |
|---|---|---|---|---|---|
| Page Navigator | 400 | 8 | 480 | 40 | Horizontal orientation, 5 entries in fixed order (Executive Overview · Air Quality Explorer · GRAP Event Explorer · Research Findings · Methodology & Trust). **Build note:** only *Executive Overview* is an active/enabled destination in this phase — the other four pages do not exist yet in the `.pbix` (out of scope per this prompt). Configure the Page Navigator's four not-yet-built entries in its **disabled-state** styling (muted ink, no hover wash, non-clickable) rather than omitting them, so the finished nav bar's structure does not need rework when Pages 2–5 are implemented in a later phase. |
| Filters button | 896 | 8 | 74 | 40 | Icon: funnel outline (design system §1.6) + label "Filters". Opens the collapsible slicer panel — see §8. |
| Reset button | 978 | 8 | 84 | 40 | Icon: circular-arrow + label "Reset". Applies the page's default-state bookmark. |
| About button | 1170 | 8 | 86 | 40 | Icon: info-circle + label "About". Opens the About overlay panel (design system §5). |

(Filters/Reset/About use the secondary/icon button style, design system §1.10:
transparent fill, 1px hairline border, 8px radius, primary ink on hover.)

---

## 2. Top KPI Row

Six cards, one row, `y=64` to `y=184` (h=120 each), per the design system's
KPI-row budget (§8: max 6 cards). Card width 192px, gutter 16px, starting
`x=24` (positions: 24, 232, 440, 648, 856, 1064 — last card ends at 1256,
flush with the right margin).

Every card uses the **Card** visual (Power BI's modern card, not the legacy
"KPI" visual), styled per design system §1.3 (8px radius, hairline border,
soft shadow, 16px padding, semibold proportional value, sentence-case label,
no trailing colon).

| # | Position (x) | Label | Field (measure) | Format | Delta | Icon |
|---|---|---|---|---|---|---|
| 1 | 24 | Monitoring Stations | `Measures[Monitoring Stations]` | Whole number, e.g. `8` | None (a roster count, not a performance indicator) | Station/pin outline |
| 2 | 232 | Total Observations | `Measures[Total Observations]` | Whole number, thousands-separated, e.g. `5,840` | None | Table/database outline |
| 3 | 440 | Verified GRAP Events | `Measures[Verified GRAP Events]` | Whole number, e.g. `9` | None | Calendar-check outline |
| 4 | 648 | Date Coverage | `Measures[Date Coverage]` **(new — see §10)** | Text, e.g. `Jan 2022 – Dec 2023` | None (a range, not a number) | Calendar-range outline |
| 5 | 856 | Average PM2.5 | `Measures[Average PM2.5 (guarded)]` | `0.0 "µg/m³"` | None (no baseline period is defined in the approved model to compare against) | none (kept deliberately unadorned — see note below) |
| 6 | 1064 | Data Completeness | `Measures[Data Completeness %]` | `0.0%` | None; **conditional font color** on the value instead (rule-based, not a delta arrow): ≥80% → good `#0ca30c`; 50–79% → warning `#fab219`; <50% → critical `#d03b3b` | Shield-check outline |

**Subtitles (caption line beneath the value, muted ink, 9px):**
- Card 5 (Average PM2.5): bound to `Measures[Coverage Caveat]`. Blank under
  normal (unfiltered, well-observed) conditions; appears only if a user
  filters into a thinly-observed slice — exactly the guarded-measure pattern
  in design system §1.3.
- Cards 1–4 and 6: no subtitle.

**Why no PM2.5 icon and no status color on the PM2.5 value.** Design system
§1.10/§1.1 reserves status colors for *state* (GRAP severity, data
completeness), never for a pollutant magnitude — coloring PM2.5 by severity
would imply an evaluative judgement ("this level is bad") that the project's
non-causal, descriptive stance does not make. Card 5 stays visually neutral;
only Card 6 (a genuine completeness *state*) uses conditional color.

---

## 3. LEFT — Monitoring Station Overview

| Attribute | Spec |
|---|---|
| **Visual placement** | `x=24, y=200, w=280, h=380` |
| **Exact visual type** | **Table** visual (not a Map — see the flagged substitution above) |
| **Required fields** | `DimStation[station_name]`, `DimStation[geographic_role]`; sort by `DimStation[station_sort]` (the calculated column already specified in `docs/powerbi_architecture.md` §5) |
| **Formatting** | A narrow leading column (header blank) carries a **background-color swatch per row**, set via **Conditional formatting → Background color → Format style: Rules**, one rule per `station_name` value, using the exact 8 hex values from design system §1.1 (e.g. `station_name = "Anand Vihar" → #2a78d6`). This is a report-level formatting rule — no new column, no model change. Table style: minimal, no banded rows, 1px hairline row dividers (gridline token), header row in muted ink, 10px body text. |
| **Title** | "Monitoring Station Overview" |
| **Subtitle** | "8 CPCB-operated stations across Delhi-NCR" (static — the count is fixed at the model's current scope; if a future station is added, update this string alongside the model) |
| **Interactions** | Row click **disabled as a KPI-affecting filter** — see §8 |

Columns, left to right: `[color swatch]` · Station Name · Geographic Role.
No per-station PM2.5/PM10 figures on this table — that analysis belongs to
Page 2 (Air Quality Explorer); repeating it here would violate the
decision-first/minimal principle for a page whose only job is orientation.

---

## 4. CENTER — Project Timeline

| Attribute | Spec |
|---|---|
| **Visual placement** | `x=320, y=200, w=560, h=380` |
| **Exact visual type** | **Line chart** (single series) + **9 manually-configured Analytics-pane constant/reference lines** |
| **Required fields** | X-axis: `DimDate[date]`. Y-axis: `DimDate[grap_stage]` (aggregation: Max — at one row per day this is equivalent to any aggregation, Max is the safest explicit choice). Tooltip fields (see §8): `DimStage[stage_label]` (via the `DimDate → DimStage` relationship), `DimGrapEvent[official_order_title]`, `DimGrapEvent[action_type]` (only populated on the 9 event dates) |
| **Formatting** | Single line, 2px, categorical slot 1 (blue `#2a78d6`) — one series, so **no legend box** (design system / data-viz rule: a single series needs no legend; the title already names what's plotted). Y-axis: numeric ticks 0–4, axis title **"GRAP Stage (0 = None · IV = Severe+)"** so the numeric axis is self-explanatory without requiring a separate legend. X-axis: date, ticks by quarter or month, format `MMM yyyy`. Gridlines: solid hairline, one step off surface (never dashed — anti-pattern). |
| **Event markers** | 9 constant/reference lines added via the visual's **Analytics** pane, one per verified event, each: vertical, thin (1px), **dashed** (a deliberate, semantically-justified exception to the "gridlines are never dashed" rule — these are annotations marking a specific date, not background grid, and there are only 9 of them, so dashing reads as "marker" rather than noise), positioned at that event's `effective_date`, colored by `event_direction`: **escalation/activation → critical `#d03b3b`**, **de-escalation → good `#0ca30c`**. Each line's built-in **Label** field is set to a short static string, e.g. `"E004: III→IV"`, sourced from `DimGrapEvent[stage_transition_label]` (already an approved calculated column) — since Power BI's Analytics-pane lines are configured once per fixed value, this is a **manual, one-time setup for the current 9 events**, not a dynamic binding. **Maintenance note:** if a future season's events are verified and added to `DimGrapEvent`, add the corresponding reference line(s) by hand — a small, deliberate manual step, consistent with the project's existing human-verification requirement for every GRAP event in the first place. |
| **Title** | "Project Timeline — GRAP Stage & Verified Events (2022–2023)" |
| **Subtitle** | "Daily active GRAP stage, with all 9 verified interventions marked" |
| **Interactions** | Hover shows the **Timeline tooltip page** (§8); data-point click **disabled as a KPI-affecting filter** — see §8 |

**Why a single-axis line + reference lines, not a dual-axis chart.** This
chart deliberately does not overlay PM2.5 on a second y-axis — that would be
exactly the dual-axis anti-pattern the design system already ruled out
(§1.1). Both series that appear here (the stage line and the 9 event
markers) share the identical 0–4 stage scale; nothing on this chart uses a
second, independently-scaled axis.

---

## 5. RIGHT — Project Summary

| Attribute | Spec |
|---|---|
| **Visual placement** | One card container `x=896, y=200, w=360, h=380`, containing a single **Text box** with four sub-headed paragraphs |
| **Exact visual type** | Rectangle (card background, 8px radius, hairline border, soft shadow — design system §1.3) + 1 Text box |
| **Required fields** | None — static, curated text, sourced from already-approved project documentation (not new prose) |
| **Formatting** | Section sub-headers: Segoe UI Semibold 11px, primary ink. Body: Segoe UI Regular 10px, secondary ink. 16px internal padding, 8px spacing between the four sub-sections. |
| **Title** | "Project Summary" (13px semibold, card-title style, above the text box) |
| **Subtitle** | None (the four sub-headers inside the text box serve this role) |
| **Content (condensed, verbatim in spirit from `docs/analysis_plan.md` and `README.md` — not newly authored characterizations)** | See below |
| **Interactions** | None — static content, no fields to filter |

**Content, four sub-sections:**

1. **Research Objective** — "How did PM2.5 and PM10 levels at Delhi's
   monitoring stations behave in the days immediately surrounding official
   GRAP stage changes between 2022 and 2023, and was that pattern consistent
   across stations and events?" (`docs/analysis_plan.md` §1, verbatim).
2. **Data Sources** — "Central Pollution Control Board (CPCB) daily station
   data (8 DPCC-operated monitors), and a manually verified calendar of
   official CAQM GRAP orders." (condensed from `README.md`).
3. **Study Scope** — "8 monitoring stations across Delhi-NCR, 2022–2023.
   PM2.5 is the primary outcome, PM10 secondary, alongside core weather
   variables. AQI is not used in this phase." (condensed from `README.md`).
4. **Methodology Summary** — "A descriptive, non-causal analysis: event
   windows around verified GRAP stage changes, station and cross-event
   comparison, and weather context — not a claim that GRAP caused any
   pattern observed. Full methodology on the Methodology & Trust page."
   (condensed from `README.md` "Methodological position" and
   `docs/analysis_plan.md` §2).

---

## 6. Bottom Section — Pipeline Overview

| Attribute | Spec |
|---|---|
| **Visual placement** | `x=24, y=588, w=1232, h=92` (section title band + chip row) |
| **Exact visual types** | 1 section Text box (title+subtitle) · 8 rounded-Rectangle shapes ("chips") · 7 small chevron glyphs (Text boxes or Icon shapes, `›`) between them |
| **Required fields** | None — static process graphic, no data binding |
| **Formatting** | Chips: rounded rectangle, 8px corner radius (global constant, design system §1.4), fill = 6%-opacity primary-ink wash on the page-plane token (visually distinct from — not identical to — the KPI cards, so the two are not confused), 1px hairline border, label centered, Segoe UI Semibold 10px, primary ink. Chevrons: muted ink, vertically centered between chips. **Last chip ("Power BI") gets a 2px bottom border in the primary blue accent** — a "you are here" indicator, since this dashboard *is* that final pipeline stage. |
| **Layout** | 8 chips, ~130px wide each, ~26px chevron gaps: `8×130 + 7×26 = 1,222px`, fits the 1,232px band with small residual margin. Chip height 40px, vertically centered in the 92px band beneath a title/subtitle line. |
| **Title** | "Pipeline Overview" |
| **Subtitle** | "From raw CPCB station data to this dashboard — every stage validated before the next began." |
| **Chip sequence (left to right)** | Raw Data → Validation → Engineering → EDA → Event Analysis → Sensitivity Analysis → Weather Context → **Power BI** *(current)* |
| **Interactions** | None — static graphic, no click targets, no tooltips beyond a plain hover title (native, not a report tooltip page — this is deliberately the simplest interactive element on the page) |

**Why native shapes, not a custom AppSource visual.** Power BI has no native
flowchart component; a certified custom visual could render this more
elaborately, but a government/enterprise deployment commonly restricts
third-party AppSource visuals pending security review. Building the pipeline
strip from native Rectangle/Text/Icon objects avoids that dependency entirely
and keeps the page fully portable.

---

## 7. Footer Caveat Strip

Per design system §6 — present on every page, unchanged here:
`x=24, y=688, w=1232, h=32`, muted ink, left-aligned, driven by
`Measures[Truncated Season Flag]` and `Measures[Coverage Caveat]` (blank
unless true for the current filter context), plus the static trailing clause
*"Descriptive analysis only — not causal inference. See Methodology &
Trust."* linking to Page 5 (link inert until Page 5 exists — see nav bar
build note, §1).

---

## 8. Interactions

| Interaction | Specification |
|---|---|
| **Global navigation** | Active, per §1. Only the *Executive Overview* destination is live in this phase; the other four show in disabled styling until built. |
| **Global slicers** | `DimDate[grap_season]` and `DimStation[station_name]`/`geographic_role` slicers live inside the **Filters flyout panel**, toggled by the nav-bar Filters button via a bookmark (slide-down panel, same overlay mechanism as the About panel — design system §5). Kept off-canvas by default so Page 1's fixed layout above is not disturbed by a permanently-docked slicer row. Slicers are members of the cross-page **Sync Slicers** group defined in design system §4 (synced to Pages 2–3 once built). |
| **Cross-highlighting / cross-filtering** | Power BI default (filter propagation, single-direction, per the finalized model) applies between the CENTER timeline and the LEFT table **only insofar as the global slicers scope both** — no visual-to-visual click-filtering is enabled between them. **Explicitly disabled:** using **Format → Edit interactions**, both the LEFT Table and the CENTER Line chart are set to **"None"** against all six KPI cards. This means clicking a station row or a single date on the timeline never re-scopes a KPI to that single row/date — KPI cards always reflect only the current global-slicer context, never a transient in-page click. This is the concrete implementation of this prompt's "cross-highlighting disabled where it would distort KPI cards." |
| **Tooltips** | One new, page-appropriate **report tooltip page** — "Timeline tooltip" (320×240px card, per design system §1.9) — shown on hovering any point on the CENTER line: date, `DimStage[stage_label]` for that day, and — only on the 9 dates where populated — `DimGrapEvent[action_type]` and `DimGrapEvent[official_order_title]`. (This is deliberately a lighter tooltip than Page 2/3's weather-context tooltip — Page 1 shows no weather data, so the tooltip does not manufacture weather context it doesn't display.) The LEFT table and KPI cards use Power BI's default hover (no custom tooltip page needed — nothing on them requires more context than is already visible). |
| **Bookmarks** | Three for this page: **default state** (Reset target — no slicers applied, Filters panel closed, About panel closed), **Filters panel open**, **About panel open**. |
| **Reset button** | Applies the *default state* bookmark (§1). |
| **Drillthrough / sync slicers** | None originate on this page in this phase — Station Detail and Event Detail drillthrough targets (design system §4) live on Pages 2–3, not built yet. |

---

## 9. Selection Pane Organization

Following design system §4's naming/z-order convention, this page's groups:

```
05 - Tooltip trigger layer          (invisible hover targets, if any beyond native)
04 - Navigation                     (nav bar rectangle, title, page navigator, 3 buttons)
03 - Filters panel (hidden by default, bookmark-toggled)
02 - Primary content
     ├─ Left: Station table
     ├─ Center: Timeline chart + 9 reference lines
     ├─ Right: Project summary card
     └─ Bottom: Pipeline chips + chevrons
01 - KPI row                        (6 cards)
00 - Background                     (page plane, footer strip)
```

Every shape/text box is renamed from its Power BI default (e.g. "Rectangle
14") to a descriptive name (e.g. "Pipeline chip 3 – Engineering") before the
page is considered complete.

---

## 10. New DAX Required

Exactly one new measure beyond the finalized catalogue, added to
`Measures[Metadata]` in the same style as the existing `Data As Of`:

```DAX
Date Coverage =
    FORMAT ( MIN ( DimDate[date] ), "MMM yyyy" ) & " – " &
    FORMAT ( MAX ( DimDate[date] ), "MMM yyyy" )
```

Every other field used on this page — `Monitoring Stations`,
`Total Observations`, `Verified GRAP Events`, `Average PM2.5 (guarded)`,
`Data Completeness %`, `Coverage Caveat`, `Truncated Season Flag` — is already
defined in `docs/dashboard_design_system.md` §2 and requires no change.

---

## 11. Consistency Note

`docs/dashboard_design_system.md` §3's original one-line sketch of Page 1
(city-wide PM2.5 trend + station ranking bar as the primary content) is
superseded in content specifics by this document, per this prompt's more
detailed brief — the page's *business question* is unchanged
("orientation," not "state of air quality"), only the visual composition
answering it is now fully specified here. The design system's global rules
(color, typography, card anatomy, nav bar, interaction patterns) are followed
exactly as written and are not altered by this document.
