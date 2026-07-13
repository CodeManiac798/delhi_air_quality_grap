# Analysis Plan

**Status:** pre-analysis protocol. This document specifies what will be examined
and how, before any event-window analysis is run. It contains no results, no
findings, and no numeric outputs. It is written to be checked *against* once
analysis is performed — later work should be traceable back to a section here,
and any deviation from this plan should be recorded as a deviation, not silently
absorbed.

This plan governs the GRAP event-window phase of the project. It builds on the
validated Phase 1/2 dataset (`data/processed/station_daily_grap.csv`) and the
descriptive EDA already completed in `notebooks/`. Nothing here overrides the
project's core methodological position, stated in `README.md`: this is a
descriptive, weather-aware study, not a causal-inference study.

---

## 1. Research Question

How did PM2.5 and PM10 levels at Delhi's monitoring stations behave in the days
immediately surrounding official GRAP stage changes between 2022 and 2023, and
was that pattern consistent across stations and across events?

The question is deliberately phrased as *behaviour around* stage changes, not
*effect of* stage changes. This phrasing is not stylistic — it reflects the
limits of what the study design in Section 8 can support.

## 2. Objectives

- Describe how PM2.5 and PM10 moved in fixed windows around each recorded GRAP
  event, per station.
- Describe the weather conditions (temperature, humidity, wind speed) present in
  those same windows, so any pollution movement can be read alongside the
  weather backdrop it occurred in.
- Compare pollutant levels immediately before and immediately after each event
  window, as a simple descriptive difference.
- Assess whether the direction and rough size of that before/after difference is
  consistent across the nine recorded events and across the eight stations, or
  whether it varies.
- Test whether the descriptive picture is sensitive to the specific choices made
  in this plan (window width, event overlap handling), and document that
  sensitivity rather than presenting a single window width as definitive.

## 3. Unit of Analysis

**Station × Day.**

A single observation is one monitoring station's readings on one calendar day.
The dataset contains 8 stations and a daily cadence across 2022–2023, so the
event-window analysis will assemble subsets of station-day rows — one subset per
(event, station) pair — rather than analysing a single citywide daily series.
Aggregating to a citywide daily average is treated as a separate, coarser view,
not the primary unit.

## 4. Outcome Variables

- **Primary: PM2.5 (`pm25_ugm3`).** PM2.5 is the pollutant most closely tied to
  the health rationale behind GRAP escalation and is the more complete of the two
  particulate measurements across stations and years.
- **Secondary: PM10 (`pm10_ugm3`).** Carried alongside PM2.5 as a corroborating
  series — used to check whether any pattern seen in PM2.5 also appears in the
  coarser particulate fraction, or is specific to PM2.5.

AQI is not used in this phase, consistent with the project's current scope.

## 5. Explanatory Variables

- **Temperature (`air_temp_c`)** — weather covariate; affects vertical mixing and
  dispersion of pollutants.
- **Humidity (`rh_pct`)** — weather covariate; associated with particulate
  formation and settling behaviour.
- **Wind Speed (`wind_speed_ms`)** — weather covariate; a primary mechanical
  driver of pollutant dispersion independent of any policy action.
- **Station (`station_id` / `station_name`)** — grouping variable; captures
  fixed differences in location, traffic exposure, and local emission sources
  between the eight sites.
- **Date (`date`)** — time index; anchors each observation relative to an
  event's `effective_date` and situates it within the seasonal calendar.
- **GRAP Stage (`grap_stage`)** — the focal categorical variable; the officially
  declared city-wide GRAP stage in force on that date (0–4).

These variables are treated as descriptive covariates and grouping keys in this
plan — not as inputs to a causal or predictive model.

## 6. Proposed Event Window

**±7 days around each event's `effective_date`.**

Two considerations bound this choice from opposite directions:

- **Too narrow a window** risks capturing only noise. Daily PM2.5 is volatile,
  so a window of one or two days either side of an event may not contain enough
  observations to describe a stable "before" or "after" level, and a single
  unusually high or low day could dominate the comparison.
