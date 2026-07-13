# Dashboard Design System — Delhi GRAP Analytics Platform

**Role of this document.** This is the UX and page-architecture blueprint for
the Presentation Layer. It defines the design system, the measure
organization, the five report pages, the interaction model, and the
accessibility/performance rules the eventual `.pbix` must follow. **It contains
no visuals, no DAX logic, and no changes to the semantic model** finalized in
`docs/powerbi_architecture.md`. One narrow, explicitly scoped exception is
Section 2 below (the `Measures` table rename and its display-folder
reorganization), which this prompt specifically authorized.

**Design philosophy (the test every page and every visual must pass):**

1. **Decision-first** — every page answers one named business question; a
   visual that does not serve that page's question does not go on the page.
2. **Minimal** — every visual must justify its existence; when in doubt, cut.
3. **Professional** — reads like an internal government or consulting
   decision-support tool, not a coursework dashboard.
4. **Trustworthy** — methodology and limitations are always one click away,
   never buried.

---

## 1. Design System

### 1.1 Color Palette

The palette below is the project's validated default instance (six
colorblind-safety and contrast checks already run — see the data-viz skill's
`palette.md` and `scripts/validate_palette.js`), mapped onto this dashboard's
specific entities rather than re-derived from scratch.

**Categorical (identity) — one slot per monitoring station, assigned once,
never re-cycled.** There are exactly 8 stations and exactly 8 validated
categorical slots — a deliberate, non-coincidental fit:

| Slot | Hue | Light | Dark | Assigned station (fixed, alphabetical by `station_id`) |
|---|---|---|---|---|
| 1 | Blue | `#2a78d6` | `#3987e5` | Anand Vihar |
| 2 | Aqua | `#1baf7a` | `#199e70` | Bawana |
| 3 | Yellow | `#eda100` | `#c98500` | Jawaharlal Nehru Stadium |
| 4 | Green | `#008300` | `#008300` | Najafgarh |
| 5 | Violet | `#4a3aa7` | `#9085e9` | Narela |
| 6 | Red | `#e34948` | `#e66767` | Okhla Phase-2 |
| 7 | Magenta | `#e87ba4` | `#d55181` | Punjabi Bagh |
| 8 | Orange | `#eb6834` | `#d95926` | R K Puram |

