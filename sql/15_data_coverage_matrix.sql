-- ===========================================================================
-- 15_data_coverage_matrix.sql
-- Business question : For every station and month, how many days actually have a
--                     PM2.5 reading (so which cells can we trust)?
-- Purpose           : A station x month coverage matrix to place beside any trend
--                     chart. Prevents over-reading months that are half-empty.
-- Expected output   : one row per (station_id, year_month). Columns: calendar
--                     days in the month, observed PM2.5 days, and coverage %.
--                     Pivot in BI to a station-by-month heatmap.
-- Dependencies      : v_station_daily_enriched
-- Notes / caveats   : This is the completeness companion to every analytical
--                     query; it makes gaps explicit. Should agree with
--                     02_missingness.sql when aggregated to station-year.
-- Run (example)     : sqlite3 data/processed/delhi_aqi_grap.db < sql/15_data_coverage_matrix.sql
-- ===========================================================================
SELECT
    station_id,
    year_month,
    COUNT(*)                                          AS calendar_days,
    COUNT(pm25_ugm3)                                  AS pm25_days,
    ROUND(100.0 * COUNT(pm25_ugm3) / COUNT(*), 0)     AS pm25_coverage_pct
FROM v_station_daily_enriched
GROUP BY station_id, year_month
ORDER BY station_id, year_month;
