"""
Phase 2 (prep) — Build the SQLite analytical warehouse from validated outputs.

Reads the Phase-1 processed CSVs and the *verified* GRAP events, applies the
schema in sql/00_schema.sql, and loads three base tables:
    stations, station_daily, grap_events

The warehouse (data/processed/delhi_aqi_grap.db) is a DERIVED artifact: it is
dropped and rebuilt on every run and is safe to delete. It never modifies raw
or processed data.

Guarantees / guardrails:
  * NaN / blank cells become SQL NULL (no '' text leaking into REAL columns).
  * GRAP events are loaded ONLY if the source file passes the data contract with
    zero ERRORs (reuses src/04_validate_grap_events.py), and only rows with
    verified == 'Yes' are inserted. No event is invented, edited, or reordered.
  * All derived GRAP state / event windows are VIEWS (see schema) — nothing is
    materialised, so the DB cannot drift from the CSVs.

Run:  python src/05_load_sqlite.py
Exit code 0 on success; 1 if the GRAP file has contract ERRORs or inputs are missing.
"""
from __future__ import annotations

import importlib.util
import os
import sqlite3
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C

# Import the GRAP validator by path (its filename starts with a digit).
_VALIDATOR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "04_validate_grap_events.py")
_spec = importlib.util.spec_from_file_location("grap_validator", _VALIDATOR_PATH)
gv = importlib.util.module_from_spec(_spec)
sys.modules["grap_validator"] = gv
_spec.loader.exec_module(gv)


def _nan_to_none(df: pd.DataFrame) -> list[tuple]:
    """Rows as tuples with NaN/NaT -> None so sqlite stores NULL, not ''."""
    return [tuple(None if pd.isna(v) else v for v in row)
            for row in df.itertuples(index=False, name=None)]


def load_stations(conn: sqlite3.Connection) -> int:
    df = pd.read_csv(C.STATIONS_CSV)
    # 'selected' arrives as True/False -> 1/0; blank lat/lon -> NULL.
    df["selected"] = df["selected"].astype(str).str.strip().str.lower().map(
        {"true": 1, "false": 0}).fillna(0).astype(int)
    for col in ("latitude", "longitude"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    cols = ["station_id", "station_name", "display_name", "operating_agency",
            "geographic_role", "selected", "selection_reason",
            "latitude", "longitude"]
    conn.executemany(
        f"INSERT INTO stations ({','.join(cols)}) "
        f"VALUES ({','.join('?' * len(cols))})",
        _nan_to_none(df[cols]),
    )
    return len(df)


def load_station_daily(conn: sqlite3.Connection) -> int:
    df = pd.read_csv(C.STATION_DAILY_CSV)
    cols = ["station_id", "date", "year", "pm25_ugm3", "pm10_ugm3",
            "air_temp_c", "rh_pct", "wind_speed_ms", "wind_dir_deg",
            "source_file"]
    conn.executemany(
        f"INSERT INTO station_daily ({','.join(cols)}) "
        f"VALUES ({','.join('?' * len(cols))})",
        _nan_to_none(df[cols]),
    )
    return len(df)


def load_grap_events(conn: sqlite3.Connection) -> tuple[int, int]:
    """Validate then load only verified rows. Returns (n_rows_in_file, n_loaded)."""
    df = pd.read_csv(C.GRAP_EVENTS_CSV, dtype=str, keep_default_na=False)
    findings = gv.validate_events(df)
    errors = [f for f in findings if f.severity == gv.ERROR]
    if errors:
        for f in errors:
            where = "file" if f.row is None else f"row {f.row}"
            print(f"  GRAP ERROR [{f.code}] {where}: {f.message}", file=sys.stderr)
        raise SystemExit(
            "Refusing to load: GRAP event file has contract ERRORs. "
            "Fix data/raw/grap/grap_events_manual.csv and re-run.")

    verified = df[df["verified"].astype(str).str.strip() == "Yes"].copy()
    # Empty strings -> None; stage codes -> int.
    for col in verified.columns:
        verified[col] = verified[col].map(lambda v: None if str(v).strip() == "" else v)
    for col in ("stage_from", "stage_to"):
        verified[col] = verified[col].map(lambda v: int(float(v)) if v is not None else None)

    cols = list(gv.EXPECTED_COLUMNS)
    conn.executemany(
        f"INSERT INTO grap_events ({','.join(cols)}) "
        f"VALUES ({','.join('?' * len(cols))})",
        [tuple(r[c] for c in cols) for _, r in verified.iterrows()],
    )
    return len(df), len(verified)


def main() -> int:
    for path, label in ((C.STATION_DAILY_CSV, "station_daily.csv"),
                        (C.STATIONS_CSV, "stations.csv"),
                        (C.GRAP_EVENTS_CSV, "grap_events_manual.csv"),
                        (C.SQL_SCHEMA, "00_schema.sql")):
        if not os.path.exists(path):
            print(f"ERROR: missing input: {path}", file=sys.stderr)
            return 1

    # Fresh build every time — the DB is a derived, disposable artifact.
    if os.path.exists(C.SQLITE_DB):
        os.remove(C.SQLITE_DB)

    schema_sql = C.SQL_SCHEMA.read_text(encoding="utf-8")
    conn = sqlite3.connect(C.SQLITE_DB)
    try:
        conn.executescript(schema_sql)
        n_stations = load_stations(conn)
        n_daily = load_station_daily(conn)
        n_events_file, n_events_loaded = load_grap_events(conn)
        conn.commit()

        # Lightweight post-load sanity (counts only; no analysis).
        n_state = conn.execute("SELECT COUNT(*) FROM daily_grap_state").fetchone()[0]
        n_win = conn.execute("SELECT COUNT(*) FROM event_windows").fetchone()[0]
    finally:
        conn.close()

    print(f"Built {C.SQLITE_DB}")
    print(f"  stations         : {n_stations}")
    print(f"  station_daily    : {n_daily} (expected {C.MAX_PROCESSED_ROWS})")
    print(f"  grap_events      : {n_events_loaded} loaded "
          f"(of {n_events_file} rows in file; verified only)")
    print(f"  daily_grap_state : {n_state} in-season date-rows (view)")
    print(f"  event_windows    : {n_win} rows (view, +/-30 days x stations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
