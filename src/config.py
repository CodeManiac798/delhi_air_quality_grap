"""
Shared configuration for the Delhi AQI / GRAP Phase 1 pipeline.

Single source of truth for:
  - repository paths
  - the locked 8-station registry (slugs, display names, geographic roles)
  - the raw-filename -> (station_id, year) mapping
  - core-variable column standardisation (raw CPCB header -> snake_case)

Design choice: filenames are consistent enough to parse, but rather than rely
on fragile heuristics we use an EXPLICIT token->slug table and validate every
inferred value against the locked registry. Reliability over cleverness.
"""
from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_CPCB_DIR = REPO_ROOT / "data" / "raw" / "cpcb"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
REPORTS_DQ_DIR = REPO_ROOT / "reports" / "data_quality"

STATION_DAILY_CSV = PROCESSED_DIR / "station_daily.csv"
STATIONS_CSV = PROCESSED_DIR / "stations.csv"
DAILY_GRAP_STATE_CSV = PROCESSED_DIR / "daily_grap_state.csv"
STATION_DAILY_GRAP_CSV = PROCESSED_DIR / "station_daily_grap.csv"

# SQL layer (Phase 2 prep). The SQLite warehouse is a *derived* artifact built
# from the processed CSVs + the verified GRAP events; it is safe to delete and
# rebuild. It is NOT a source of truth.
SQL_DIR = REPO_ROOT / "sql"
SQL_SCHEMA = SQL_DIR / "00_schema.sql"
SQLITE_DB = PROCESSED_DIR / "delhi_aqi_grap.db"
GRAP_EVENTS_CSV = REPO_ROOT / "data" / "raw" / "grap" / "grap_events_manual.csv"

EXPECTED_YEARS = (2022, 2023)
EXPECTED_ROWS_PER_FILE = 365          # non-leap years; both 2022 and 2023
EXPECTED_RAW_COLUMNS = 25
MAX_PROCESSED_ROWS = 8 * 730          # 8 stations x 730 station-days = 5840

# --------------------------------------------------------------------------
# Locked station registry (selected before outcome analysis)
# station_id (slug) -> metadata
# --------------------------------------------------------------------------
STATIONS: dict[str, dict[str, str]] = {
    "narela": {
        "station_name": "Narela",
        "display_name": "Narela",
        "operating_agency": "DPCC",
        "geographic_role": "northern edge",
    },
    "bawana": {
        "station_name": "Bawana",
        "display_name": "Bawana",
        "operating_agency": "DPCC",
        "geographic_role": "outer north-west",
    },
    "anand_vihar": {
        "station_name": "Anand Vihar",
        "display_name": "Anand Vihar",
        "operating_agency": "DPCC",
        "geographic_role": "east",
    },
    "punjabi_bagh": {
        "station_name": "Punjabi Bagh",
        "display_name": "Punjabi Bagh",
        "operating_agency": "DPCC",
        "geographic_role": "west",
    },
    "r_k_puram": {
        "station_name": "R K Puram",
        "display_name": "R K Puram",
        "operating_agency": "DPCC",
        "geographic_role": "south",
    },
    "okhla_phase_2": {
        "station_name": "Okhla Phase-2",
        "display_name": "Okhla Phase-2",
        "operating_agency": "DPCC",
        "geographic_role": "south-east",
    },
    "najafgarh": {
        "station_name": "Najafgarh",
        "display_name": "Najafgarh",
        "operating_agency": "DPCC",
        "geographic_role": "south-west edge",
    },
    "jawaharlal_nehru_stadium": {
        "station_name": "Jawaharlal Nehru Stadium",
        "display_name": "Jawaharlal Nehru Stadium",
        "operating_agency": "DPCC",
        "geographic_role": "central",
    },
}

# Raw-filename station token (as it appears between "raw_data_data_" and
# ",_delhi_-_dpcc_1D") mapped to the registry slug. Explicit on purpose.
FILENAME_TOKEN_TO_SLUG: dict[str, str] = {
    "narela": "narela",
    "bawana": "bawana",
    "anand_vihar": "anand_vihar",
    "punjabi_bagh": "punjabi_bagh",
    "r_k_puram": "r_k_puram",
    "okhla_phase-2": "okhla_phase_2",   # note: hyphen in filename, underscore in slug
    "najafgarh": "najafgarh",
    "jawaharlal_nehru_stadium": "jawaharlal_nehru_stadium",
}

# --------------------------------------------------------------------------
# Core variables: raw CPCB header -> standardised snake_case name.
# Only these 6 (plus the parsed date) are retained in station_daily.csv,
# per project decision. All 25 raw columns are still AUDITED upstream.
# --------------------------------------------------------------------------
CORE_COLUMN_MAP: dict[str, str] = {
    "PM2.5 (µg/m³)": "pm25_ugm3",
    "PM10 (µg/m³)": "pm10_ugm3",
    "AT (°C)": "air_temp_c",
    "RH (%)": "rh_pct",
    "WS (m/s)": "wind_speed_ms",
    "WD (deg)": "wind_dir_deg",
}
CORE_RAW_COLUMNS = tuple(CORE_COLUMN_MAP.keys())
CORE_STD_COLUMNS = tuple(CORE_COLUMN_MAP.values())

TIMESTAMP_COL = "Timestamp"

# Physical plausibility bounds for FLAGGING ONLY (never used to delete/clip).
PLAUSIBILITY = {
    "pm25_ugm3": {"min": 0.0, "max": None, "label": "negative concentration"},
    "pm10_ugm3": {"min": 0.0, "max": None, "label": "negative concentration"},
    "air_temp_c": {"min": -10.0, "max": 55.0, "label": "temperature out of [-10, 55] C"},
    "rh_pct": {"min": 0.0, "max": 100.0, "label": "RH out of [0, 100] %"},
    "wind_speed_ms": {"min": 0.0, "max": None, "label": "negative wind speed"},
    "wind_dir_deg": {"min": 0.0, "max": 360.0, "label": "wind direction out of [0, 360] deg"},
}

_RAW_PREFIX = "raw_data_data_"
_RAW_STATION_SUFFIX = ",_delhi_-_dpcc_1D"


def parse_raw_filename(filename: str) -> dict:
    """
    Infer (station_id, station_name, year) from a raw CPCB filename and
    validate against the locked registry.

    Returns a dict with keys: station_id, station_name, year, source_file.
    Raises ValueError if the filename cannot be resolved to a known station
    (fail loud rather than guess).
    """
    name = filename
    if name.endswith(".csv"):
        name = name[:-4]

    # Year: trailing "_22" => 2022, otherwise 2023 (the un-suffixed vintage).
    if name.endswith("_22"):
        year = 2022
        name = name[:-3]
    else:
        year = 2023

    if not name.startswith(_RAW_PREFIX):
        raise ValueError(f"Unexpected raw filename (missing prefix): {filename!r}")
    core = name[len(_RAW_PREFIX):]

    if not core.endswith(_RAW_STATION_SUFFIX):
        raise ValueError(f"Unexpected raw filename (missing station suffix): {filename!r}")
    token = core[: -len(_RAW_STATION_SUFFIX)]

    if token not in FILENAME_TOKEN_TO_SLUG:
        raise ValueError(f"Unknown station token {token!r} in filename {filename!r}")
    slug = FILENAME_TOKEN_TO_SLUG[token]

    return {
        "station_id": slug,
        "station_name": STATIONS[slug]["station_name"],
        "year": year,
        "source_file": filename,
    }
