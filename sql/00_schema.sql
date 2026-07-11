-- ============================================================================
-- Delhi AQI / GRAP — SQLite analytical schema (Phase 2 layer)
-- ============================================================================
-- PURPOSE
--   Turn the validated Phase-1 CSV outputs into a small, well-keyed SQLite
--   warehouse that supports rolling averages, window functions, event studies,
--   station comparisons and Power BI — with NO redundant storage.
--
-- DESIGN PRINCIPLES
--   * Three BASE tables only (stations, station_daily, grap_events). Everything
--     else is a VIEW derived from them — the derived GRAP state and event
--     windows are never stored twice, so they can never drift from the source.
--   * The warehouse is a *derived* artifact. It is rebuilt from
--     data/processed/*.csv and the verified rows of grap_events_manual.csv.
--     Deleting delhi_aqi_grap.db loses nothing.
--   * Grain is explicit and enforced with primary keys.
--   * No imputation, winsorising, or row-dropping happens here — missing values
--     arrive as NULL and stay NULL, exactly as in Phase 1.
--
-- WHAT THIS FILE DOES
--   Creates the 3 base tables + their keys/indexes, then the derived views:
--     v_calendar            date dimension (year/month/season/is_grap_season)
--     daily_grap_state      one row per in-season date -> active GRAP stage
--     v_station_daily_enriched   station_daily + season + active_stage (BI feed)
--     event_windows         +/-30-day panel around each event's effective_date
--
-- LOAD ORDER: run this file, then load the 3 CSVs (see sql/README.md or
--   `python src/05_load_sqlite.py`). Views are lazy, so creating them before the
--   data is loaded is fine.
--
-- SQLite version: requires >= 3.25 (window functions). Ships with Python 3.13.
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- DIMENSION: stations  (one row per selected monitoring station)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stations (
    station_id       TEXT PRIMARY KEY,          -- slug, e.g. 'anand_vihar'
    station_name     TEXT NOT NULL,
    display_name     TEXT,
    operating_agency TEXT,                       -- all 'DPCC' in current sample
    geographic_role  TEXT,                       -- 'east', 'central', ...
    selected         INTEGER,                    -- 1/0 boolean
    selection_reason TEXT,
    latitude         REAL,                        -- NULL until verified
    longitude        REAL                         -- NULL until verified
);

-- ----------------------------------------------------------------------------
-- FACT: station_daily  (grain: one station x one calendar day)
-- ----------------------------------------------------------------------------
-- Expected 8 stations x 730 days = 5,840 rows. Every (station_id, date) is
-- present even when the measured values are NULL, so ROWS-based window frames
-- equal calendar-day frames (relied on by the rolling-average queries).
CREATE TABLE IF NOT EXISTS station_daily (
    station_id     TEXT NOT NULL,
    date           TEXT NOT NULL,                -- ISO 'YYYY-MM-DD' (sorts correctly)
    year           INTEGER NOT NULL,
    pm25_ugm3      REAL,                          -- primary outcome; NULL if missing
    pm10_ugm3      REAL,
    air_temp_c     REAL,
    rh_pct         REAL,
    wind_speed_ms  REAL,
    wind_dir_deg   REAL,
    source_file    TEXT NOT NULL,                -- provenance
    PRIMARY KEY (station_id, date),
    FOREIGN KEY (station_id) REFERENCES stations(station_id)
);

-- Cross-station scans on a date range (event windows, daily state joins).
CREATE INDEX IF NOT EXISTS ix_station_daily_date        ON station_daily(date);
CREATE INDEX IF NOT EXISTS ix_station_daily_station_year ON station_daily(station_id, year);

-- ----------------------------------------------------------------------------
-- EVENT CALENDAR: grap_events  (only verified=Yes rows are ever loaded)
-- ----------------------------------------------------------------------------
-- Mirrors docs/grap_event_data_contract.md. A row is a point at which the
-- active GRAP state changed for Delhi-NCR. effective_date is the analytical
-- anchor. Load is gated: src/05_load_sqlite.py refuses to load unless the file
-- passes src/04_validate_grap_events.py with zero ERRORs, and inserts only
-- verified='Yes' rows.
CREATE TABLE IF NOT EXISTS grap_events (
    event_id             TEXT PRIMARY KEY,
    order_date           TEXT,                    -- ISO date or NULL
    effective_date       TEXT NOT NULL,           -- ISO date; analysis anchor
    season               TEXT NOT NULL,           -- '2022-23' | '2023-24'
    action_type          TEXT,                    -- invoke|escalate|de_escalate|revoke|other
    stage_from           INTEGER,                 -- 0..4
    stage_to             INTEGER,                 -- 0..4
    event_direction      TEXT,                    -- activation|escalation|de_escalation|full_revocation|other
    immediate_effect     TEXT,                    -- 'Yes'|'No'
    official_order_title  TEXT,
    official_source      TEXT,                    -- official CAQM URL
    notes                TEXT,
    verified             TEXT                     -- always 'Yes' once loaded
);

CREATE INDEX IF NOT EXISTS ix_grap_events_effective ON grap_events(effective_date);
CREATE INDEX IF NOT EXISTS ix_grap_events_season    ON grap_events(season, effective_date);

-- ============================================================================
-- DERIVED VIEWS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- v_calendar — date dimension derived from the dates present in station_daily.
-- ----------------------------------------------------------------------------
-- GRAP "season" is the Oct 1 -> Feb (next year) 28/29 window. NOTE the data only
-- spans 2022-01-01..2023-12-31, so season 2023-24 is TRUNCATED at 2023-12-31
-- (Jan/Feb 2024 are not in the dataset). Downstream analysis must respect this.
DROP VIEW IF EXISTS v_calendar;
CREATE VIEW v_calendar AS
WITH d AS (SELECT DISTINCT date FROM station_daily)
SELECT
    date,
    CAST(strftime('%Y', date) AS INTEGER)               AS year,
    CAST(strftime('%m', date) AS INTEGER)               AS month,
    strftime('%Y-%m', date)                             AS year_month,
    CAST(strftime('%d', date) AS INTEGER)               AS day,
    CAST(strftime('%w', date) AS INTEGER)               AS dow,   -- 0=Sun..6=Sat
    CASE
        WHEN date BETWEEN '2022-10-01' AND '2023-02-28' THEN '2022-23'
        WHEN date BETWEEN '2023-10-01' AND '2024-02-29' THEN '2023-24'
        ELSE NULL
    END                                                 AS grap_season,
    CASE
        WHEN date BETWEEN '2022-10-01' AND '2023-02-28'
          OR date BETWEEN '2023-10-01' AND '2024-02-29' THEN 1
        ELSE 0
    END                                                 AS is_grap_season
FROM d;

-- ----------------------------------------------------------------------------
-- daily_grap_state — one row per IN-SEASON date -> the active GRAP stage.
-- ----------------------------------------------------------------------------
-- Active stage on date D = stage_to of the most recent event (max effective_date
-- <= D) WITHIN the same season; 0 if no event has fired yet in that season.
-- The step-function is scoped per season so a prior season's stage never leaks
-- into the next. Because the loaded calendar is a FIRST BATCH (season 2022-23,
-- no end-of-season revocation yet, no 2023-24 events), the derived state trails
-- the last known event to season end — a known data-completeness limitation,
-- NOT an inferred fact. See docs/issue_tracker.md.
DROP VIEW IF EXISTS daily_grap_state;
CREATE VIEW daily_grap_state AS
SELECT
    c.date,
    c.grap_season AS season,
    COALESCE((
        SELECT e.stage_to
        FROM grap_events e
        WHERE e.season = c.grap_season
          AND e.effective_date <= c.date
        ORDER BY e.effective_date DESC
        LIMIT 1
    ), 0) AS active_stage
FROM v_calendar c
WHERE c.grap_season IS NOT NULL;

-- ----------------------------------------------------------------------------
-- v_station_daily_enriched — the workhorse fact view for BI and most queries.
-- ----------------------------------------------------------------------------
-- station_daily + station attributes + calendar attributes + active GRAP stage.
-- active_stage is NULL for off-season days (no GRAP concept there). No values
-- are imputed. This is the single view Power BI should point its fact table at.
DROP VIEW IF EXISTS v_station_daily_enriched;
CREATE VIEW v_station_daily_enriched AS
SELECT
    sd.station_id,
    s.station_name,
    s.geographic_role,
    sd.date,
    sd.year,
    cal.month,
    cal.year_month,
    cal.dow,
    cal.grap_season          AS season,
    cal.is_grap_season,
    gs.active_stage,
    sd.pm25_ugm3,
    sd.pm10_ugm3,
    sd.air_temp_c,
    sd.rh_pct,
    sd.wind_speed_ms,
    sd.wind_dir_deg
FROM station_daily sd
JOIN stations   s   ON s.station_id = sd.station_id
JOIN v_calendar cal ON cal.date     = sd.date
LEFT JOIN daily_grap_state gs ON gs.date = sd.date;

-- ----------------------------------------------------------------------------
-- event_windows — +/-30 calendar-day panel around each event's effective_date.
-- ----------------------------------------------------------------------------
-- One row per (event_id x station_id x date) within the window. rel_day is the
-- signed day offset from effective_date (0 = event day). period buckets it into
-- before / event_day / after. Downstream event-study queries narrow the window
-- (e.g. rel_day BETWEEN -7 AND 7). The half-window is fixed at 30 here; widen
-- by editing the BETWEEN bounds below. Windows may overlap adjacent events and
-- may spill past the 2023-12-31 data boundary — filter by rel_day availability.
DROP VIEW IF EXISTS event_windows;
CREATE VIEW event_windows AS
SELECT
    e.event_id,
    e.season,
    e.effective_date,
    e.stage_from,
    e.stage_to,
    e.event_direction,
    sd.station_id,
    sd.date,
    CAST(julianday(sd.date) - julianday(e.effective_date) AS INTEGER) AS rel_day,
    CASE
        WHEN sd.date <  e.effective_date THEN 'before'
        WHEN sd.date =  e.effective_date THEN 'event_day'
        ELSE 'after'
    END AS period,
    sd.pm25_ugm3,
    sd.pm10_ugm3,
    sd.air_temp_c,
    sd.rh_pct,
    sd.wind_speed_ms,
    sd.wind_dir_deg
FROM grap_events e
JOIN station_daily sd
  ON julianday(sd.date) BETWEEN julianday(e.effective_date) - 30
                            AND julianday(e.effective_date) + 30;

-- ============================================================================
-- End of schema. Load data next (sql/README.md). No analysis runs here.
-- ============================================================================
