-- ===========================================================================
-- 12_stage_transitions.sql
-- Business question : What was the sequence of GRAP stage changes each season, and
--                     how long did each resulting stage stay in force?
-- Purpose           : Turn the point-in-time event calendar into an episode/spell
--                     table (how many days each stage was active). Feeds a Gantt /
--                     timeline and gives denominators for stage-level stats.
-- Expected output   : one row per event. Columns: event_id, season,
--                     effective_date, stage_from, stage_to, event_direction,
--                     next_event_date, days_stage_active.
-- Dependencies      : grap_events
-- Notes / caveats   : days_stage_active = days from this event to the next event
--                     in the same season; the LAST spell of a season is capped at
--                     the season end (2023-02-28 for 2022-23) or the DATA boundary
--                     (2023-12-31 for the truncated 2023-24) and is RIGHT-CENSORED
--                     because no closing/revocation event has been entered yet.
--                     With only E001-E005 loaded, the 2022-23 season currently
--                     shows Stage III running to season end — a data-completeness
--                     artifact, not a finding.
-- Run (example)     : sqlite3 data/processed/delhi_aqi_grap.db < sql/12_stage_transitions.sql
-- ===========================================================================
SELECT
    event_id,
    season,
    effective_date,
    stage_from,
    stage_to,
    event_direction,
    LEAD(effective_date) OVER (PARTITION BY season ORDER BY effective_date) AS next_event_date,
    CAST(
        julianday(
            COALESCE(
                LEAD(effective_date) OVER (PARTITION BY season ORDER BY effective_date),
                CASE season
                    WHEN '2022-23' THEN '2023-02-28'   -- season end (in data)
                    WHEN '2023-24' THEN '2023-12-31'   -- DATA boundary (season truncated)
                END
            )
        ) - julianday(effective_date)
    AS INTEGER) AS days_stage_active
FROM grap_events
ORDER BY season, effective_date;
