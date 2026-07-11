-- ===========================================================================
-- 03_monthly_pm25.sql
-- Business question : How does monthly-average PM2.5 move over 2022-2023 at each
--                     station (the seasonal winter-pollution shape)?
-- Purpose           : Long-format monthly time series to feed a line chart and to
--                     sanity-check that the winter GRAP season is where the peaks
--                     actually are, before doing event-level work.
-- Expected output   : up to 8 stations x 24 months rows. Columns: station_id,
--                     year_month, season, is_grap_season, n_obs, pm25_mean.
-- Dependencies      : v_station_daily_enriched (-> station_daily, v_calendar)
-- Notes / caveats   : n_obs is the number of non-null PM2.5 days behind each mean
--                     — treat months with low n_obs with caution. Monthly means
--                     mix GRAP stages within a month; this is context, not an
--                     event analysis.
-- Run (example)     : sqlite3 data/processed/delhi_aqi_grap.db < sql/03_monthly_pm25.sql
-- ===========================================================================
SELECT
    station_id,
    year_month,
    season,
    is_grap_season,
    COUNT(pm25_ugm3)             AS n_obs,
    ROUND(AVG(pm25_ugm3), 1)     AS pm25_mean
FROM v_station_daily_enriched
GROUP BY station_id, year_month
ORDER BY station_id, year_month;
