-- ===========================================================================
-- 01_station_summary.sql
-- Business question : What is each station's overall pollution + weather profile
--                     across the full 2022-2023 daily record?
-- Purpose           : One-line-per-station orientation table; the first thing to
--                     read before any GRAP-specific analysis.
-- Expected output   : 8 rows (one per station). Columns: identity, day counts,
--                     PM2.5 completeness, PM2.5 mean/min/max, PM10 mean, weather
--                     means. Ordered dirtiest-first by PM2.5 mean.
-- Dependencies      : station_daily, stations
-- Notes / caveats   : Means are simple daily means over ALL available days (both
--                     GRAP and off-season). NULLs are ignored by AVG/MIN/MAX.
--                     Median/percentiles are intentionally NOT computed in SQL
--                     (SQLite has no MEDIAN) — do those in the pandas EDA step.
-- Run (example)     : sqlite3 data/processed/delhi_aqi_grap.db < sql/01_station_summary.sql
-- ===========================================================================
SELECT
    s.station_id,
    s.station_name,
    s.geographic_role,
    COUNT(*)                                             AS n_station_days,
    COUNT(sd.pm25_ugm3)                                  AS n_pm25_obs,
    ROUND(100.0 * COUNT(sd.pm25_ugm3) / COUNT(*), 1)     AS pm25_completeness_pct,
    ROUND(AVG(sd.pm25_ugm3), 1)                          AS pm25_mean,
    ROUND(MIN(sd.pm25_ugm3), 1)                          AS pm25_min,
    ROUND(MAX(sd.pm25_ugm3), 1)                          AS pm25_max,
    ROUND(AVG(sd.pm10_ugm3), 1)                          AS pm10_mean,
    ROUND(AVG(sd.air_temp_c), 1)                         AS temp_mean_c,
    ROUND(AVG(sd.rh_pct), 1)                             AS rh_mean_pct,
    ROUND(AVG(sd.wind_speed_ms), 2)                      AS wind_mean_ms
FROM station_daily sd
JOIN stations s ON s.station_id = sd.station_id
GROUP BY s.station_id, s.station_name, s.geographic_role
ORDER BY pm25_mean DESC;
