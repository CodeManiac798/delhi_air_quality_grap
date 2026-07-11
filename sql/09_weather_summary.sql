-- ===========================================================================
-- 09_weather_summary.sql
-- Business question : Do weather conditions (wind, temperature, humidity) differ
--                     systematically across GRAP stages and seasons?
-- Purpose           : Motivates and later supports the weather-adjustment step.
--                     If wind/temperature differ by stage, then raw PM2.5-by-stage
--                     comparisons (05/07) are confounded and must be adjusted.
-- Expected output   : one row per (season, active_stage). Columns: counts and
--                     mean/min/max wind, mean temperature, mean humidity.
-- Dependencies      : v_station_daily_enriched
-- Notes / caveats   : Low wind speed traps pollution; if higher GRAP stages
--                     coincide with lower wind, some of the stage-PM2.5 pattern is
--                     weather, not policy. This query only DESCRIBES weather; it
--                     performs no adjustment. In-season days only.
-- Run (example)     : sqlite3 data/processed/delhi_aqi_grap.db < sql/09_weather_summary.sql
-- ===========================================================================
SELECT
    season,
    active_stage,
    COUNT(*)                         AS n_station_days,
    COUNT(wind_speed_ms)             AS n_wind_obs,
    ROUND(AVG(wind_speed_ms), 2)     AS wind_mean_ms,
    ROUND(MIN(wind_speed_ms), 2)     AS wind_min_ms,
    ROUND(MAX(wind_speed_ms), 2)     AS wind_max_ms,
    ROUND(AVG(air_temp_c), 1)        AS temp_mean_c,
    ROUND(AVG(rh_pct), 1)            AS rh_mean_pct
FROM v_station_daily_enriched
WHERE is_grap_season = 1
  AND active_stage IS NOT NULL
GROUP BY season, active_stage
ORDER BY season, active_stage;
