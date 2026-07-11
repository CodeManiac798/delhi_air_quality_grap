-- ===========================================================================
-- 10_rolling_pm25.sql
-- Business question : What is the smoothed 7-day and 30-day trailing PM2.5 trend
--                     at each station (removing day-to-day noise)?
-- Purpose           : Rolling averages for trend lines and to stabilise the
--                     event-window reading. Demonstrates SQL window frames.
-- Expected output   : one row per (station_id, date) across all 730 days.
--                     Columns: pm25_ugm3 (raw), pm25_roll7, pm25_roll30, and the
--                     count of observed days inside each window.
-- Dependencies      : station_daily
-- Notes / caveats   : Frames are ROWS-based (6 / 29 preceding + current). This
--                     equals CALENDAR-day windows ONLY because station_daily has a
--                     row for every station-day (grain is complete, 730/station) —
--                     verified in Phase 1. AVG() skips NULLs, so n_obs_7 / n_obs_30
--                     expose how much of each window was actually observed; a
--                     rolling mean built on 2 of 7 days is not trustworthy. The
--                     first 6 (resp. 29) days per station are ramp-up (partial
--                     windows).
-- Run (example)     : sqlite3 data/processed/delhi_aqi_grap.db < sql/10_rolling_pm25.sql
-- ===========================================================================
SELECT
    station_id,
    date,
    pm25_ugm3,
    ROUND(AVG(pm25_ugm3) OVER w7,  1) AS pm25_roll7,
    ROUND(AVG(pm25_ugm3) OVER w30, 1) AS pm25_roll30,
    COUNT(pm25_ugm3)     OVER w7      AS n_obs_7,
    COUNT(pm25_ugm3)     OVER w30     AS n_obs_30
FROM station_daily
WINDOW
    w7  AS (PARTITION BY station_id ORDER BY date ROWS BETWEEN  6 PRECEDING AND CURRENT ROW),
    w30 AS (PARTITION BY station_id ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW)
ORDER BY station_id, date;
