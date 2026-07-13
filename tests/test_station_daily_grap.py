"""
Tests for station_daily_grap.csv (Phase 2B: merged analytical dataset).

Grain: one row per station × date (8 stations × 730 days = 5,840 rows).
"""
import sys
from pathlib import Path
from datetime import date, timedelta

import pandas as pd
import pytest

# Add src to path for config imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import config as C


@pytest.fixture
def merged_df():
    """Load the merged analytical dataset."""
    df = pd.read_csv(C.STATION_DAILY_GRAP_CSV)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def test_merged_dataset_exists():
    """Check that the merged dataset file exists."""
    assert C.STATION_DAILY_GRAP_CSV.exists(), f"Missing: {C.STATION_DAILY_GRAP_CSV}"


def test_merged_exactly_5840_rows(merged_df):
    """Exactly 5,840 rows (8 stations × 730 days)."""
    expected_rows = 8 * 730
    assert len(merged_df) == expected_rows, f"Expected {expected_rows} rows, got {len(merged_df)}"


def test_merged_exactly_eight_stations(merged_df):
    """Exactly 8 unique stations."""
    stations = merged_df["station_id"].nunique()
    assert stations == 8, f"Expected 8 unique stations, got {stations}"


def test_merged_station_ids_correct(merged_df):
    """Station IDs match the locked registry."""
    expected_ids = {
        "narela",
        "bawana",
        "anand_vihar",
        "punjabi_bagh",
        "r_k_puram",
        "okhla_phase_2",
        "najafgarh",
        "jawaharlal_nehru_stadium",
    }
    actual_ids = set(merged_df["station_id"].unique())
    assert actual_ids == expected_ids, f"Station IDs mismatch: {actual_ids - expected_ids}"


def test_merged_no_duplicate_station_dates(merged_df):
    """No duplicate (station_id, date) pairs (grain violation)."""
    duplicates = merged_df[merged_df.duplicated(subset=["station_id", "date"], keep=False)]
    assert len(duplicates) == 0, f"Found {len(duplicates)} duplicate (station, date) pairs"


def test_merged_date_range(merged_df):
    """Date range is 2022-01-01 to 2023-12-31."""
    assert merged_df["date"].min() == date(2022, 1, 1)
    assert merged_df["date"].max() == date(2023, 12, 31)


def test_merged_required_columns(merged_df):
    """All required columns present."""
    required_cols = [
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
    for col in required_cols:
        assert col in merged_df.columns, f"Missing column: {col}"


def test_merged_every_station_has_730_days(merged_df):
    """Every station has exactly 730 days of data."""
    for station_id in merged_df["station_id"].unique():
        station_days = len(merged_df[merged_df["station_id"] == station_id])
        assert station_days == 730, \
            f"Station {station_id}: expected 730 days, got {station_days}"


def test_merged_every_date_has_eight_stations(merged_df):
    """Every date has exactly 8 stations."""
    for date_val in merged_df["date"].unique():
        stations_on_date = len(merged_df[merged_df["date"] == date_val])
        assert stations_on_date == 8, \
            f"Date {date_val}: expected 8 stations, got {stations_on_date}"


def test_merged_no_null_grap_stage(merged_df):
    """No NULL GRAP stages (all station-days have a stage)."""
    null_stages = merged_df[merged_df["grap_stage"].isna()]
    assert len(null_stages) == 0, f"Found {len(null_stages)} rows with NULL grap_stage"


def test_merged_no_null_station_key_fields(merged_df):
    """No NULL in critical merge key fields (station_id, date, grap_stage)."""
    critical = ["station_id", "date", "grap_stage"]
    null_rows = merged_df[merged_df[critical].isna().any(axis=1)]
    assert len(null_rows) == 0, f"Found {len(null_rows)} rows with NULL in critical fields"


def test_merged_stage_valid_range(merged_df):
    """GRAP stages are in valid range [0, 4]."""
    invalid = merged_df[
        (merged_df["grap_stage"] < 0) | (merged_df["grap_stage"] > 4)
    ]
    assert len(invalid) == 0, f"Found {len(invalid)} rows with invalid GRAP stage"


def test_merged_event_day_flag_binary(merged_df):
    """is_event_day is 0 or 1."""
    assert set(merged_df["is_event_day"].dropna().unique()).issubset({0, 1})


def test_merged_season_or_null(merged_df):
    """Season is either YYYY-YY format or NULL."""
    seasons = merged_df["season"].dropna().unique()
    for season in seasons:
        assert isinstance(season, str) and len(season) == 7 and season[4] == "-", \
            f"Invalid season format: {season}"


def test_merged_before_e001_stage_zero(merged_df):
    """All dates before 2022-10-05 (E001) have grap_stage = 0."""
    before_e001 = merged_df[merged_df["date"] < date(2022, 10, 5)]
    assert (before_e001["grap_stage"] == 0).all(), "Pre-GRAP dates should have stage 0"


def test_merged_off_season_rows_count(merged_df):
    """Correct count of off-season rows (8 stations × 428 off-season days)."""
    # 730 total days - 302 in-season days = 428 off-season days
    off_season = merged_df[merged_df["season"].isna()]
    expected_off_season_rows = 8 * 428
    assert len(off_season) == expected_off_season_rows, \
        f"Expected {expected_off_season_rows} off-season rows, got {len(off_season)}"


def test_merged_in_season_rows_count(merged_df):
    """Correct count of in-season rows (8 stations × 302 in-season days)."""
    in_season = merged_df[merged_df["season"].notna()]
    expected_in_season_rows = 8 * 302
    assert len(in_season) == expected_in_season_rows, \
        f"Expected {expected_in_season_rows} in-season rows, got {len(in_season)}"


def test_merged_year_assignment(merged_df):
    """Year field matches date (2022 for 2022 dates, 2023 for 2023 dates)."""
    # Convert dates to datetime to extract year
    test_df = merged_df.copy()
    test_df["date_as_date"] = pd.to_datetime(test_df["date"])
    test_df["extracted_year"] = test_df["date_as_date"].dt.year

    # Check that year column matches the extracted year from date
    mismatches = test_df[test_df["year"] != test_df["extracted_year"]]
    assert len(mismatches) == 0, f"Found {len(mismatches)} rows where year doesn't match date"


def test_merged_total_event_days(merged_df):
    """Exactly 9 event days across all stations (8 × 1 event date each)."""
    # There are 9 unique event dates; each appears once per station = 72 total event rows
    event_rows = len(merged_df[merged_df["is_event_day"] == 1])
    assert event_rows == 72, f"Expected 72 event rows (9 dates × 8 stations), got {event_rows}"
