"""
Phase 4 — Build the canonical clean dataset.

Reads all 16 validated raw CPCB files and produces:
  data/processed/station_daily.csv   (grain: one station x one calendar day)

Also (Phase 5) writes the explicit station metadata:
  data/processed/stations.csv

Guarantees:
  - raw files are read only, never modified
  - column names standardised to snake_case
  - dates parsed from the two different raw timestamp formats
  - station_id / station_name / year / source_file provenance retained
  - NO imputation, interpolation, winsorising, or row dropping for missing values
  - only the 6 core variables + date are retained (project decision)

Run:  python src/03_build_station_daily.py
"""
from __future__ import annotations

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C

FINAL_COLUMNS = [
    "station_id", "station_name", "year", "date",
    *C.CORE_STD_COLUMNS,
    "source_file",
]


def build_one(path: str) -> pd.DataFrame:
    meta = C.parse_raw_filename(os.path.basename(path))
    df = pd.read_csv(path)

    # Parse both raw timestamp vintages ("YYYY-MM-DD" and "YYYY-MM-DD HH:MM:SS").
    date = pd.to_datetime(df[C.TIMESTAMP_COL], errors="coerce").dt.normalize()

    out = pd.DataFrame({
        "station_id": meta["station_id"],
        "station_name": meta["station_name"],
        "year": meta["year"],
        "date": date,
    })
    # Core variables -> numeric (coercion only; missing stays missing).
    for raw_col, std_col in C.CORE_COLUMN_MAP.items():
        out[std_col] = pd.to_numeric(df[raw_col], errors="coerce")
    out["source_file"] = meta["source_file"]
    return out


def build_station_daily() -> pd.DataFrame:
    paths = sorted(str(p) for p in C.RAW_CPCB_DIR.glob("*.csv"))
    if not paths:
        raise FileNotFoundError(f"No CSV files under {C.RAW_CPCB_DIR}")

    frames = [build_one(p) for p in paths]
    daily = pd.concat(frames, ignore_index=True)
    daily = daily[FINAL_COLUMNS]
    daily = daily.sort_values(["station_id", "date"]).reset_index(drop=True)

    # Validate uniqueness of the grain (station_id + date). Fail loud.
    dupes = daily.duplicated(subset=["station_id", "date"]).sum()
    if dupes:
        raise ValueError(f"{dupes} duplicate station_id+date rows in processed data")
    if len(daily) > C.MAX_PROCESSED_ROWS:
        raise ValueError(
            f"{len(daily)} rows exceeds max {C.MAX_PROCESSED_ROWS}")

    # keep date as ISO date string for a clean CSV
    daily["date"] = daily["date"].dt.strftime("%Y-%m-%d")
    return daily


def build_stations() -> pd.DataFrame:
    rows = []
    for slug, m in C.STATIONS.items():
        rows.append({
            "station_id": slug,
            "station_name": m["station_name"],
            "display_name": m["display_name"],
            "operating_agency": m["operating_agency"],
            "geographic_role": m["geographic_role"],
            "selected": True,
            "selection_reason": (
                "geographic coverage; 2022+2023 availability; "
                "PM2.5 & weather availability; missingness quality filter"
            ),
            "latitude": "",   # left blank — no verified coordinates in source yet
            "longitude": "",
        })
    return pd.DataFrame(rows)


def main() -> int:
    C.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    daily = build_station_daily()
    daily.to_csv(C.STATION_DAILY_CSV, index=False, encoding="utf-8")

    stations = build_stations()
    stations.to_csv(C.STATIONS_CSV, index=False, encoding="utf-8")

    print(f"Wrote {C.STATION_DAILY_CSV}")
    print(f"  rows: {len(daily)} (max allowed {C.MAX_PROCESSED_ROWS})")
    print(f"  stations: {daily['station_id'].nunique()} | "
          f"years: {sorted(daily['year'].unique())}")
    print(f"  date range: {daily['date'].min()} .. {daily['date'].max()}")
    print(f"  core-var null counts:")
    for col in C.CORE_STD_COLUMNS:
        print(f"    {col:16} {int(daily[col].isna().sum())}")
    print(f"Wrote {C.STATIONS_CSV} ({len(stations)} stations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
