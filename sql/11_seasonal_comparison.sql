-- ===========================================================================
-- 11_seasonal_comparison.sql
-- Business question : Was PM2.5 higher or lower in the 2023-24 GRAP season than in
--                     2022-23, at each station?
-- Purpose           : Season-over-season comparison per station, done FAIRLY given
--                     that the two seasons are not equally covered in the data.
-- Expected output   : one row per (station_id, season). Columns: station_id,
--                     season, n_obs, pm25_mean — restricted to the Oct-Dec window.
-- Dependencies      : v_station_daily_enriched
-- Notes / caveats   : *** COMPARABILITY FIX *** The data ends 2023-12-31, so the
--                     2023-24 season only has Oct-Dec. A naive full-season mean
--                     would compare Oct-Feb (2022-23) against Oct-Dec (2023-24) and
--                     be biased. This query restricts BOTH seasons to months 10-12
--                     so the comparison is on a like-for-like window. It is still a
--                     raw comparison (not weather-adjusted) and 2023-24 remains
--                     incomplete — see docs/issue_tracker.md.
-- Run (example)     : sqlite3 data/processed/delhi_aqi_grap.db < sql/11_seasonal_comparison.sql
-- ===========================================================================
WITH oct_dec AS (
    SELECT station_id, season, pm25_ugm3
    FROM v_station_daily_enriched
    WHERE season IS NOT NULL
      AND month IN (10, 11, 12)      -- the window both seasons share within the data
)
SELECT
    station_id,
    season,
    COUNT(pm25_ugm3)          AS n_obs,
    ROUND(AVG(pm25_ugm3), 1)  AS pm25_mean
FROM oct_dec
GROUP BY station_id, season
ORDER BY station_id, season;