A station keeps its slot regardless of which stations a slicer leaves visible
— filtering out Bawana never repaints Najafgarh's green as Bawana's aqua.
Three light-mode slots (aqua, yellow, magenta) fall below 3:1 contrast on the
light surface: any visual using them **must** carry a direct label or legend
entry, never rely on the swatch color alone to identify a station (the
"relief rule" from the palette's own validation).

**Status — GRAP stage severity, reserved, never reused for anything else:**

| Stage | Label | Status color | Hex |
|---|---|---|---|
| 0 | No Active GRAP | Good | `#0ca30c` |
| I | Poor | Warning | `#fab219` |
| II | Very Poor | Serious | `#ec835a` |
| III | Severe | Critical | `#d03b3b` |
| IV | Severe+ | Critical (same hex, distinct icon) | `#d03b3b` |

Only four status steps exist in the validated palette, and GRAP has five
stages. Stage III and Stage IV **share the critical hex** rather than
inventing a fifth ad-hoc red — per the palette's own rule, a status color
always ships with an icon and label, never color alone, so Stage IV is
distinguished from Stage III by a filled/double-weight icon and the visible
"IV" / "Severe+" label, not by a new hue. This also reads correctly: Stage IV
is "more severe than severe," not a different kind of state.

**Sequential (magnitude) — one hue, light → dark, for the one continuous
heatmap the dashboard uses** (the station × month completeness matrix on the
Methodology & Trust page): the default **blue** ramp, steps 100→700 as
specified in the palette. Never a rainbow.

**Diverging (polarity) — blue ↔ red, neutral gray midpoint** — used only for
the per-event Pre/Post paired-bar comparison on the GRAP Event Explorer page
(Section 4, Page 3), where blue = lower in the post-window than the
pre-window and red = higher, both read against a gray zero baseline. This
reuses a finding already computed and validated in
`08_cross_event_analysis.ipynb` Section 4 — the chart form is new, the number
is not.

**Chart chrome & ink (both modes selected, not an auto dark-mode flip):**

| Role | Light | Dark |
|---|---|---|
| Page plane | `#f9f9f7` | `#0d0d0d` |
| Card/chart surface | `#fcfcfb` | `#1a1a19` |
| Primary ink | `#0b0b0b` | `#ffffff` |
| Secondary ink | `#52514e` | `#c3c2b7` |
| Muted (axis/labels) | `#898781` | `#898781` |
| Gridline (hairline) | `#e1e0d9` | `#2c2c2a` |
| Baseline / axis | `#c3c2b7` | `#383835` |
| Border (hairline ring) | `rgba(11,11,11,0.10)` | `rgba(255,255,255,0.10)` |

Dark mode is a **selected second pass**, not an automatic invert — the dark
categorical/status steps above were independently chosen and validated
against the dark surface, and should ship as the report's dark theme rather
than a CSS-filter-style flip.

**A deliberate departure from the frozen analysis notebooks' chart style.**
`10_weather_context_analysis.ipynb` (Sections 1–3) used dual-axis matplotlib
charts (PM2.5 on a left axis, a weather variable on an independent right
axis). That was an acceptable exploratory-analysis device inside a frozen,
already-approved notebook — but it is a documented anti-pattern for a
polished product (two independent y-scales make the visual alignment of the
two lines arbitrary, inventing a "co-movement" that is not really in the
data). **This dashboard replaces every dual-axis pairing with small
multiples** — PM2.5 and a weather variable as two stacked single-axis charts
sharing one x-axis — on Page 2 and Page 3. This changes only the chart form;
the underlying numbers are the ones already validated in the frozen
notebooks, untouched.

### 1.2 Typography

System sans throughout — `Segoe UI` (Power BI's native default), no display
or serif face anywhere, including the hero KPI figures:

| Role | Size | Weight | Notes |
|---|---|---|---|
| Hero KPI value (Executive Overview only) | 40px | Semibold | Proportional figures, not `tabular-nums` |
| Standard KPI value | 28px | Semibold | Proportional figures |
| Page title | 20px | Semibold | One per page, top-left |
| Section / card title | 13px | Semibold | Sentence case, no trailing colon |
| Body / axis labels | 10–11px | Regular | Power BI default minimum for legibility at 100% zoom |
| Caption / footnote (methodology notes, caveats) | 9px | Regular, secondary ink | Never used for a value the user needs to act on |
| Table figures | 10px | Regular | `tabular-nums`-equivalent (Power BI table/matrix numeric alignment) |

### 1.3 Card & KPI Design

**Card anatomy** (applies to every KPI tile and every chart container):

- Surface color: card/chart surface token above (never pure white/black).
- Corner radius: **8px**.
- Border: 1px hairline ring token above — not a heavy stroke.
- Shadow: single soft drop shadow, `0px 1px 4px rgba(11,11,11,0.08)` in light
  mode, omitted (or reduced to `rgba(0,0,0,0.30)` at the same offset) in dark
  mode where shadows read poorly against a dark plane.
- Padding: 16px on all sides, minimum, between card edge and content.
- A card's fixed height always includes its axis-label band — never let a
  chart's x-axis get clipped inside a scrolling card.

**KPI (stat-tile) contract** — every KPI card carries the same four slots, so
the eye learns the pattern once:

1. **Label** — sentence case, no trailing colon (e.g. "Average PM2.5").
2. **Value** — the semibold proportional figure, auto-compact where relevant
   (e.g. `1,284`, not `1284.0`).
3. **Delta** (optional, only where a comparison is meaningful) — signed,
   against a named period, colored by **direction × whether up is good for
   that specific metric**, never a blanket "up = green":
   - PM2.5 / PM10 KPIs: increase = critical/red, decrease = good/green.
   - Data Completeness %: increase = good/green, decrease = warning/amber.
   - Active GRAP Days / Verified GRAP Events / Total Observations: **no
     colored delta** — these are counts of what happened, not performance
     indicators; a colored arrow here would imply a value judgement the data
     doesn't support.
4. **Trend** (optional) — a 12-point sparkline in the muted/de-emphasis tone,
   with only the current period, if shown, picked out in the accent hue.

A KPI with weak underlying coverage never silently looks as confident as a
well-observed one: every pollutant KPI has a **guarded** counterpart
(`docs/powerbi_architecture.md` §6.6) and the card itself shows a small
muted-ink coverage caption (e.g. "78% observed") beneath the value whenever
completeness for the current filter context is below 80% — sourced from the
`Metadata` measures in Section 2 below, not hardcoded text.

### 1.4 Borders, Shadows, Corner Radius (dashboard-wide constants)

- Corner radius: **8px** everywhere (cards, buttons, slicers, the About
  panel) — one radius value, used consistently, never mixed with sharp
  corners on some elements and rounded on others.
- Border: 1px hairline ring token; no border heavier than 1px anywhere in the
  report.
- Shadow: the single soft drop-shadow spec above; never more than one shadow
  style in the same report.

### 1.5 Spacing, Margins, Grid Layout

- **Canvas**: 16:9, 1280 × 720, identical across all five pages (no
  page-to-page canvas-size drift).
- **Outer margin**: 24px from canvas edge to any visual, all four sides.
- **Gutter**: 16px minimum between adjacent cards/visuals.
- **Grid**: a 12-column reference grid across the 1280px width (approx. 88px
  per column plus gutter) — Power BI has no enforced CSS grid, so this is a
  design-time discipline: enable **View → Gridlines** and **Snap to Grid** in
  Power BI Desktop and align every visual's left/right edge to a column
  boundary rather than eyeballing position.
- **Vertical rhythm**: page title band (56px) → KPI row (120px) → primary
  visual band → secondary visual band → footer caveat strip (32px, present on
  every page — see Section 6).

### 1.6 Icons

- One icon set, one weight (outline, not filled, except where an icon sits
  inside a filled status chip). Mixing icon sets/weights is a common
  "student project" tell — pick one (e.g. Fluent UI System Icons, since it is
  Microsoft's own set and matches Power BI's native chrome) and use it
  everywhere.
- **Navigation icons**: page-appropriate glyphs (overview/home, magnifier for
  Explorer, a calendar-flag for Event Explorer, a document for Findings, a
  shield/check for Methodology & Trust).
- **Status icons**: a filled dot or shield glyph beside every GRAP stage
  chip, colored by the status token, per Section 1.1 — the icon shape, not
  just the fill color, should differ between Stage III and Stage IV (e.g. a
  single exclamation vs. a double exclamation) since both share one hex.
- **Utility icons**: info-circle (About This Analysis), reset/circular-arrow
  (Reset button), filter funnel (slicer panel toggle) — all 20px, muted-ink
  colored at rest, primary-ink on hover.

### 1.7 Navigation Style

- A persistent **top navigation bar** (56px tall, spans all pages), not a
  left rail — a horizontal bar reads as "one product with five sections"
  more than a sidebar does at this small a page count, and keeps full canvas
  width free for content.
- Five page buttons (Executive Overview · Air Quality Explorer · GRAP Event
  Explorer · Research Findings · Methodology & Trust), left-aligned, plus the
  **About This Analysis** icon button and a **Reset** icon button,
  right-aligned.
- Active page indicator: a 3px underline in the blue categorical/primary
  accent beneath the current page's button — not a background-color fill
  (which would compete with card surfaces).
- Implement with Power BI's native **Page Navigator** visual where available
  (single source of truth for the page list; add/re-order pages once and the
  nav updates itself) rather than five hand-built buttons that must be
  copy-pasted onto every page and kept in sync manually.

### 1.8 Hover Behaviour

- Default Power BI cross-highlight (not cross-filter) on hover/click for
  in-page visual interactions, except where Section 5 specifies a drillthrough
  or a deliberate cross-filter.
- Buttons and nav items: background shifts from transparent to a 6%-opacity
  wash of primary ink on hover; icon shifts from muted to primary ink.
- KPI cards do **not** have a hover state — they are not interactive targets
  (no drillthrough or filter action lives on a KPI card in this system); a
  hover affordance on a non-interactive element is a common false signal to
  avoid.
- Chart marks: hover reveals the report tooltip page (Section 5); hit target
  extends beyond the visible mark (Power BI's default tooltip trigger area is
  adequate here — no custom hit-testing needed).

### 1.9 Tooltip Style

- **Report tooltip pages**, not default hover text, for every chart with more
  than one field worth surfacing on hover (matches
  `docs/powerbi_architecture.md` §7).
- Fixed tooltip page canvas: 320 × 240px, card surface token, 8px corner
  radius, single soft shadow — a miniature card, styled identically to the
  main report's cards so it never looks like a different product.
- Content order inside a tooltip: date/context line (muted ink, top) → 1–2
  headline values (semibold, primary ink) → up to 3 supporting values
  (regular weight) → a one-line data-completeness caveat if coverage for that
  point is below 80%.
- Tooltips **enhance, never gate** — every value shown in a tooltip is also
  visible via a direct label, the KPI row, or the underlying table/drillthrough
  page; nothing is tooltip-only.

### 1.10 Button Style

- **Primary action button** (rare — e.g. "View Event Detail" inside the
  flagship page): filled, primary-ink background inverted (light text on a
  dark/blue fill), 8px radius, 12px vertical / 20px horizontal padding.
- **Secondary / icon buttons** (nav, Reset, About): transparent fill,
  1px hairline border, icon + short label, same 8px radius.
- **Disabled state** (e.g. a drillthrough button before any point is
  selected): 40% opacity, no hover wash.
- No button ever uses a status color (good/warning/serious/critical) as its
  fill — status colors are reserved for state, not for action affordances.

### 1.11 Recommended Power BI Theme (JSON)

Apply as a custom report theme so every new visual inherits these values by
default, rather than re-styling each visual by hand:

```json
{
  "name": "Delhi GRAP Analytics Platform",
  "dataColors": [
    "#2a78d6", "#1baf7a", "#eda100", "#008300",
    "#4a3aa7", "#e34948", "#e87ba4", "#eb6834"
  ],
  "background": "#fcfcfb",
  "foreground": "#0b0b0b",
  "tableAccent": "#2a78d6",
  "good": "#0ca30c",
  "neutral": "#fab219",
  "bad": "#d03b3b",
  "maximum": "#0d366b",
  "center": "#f0efec",
  "minimum": "#cde2fb",
  "textClasses": {
    "label": { "fontFace": "Segoe UI", "color": "#52514e" },
    "callout": { "fontFace": "Segoe UI Semibold", "color": "#0b0b0b" },
    "title": { "fontFace": "Segoe UI Semibold", "color": "#0b0b0b" }
  }
}
```

A parallel `Delhi GRAP Analytics Platform — Dark` theme file swaps
`background`/`foreground`/`dataColors` for the dark-mode steps in Section
1.1, and is switched by report-level bookmark rather than relying on any
OS-level auto dark mode (Power BI report themes do not auto-switch with the
OS). If the Power BI Desktop version in use supports the newer `visualStyles`
theme block, add default `card`/`background`/`border` entries there for the
8px corner radius and hairline border specified in Section 1.4, so KPI cards
and chart containers pick up the design system without per-visual formatting.

---

## 2. Measures Table (Architecture Amendment)

**Scope of this change.** The finalized semantic model in
`docs/powerbi_architecture.md` §6 defined a disconnected measure table named
`_Measures`. This prompt asks for one specific, scoped amendment: rename it to
`Measures` and reorganize its contents into five display folders (KPIs,
Pollution, Weather, Events, Metadata). **No fact table, dimension table,
column, or relationship changes.** Every DAX expression below is unchanged
from `docs/powerbi_architecture.md` except where noted as new in the
Metadata folder.

```
Measures                              (renamed from _Measures; still a
│                                       disconnected table — no relationships)
├── KPIs
│   ├── Total Observations
│   ├── Monitoring Stations
│   ├── Verified GRAP Events
│   ├── Active GRAP Days
│   └── Data Completeness %
├── Pollution
│   ├── Average PM2.5
│   ├── Average PM2.5 (guarded)
│   ├── Median PM2.5
│   ├── Maximum PM2.5
│   ├── Average PM10
│   ├── Average PM10 (guarded)
│   ├── Median PM10
│   └── Maximum PM10
├── Weather
│   ├── Average Temperature
│   ├── Average Humidity
│   └── Average Wind Speed
├── Events
│   ├── Stage-wise Observation Count
│   ├── Event Window Observations
│   ├── Pre-Event Avg PM2.5
│   ├── Post-Event Avg PM2.5
│   ├── Pre-Event Avg PM10
│   └── Post-Event Avg PM10
└── Metadata
    ├── Selected Season Label
    ├── Data As Of
    ├── Truncated Season Flag
    └── Coverage Caveat
```

**Placement rationale.** `KPIs` holds the five cross-domain "at a glance"
counts used on the Executive Overview landing page (Section 4, Page 1) —
nothing pollutant- or weather-specific lives there, so the folder stays short
and scannable. `Pollution` and `Weather` are unchanged from the finalized
architecture's groupings. `Events` absorbs both the GRAP-state measure
(`Stage-wise Observation Count`, which reads through `DimStage`/`DimDate`) and
the `FactEventWindow`-based Pre/Post pair — both are, from a report user's
perspective, "the GRAP-event side of the model," even though they technically
read different tables underneath.

**New in `Metadata`.** These four small text/utility measures did not exist in
the finalized architecture; they are added here because Section 6 (this
document) requires dynamic, always-current caption text for the trust
footer, rather than a hardcoded text box that can silently go stale:

```DAX
Selected Season Label =
    SELECTEDVALUE ( DimDate[grap_season], "All Seasons" )

Data As Of =
    FORMAT ( MAX ( DimDate[date] ), "d MMMM yyyy" )

Truncated Season Flag =
    IF (
        SELECTEDVALUE ( DimDate[grap_season] ) = "2023-24",
        "Season truncated — data ends 31 Dec 2023",
        BLANK ()
    )

Coverage Caveat =
    IF (
        [Data Completeness %] < 0.8,
        "Coverage " & FORMAT ( [Data Completeness %], "0%" ) & " for this selection",
        BLANK ()
    )
```

These four are consumed only by the footer caveat strip (Section 1.5, Section
6) and the KPI coverage captions (Section 1.3) — they are never plotted on an
axis and should sit in the field list under `Metadata`, out of the way of the
analytical measures a user is browsing for a chart.

**Naming conventions (unchanged from `docs/powerbi_architecture.md` §12,
restated for completeness):** Title Case for measures, unit implied by format
string rather than spelled out in the name, guarded variants append
`(guarded)`, and the table name itself now carries no leading underscore —
`Measures` sorts naturally near the bottom of an alphabetized field list
(after the `Fact`/`Dim` tables), which is an acceptable, deliberate trade for
a friendlier table name in a report meant for non-technical government users
who may open the field list directly.

---

## 3. Page Architecture

Five pages. Each is judged against the one business question it must answer.

### Page 1 — Executive Overview

**Superseded by `docs/page1_executive_overview.md`.** That document is the
authoritative, buildable implementation spec for this page (exact visual
placements, fields, formatting, and interactions) and is the one to build
from. The row below is kept only as the short cross-reference summary; where
it and the implementation spec differ in any content detail, the
implementation spec governs.

| | |
|---|---|
| **Business question** | "What is this project and what does it contain?" (orientation, not a live analytical briefing) |
| **Target user** | Government officials, senior stakeholders, and any first-time viewer of the platform |
| **KPIs** | Monitoring Stations, Total Observations, Verified GRAP Events, Date Coverage, Average PM2.5 (guarded), Data Completeness % — 6 cards, one row |
| **Visual hierarchy** | KPI row (top) → Left: monitoring station list · Center: project timeline with all 9 verified GRAP events marked · Right: project summary text → Pipeline overview strip (bottom) → footer caveat strip |
| **Visual list** | See `docs/page1_executive_overview.md` §§2–6 for the full, exact visual-by-visual specification |
| **Filters** | Global slicers (`grap_season`, station) live in a collapsible Filters flyout, not a permanently docked row — see implementation spec §8 |
| **Interactions** | Nav bar (Filters / Reset / About), KPI cards deliberately shielded from in-page cross-filtering (Edit Interactions set to "None" from the Left table and Center chart) so they only ever reflect the global slicer state |
| **Navigation** | Landing page; top nav bar present; other four destinations shown disabled until built |
| **Expected insight** | What the platform is, what it covers, and what pipeline produced it — orientation before a viewer moves to any of the analytical pages |

### Page 2 — Air Quality Explorer

| | |
|---|---|
| **Business question** | "How does pollution and weather vary by station, month, and season?" |
| **Target user** | Environmental researchers, urban planning teams — exploratory use |
| **KPIs** | Average PM2.5, Average PM10, Average Temperature, Average Humidity, Average Wind Speed — 5 cards, values react live to the filters below |
| **Visual hierarchy** | Filter row (top) → PM2.5 + PM10 trend, stacked small multiples sharing one x-axis (primary) → station comparison box plot (secondary) → weather small multiples: temperature / humidity / wind speed as three separate single-axis line charts (replaces the frozen notebooks' dual-axis form, per §1.1) → monthly variability box plot (PM2.5 by calendar month) |
| **Visual list** | 1 KPI row (5 cards) · 2 stacked trend lines (PM2.5, PM10) · 1 station box plot · 3 weather line charts (temperature, humidity, wind speed — small multiples, never dual-axis) · 1 monthly box plot |
| **Filters** | Station (multi-select), `geographic_role`, `grap_season`, month |
| **Interactions** | Clicking a station in the box plot cross-filters the trend and weather charts to that station; a "View Station Detail" button opens the `DimStation` drillthrough page (per `docs/powerbi_architecture.md` §7) |
| **Navigation** | Top nav bar; back-link to Executive Overview; forward-link to GRAP Event Explorer |
| **Expected insight** | Which stations run persistently higher/lower; the seasonal shape of PM2.5/PM10; weather's co-movement with pollution shown as parallel context, explicitly captioned as non-causal (footer strip, Section 6) |

### Page 3 — GRAP Event Explorer *(flagship page)*

| | |
|---|---|
| **Business question** | "What did pollution and weather look like around each verified GRAP intervention, and how consistent was that pattern across the nine events?" |
| **Target user** | Policy analysts and government officials evaluating specific interventions — the primary audience this whole product exists for |
| **KPIs** | Verified GRAP Events, Event Window Observations, Pre-Event Avg PM2.5, Post-Event Avg PM2.5, Data Completeness % (scoped to the event window) |
| **Visual hierarchy** | Event selector (top, most prominent — this page is organized around "pick an event") → selected-event PM2.5 profile by relative day, Day-0 marked (primary) → Pre/Event/Post paired bar, diverging blue↔red (secondary; a paired comparison, never a bare delta KPI, per `docs/powerbi_architecture.md` §6.5) → cross-event consistency view: all nine event profiles shown with the selected event emphasized in the accent hue and the other eight de-emphasized to muted gray (the skill's "emphasis" pattern, not eight competing hues) → stage-transition context card |
| **Visual list** | 1 event selector (list/dropdown, 9 rows: event id, date, stage transition label) · 1 KPI row (5 cards) · 1 relative-day PM2.5 profile line · 1 Pre/Event/Post diverging paired bar · 1 emphasis-style cross-event overlay · 1 stage-transition detail card (`official_order_title`, `action_type`, `stage_transition_label`) |
| **Filters** | Event selector (primary interaction on this page), station (secondary) |
| **Interactions** | Selecting an event re-centers the profile chart and re-highlights it in the overlay; a "View Event Detail" button opens the `DimGrapEvent` drillthrough page; hovering any date shows the weather-context tooltip page (§1.9) |
| **Navigation** | Top nav bar; this page also carries a small callout linking to Research Findings ("How consistent is this across events? See Findings →") and to Methodology & Trust for the sensitivity-analysis caveat (window-width choice — `09_sensitivity_analysis.ipynb`) |
| **Expected insight** | The per-event descriptive picture already established in `07_event_profile_analysis.ipynb` and `08_cross_event_analysis.ipynb`: visible event-to-event heterogeneity, no single clean before/after story, weather context visible alongside every event |

### Page 4 — Research Findings

| | |
|---|---|
| **Business question** | "What are the descriptive findings this analysis is prepared to state, in plain language?" |
| **Target user** | Policy analysts, academic researchers, students, and officials who want the headline takeaways without re-deriving them from charts |
| **KPIs** | None — this page is a curated narrative, not a live-filtering explorer (see below) |
| **Visual hierarchy** | Findings grouped by theme, each as a short text block with **at most one** small supporting chart, in this order: pollution patterns → weather context → cross-event consistency → sensitivity to window width |
| **Visual list** | 4 themed text/callout cards, each paired with one small static supporting visual pulled directly from the already-validated figures in `08_cross_event_analysis.ipynb` / `09_sensitivity_analysis.ipynb` / `10_weather_context_analysis.ipynb` (no new chart, no new number) |
| **Filters** | **None.** This page deliberately opts out of the global season/station slicers (see below) |
| **Interactions** | Read-only; no cross-filtering, no drillthrough. A "See it in the Explorer →" link per finding jumps to Page 2 or 3 with a bookmark that restores that finding's relevant filter state |
| **Navigation** | Top nav bar; primarily a destination, not a hub |
| **Expected insight** | The findings text is exactly what a reader takes away without touching a single filter |

**Why this page has no filters.** Every sentence on this page was written
against a specific, already-validated computation in a frozen notebook. If
this page inherited the global station/season slicers, a user could filter it
into a state where the printed finding text no longer matches the charts
beside it — a direct hit against the "Trustworthy" design principle. Page 4 is
intentionally the one static, citable page in the product.

### Page 5 — Methodology & Trust

| | |
|---|---|
| **Business question** | "How was this data collected, validated, and analyzed, and what are its limits?" |
| **Target user** | Everyone — especially first-time and skeptical users who need to trust the platform before acting on it; also the destination for the About button (Section 6) |
| **KPIs** | Total Observations, Monitoring Stations, Verified GRAP Events, Data Completeness % — presented as trust indicators, not analytical headlines (visually distinct, smaller card treatment than Page 1's KPI row) |
| **Visual hierarchy** | Pipeline diagram (top, static image/SmartArt-style) → data completeness heatmap (station × month, sequential blue ramp) → Allowed / Unsupported claims side-by-side list (from `docs/analysis_plan.md` §9–10) → limitations list → glossary/definitions |
| **Visual list** | 1 static pipeline diagram · 1 completeness heatmap (station × month) · 2 side-by-side claim lists (allowed / unsupported) · 1 limitations text block · 1 glossary/definitions table |
| **Filters** | None — fixed content, same reasoning as Page 4 |
| **Interactions** | Read-only; this is also the panel the About button (Section 6) surfaces a condensed version of |
| **Navigation** | Top nav bar; always reachable, and the fallback destination if the About panel's "Read full methodology" link is clicked |
| **Expected insight** | Correct interpretation guardrails; why the platform does not, and will not, claim GRAP caused any pattern shown elsewhere in the product |

---

## 4. Interactions

- **Global slicers** — `DimDate[grap_season]`, `DimDate[is_grap_season]`,
  `DimStation[station_name]`/`geographic_role` — placed in a slim, collapsible
  filter panel synced (Power BI **Sync Slicers** pane) across **Pages 1–3
  only**. Pages 4–5 explicitly opt out (see Page 4's rationale above; the same
  applies to Page 5).
- **Cross-filtering** — single-direction, dimension → fact, exactly as fixed
  in the finalized semantic model (`docs/powerbi_architecture.md` §4). No
  visual-level bidirectional cross-filtering is enabled anywhere.
- **Bookmarks** — one bookmark group per page for: (a) **default state** (used
  by the Reset button), (b) **About panel open/closed**, and on Page 3
  specifically, (c) one bookmark per event for the "See it in the Explorer"
  deep-links from Page 4.
- **Reset button** — top-right of the nav bar (Section 1.10), present on every
  page; applies that page's "default state" bookmark, clearing all local
  selections and returning global slicers to "All Seasons" / in-season off.
- **Tooltip pages** — as specified in Section 1.9: one weather-context
  tooltip page (used on Pages 2 and 3) and one event-summary tooltip page
  (used on Page 3's overlay chart).
- **Drillthrough** — two drillthrough pages, matching
  `docs/powerbi_architecture.md` §7: **Station Detail** (from Page 2) and
  **Event Detail** (from Page 3). Both carry a visible "← Back" button
  (Power BI's native back-button visual) and inherit the drillthrough filter
  automatically — no additional local filter needed on the drillthrough page
  itself.
- **Sync slicers** — the filter panel's slicer visuals are built once and
  synced (not duplicated) across Pages 1–3, with "Sync" ticked and "Visible"
  ticked for all three so the same physical slicer state is shared; Pages 4–5
  have sync ticked **off** (they carry no slicer visuals at all).
- **Navigation buttons** — the Page Navigator visual (Section 1.7) plus the
  two icon buttons (About, Reset); no other free-floating navigation buttons
  on any page, to avoid multiple competing ways to move around the product.
- **Selection pane organization** — every page's Selection pane is grouped and
  named consistently, top to bottom in z-order:
  ```
  05 - Tooltip/Drillthrough triggers
  04 - Navigation (nav bar, About/Reset icons)
  03 - Filter panel
  02 - Primary content (charts, tables)
  01 - KPI row
  00 - Background/page plane
  ```
  Every group and layer gets a descriptive name (not the Power BI default
  "Text box 14") — this is what makes a large `.pbix` maintainable by someone
  other than its original author.

---

## 5. Special Feature — "About This Analysis"

An info-circle icon button, permanently docked in the top nav bar
(Section 1.7), present on every page.

**Behaviour.** Clicking it applies a bookmark that overlays a **panel**, not a
full-page navigation — the user's current page, filters, and any drillthrough
state stay exactly as they were underneath. The panel is a fixed 720 × 480px
card (surface token, 8px radius, shadow, per Section 1.3), centered on the
canvas, with a dimmed 40%-opacity scrim behind it (a full-canvas rectangle at
low z-order beneath the panel, above the report content) and a visible "✕
Close" button that reverts the bookmark.

**Content**, in this order, mirroring exactly what the prompt requested and
pulling directly from already-written project documentation rather than new
prose:

1. **Research Question** — verbatim from `docs/analysis_plan.md` §1.
2. **Dataset** — station count, date range, pollutant/weather variables,
   verified event count (live values via the `KPIs` measures, Section 2 — this
   part of the panel is the one place it reads live measures rather than
   static text, so it never goes stale).
3. **Methodology** — one-paragraph summary of the descriptive, non-causal
   approach, condensed from `docs/analysis_plan.md` §2 and §6.
4. **Pipeline** — a condensed version of the same pipeline diagram used on
   Page 5, small multiple of the full one.
5. **Validation** — one line each on data-quality checks and GRAP-event
   verification, condensed from `reports/data_quality/` and
   `docs/grap_event_data_contract.md`.
6. **Limitations** — condensed bullet list from `docs/analysis_plan.md` §11.
7. **Definitions** — a short glossary (PM2.5, PM10, GRAP stage 0–4, relative
   day, Pre/Event/Post) — the same glossary as Page 5, condensed.

Every section ends with a "Read full methodology →" link that closes the
panel and navigates to Page 5, where the un-condensed version of the same
content lives. **The panel is a summary of Page 5, never a divergent second
copy** — one page owns the full text; the panel only excerpts it.

**Why a panel and not a forced navigation.** A first-time user who clicks
"About" mid-exploration (say, halfway through the GRAP Event Explorer) should
not lose their place. A panel answers "what am I looking at?" without
discarding the state that produced the question.

---

## 6. Footer Caveat Strip (cross-page trust element)

Not a page of its own, but a 32px strip pinned to the bottom of every page
except the About panel: muted-ink text, left-aligned, driven by the
`Metadata` measures (Section 2) — `Truncated Season Flag` and
`Coverage Caveat` — so it only appears when it is actually true for the
current filter context, and a static trailing clause: *"Descriptive analysis
only — not causal inference. See Methodology & Trust."* linking to Page 5.
This is the single mechanism that keeps the "Trustworthy" design principle
enforced on every page automatically, rather than depending on a designer
remembering to add a caveat text box to each new page by hand.

---

## 7. Accessibility

- **Color accessibility.** The categorical palette (§1.1) is pre-validated to
  a worst-case adjacent ΔE of 24.2 in light mode (well clear of the ≥12
  target) and 10.3 in dark mode (the accepted floor band). Status colors
  always ship with an icon and a text label (Section 1.6) — color is never
  the only channel carrying a GRAP stage's meaning. Any visual using a
  sub-3:1-contrast slot (aqua, yellow, magenta — §1.1) must carry a direct
  label or legend, not rely on the swatch alone.
- **Font sizes.** No data label smaller than 9px anywhere (Section 1.2); body
  text 10–11px minimum; KPI values large enough (28–40px) to be read at a
  normal viewing distance on a shared-screen briefing, which is this
  product's most common real-world usage pattern.
- **Contrast.** Primary ink on the card surface exceeds WCAG AA for both
  modes (verified against the palette's own surface tokens); the footer
  caveat strip and captions use secondary/muted ink only where the text is
  supplementary, never for a value a user must act on.
- **Keyboard navigation.** Set an explicit tab order in the Selection pane
  (top to bottom matches the visual hierarchy: nav → filters → KPIs →
  primary chart → secondary charts) using Power BI's **Tab Order** pane; every
  interactive visual gets Alt Text describing its content and current state
  (not just its chart type); the Page Navigator, About, and Reset buttons are
  reachable and operable via keyboard (Enter/Space) without a mouse. Every
  chart's underlying values remain reachable via **Power BI's "See data" /
  table view** in addition to the visual, so no value is chart-only for a
  screen-reader or low-vision user.

---

## 8. Performance

- **Visual count per page.** Target 6–8 visuals per page including the KPI
  row (counted as one row, not one-per-card for this budget); the flagship
  GRAP Event Explorer (Page 3) is the densest at 6 content visuals + 1
  selector + 1 KPI row, still within budget because the KPI row is compact.
- **Maximum cards.** No more than **6 KPI cards** in a single row on any page
  (Pages 1 and 2 use 6 and 5 respectively) — beyond 6, a reader stops scanning
  and starts searching, defeating the point of a KPI row.
- **Best practices.**
  - Import mode only (per `docs/powerbi_architecture.md` §9) — no
    DirectQuery round-trips to slow down page load.
  - Disable Auto Date/Time (already specified in the finalized architecture;
    restated here because it also affects report-level render performance,
    not just model size).
  - Prefer the report tooltip pages and drillthrough pages (Sections 1.9,
    4) over cramming every possible view onto one busy page — this is this
    product's practical equivalent of "lazy loading": a tooltip or
    drillthrough page only renders when it is actually invoked, rather than
    every page rendering everything at once.
  - Keep the footer caveat strip's measures (`Metadata` folder, Section 2)
    simple `IF`/`SELECTEDVALUE` expressions — no iterator functions in a
    measure that renders on every single page.
  - Turn off "See data" export where a page is meant purely as a stable,
    citable view (Page 4) if the organization's data-governance policy
    requires limiting export surface — a product decision, not a design
    requirement, but worth flagging here since it is configured at the
    visual level.
- **Performance Analyzer usage.** Before shipping any page: open the
  **View → Performance Analyzer** pane, **Start Recording**, refresh the
  page, interact with every filter and cross-filter path once, **Stop**, and
  review the per-visual breakdown (DAX query time vs. visual rendering time).
  Target under ~1 second per visual; a visual consistently over that on this
  small a dataset almost always indicates an unnecessarily complex measure
  (missing a `VAR`, an avoidable iterator) rather than a genuine data-volume
  problem — investigate the DAX before adding any caching or aggregation
  workaround.

---

## 9. Governance Note

This document and `docs/powerbi_architecture.md` together are the complete
design contract for the `.pbix` build. If the built report ever drifts from
either document, treat the `.pbix` as the source of *current* state and one
of these two documents as needing an update — never silently let the two
diverge. No further analytical notebooks, semantic-model changes, or new
findings are introduced by this document; it is UX and page architecture
only.
