"""
Phase 3 — Data-quality audit.

For every station-year raw file, computes structural checks and core-variable
statistics, and FLAGS (never deletes) physically implausible values.

Outputs:
  reports/data_quality/core_variable_missingness.csv
  reports/data_quality/data_quality_flags.csv
  reports/data_quality/data_quality_summary.md

No cleaning, imputation, interpolation, winsorising, or row removal happens here.

Run:  python src/02_audit_data_quality.py
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C


def _load(path: str):
    df = pd.read_csv(path)
    ts = pd.to_datetime(df[C.TIMESTAMP_COL], errors="coerce")
    dates = ts.dt.normalize()
    return df, ts, dates


def audit_structural(df, ts, dates, year) -> dict:
    cal = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    present = set(dates.dropna())
    missing_cols = [c for c in C.CORE_RAW_COLUMNS if c not in df.columns]
    unexpected_cols = df.shape[1] - C.EXPECTED_RAW_COLUMNS
    return {
        "row_count": len(df),
        "unique_date_count": int(dates.nunique()),
        "duplicate_date_count": int(dates.duplicated().sum()),
        "missing_calendar_dates": len(set(cal) - present),
        "dates_outside_year": int((dates.dt.year != year).sum()),
        "unparseable_timestamps": int(ts.isna().sum()),
        "unexpected_column_count": int(unexpected_cols),
        "missing_required_columns": ",".join(missing_cols) if missing_cols else "",
        "structural_ok": bool(
            len(df) == C.EXPECTED_ROWS_PER_FILE
            and int(dates.duplicated().sum()) == 0
            and len(set(cal) - present) == 0
            and int((dates.dt.year != year).sum()) == 0
            and not missing_cols
        ),
    }


def audit_core_variables(df, meta):
    """Returns (missingness_rows, flag_rows) for the 6 core variables."""
    miss_rows, flag_rows = [], []
    n = len(df)
    for raw_col, std_col in C.CORE_COLUMN_MAP.items():
        raw_series = df[raw_col]
        num = pd.to_numeric(raw_series, errors="coerce")
        # coercion failures = values that were non-null text but became NaN
        coercion_failures = int((num.isna() & raw_series.notna()).sum())
        null_count = int(num.isna().sum())
        miss_rows.append({
            "source_file": meta["source_file"],
            "station_id": meta["station_id"],
            "year": meta["year"],
            "variable": std_col,
            "non_null_count": int(num.notna().sum()),
            "null_count": null_count,
            "null_pct": round(100.0 * null_count / n, 2),
            "numeric_coercion_failures": coercion_failures,
            "min": None if num.notna().sum() == 0 else float(np.nanmin(num)),
            "max": None if num.notna().sum() == 0 else float(np.nanmax(num)),
            "median": None if num.notna().sum() == 0 else float(np.nanmedian(num)),
        })

        # Plausibility flags (flag only, never modify)
        bounds = C.PLAUSIBILITY[std_col]
        mask = pd.Series(False, index=num.index)
        if bounds["min"] is not None:
            mask |= num < bounds["min"]
        if bounds["max"] is not None:
            mask |= num > bounds["max"]
        n_flagged = int(mask.sum())
        if n_flagged:
            flagged_vals = num[mask]
            flag_rows.append({
                "source_file": meta["source_file"],
                "station_id": meta["station_id"],
                "year": meta["year"],
                "variable": std_col,
                "flag_type": bounds["label"],
                "n_flagged": n_flagged,
                "example_min": float(flagged_vals.min()),
                "example_max": float(flagged_vals.max()),
            })
    return miss_rows, flag_rows


def main() -> int:
    C.REPORTS_DQ_DIR.mkdir(parents=True, exist_ok=True)
    paths = sorted(str(p) for p in C.RAW_CPCB_DIR.glob("*.csv"))
    if not paths:
        print(f"ERROR: no CSV files under {C.RAW_CPCB_DIR}", file=sys.stderr)
        return 1

    struct_rows, miss_rows, flag_rows = [], [], []
    for path in paths:
        meta = C.parse_raw_filename(os.path.basename(path))
        df, ts, dates = _load(path)
        s = audit_structural(df, ts, dates, meta["year"])
        s.update({"source_file": meta["source_file"],
                  "station_id": meta["station_id"], "year": meta["year"]})
        struct_rows.append(s)
        m, f = audit_core_variables(df, meta)
        miss_rows.extend(m)
        flag_rows.extend(f)

    struct = pd.DataFrame(struct_rows).sort_values(["station_id", "year"])
    miss = pd.DataFrame(miss_rows).sort_values(["station_id", "year", "variable"])
    flags = (pd.DataFrame(flag_rows) if flag_rows
             else pd.DataFrame(columns=["source_file", "station_id", "year",
                                        "variable", "flag_type", "n_flagged",
                                        "example_min", "example_max"]))

    miss_out = C.REPORTS_DQ_DIR / "core_variable_missingness.csv"
    flags_out = C.REPORTS_DQ_DIR / "data_quality_flags.csv"
    miss.to_csv(miss_out, index=False, encoding="utf-8")
    flags.to_csv(flags_out, index=False, encoding="utf-8")

    _write_summary(struct, miss, flags)

    print(f"Wrote {miss_out}")
    print(f"Wrote {flags_out} ({len(flags)} flag rows)")
    print(f"Wrote {C.REPORTS_DQ_DIR / 'data_quality_summary.md'}")
    print(f"Structural OK: {int(struct['structural_ok'].sum())}/{len(struct)}")
    print(f"Impossible-value flags: {len(flags)}")
    return 0


def _write_summary(struct, miss, flags) -> None:
    n_files = len(struct)
    all_present = n_files == 16
    schema_consistent = (struct["unexpected_column_count"].eq(0).all()
                         and struct["missing_required_columns"].eq("").all())
    coverage_complete = (struct["missing_calendar_dates"].eq(0).all()
                         and struct["dates_outside_year"].eq(0).all())
    dupes = int(struct["duplicate_date_count"].sum())

    pm25 = miss[miss["variable"] == "pm25_ugm3"].nlargest(5, "null_pct")
    weather_vars = ["air_temp_c", "rh_pct", "wind_speed_ms", "wind_dir_deg"]
    weather = (miss[miss["variable"].isin(weather_vars)]
               .sort_values("null_pct", ascending=False).head(5))

    gate1_pass = bool(all_present and schema_consistent and coverage_complete
                      and dupes == 0)

    def yn(b):
        return "Yes" if b else "No"

    lines = []
    lines.append("# Phase 1 Data-Quality Summary\n")
    lines.append("_Generated by `src/02_audit_data_quality.py`. Flags expose "
                 "problems; nothing is deleted, imputed, or clipped._\n")
    lines.append("## Gate 1 questions\n")
    lines.append(f"- **All 16 expected files present?** {yn(all_present)} "
                 f"({n_files}/16)")
    lines.append(f"- **Schema consistent (25 cols, all required present)?** "
                 f"{yn(schema_consistent)}")
    lines.append(f"- **Date coverage complete (365/yr, in-year)?** "
                 f"{yn(coverage_complete)}")
    lines.append(f"- **Duplicate dates present?** {yn(dupes > 0)} "
                 f"(total {dupes})")
    lines.append(f"- **Impossible values found?** {yn(len(flags) > 0)} "
                 f"({len(flags)} flag rows)")
    lines.append("")
    lines.append(f"### Gate 1 verdict: **{'PASS' if gate1_pass else 'FAIL'}**\n")

    lines.append("## Highest PM2.5 missingness (top 5 station-years)\n")
    lines.append("| station_id | year | null_pct |")
    lines.append("|---|---|---|")
    for _, r in pm25.iterrows():
        lines.append(f"| {r['station_id']} | {r['year']} | {r['null_pct']} |")
    lines.append("")

    lines.append("## Highest weather-variable missingness (top 5)\n")
    lines.append("| station_id | year | variable | null_pct |")
    lines.append("|---|---|---|---|")
    for _, r in weather.iterrows():
        lines.append(f"| {r['station_id']} | {r['year']} | {r['variable']} "
                     f"| {r['null_pct']} |")
    lines.append("")

    lines.append("## Impossible / suspicious values\n")
    if len(flags) == 0:
        lines.append("None detected across the 6 core variables "
                     "(no negative PM/WS, RH within 0–100, temps within "
                     "[-10, 55] °C, WD within [0, 360]).\n")
    else:
        lines.append("| station_id | year | variable | flag | n |")
        lines.append("|---|---|---|---|---|")
        for _, r in flags.iterrows():
            lines.append(f"| {r['station_id']} | {r['year']} | {r['variable']} "
                         f"| {r['flag_type']} | {r['n_flagged']} |")
        lines.append("")

    lines.append("## Files failing structural checks\n")
    bad = struct[~struct["structural_ok"]]
    if bad.empty:
        lines.append("None — all files pass structural checks.\n")
    else:
        for _, r in bad.iterrows():
            lines.append(f"- {r['source_file']}")
        lines.append("")

    (C.REPORTS_DQ_DIR / "data_quality_summary.md").write_text(
        "\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
