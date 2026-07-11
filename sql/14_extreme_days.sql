-- ===========================================================================
-- 14_extreme_days.sql
-- Business question : How often does each station cross high-PM2.5 reference
--                     levels within a season, and which were its worst days?
-- Purpose           : Threshold-exceedance counts per station-season (robust to
--                     the lack of a SQL median) plus a top-10 worst-days list.
-- Expected output   : Part A: one row per (station_id, season) with day counts
--                     above each reference level. Part B (commented): top-10
--                     highest-PM2.5 days per station.
-- Dependencies      : v_station_daily_enriched ; station_daily (Part B)
-- Notes / caveats   : *** The 60 / 120 / 250 ug/m3 cut points are PLACEHOLDERS ***
--                     They are raw-concentration reference lines only. Confirm the
--                     exact values against CPCB National Ambient Air Quality
--                     Standards / the 24-hour PM2.5 breakpoints BEFORE reporting,
--                     and do NOT label them as AQI categories (AQI is out of scope
--                     this phase). In-season days only.
-- Run (example)     : sqlite3 data/processed/delhi_aqi_grap.db < sql/14_extreme_days.sql
-- ===========================================================================
-- Part A — exceedance counts per station-season
SELECT
    station_id,
    season,
    COUNT(pm25_ugm3)                                        AS n_obs,
    SUM(CASE WHEN pm25_ugm3 >  60 THEN 1 ELSE 0 END)        AS days_gt_60,
    SUM(CASE WHEN pm25_ugm3 > 120 THEN 1 ELSE 0 END)        AS days_gt_120,
    SUM(CASE WHEN pm25_ugm3 > 250 THEN 1 ELSE 0 END)        AS days_gt_250,
    ROUND(100.0 * SUM(CASE WHEN pm25_ugm3 > 120 THEN 1 ELSE 0 END)
                / COUNT(pm25_ugm3), 1)                      AS pct_days_gt_120
FROM v_station_daily_enriched
WHERE season IS NOT NULL
GROUP BY station_id, season
ORDER BY station_id, season;

-- Part B — top-10 worst PM2.5 days per station (uncomment to run instead)
-- SELECT station_id, date, pm25_ugm3, rnk FROM (
--     SELECT station_id, date, pm25_ugm3,
--            RANK() OVER (PARTITION BY station_id ORDER BY pm25_ugm3 DESC) AS rnk
--     FROM station_daily
--     WHERE pm25_ugm3 IS NOT NULL
-- ) WHERE rnk <= 10
-- ORDER BY station_id, rnk;
