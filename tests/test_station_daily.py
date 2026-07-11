"""
Phase 6 — automated tests for the processed dataset.

Run:  python -m pytest -q
"""
from __future__ import annotations

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import config as C  # noqa: E402

REQUIRED_CORE = list(C.CORE_STD_COLUMNS)
SELECTED_STATIONS = set(C.STATIONS.keys())


@pytest.fixture(scope="module")
def daily() -> pd.DataFrame:
    if not C.STATION_DAILY_CSV.exists():
        pytest.skip("station_daily.csv not built yet; run src/03_build_station_daily.py")
    df = pd.read_csv(C.STATION_DAILY_CSV)
    df["date"] = pd.to_datetime(df["date"])
    return df


@pytest.fixture(scope="module")
def stations() -> pd.DataFrame:
    if not C.STATIONS_CSV.exists():
        pytest.skip("stations.csv not built yet; run src/03_build_station_daily.py")
    return pd.read_csv(C.STATIONS_CSV)


def test_exactly_eight_selected_stations(daily):
    assert set(daily["station_id"].unique()) == SELECTED_STATIONS
    assert daily["station_id"].nunique() == 8


def test_exactly_two_years(daily):
    assert sorted(daily["year"].unique()) == [2022, 2023]


def test_no_duplicate_station_day(daily):
    assert daily.duplicated(subset=["station_id", "date"]).sum() == 0


def test_dates_within_2022_2023(daily):
    assert daily["date"].dt.year.isin([2022, 2023]).all()
    assert daily["date"].min() == pd.Timestamp("2022-01-01")
    assert daily["date"].max() == pd.Timestamp("2023-12-31")


def test_required_core_columns_exist(daily):
    for col in REQUIRED_CORE:
        assert col in daily.columns, f"missing core column {col}"


def test_station_metadata_keys_match(daily, stations):
    meta_ids = set(stations["station_id"])
    data_ids = set(daily["station_id"])
    assert meta_ids == data_ids == SELECTED_STATIONS


def test_row_count_not_exceeding_max(daily):
    assert len(daily) <= C.MAX_PROCESSED_ROWS  # 5840


def test_every_row_has_source_provenance(daily):
    assert daily["source_file"].notna().all()
    assert (daily["source_file"].str.len() > 0).all()


def test_grain_completeness(daily):
    # 8 stations x 730 calendar days = 5840 expected station-days
    assert len(daily) == 8 * 730
