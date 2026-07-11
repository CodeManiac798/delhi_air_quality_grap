"""
Phase 2 (prep) — Validate the manually entered GRAP event source file.

Validates data/raw/grap/grap_events_manual.csv against the data contract in
docs/grap_event_data_contract.md. It VALIDATES ONLY — it never invents, edits,
repairs, reorders, or fills in event data.

Findings have three severities:
  ERROR     — contract violation; the file is not valid until a human fixes it.
  FLAG      — structurally valid but logically suspicious; needs human review.
  NOT_READY — valid but verified != Yes; excluded from analysis until verified.

An empty file (headers only) is a valid empty template: no ERRORs, zero
analysis-ready events, so Phase 2 cannot begin.

Run:  python src/04_validate_grap_events.py
Exit code 0 if no ERRORs, 1 if any ERROR (or the file/columns are missing).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import pandas as pd

# --------------------------------------------------------------------------
# Contract constants (kept self-contained; does not touch the Phase 1 config)
# --------------------------------------------------------------------------
GRAP_EVENTS_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "data", "raw", "grap", "grap_events_manual.csv",
)

EXPECTED_COLUMNS = [
    "event_id", "order_date", "effective_date", "season", "action_type",
    "stage_from", "stage_to", "event_direction", "immediate_effect",
    "official_order_title", "official_source", "notes", "verified",
]

ALLOWED_SEASON = {"2022-23", "2023-24"}
ALLOWED_ACTION_TYPE = {"invoke", "escalate", "de_escalate", "revoke", "other"}
ALLOWED_EVENT_DIRECTION = {
    "activation", "escalation", "de_escalation", "full_revocation", "other",
}
ALLOWED_STAGE = {0, 1, 2, 3, 4}           # 0 = No active GRAP, 1..4 = Stage I..IV
ALLOWED_IMMEDIATE_EFFECT = {"Yes", "No"}
ALLOWED_VERIFIED = {"Yes", "No"}
REQUIRED_NONEMPTY = ["event_id", "effective_date", "season", "action_type",
                     "official_order_title", "official_source", "verified"]

ERROR, FLAG, NOT_READY = "ERROR", "FLAG", "NOT_READY"


@dataclass
class Finding:
    severity: str
    code: str
    row: object   # 1-based data-row number, or None for file-level findings
    message: str


def _is_iso_date(value) -> bool:
    if value is None:
        return False
    s = str(value).strip()
    if not s:
        return False
    parsed = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    return not pd.isna(parsed)


def _blank(value) -> bool:
    return value is None or (isinstance(value, float) and pd.isna(value)) \
        or str(value).strip() == ""


def _stage_int(value):
    """Return int stage if value is a clean 0..4 code, else None."""
    if _blank(value):
        return None
    s = str(value).strip()
    try:
        f = float(s)
    except ValueError:
        return None
    if f != int(f):
        return None
    return int(f)


def validate_events(df: pd.DataFrame) -> list[Finding]:
    """
    Validate a GRAP-events DataFrame against the contract.
    Returns a list of Findings. Does not modify df.
    """
    findings: list[Finding] = []

    # --- structural: columns exactly as contract (names + order) ---
    if list(df.columns) != EXPECTED_COLUMNS:
        findings.append(Finding(
            ERROR, "columns_mismatch", None,
            f"Columns must be exactly {EXPECTED_COLUMNS}; got {list(df.columns)}",
        ))
        # Without the right columns we cannot do row-level checks reliably.
        return findings

    if len(df) == 0:
        # Valid empty template.
        findings.append(Finding(
            NOT_READY, "empty_file", None,
            "No events entered. Valid empty template; 0 analysis-ready events.",
        ))
        return findings

    # --- per-row checks ---
    for pos, (_, r) in enumerate(df.iterrows(), start=1):
        # required non-empty fields
        for col in REQUIRED_NONEMPTY:
            if _blank(r[col]):
                findings.append(Finding(
                    ERROR, "missing_required", pos,
                    f"Required field '{col}' is empty.",
                ))

        # dates
        if not _blank(r["order_date"]) and not _is_iso_date(r["order_date"]):
            findings.append(Finding(ERROR, "bad_order_date", pos,
                            f"order_date '{r['order_date']}' is not YYYY-MM-DD."))
        if _blank(r["effective_date"]):
            findings.append(Finding(ERROR, "missing_effective_date", pos,
                            "effective_date must not be missing."))
        elif not _is_iso_date(r["effective_date"]):
            findings.append(Finding(ERROR, "bad_effective_date", pos,
                            f"effective_date '{r['effective_date']}' is not YYYY-MM-DD."))

        # controlled vocabularies
        if not _blank(r["season"]) and str(r["season"]).strip() not in ALLOWED_SEASON:
            findings.append(Finding(ERROR, "bad_season", pos,
                            f"season '{r['season']}' not in {sorted(ALLOWED_SEASON)}."))
        if not _blank(r["action_type"]) and str(r["action_type"]).strip() not in ALLOWED_ACTION_TYPE:
            findings.append(Finding(ERROR, "bad_action_type", pos,
                            f"action_type '{r['action_type']}' not in {sorted(ALLOWED_ACTION_TYPE)}."))
        if not _blank(r["event_direction"]) and str(r["event_direction"]).strip() not in ALLOWED_EVENT_DIRECTION:
            findings.append(Finding(ERROR, "bad_event_direction", pos,
                            f"event_direction '{r['event_direction']}' not in {sorted(ALLOWED_EVENT_DIRECTION)}."))
        if not _blank(r["immediate_effect"]) and str(r["immediate_effect"]).strip() not in ALLOWED_IMMEDIATE_EFFECT:
            findings.append(Finding(ERROR, "bad_immediate_effect", pos,
                            f"immediate_effect '{r['immediate_effect']}' not in {sorted(ALLOWED_IMMEDIATE_EFFECT)}."))

        # stages — must be clean integers AND within the allowed 0..4 set
        s_from = _stage_int(r["stage_from"])
        s_to = _stage_int(r["stage_to"])
        if s_from not in ALLOWED_STAGE:
            findings.append(Finding(ERROR, "bad_stage_from", pos,
                            f"stage_from '{r['stage_from']}' not in {sorted(ALLOWED_STAGE)}."))
            s_from = None
        if s_to not in ALLOWED_STAGE:
            findings.append(Finding(ERROR, "bad_stage_to", pos,
                            f"stage_to '{r['stage_to']}' not in {sorted(ALLOWED_STAGE)}."))
            s_to = None

        # verified gate (readiness, not a hard error)
        verified = str(r["verified"]).strip() if not _blank(r["verified"]) else ""
        if verified and verified not in ALLOWED_VERIFIED:
            findings.append(Finding(ERROR, "bad_verified", pos,
                            f"verified '{r['verified']}' not in {sorted(ALLOWED_VERIFIED)}."))
        elif verified != "Yes":
            findings.append(Finding(NOT_READY, "not_verified", pos,
                            "verified != Yes; excluded from analysis until verified."))

        # official_source should look like a URL (soft flag, not an error)
        src = "" if _blank(r["official_source"]) else str(r["official_source"]).strip()
        if src and not (src.startswith("http://") or src.startswith("https://")):
            findings.append(Finding(FLAG, "source_not_url", pos,
                            "official_source does not look like a URL; must be an official CAQM URL."))

        # --- logical stage-transition flags (only if both stages parsed) ---
        if s_from is not None and s_to is not None:
            _transition_flags(findings, pos, r, s_from, s_to)

    # --- cross-row checks ---
    _duplicate_ids(findings, df)
    _chronology(findings, df)

    return findings


def _transition_flags(findings, pos, r, s_from, s_to) -> None:
    action = str(r["action_type"]).strip() if not _blank(r["action_type"]) else ""
    direction = str(r["event_direction"]).strip() if not _blank(r["event_direction"]) else ""

    # no state change
    if s_from == s_to:
        findings.append(Finding(FLAG, "no_state_change", pos,
                        f"stage_from == stage_to ({s_from}); no state change — "
                        "review whether this should be an event at all."))

    # multi-stage jumps (possible, but flag for review)
    if s_to - s_from >= 2:
        findings.append(Finding(FLAG, "multi_stage_escalation", pos,
                        f"escalation jumps {s_from} -> {s_to} (>=2 stages); verify."))
    if s_from - s_to >= 2 and s_to != 0:
        findings.append(Finding(FLAG, "multi_stage_de_escalation", pos,
                        f"de-escalation drops {s_from} -> {s_to} (>=2 stages); verify."))

    # action_type / direction / stage-delta consistency
    if direction == "escalation" and not s_to > s_from:
        findings.append(Finding(FLAG, "direction_stage_mismatch", pos,
                        f"event_direction=escalation but stage {s_from} -> {s_to}."))
    if direction == "de_escalation" and not (s_to < s_from and s_to >= 1):
        findings.append(Finding(FLAG, "direction_stage_mismatch", pos,
                        f"event_direction=de_escalation but stage {s_from} -> {s_to}."))
    if direction == "activation" and not (s_from == 0 and s_to >= 1):
        findings.append(Finding(FLAG, "direction_stage_mismatch", pos,
                        f"event_direction=activation but stage {s_from} -> {s_to} "
                        "(expected 0 -> >=1)."))
    if direction == "full_revocation" and s_to != 0:
        findings.append(Finding(FLAG, "direction_stage_mismatch", pos,
                        f"event_direction=full_revocation but stage_to={s_to} "
                        "(expected 0)."))
    if action == "invoke" and not (s_from == 0 and s_to >= 1):
        findings.append(Finding(FLAG, "action_stage_mismatch", pos,
                        f"action_type=invoke but stage {s_from} -> {s_to} "
                        "(expected 0 -> >=1)."))
    if action == "revoke" and s_to != 0:
        findings.append(Finding(FLAG, "action_stage_mismatch", pos,
                        f"action_type=revoke but stage_to={s_to} "
                        "(expected 0). Revoking a higher stage may leave a lower "
                        "stage active — that is de_escalate, not revoke."))
    if action == "escalate" and not s_to > s_from:
        findings.append(Finding(FLAG, "action_stage_mismatch", pos,
                        f"action_type=escalate but stage {s_from} -> {s_to}."))
    if action == "de_escalate" and not (s_to < s_from and s_to >= 1):
        findings.append(Finding(FLAG, "action_stage_mismatch", pos,
                        f"action_type=de_escalate but stage {s_from} -> {s_to}."))


def _duplicate_ids(findings, df) -> None:
    ids = df["event_id"].astype(str).str.strip()
    dupes = ids[ids.duplicated(keep=False) & (ids != "")]
    for val in sorted(dupes.unique()):
        rows = [i + 1 for i in range(len(ids)) if ids.iloc[i] == val]
        findings.append(Finding(ERROR, "duplicate_event_id", None,
                        f"event_id '{val}' duplicated on rows {rows}."))


def _chronology(findings, df) -> None:
    eff = pd.to_datetime(df["effective_date"], format="%Y-%m-%d", errors="coerce")
    if eff.isna().any():
        return  # date errors already reported; skip ordering check
    if not eff.is_monotonic_increasing:
        findings.append(Finding(ERROR, "not_chronological", None,
                        "Rows are not sorted by effective_date ascending."))


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def _load_csv(path: str) -> pd.DataFrame:
    # dtype=str keeps stages/dates/flags exactly as entered for validation.
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def main() -> int:
    path = os.path.abspath(GRAP_EVENTS_CSV)
    if not os.path.exists(path):
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 1

    df = _load_csv(path)
    findings = validate_events(df)

    errors = [f for f in findings if f.severity == ERROR]
    flags = [f for f in findings if f.severity == FLAG]
    not_ready = [f for f in findings if f.severity == NOT_READY]

    def _print(group, label):
        if group:
            print(f"\n{label} ({len(group)}):")
            for f in group:
                where = "file" if f.row is None else f"row {f.row}"
                print(f"  [{f.code}] {where}: {f.message}")

    print(f"Validating {path}")
    print(f"Rows: {len(df)}")
    _print(errors, "ERRORS")
    _print(flags, "FLAGS (human review)")
    _print(not_ready, "NOT READY (verify before use)")

    n_ready = 0
    if list(df.columns) == EXPECTED_COLUMNS and len(df) > 0:
        verified = df["verified"].astype(str).str.strip()
        n_ready = int((verified == "Yes").sum()) - 0
        # subtract rows that are verified=Yes but still have ERRORs
        error_rows = {f.row for f in errors if f.row is not None}
        ready_mask = (verified == "Yes")
        n_ready = int(sum(1 for i, v in enumerate(ready_mask, start=1)
                          if v and i not in error_rows))

    print(f"\nSummary: {len(errors)} error(s), {len(flags)} flag(s), "
          f"{len(not_ready)} not-ready.")
    print(f"Analysis-ready events (verified=Yes, no errors): {n_ready}")
    if n_ready == 0:
        print("Phase 2 analysis cannot begin: no analysis-ready GRAP events.")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
