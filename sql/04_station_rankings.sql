-- ===========================================================================
-- 04_station_rankings.sql
-- Business question : Within each GRAP season, which stations are the most and
--                     least polluted (by mean PM2.5)?
-- Purpose           : Rank the 8 stations per season so later "where were
--                     improvements weakest?" work has a clear ordering to anchor
--                     on. Demonstrates window RANK().
-- Expected output   : one row per (season, station); rank 1 = dirtiest. Columns:
--                     season, station_id, n_obs, pm25_mean, rank_dirtiest.
-- Dependencies      : v_station_daily_enriched
-- Notes / caveats   : Restricted to in-season days (season IS NOT NULL). Season
--                     2023-24 is TRUNCATED at 2023-12-31, so its ranking covers
--                     Oct-Dec only and is NOT comparable to the full 2022-23
--                     season. To rank OVERALL instead, drop `PARTITION BY season`.
-- Run (example)     : sqlite3 data/processed/delhi_aqi_grap.db < sql/04_station_rankings.sql
-- ===========================================================================
WITH season_means AS (
    SELECT
        season,
        station_id,
        COUNT(pm25_ugm3)          AS n_obs,
        ROUND(AVG(pm25_ugm3), 1)  AS pm25_mean
    FROM v_station_daily_enriched
    WHERE season IS NOT NULL
    GROUP BY season, station_id
)
SELECT
    season,
    station_id,
    n_obs,
    pm25_mean,
    RANK() OVER (PARTITION BY season ORDER BY pm25_mean DESC) AS rank_dirtiest
FROM season_means
ORDER BY season, rank_dirtiest;
