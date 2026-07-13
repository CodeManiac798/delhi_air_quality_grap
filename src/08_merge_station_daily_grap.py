"""
Phase 4 (PHASE D) — Merge datasets: station_daily + daily_grap_state.

Input:
  - data/processed/station_daily.csv (8 stations × 730 days = 5,840 rows)
  - data/processed/daily_grap_state.csv (730 days)

Output:
  - data/processed/station_daily_grap.csv

Grain: one station × one day (5,840 rows expected)

Fields:
  station_id, station_name, date, year, pm25_ugm3, pm10_ugm3,
  air_temp_c, rh_pct, wind_speed_ms, wind_dir_deg,
  grap_stage, is_event_day, days_since_last_change, days_until_next_change, source_file
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C


def main() -> int:
    try:
        # Read inputs
        station_daily = pd.read_csv(C.STATION_DAILY_CSV)
        daily_grap_state = pd.read_csv(C.DAILY_GRAP_STATE_CSV)
    except FileNotFoundError as e:
        print(f"ERROR: Input file missing: {e}", file=sys.stderr)
        return 1

    # Merge station_daily with daily_grap_state
    merged = station_daily.merge(
        daily_grap_state,
        on="date",
        how="left"
    )

    # Reorder columns for output
    output_cols = [
        "station_id",
        "station_name",
        "date",
        "year",
        "pm25_ugm3",
        "pm10_ugm3",
        "air_temp_c",
        "rh_pct",
        "wind_speed_ms",
        "wind_dir_deg",
        "season",
        "grap_stage",
        "is_event_day",
        "days_since_last_change",
        "days_until_next_change",
        "source_file",
    ]

    merged = merged[output_cols]

    # Write output
    output_path = Path(C.DAILY_GRAP_STATE_CSV).parent / "station_daily_grap.csv"
    merged.to_csv(output_path, index=False)

    print(f"Built {output_path}")
    print(f"  Rows: {len(merged)}")
    print(f"  Expected: {8 * 730}")
    print(f"  Unique stations: {merged['station_id'].nunique()}")
    print(f"  Date range: {merged['date'].min()} to {merged['date'].max()}")
    print(f"  Unique GRAP stages: {sorted(merged['grap_stage'].dropna().unique())}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