- **Too wide a window** risks capturing seasonal drift rather than any change
  local to the event. Delhi's winter PM2.5 rises and falls on a roughly monthly
  scale as documented in `notebooks/05_time_series_exploration.ipynb`, so a
  three- or four-week window would mix genuine event-adjacent movement with the
  broader seasonal trend, making the two indistinguishable.

A ±7-day window is a compromise: seven days is short relative to the monthly
scale of the seasonal cycle, so seasonal drift within the window is expected to
be small, while still giving each side of the comparison a full week of daily
readings to average over.

This width also interacts directly with a fact specific to this dataset: the
nine recorded GRAP events in `data/raw/grap/grap_events_manual.csv` are not
evenly spaced. Several are only three to eight days apart (for example, the
Stage III→IV escalation on 2022-11-03 and the Stage IV→III de-escalation on
2022-11-06 are three days apart; the Stage II→III escalation on 2022-12-04 and
the Stage III→II de-escalation on 2022-12-07 are also three days apart). A
±7-day window therefore still overlaps between some adjacent events. This is
treated as a known, documented consequence of the chosen width rather than a
reason to widen it further — widening the window would not remove the overlap
for these closely spaced pairs and would worsen the seasonal-drift risk for the
more isolated events. Overlap handling is addressed explicitly in the
cross-event consistency and sensitivity steps below (Section 7).

## 7. Planned Analytical Sequence

The analysis will proceed in the following order. Each step is descriptive; none
of the outputs from these steps are to be read as an estimate of a GRAP effect.

1. **Descriptive event summaries.** For each of the nine recorded events, tabulate
   and plot daily PM2.5 and PM10 for every station across the ±7-day window,
   centred on the event's `effective_date`.
2. **Weather summaries.** For the same nine windows, tabulate and plot daily
   temperature, humidity, and wind speed, so the pollutant series can be read
   next to the weather conditions present at the same time.
3. **Before vs. after comparisons.** For each (event, station) pair, compute
   simple summary statistics (mean, median) of PM2.5 and PM10 for the days
   before `effective_date` versus the days on and after it, within the window,
   and report the difference as a plain descriptive quantity.
4. **Cross-event consistency.** Compare the before/after differences computed in
   step 3 across the nine events and eight stations, to describe whether the
   direction and rough magnitude of change is similar from one event to the
   next, or whether it varies — including a specific check of events whose
   windows overlap, flagged as such rather than treated identically to isolated
   events.
5. **Sensitivity checks.** Repeat steps 3–4 using alternative window widths
   (e.g., ±3 and ±5 days) and, separately, with overlapping-window events
   excluded, to check whether the descriptive picture from steps 3–4 depends on
   the specific ±7-day choice made in Section 6.

## 8. Confounding Variables

The following factors change over the same time span as GRAP stage changes and
are not controlled by this design:

- **Weather.** Temperature, humidity, and wind speed vary day to day for reasons
  unrelated to GRAP and are independently known to affect PM2.5 dispersion. A
  calm, cold, humid day and a windy day will look different in the pollutant
  record regardless of what GRAP stage is in force.
- **Seasonal effects.** All nine recorded events fall within the October–December
  window of a single GRAP season (2022–23); none are yet available for a second
  season. Delhi's PM2.5 rises through autumn and into winter as a matter of
  seasonal pattern, so a before/after difference measured in this period cannot
  be separated from the seasonal trend that would have occurred with or without
  a GRAP order.
- **Station differences.** The eight stations differ in geography, traffic
  exposure, and proximity to local emission sources. A citywide summary can mask
  station-level patterns that move in different directions or at different
  speeds.
- **Missing values.** Gaps in the pollutant or weather fields (documented in the
  Phase 1 data-quality checks and the EDA notebooks) shrink the effective number
  of days available in some windows. If missingness is not evenly distributed —
  for example, concentrated around a particular station or period — a
  before/after comparison built from an incomplete window could be biased
  without that bias being visible in the summary statistic alone.
