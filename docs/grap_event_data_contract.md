# GRAP Event Data Contract

**Status: the event calendar is NOT yet populated.** This document defines the
schema and rules that every manually entered GRAP event must satisfy *before* it
is allowed into Phase 2 analysis. It is a contract for human data entry, not an
analytical dataset.

Source file governed by this contract:
`data/raw/grap/grap_events_manual.csv`

## Golden rules

1. **Every row is entered by a human from an official CAQM order.** No row may be
   generated, inferred, scraped, or recalled from memory.
2. **A row is not usable until `verified = Yes`.** The validator treats any other
   value as "not analysis-ready".
3. **The validator flags suspicious rows; it never edits or repairs them.**
   Suspicious ≠ impossible — a flag means "a human must confirm this", not "delete it".

## What counts as an *event*

A GRAP **event** is a point in time at which the **active GRAP state changed** for
Delhi-NCR under an official CAQM Sub-Committee decision.

- A **review meeting is not automatically an event.** CAQM's Sub-Committee meets
  frequently to review air quality and forecasts. A meeting that decides to keep
  the current stage unchanged produces **no state change**, therefore **no row**.
  Only enter a row when the meeting's order actually changes the active stage
  (or invokes / revokes GRAP).
- A **GRAP order is not automatically a state change.** An order may reaffirm the
  existing stage, clarify enforcement, or direct agencies without moving the stage.
  Only the orders that move `stage_from → stage_to` (or activate/revoke) are events.
- **Revoking a higher stage does not mean GRAP is gone.** When CAQM lifts Stage IV,
  Stages I–III restrictions often **remain in force**. Such a row is a
  `de_escalation` from Stage IV to the stage that remains active (e.g. `4 → 3`),
  **not** a `full_revocation` to `0`. `full_revocation` (`stage_to = 0`) is used
  only when *all* GRAP restrictions are withdrawn.

## Date fields — order vs effective vs publication

These three dates can differ and must not be conflated:

| Date | Meaning | Field |
|---|---|---|
| **Order date** | The date printed on / officially associated with the CAQM order that decides the change. | `order_date` |
| **Effective date** | The date the GRAP state *actually* changed — when restrictions of the new stage take effect. This is the analytically meaningful date. | `effective_date` |
| **Publication date** | The date the order was published / circulated, if it differs from both. Not a separate column — if encountered and materially different, record it in `notes`. | `notes` |

- If the order says restrictions apply "with immediate effect", `effective_date`
  usually equals `order_date` and `immediate_effect = Yes`.
- If the order states a future start (e.g. "from 08:00 on the next day"),
  `effective_date` is that later date and `immediate_effect = No`; explain in `notes`.
- **`effective_date` is mandatory. `order_date` should be recorded but may equal
  `effective_date`.** Phase 2 event windows will be anchored on `effective_date`.

## Field definitions

### `event_id`  — required, unique
Stable, human-assigned identifier. Never reused, never renumbered.
Suggested convention: `grap_<season>_<effective_date>_<action>`, e.g.
`grap_2022_23_2022-10-05_invoke`. Free text, but must be unique and non-empty.

### `order_date`  — recommended
ISO date `YYYY-MM-DD`. Date on/associated with the CAQM order. May equal
`effective_date`. If genuinely unknown, leave blank and note why in `notes`.

### `effective_date`  — required
ISO date `YYYY-MM-DD`. The date the GRAP state changed. **Must not be missing.**

### `season`  — required, controlled
One of exactly:
- `2022-23`
- `2023-24`

(The Oct–Feb GRAP season. Events are attributed to the season they belong to,
not the calendar year.)

### `action_type`  — required, controlled
One of exactly:
- `invoke` — GRAP (or a stage) is brought into force from no active GRAP
- `escalate` — move to a higher stage
- `de_escalate` — move to a lower stage that is still ≥ Stage I
- `revoke` — withdraw all GRAP restrictions (back to no active GRAP)
- `other` — anything that does not fit the above; **must** be explained in `notes`

### `stage_from` / `stage_to`  — required, controlled integer codes
The active GRAP stage before and after the event. Representation:

| Code | Meaning |
|---|---|
| `0` | No active GRAP |
| `1` | Stage I (Poor) |
| `2` | Stage II (Very Poor) |
| `3` | Stage III (Severe) |
| `4` | Stage IV (Severe+) |

`stage_from` = the stage in force immediately before the event.
`stage_to` = the stage in force immediately after the event.

### `event_direction`  — required, controlled
One of exactly:
- `activation` — from `0` to any active stage (first invocation of GRAP)
- `escalation` — stage increases (and `stage_from ≥ 1`)
- `de_escalation` — stage decreases but `stage_to ≥ 1` (GRAP still active)
- `full_revocation` — `stage_to = 0` (all GRAP restrictions withdrawn)
- `other` — must be explained in `notes`

`event_direction` describes the stage movement; `action_type` describes the
official action. They must be mutually consistent (see validation rules).

### `immediate_effect`  — required, controlled
Whether the new stage applied immediately on `effective_date`:
- `Yes` — restrictions applied with immediate effect
- `No` — a stated lag/future start (explain in `notes`)

### `official_order_title`  — required
The exact title of the source CAQM order document, transcribed as printed.

### `official_source`  — required
An **official CAQM URL only** (the order/press release on the CAQM domain).
Not a news article, not a blog, not a screenshot. One URL per row.

### `notes`  — optional
Human interpretation: ambiguities, publication-vs-effective differences,
same-day multi-stage decisions, partial revocations, etc.

### `verified`  — required, controlled
- `Yes` — a human has confirmed every field against the official order
- `No` — not yet verified

**Only `verified = Yes` rows may enter Phase 2 analysis.**

## Why every row must be human-verified

GRAP decisions are legal orders with wording that determines meaning (immediate
vs deferred effect, partial vs full revocation, stage remaining active after a
higher stage is lifted). These distinctions cannot be reliably parsed
automatically and cannot be recalled from memory without risk of error. Because
the entire project rests on *when the state actually changed*, each event must be
transcribed and confirmed by a human from the primary CAQM source. The `verified`
flag is the auditable record that this happened.

## Relationship to validation

`src/04_validate_grap_events.py` enforces this contract. It distinguishes:

- **ERROR** — contract violation (malformed/missing required value, bad controlled
  value, duplicate id, unordered dates). The file is not valid until fixed.
- **FLAG** — structurally valid but logically suspicious (no-change transition,
  multi-stage jump, action/direction/stage inconsistency). Requires human review;
  never auto-corrected.
- **NOT-READY** — valid but `verified ≠ Yes`; excluded from analysis until verified.

An empty file (headers only) is a *valid but empty* template: it passes structural
checks and reports that there are zero analysis-ready events, so Phase 2 cannot begin.
