"""
Phase 2 — Raw-data inventory.

Scans data/raw/cpcb/*.csv and writes a machine-readable inventory to
reports/data_quality/raw_file_inventory.csv.

Read-only with respect to raw files. Does not clean, impute, or modify anything.

Run:  python src/01_inventory_raw_data.py
"""
from __future__ import annotations

import hashlib
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C


def schema_signature(columns: list[str]) -> str:
    """Stable short hash of the ordered column list."""
    joined = "|".join(columns)
    return hashlib.md5(joined.encode("utf-8")).hexdigest()[:12]


def inventory_one(path: str) -> dict:
    filename = os.path.basename(path)
    meta = C.parse_raw_filename(filename)  # raises if unknown -> fail loud
    year = meta["year"]

    df = pd.read_csv(path)
    ts = pd.to_datetime(df[C.TIMESTAMP_COL], errors="coerce")
    dates = ts.dt.normalize()

    cal = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    present = set(dates.dropna())
    missing_dates = len(set(cal) - present)
    outside = int((dates.dt.year != year).sum())
    dup_dates = int(dates.duplicated().sum())

    return {
        "source_file": filename,
        "station_id": meta["station_id"],
        "station_name": meta["station_name"],
        "year": year,
        "row_count": len(df),
        "column_count": df.shape[1],
        "first_date": None if dates.dropna().empty else str(dates.min().date()),
        "last_date": None if dates.dropna().empty else str(dates.max().date()),
        "unparseable_timestamps": int(ts.isna().sum()),
        "duplicate_date_count": dup_dates,
        "missing_calendar_dates": missing_dates,
        "dates_outside_year": outside,
        "schema_signature": schema_signature(list(df.columns)),
        "file_size_bytes": os.path.getsize(path),
        "structural_pass": bool(
            len(df) == C.EXPECTED_ROWS_PER_FILE
            and df.shape[1] == C.EXPECTED_RAW_COLUMNS
            and dup_dates == 0
            and missing_dates == 0
            and outside == 0
        ),
    }


def main() -> int:
    C.REPORTS_DQ_DIR.mkdir(parents=True, exist_ok=True)
    paths = sorted(str(p) for p in C.RAW_CPCB_DIR.glob("*.csv"))
    if not paths:
        print(f"ERROR: no CSV files found under {C.RAW_CPCB_DIR}", file=sys.stderr)
        return 1

    rows = [inventory_one(p) for p in paths]
    inv = pd.DataFrame(rows).sort_values(["station_id", "year"]).reset_index(drop=True)

    out = C.REPORTS_DQ_DIR / "raw_file_inventory.csv"
    inv.to_csv(out, index=False, encoding="utf-8")

    n_pass = int(inv["structural_pass"].sum())
    print(f"Inventoried {len(inv)} files -> {out}")
    print(f"Structural pass: {n_pass}/{len(inv)}")
    print(f"Distinct schema signatures: {inv['schema_signature'].nunique()} "
          f"(expected 1): {sorted(inv['schema_signature'].unique())}")
    print(f"Station-years present: {len(inv)} (expected 16)")
    missing_combos = _missing_station_years(inv)
    if missing_combos:
        print(f"WARNING missing station-years: {missing_combos}")
    else:
        print("All 8 stations x 2 years present.")
    return 0


def _missing_station_years(inv: pd.DataFrame) -> list[tuple[str, int]]:
    have = set(zip(inv["station_id"], inv["year"]))
    want = {(s, y) for s in C.STATIONS for y in C.EXPECTED_YEARS}
    return sorted(want - have)


if __name__ == "__main__":
    raise SystemExit(main())
