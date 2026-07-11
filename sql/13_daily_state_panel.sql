-- ===========================================================================
-- 13_daily_state_panel.sql
-- Business question : On any given in-season day, what GRAP stage was active and
--                     how many stations were actually reporting PM2.5?
-- Purpose           : The daily "spine" that (a) lets you visually verify the
--                     step-function state is correct and (b) drives date/stage
--                     slicers in Power BI. Also exposes daily station coverage.
-- Expected output   : one row per in-season date (243 with current data).
--                     Columns: date, season, active_stage, n_stations_pm25.
-- Dependencies      : daily_grap_state, station_daily
-- Notes / caveats   : active_stage is the derived state (see 00_schema.sql).
--                     n_stations_pm25 out of 8 = how many stations had a non-null
--                     PM2.5 that day; days well below 8 mean the daily cross-
--                     station mean rests on fewer stations. Off-season days are
--                     excluded by construction (no GRAP state there).
-- Run (example)     : sqlite3 data/processed/delhi_aqi_grap.db < sql/13_daily_state_panel.sql
-- ===========================================================================
SELECT
    gs.date,
    gs.season,
    gs.active_stage,
    COUNT(sd.pm25_ugm3) AS n_stations_pm25
FROM daily_grap_state gs
LEFT JOIN station_daily sd ON sd.date = gs.date
GROUP BY gs.date, gs.season, gs.active_stage
ORDER BY gs.date;
