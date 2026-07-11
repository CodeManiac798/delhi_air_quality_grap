-- ===========================================================================
-- 07_station_vs_stage.sql
-- Business question : Does every station show the same PM2.5 gradient across GRAP
--                     stages, or do some stations barely differ between stages?
-- Purpose           : Station x stage mean-PM2.5 matrix (long format) — the data
--                     behind a station-by-stage heatmap and the "where were
--                     improvements weakest?" question.
-- Expected output   : one row per (station_id, active_stage). Columns: station_id,
--                     active_stage, n_obs, pm25_mean. Pivot in BI to a matrix.
-- Dependencies      : v_station_daily_enriched (-> daily_grap_state)
-- Notes / caveats   : Same interpretation warning as 05: stage is defined by
--                     regional air quality, so cross-stage differences are not a
--                     causal GRAP effect and are confounded by weather and by how
--                     few days some stage/station cells contain (check n_obs).
--                     In-season days only.
-- Run (example)     : sqlite3 data/processed/delhi_aqi_grap.db < sql/07_station_vs_stage.sql
-- ===========================================================================
SELECT
    station_id,
    active_stage,
    COUNT(pm25_ugm3)          AS n_obs,
    ROUND(AVG(pm25_ugm3), 1)  AS pm25_mean
FROM v_station_daily_enriched
WHERE is_grap_season = 1
  AND active_stage IS NOT NULL
GROUP BY station_id, active_stage
ORDER BY station_id, active_stage;
