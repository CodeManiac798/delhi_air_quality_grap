-- ===========================================================================
-- 06_event_window.sql
-- Business question : Around each GRAP event, how does average PM2.5 evolve day
--                     by day from 14 days before to 14 days after the change?
-- Purpose           : The raw material for event-study line plots (x = rel_day,
--                     y = PM2.5). Pools across the 8 stations to one series per
--                     event per relative day.
-- Expected output   : one row per (event_id, rel_day) for rel_day in [-14, 14].
--                     Columns: event_id, rel_day, n_stations_reporting,
--                     pm25_mean_across_stations.
-- Dependencies      : event_windows (-> grap_events, station_daily)
-- Notes / caveats   : rel_day 0 = effective_date. This is a RAW descriptive
--                     window: NOT weather-adjusted (see the weather-adjustment
--                     step) and the +/-14 windows of the 5 events overlap (events
--                     are 3-14 days apart), so a "before" window can contain a
--                     neighbouring event. Use event_direction from grap_events to
--                     interpret each panel. n_stations_reporting guards thin days.
-- Run (example)     : sqlite3 data/processed/delhi_aqi_grap.db < sql/06_event_window.sql
-- ===========================================================================
SELECT
    event_id,
    rel_day,
    COUNT(pm25_ugm3)           AS n_stations_reporting,
    ROUND(AVG(pm25_ugm3), 1)   AS pm25_mean_across_stations
FROM event_windows
WHERE rel_day BETWEEN -14 AND 14
GROUP BY event_id, rel_day
ORDER BY event_id, rel_day;
