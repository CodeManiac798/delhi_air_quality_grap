"""
Phase 5 (PHASE E) — Validate merged dataset integrity.

Input: data/processed/station_daily_grap.csv

Checks:
  1. Expected row count (5,840 = 8 stations × 730 days)
  2. Exactly 8 unique stations
  3. No duplicate (station_id, date) pairs
  4. Every station-day has one GRAP stage
  5. Every station-day belongs to exactly one season
  6. No merge failures (no unexpected NULLs in critical fields)
  7. No orphan dates (all dates 2022-01-01 to 2023-12-31)
  8. No NULL GRAP stage before E001
"""
from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C


def validate_merged_dataset() -> dict:
    """Run all validation checks. Return findings dict."""
    findings = {
        "checks_passed": [],
        "checks_failed": [],
        "data_overview": {},
    }

    try:
        merged_df = pd.read_csv(C.STATION_DAILY_GRAP_CSV)
    except FileNotFoundError as e:
        findings["checks_failed"].append(f"Input file missing: {e}")
        return findings

    # Parse dates
    merged_df["date"] = pd.to_datetime(merged_df["date"]).dt.date

    # =====================================================================
    # CHECK 1: Expected row count
    # =====================================================================
    expected_rows = 8 * 730  # 8 stations, 730 days
    actual_rows = len(merged_df)

    if actual_rows == expected_rows:
        findings["checks_passed"].append(
            f"CHECK 1: Expected row count ({actual_rows})"
        )
    else:
        findings["checks_failed"].append(
            f"CHECK 1 FAILED: Expected {expected_rows} rows, got {actual_rows}"
        )

    # =====================================================================
    # CHECK 2: Exactly 8 unique stations
    # =====================================================================
    unique_stations = merged_df["station_id"].nunique()

    if unique_stations == 8:
        findings["checks_passed"].append(
            f"CHECK 2: Exactly 8 unique stations"
        )
    else:
        findings["checks_failed"].append(
            f"CHECK 2 FAILED: Expected 8 unique stations, got {unique_stations}"
        )

    # =====================================================================
    # CHECK 3: No duplicate (station_id, date) pairs
    # =====================================================================
    duplicates = merged_df[merged_df.duplicated(subset=["station_id", "date"], keep=False)]

    if len(duplicates) == 0:
        findings["checks_passed"].append(
            "CHECK 3: No duplicate (station_id, date) pairs"
        )
    else:
        findings["checks_failed"].append(
            f"CHECK 3 FAILED: Found {len(duplicates)} duplicate station-day pairs"
        )

    # =====================================================================
    # CHECK 4: Every station-day has one GRAP stage
    # =====================================================================
    null_stages = merged_df[merged_df["grap_stage"].isna()]

    if len(null_stages) == 0:
        findings["checks_passed"].append(
            "CHECK 4: Every station-day has a GRAP stage (no NULL)"
        )
    else:
        findings["checks_failed"].append(
            f"CHECK 4 FAILED: {len(null_stages)} station-days have NULL grap_stage"
        )

    # =====================================================================
    # CHECK 5: Every station-day belongs to exactly one season
    # =====================================================================
    # Note: off-season days have season=NULL, which is valid
    null_seasons = merged_df[merged_df["season"].isna()]
    total_off_season = len(null_seasons)
    expected_off_season = 8 * (730 - 302)  # 730 total days - 302 in-season days = 428 off-season per station

    if total_off_season == expected_off_season:
        findings["checks_passed"].append(
            f"CHECK 5: Season assignment correct ({total_off_season} off-season station-days)"
        )
    else:
        findings["checks_failed"].append(
            f"CHECK 5 FAILED: Expected {expected_off_season} off-season station-days, got {total_off_season}"
        )

    # =====================================================================
    # CHECK 6: No merge failures
    # =====================================================================
    critical_cols = ["station_id", "station_name", "date", "grap_stage"]
    merge_failures = merged_df[merged_df[critical_cols].isna().any(axis=1)]

    if len(merge_failures) == 0:
        findings["checks_passed"].append(
            "CHECK 6: No NULL values in critical merge columns"
        )
    else:
        findings["checks_failed"].append(
            f"CHECK 6 FAILED: {len(merge_failures)} rows have NULL in critical columns"
        )

    # =====================================================================
    # CHECK 7: No orphan dates
    # =====================================================================
    dates_in_data = set(merged_df["date"].unique())
    expected_start = date(2022, 1, 1)
    expected_end = date(2023, 12, 31)
    expected_count = (expected_end - expected_start).days + 1

    current = expected_start
    missing_dates = []
    while current <= expected_end:
        if current not in dates_in_data:
            missing_dates.append(current)
        current += timedelta(days=1)

    if len(missing_dates) == 0:
        findings["checks_passed"].append(
            f"CHECK 7: No orphan dates ({expected_count} consecutive dates covered)"
        )
    else:
        findings["checks_failed"].append(
            f"CHECK 7 FAILED: {len(missing_dates)} missing dates"
        )

    # =====================================================================
    # CHECK 8: No NULL GRAP stage before E001
    # =====================================================================
    # E001 is 2022-10-05, so before that date, stage should be 0 (not NULL)
    e001_date = date(2022, 10, 5)
    before_e001 = merged_df[merged_df["date"] < e001_date]
    null_before_e001 = before_e001[before_e001["grap_stage"].isna()]

    if len(null_before_e001) == 0:
        findings["checks_passed"].append(
            "CHECK 8: No NULL GRAP stages before E001 (pre-GRAP dates have stage 0)"
        )
    else:
        findings["checks_failed"].append(
            f"CHECK 8 FAILED: {len(null_before_e001)} pre-GRAP dates have NULL grap_stage"
        )

    # =====================================================================
    # Data overview
    # =====================================================================
    findings["data_overview"] = {
        "total_rows": len(merged_df),
        "unique_stations": merged_df["station_id"].nunique(),
        "date_range": f"{merged_df['date'].min()} to {merged_df['date'].max()}",
        "expected_rows": expected_rows,
        "rows_per_station": len(merged_df) // 8,
        "in_season_rows": len(merged_df[merged_df["season"].notna()]),
        "off_season_rows": len(merged_df[merged_df["season"].isna()]),
        "unique_grap_stages": sorted(merged_df["grap_stage"].dropna().unique()),
        "event_days": len(merged_df[merged_df["is_event_day"] == 1]),
    }

    return findings


