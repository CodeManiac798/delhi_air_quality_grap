-- ===========================================================================
-- 05_stage_summary.sql
-- Business question : While each GRAP stage was the active state, what did PM2.5,
--                     PM10 and weather look like on average?
-- Purpose           : Descriptive profile of conditions by active stage — the
--                     backbone of the "stage summary" narrative and a first look
--                     at whether higher stages coincide with worse air/weather.
-- Expected output   : one row per active_stage (0..4 as present). Columns:
--                     active_stage, station-day count, PM2.5/PM10 means, weather
--                     means.
-- Dependencies      : v_station_daily_enriched (-> daily_grap_state)
-- Notes / caveats   : *** INTERPRETATION WARNING *** GRAP stages are DECLARED
--                     BECAUSE air quality is already bad, so a raw "higher stage
--                     -> higher PM2.5" pattern is mechanical/definitional, NOT
--                     evidence about GRAP's effect. Weather also differs across
--                     stages (see 09_weather_summary.sql). This table is context
--                     only; it makes no causal claim. In-season days only.
-- Run (example)     : sqlite3 data/processed/delhi_aqi_grap.db < sql/05_stage_summary.sql
-- ===========================================================================
SELECT
    active_stage,
    COUNT(*)                        AS n_station_days,
    COUNT(pm25_ugm3)                AS n_pm25_obs,
    ROUND(AVG(pm25_ugm3), 1)        AS pm25_mean,
    ROUND(AVG(pm10_ugm3), 1)        AS pm10_mean,
    ROUND(AVG(wind_speed_ms), 2)    AS wind_mean_ms,
    ROUND(AVG(air_temp_c), 1)       AS temp_mean_c,
    ROUND(AVG(rh_pct), 1)           AS rh_mean_pct
FROM v_station_daily_enriched
WHERE is_grap_season = 1
  AND active_stage IS NOT NULL
GROUP BY active_stage
ORDER BY active_stage;
