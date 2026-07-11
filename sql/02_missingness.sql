-- ===========================================================================
-- 02_missingness.sql
-- Business question : Where are the data holes? Per station-year, how complete is
--                     each of the 6 core variables?
-- Purpose           : Reproduce the Phase-1 missingness audit from the warehouse
--                     so completeness travels with every downstream query/BI page.
--                     Trust in any trend depends on the denominator behind it.
-- Expected output   : 16 rows (8 stations x 2 years). n_days plus null_pct per
--                     variable. Ordered by station, year.
-- Dependencies      : station_daily
-- Notes / caveats   : Should reconcile with
--                     reports/data_quality/core_variable_missingness.csv (that
--                     file is the authoritative Phase-1 audit; this is a live
--                     mirror). JLN Stadium 2023 PM10 (~13%) is the known worst.
-- Run (example)     : sqlite3 data/processed/delhi_aqi_grap.db < sql/02_missingness.sql
-- ===========================================================================
SELECT
    station_id,
    year,
    COUNT(*)                                                       AS n_days,
    ROUND(100.0 * (COUNT(*) - COUNT(pm25_ugm3))    / COUNT(*), 2)  AS pm25_null_pct,
    ROUND(100.0 * (COUNT(*) - COUNT(pm10_ugm3))    / COUNT(*), 2)  AS pm10_null_pct,
    ROUND(100.0 * (COUNT(*) - COUNT(air_temp_c))   / COUNT(*), 2)  AS temp_null_pct,
    ROUND(100.0 * (COUNT(*) - COUNT(rh_pct))       / COUNT(*), 2)  AS rh_null_pct,
    ROUND(100.0 * (COUNT(*) - COUNT(wind_speed_ms))/ COUNT(*), 2)  AS wind_speed_null_pct,
    ROUND(100.0 * (COUNT(*) - COUNT(wind_dir_deg)) / COUNT(*), 2)  AS wind_dir_null_pct
FROM station_daily
GROUP BY station_id, year
ORDER BY station_id, year;
