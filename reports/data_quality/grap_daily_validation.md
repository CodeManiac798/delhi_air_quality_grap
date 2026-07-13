# GRAP Daily State Table Validation Report

## Data Overview

- **Total rows**: 730
- **Date range**: 2022-01-01 to 2023-12-31
- **In-season rows**: 302
- **Off-season rows**: 428
- **Unique GRAP stages**: [np.int64(0), np.int64(1), np.int64(2), np.int64(3), np.int64(4)]
- **Event days**: 9
- **Verified events**: 9

## Validation Checks

### Passed

- CHECK 1: No duplicate dates
- CHECK 2: No missing dates (730 consecutive dates)
- CHECK 3: Dates in chronological order
- CHECK 4: All 9 event dates have correct stage
- CHECK 5: All 9 pre-event days retain previous stage
- CHECK 6: No unexplained stage jumps

### Failed

- None

## Assumptions & Limitations

1. **Season scoping**: GRAP stages are scoped per season (Oct 1 – Feb 28/29).
2. **Off-season data**: Off-season dates (Mar–Sep) have `season=NULL` and no stage concept.
3. **Event-day logic**: An event date takes the `stage_to` value immediately.
4. **No extrapolation**: After E009 (2022-12-30), stage remains 3 to season end (2023-02-28).
   - Season 2023-24 (Oct 2023 – Feb 2024) is marked but has no events and falls outside
   - the loaded data window (ends 2023-12-31). This is a known data-completeness gap, not an error.

## Summary

**Passed**: 6 / 6