def write_summary(findings: dict) -> None:
    """Print validation summary."""
    n_passed = len(findings["checks_passed"])
    n_failed = len(findings["checks_failed"])

    print(f"\n{'='*70}")
    print(f"Merged Dataset Integrity Validation")
    print(f"{'='*70}")
    print(f"\nSummary: {n_passed} passed, {n_failed} failed\n")

    overview = findings["data_overview"]
    if overview:
        print("Data Overview:")
        print(f"  Total rows: {overview.get('total_rows', 'N/A')}")
        print(f"  Expected: {overview.get('expected_rows', 'N/A')}")
        print(f"  Unique stations: {overview.get('unique_stations', 'N/A')}")
        print(f"  Date range: {overview.get('date_range', 'N/A')}")
        print(f"  Unique GRAP stages: {overview.get('unique_grap_stages', 'N/A')}")
        print()

    if findings["checks_passed"]:
        print("Passed:")
        for msg in findings["checks_passed"]:
            print(f"  [OK] {msg}")

    if findings["checks_failed"]:
        print("\nFailed:")
        for msg in findings["checks_failed"]:
            print(f"  [FAIL] {msg}")
    else:
        print("\nAll checks passed!")


def main() -> int:
    findings = validate_merged_dataset()
    write_summary(findings)

    if findings["checks_failed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