- **Other unmeasured emission sources.** Crop-residue burning, festival-related
  combustion (the Diwali period falls within or near several of the recorded
  event windows), construction activity, and ordinary vehicular-traffic
  fluctuation are not recorded in this dataset. Any of these could plausibly
  move PM2.5 independently of, or at the same time as, a GRAP stage change.

Because these factors are not randomized, not held constant, and in several
cases move on the same calendar timeline as the GRAP events themselves, this
design cannot isolate the contribution of a GRAP order from the contribution of
the conditions surrounding it. This is the reason the analysis is described
throughout this plan as descriptive and associational, and why Section 9 and
Section 10 draw an explicit line between what can and cannot be stated from it.

## 9. Allowed Claims

Statements of the following kind are supported by this study design:

- "Mean PM2.5 at [station] was [X] µg/m³ lower in the seven days after [event]
  than in the seven days before it."
- "Across the nine recorded events, [N] of the eight stations showed a decline in
  mean PM2.5 following escalation, while [M] showed an increase."
- "PM2.5 moved in the same direction as the GRAP stage change in some events and
  in the opposite direction in others."
- "Temperature, humidity, or wind speed differed between the before and after
  windows for [event], which coincided with the observed change in PM2.5."
- "The before/after pattern for [station] was/was not consistent with the
  before/after pattern for the other seven stations."
- "The descriptive picture for [event] did/did not change materially when the
  window width was narrowed to ±3 days."

## 10. Unsupported Claims

Statements of the following kind are **not** supported by this study design and
will not be made:

- "GRAP escalation caused PM2.5 to fall/rise."
- "Stage III/IV is more effective than Stage I/II at reducing pollution."
- "Station X's air quality management is worse than Station Y's."
- "Without GRAP, PM2.5 would have been higher."
- "GRAP is/is not an effective policy."
- "The weather-adjusted change represents the true effect of the policy," or any
  other statement that treats a partial weather adjustment as full statistical
  control.
- Any claim that assigns a specific numeric magnitude to "the effect of GRAP,"
  net of weather and season.

## 11. Limitations

- Only nine verified events are available, and all nine fall within a single
  GRAP season (October–December 2022). No events from a second season are yet
  available, so the analysis cannot speak to whether any observed pattern
  repeats in a different year.
- Several events are closely spaced (three to eight days apart), so their ±7-day
  windows overlap. Isolated, non-overlapping windows are not available for every
  event.
- There is no untreated comparison group: every station is subject to the same
  city-wide GRAP stage at the same time, so there is no station that experiences
  "no GRAP" while others experience an active stage on the same dates.
- Any weather adjustment performed downstream of this plan is partial — it can
  account for temperature, humidity, and wind speed as recorded, but not wind
  direction, boundary-layer height, or regional pollutant transport.
- Missing values in the pollutant and weather fields (quantified in the Phase 1
  data-quality reports and the EDA notebooks) are not necessarily distributed
  evenly across stations, months, or event windows.
- The `grap_stage` field records the officially declared stage for Delhi-NCR; it
  does not measure on-the-ground enforcement or compliance with that stage.
- AQI is not used in this phase. Public and media discussion of GRAP is often
  framed in AQI terms, so this analysis is not directly comparable to those
  narratives.

## 12. Future Improvements

- Extend the verified GRAP event calendar as further seasons (e.g., 2023–24)
  become available, to increase the number of independent events and allow a
  genuine across-season comparison.
- Incorporate wind direction and, if obtainable, boundary-layer or atmospheric
  mixing indices to move from a partial to a fuller weather adjustment.
- Explore a matched-comparison or synthetic-control approach using periods
  without a nearby GRAP change as a contextual baseline, rather than relying
  solely on the before/after structure in Section 7.
- Incorporate additional emission-context variables where they become available
  (regional crop-fire counts, a festival/calendar flag, construction or traffic
  indices) to make the confounding factors in Section 8 more observable rather
  than only documented as unmeasured.
- Extend station coverage beyond the eight currently selected stations, subject
  to the same data-quality bar applied in Phase 1.
- Formalise the sensitivity check in Section 7 into a systematic sweep of window
  widths (e.g., ±3 through ±14 days) with the results reported together, rather
  than a single width presented as the only choice.
