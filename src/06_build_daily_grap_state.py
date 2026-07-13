"""
Phase 3A (PHASE B) — Build daily GRAP state table.

Input:  data/raw/grap/grap_events_manual.csv (verified events only)
Output: data/processed/daily_grap_state.csv

One row per calendar date (2022-01-01 to 2023-12-31).
Fields: date, grap_stage, season, active_event_id, is_event_day, days_since_last_change, days_until_next_change

Rules:
  * Before any event: stage = 0.
  * After an event: stage = event.stage_to, maintained until next event.
  * Each season (Oct 1 – Feb 28/29) is scoped independently.
  * If events run to season end and next season has no event: mark clearly (no extrapolation).
  * days_since_last_change, days_until_next_change: count from effective_date.
"""
from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C


def get_grap_season(d: date) -> str | None:
    """Return GRAP season for a date, or None if off-season."""
    year = d.year
    month = d.month
    # GRAP season: Oct 1 (year Y) to Feb 28/29 (year Y+1)
    # Format: YYYY-YY (e.g., 2022-23, 2023-24)
    if month >= 10:
        # Oct, Nov, Dec of year Y -> season Y-(Y+1)
        next_year = year + 1
        return f"{year}-{next_year % 100}"
    elif month <= 2:
        # Jan, Feb of year Y -> season (Y-1)-Y
        prev_year = year - 1
        return f"{prev_year}-{year % 100}"
    return None


def main() -> int:
    # Read verified GRAP events
    grap_df = pd.read_csv(C.GRAP_EVENTS_CSV, dtype=str, keep_default_na=False)
    verified = grap_df[grap_df["verified"].astype(str).str.strip() == "Yes"].copy()

    # Parse dates and stages
    events = []
    for _, row in verified.iterrows():
        try:
            eff_date = pd.to_datetime(row["effective_date"]).date()
            stage_to = int(float(row["stage_to"]))
            season = row["season"].strip()
            event_id = row["event_id"].strip()
            events.append({
                "event_id": event_id,
                "effective_date": eff_date,
                "stage_to": stage_to,
                "season": season,
            })
        except (ValueError, KeyError) as e:
            print(f"ERROR parsing event {row.get('event_id', 'UNKNOWN')}: {e}", file=sys.stderr)
            return 1

    # Sort by effective_date
    events = sorted(events, key=lambda x: x["effective_date"])

    # Generate all dates 2022-01-01 to 2023-12-31
    start_date = date(2022, 1, 1)
    end_date = date(2023, 12, 31)

    rows = []
    current_date = start_date
    while current_date <= end_date:
        season = get_grap_season(current_date)

        # Find the most recent event (within the same season, if in-season)
        active_event = None
        active_stage = 0

        if season is not None:
            # In-season: find most recent event in this season with effective_date <= current_date
            for evt in events:
                if evt["season"] == season and evt["effective_date"] <= current_date:
                    active_event = evt
                    active_stage = evt["stage_to"]

        # Check if current_date is an event day
        is_event_day = any(e["effective_date"] == current_date for e in events)
        active_event_id = None
        if is_event_day:
            active_event_id = next(e["event_id"] for e in events if e["effective_date"] == current_date)

        # Days since last change
        if active_event and active_event["effective_date"] < current_date:
            days_since_last_change = (current_date - active_event["effective_date"]).days
        elif is_event_day:
            days_since_last_change = 0
        else:
            days_since_last_change = None  # No prior event in this season yet

        # Days until next change
        next_event = None
        if season is not None:
            for evt in events:
                if evt["season"] == season and evt["effective_date"] > current_date:
                    next_event = evt
                    break

        if next_event:
            days_until_next_change = (next_event["effective_date"] - current_date).days
        else:
            days_until_next_change = None  # No known future event

        rows.append({
            "date": current_date.isoformat(),
            "grap_stage": active_stage,
            "season": season,
            "active_event_id": active_event_id if active_event_id else "",
            "is_event_day": 1 if is_event_day else 0,
            "days_since_last_change": days_since_last_change if days_since_last_change is not None else "",
            "days_until_next_change": days_until_next_change if days_until_next_change is not None else "",
        })

        current_date += timedelta(days=1)

    df = pd.DataFrame(rows)

    # Write output
    output_path = Path(C.DAILY_GRAP_STATE_CSV)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"Built {output_path}")
    print(f"  Rows: {len(df)}")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  Unique GRAP stages: {sorted(df['grap_stage'].unique())}")
    print(f"  Event days: {df['is_event_day'].sum()}")
    print(f"  In-season rows: {df[df['season'].notna()].shape[0]}")
    print(f"  Off-season rows: {df[df['season'].isna()].shape[0]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
