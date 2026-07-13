"""
Tests for daily_grap_state.csv (Phase 2B: daily GRAP state table).

Grain: one row per calendar date (2022-01-01 to 2023-12-31).
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
def daily_grap_df():
    """Load the daily GRAP state table."""
    return pd.read_csv(C.DAILY_GRAP_STATE_CSV)


def test_daily_grap_state_exists():
    """Check that the daily GRAP state file exists."""
    assert C.DAILY_GRAP_STATE_CSV.exists(), f"Missing: {C.DAILY_GRAP_STATE_CSV}"


def test_daily_grap_exactly_730_rows(daily_grap_df):
    """Exactly 730 rows (2022-01-01 to 2023-12-31, inclusive)."""
    expected_rows = 730  # 365 + 365
    assert len(daily_grap_df) == expected_rows, f"Expected {expected_rows} rows, got {len(daily_grap_df)}"


def test_daily_grap_date_range(daily_grap_df):
    """Date range is 2022-01-01 to 2023-12-31."""
    daily_grap_df["date"] = pd.to_datetime(daily_grap_df["date"]).dt.date
    assert daily_grap_df["date"].min() == date(2022, 1, 1)
    assert daily_grap_df["date"].max() == date(2023, 12, 31)


def test_daily_grap_no_duplicate_dates(daily_grap_df):
    """No duplicate dates."""
    duplicates = daily_grap_df[daily_grap_df.duplicated(subset=["date"], keep=False)]
    assert len(duplicates) == 0, f"Found {len(duplicates)} duplicate dates"


def test_daily_grap_dates_continuous(daily_grap_df):
    """All 730 consecutive dates present (no gaps)."""
    daily_grap_df["date"] = pd.to_datetime(daily_grap_df["date"]).dt.date
    dates_set = set(daily_grap_df["date"])
    current = date(2022, 1, 1)
    end = date(2023, 12, 31)
    while current <= end:
        assert current in dates_set, f"Missing date: {current}"
        current += timedelta(days=1)


def test_daily_grap_required_columns(daily_grap_df):
    """All required columns present."""
    required_cols = [
        "date",
        "grap_stage",
        "season",
        "active_event_id",
        "is_event_day",
        "days_since_last_change",
        "days_until_next_change",
    ]
    for col in required_cols:
        assert col in daily_grap_df.columns, f"Missing column: {col}"


def test_daily_grap_stage_valid_range(daily_grap_df):
    """GRAP stages are in valid range [0, 4]."""
    invalid = daily_grap_df[
        (daily_grap_df["grap_stage"] < 0) | (daily_grap_df["grap_stage"] > 4)
    ]
    assert len(invalid) == 0, f"Found {len(invalid)} rows with invalid GRAP stage"


def test_daily_grap_event_day_flag_binary(daily_grap_df):
    """is_event_day is 0 or 1."""
    assert set(daily_grap_df["is_event_day"].dropna().unique()).issubset({0, 1})


def test_daily_grap_nine_event_days(daily_grap_df):
    """Exactly 9 event days (E001–E009)."""
    event_days = len(daily_grap_df[daily_grap_df["is_event_day"] == 1])
    assert event_days == 9, f"Expected 9 event days, got {event_days}"


def test_daily_grap_season_format(daily_grap_df):
    """Season format is YYYY-YY or NULL."""
    seasons = daily_grap_df["season"].dropna().unique()
    for season in seasons:
        # Format: YYYY-YY (e.g., 2022-23, 2023-24)
        assert isinstance(season, str) and len(season) == 7 and season[4] == "-", \
            f"Invalid season format: {season}"


def test_daily_grap_before_e001_is_stage_zero(daily_grap_df):
    """All dates before 2022-10-05 (E001) have grap_stage = 0."""
    daily_grap_df["date"] = pd.to_datetime(daily_grap_df["date"]).dt.date
    before_e001 = daily_grap_df[daily_grap_df["date"] < date(2022, 10, 5)]
    assert (before_e001["grap_stage"] == 0).all(), "Pre-GRAP dates should have stage 0"


def test_daily_grap_event_dates_correct_stage():
    """Event dates transition to expected stages (spot check)."""
    daily_grap_df = pd.read_csv(C.DAILY_GRAP_STATE_CSV)
    daily_grap_df["date"] = pd.to_datetime(daily_grap_df["date"]).dt.date

    # Load verified events
    events_df = pd.read_csv(C.GRAP_EVENTS_CSV, dtype=str, keep_default_na=False)
    verified = events_df[events_df["verified"].astype(str).str.strip() == "Yes"]

    for _, evt in verified.iterrows():
        evt_date = pd.to_datetime(evt["effective_date"]).date()
        expected_stage = int(float(evt["stage_to"]))
        evt_row = daily_grap_df[daily_grap_df["date"] == evt_date]
        assert len(evt_row) > 0, f"Event date not found: {evt_date}"
        actual_stage = evt_row.iloc[0]["grap_stage"]
        assert actual_stage == expected_stage, \
            f"Event {evt['event_id']} ({evt_date}): expected stage {expected_stage}, got {actual_stage}"


def test_daily_grap_no_null_stage(daily_grap_df):
    """No NULL GRAP stages (all dates should have a stage, even if 0)."""
    null_stages = daily_grap_df[daily_grap_df["grap_stage"].isna()]
    assert len(null_stages) == 0, f"Found {len(null_stages)} rows with NULL grap_stage"


def test_daily_grap_in_season_rows_correct_count(daily_grap_df):
    """In-season rows match expected count (302 per season formula)."""
    # Oct 1 - Feb 28 (includes leap year Feb 29 if present)
    # 2022-23: Oct 1 (31 days) + Nov (30) + Dec (31) + Jan (31) + Feb (28) = 151 days
    #         plus 151 days in 2023 (same months) = 302 total
    in_season = daily_grap_df[daily_grap_df["season"].notna()]
    assert len(in_season) == 302, f"Expected 302 in-season rows, got {len(in_season)}"
