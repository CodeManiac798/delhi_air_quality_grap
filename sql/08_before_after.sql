-- ===========================================================================
-- 08_before_after.sql
-- Business question : For each GRAP event, how did mean PM2.5 in the 7 days AFTER
--                     compare with the 7 days BEFORE, at each station?
-- Purpose           : The compact before/after delta table that most people will
--                     ask to see first. Feeds a diverging bar chart per event.
-- Expected output   : one row per (event_id, station_id). Columns: event_id,
--                     event_direction, stage_from, stage_to, station_id,
--                     pm25_before, pm25_after, pm25_delta (after - before).
-- Dependencies      : event_windows (-> grap_events, station_daily)
-- Notes / caveats   : Windows are [-7,-1] vs [+1,+7]; the event day (rel_day 0) is
--                     excluded. *** RAW, NOT weather-adjusted *** — a negative
--                     delta after an escalation does NOT prove GRAP worked (winter
--                     weather, mean reversion from a spike, and OVERLAPPING event
--                     windows all confound it; E001-E005 are only 3-14 days apart,
--                     so a 7-day window routinely straddles a neighbouring event).
--                     Interpret alongside 09/weather adjustment. A pooled
--                     (all-stations) variant is at the bottom, commented out.
-- Run (example)     : sqlite3 data/processed/delhi_aqi_grap.db < sql/08_before_after.sql
-- ===========================================================================
WITH windowed AS (
    SELECT
        event_id,
        event_direction,
        stage_from,
        stage_to,
        station_id,
        CASE
            WHEN rel_day BETWEEN -7 AND -1 THEN 'before'
            WHEN rel_day BETWEEN  1 AND  7 THEN 'after'
        END AS ba,
        pm25_ugm3
    FROM event_windows
    WHERE rel_day BETWEEN -7 AND 7
      AND rel_day <> 0
)
SELECT
    event_id,
    event_direction,
    stage_from,
    stage_to,
    station_id,
    ROUND(AVG(CASE WHEN ba = 'before' THEN pm25_ugm3 END), 1) AS pm25_before,
    ROUND(AVG(CASE WHEN ba = 'after'  THEN pm25_ugm3 END), 1) AS pm25_after,
    ROUND(AVG(CASE WHEN ba = 'after'  THEN pm25_ugm3 END)
        - AVG(CASE WHEN ba = 'before' THEN pm25_ugm3 END), 1) AS pm25_delta
FROM windowed
GROUP BY event_id, event_direction, stage_from, stage_to, station_id
ORDER BY event_id, station_id;

-- --- Pooled across all 8 stations (uncomment to run instead) --------------
-- WITH windowed AS (
--     SELECT event_id, event_direction,
--         CASE WHEN rel_day BETWEEN -7 AND -1 THEN 'before'
--              WHEN rel_day BETWEEN  1 AND  7 THEN 'after' END AS ba,
--         pm25_ugm3
--     FROM event_windows
--     WHERE rel_day BETWEEN -7 AND 7 AND rel_day <> 0
-- )
-- SELECT event_id, event_direction,
--     ROUND(AVG(CASE WHEN ba='before' THEN pm25_ugm3 END),1) AS pm25_before,
--     ROUND(AVG(CASE WHEN ba='after'  THEN pm25_ugm3 END),1) AS pm25_after,
--     ROUND(AVG(CASE WHEN ba='after'  THEN pm25_ugm3 END)
--         - AVG(CASE WHEN ba='before' THEN pm25_ugm3 END),1) AS pm25_delta
-- FROM windowed GROUP BY event_id, event_direction ORDER BY event_id;
