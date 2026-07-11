"""
Tests for the GRAP event validator (src/04_validate_grap_events.py).

All data here is SMALL SYNTHETIC FIXTURE DATA used only to exercise the
validation rules. It is NOT real GRAP event data and must never be treated as
such or copied into data/raw/grap/grap_events_manual.csv.

Run:  python -m pytest -q tests/test_grap_events_validator.py
"""
from __future__ import annotations

import importlib.util
import os
import sys

import pandas as pd
import pytest

# The module filename starts with a digit, so import it by path.
_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src",
                    "04_validate_grap_events.py")
_spec = importlib.util.spec_from_file_location("grap_validator", _SRC)
gv = importlib.util.module_from_spec(_spec)
sys.modules["grap_validator"] = gv   # required so @dataclass can resolve __module__
_spec.loader.exec_module(gv)


def _row(**over):
    """A single well-formed, verified synthetic event row (all fields valid)."""
    base = {
        "event_id": "syn_1",
        "order_date": "2022-10-05",
        "effective_date": "2022-10-05",
        "season": "2022-23",
        "action_type": "invoke",
        "stage_from": "0",
        "stage_to": "1",
        "event_direction": "activation",
        "immediate_effect": "Yes",
        "official_order_title": "SYNTHETIC ORDER (test only)",
        "official_source": "https://example.org/synthetic",
        "notes": "synthetic fixture",
        "verified": "Yes",
    }
    base.update(over)
    return base


def _df(rows):
    return pd.DataFrame(rows, columns=gv.EXPECTED_COLUMNS)


def _codes(findings, severity=None):
    return {f.code for f in findings if severity is None or f.severity == severity}


# --- baseline -------------------------------------------------------------
def test_clean_verified_row_has_no_errors_or_flags():
    findings = gv.validate_events(_df([_row()]))
    assert _codes(findings, gv.ERROR) == set()
    assert _codes(findings, gv.FLAG) == set()
    assert _codes(findings, gv.NOT_READY) == set()


def test_empty_file_is_valid_empty_template():
    findings = gv.validate_events(_df([]))
    assert _codes(findings, gv.ERROR) == set()
    assert "empty_file" in _codes(findings)


# --- required rules -------------------------------------------------------
def test_duplicate_event_ids():
    findings = gv.validate_events(_df([
        _row(event_id="dup", effective_date="2022-10-05"),
        _row(event_id="dup", effective_date="2022-10-06",
             action_type="escalate", stage_from="1", stage_to="2",
             event_direction="escalation"),
    ]))
    assert "duplicate_event_id" in _codes(findings, gv.ERROR)


def test_invalid_dates():
    findings = gv.validate_events(_df([_row(effective_date="05-10-2022")]))
    assert "bad_effective_date" in _codes(findings, gv.ERROR)


def test_missing_effective_date():
    findings = gv.validate_events(_df([_row(effective_date="")]))
    codes = _codes(findings, gv.ERROR)
    assert "missing_effective_date" in codes or "missing_required" in codes


def test_unverified_event_is_not_ready():
    findings = gv.validate_events(_df([_row(verified="No")]))
    assert "not_verified" in _codes(findings, gv.NOT_READY)
    # 'No' is a valid controlled value, so it must not be an ERROR
    assert "bad_verified" not in _codes(findings, gv.ERROR)


def test_invalid_verified_value_is_error():
    findings = gv.validate_events(_df([_row(verified="maybe")]))
    assert "bad_verified" in _codes(findings, gv.ERROR)


def test_invalid_stage_label():
    findings = gv.validate_events(_df([_row(stage_to="5")]))
    assert "bad_stage_to" in _codes(findings, gv.ERROR)


def test_invalid_action_type():
    findings = gv.validate_events(_df([_row(action_type="pause")]))
    assert "bad_action_type" in _codes(findings, gv.ERROR)


def test_invalid_season():
    findings = gv.validate_events(_df([_row(season="2024-25")]))
    assert "bad_season" in _codes(findings, gv.ERROR)


# --- logical transition flags (not errors) --------------------------------
def test_no_state_change_is_flagged():
    findings = gv.validate_events(_df([
        _row(action_type="other", stage_from="3", stage_to="3",
             event_direction="other"),
    ]))
    assert "no_state_change" in _codes(findings, gv.FLAG)
    assert "no_state_change" not in _codes(findings, gv.ERROR)


def test_suspicious_multi_stage_escalation_is_flagged():
    # Stage II -> Stage IV: possible but must be flagged, not rejected.
    findings = gv.validate_events(_df([
        _row(action_type="escalate", stage_from="2", stage_to="4",
             event_direction="escalation"),
    ]))
    assert "multi_stage_escalation" in _codes(findings, gv.FLAG)
    assert _codes(findings, gv.ERROR) == set()


def test_suspicious_multi_stage_de_escalation_is_flagged():
    # Stage IV -> Stage II: flag for human verification, not an error.
    findings = gv.validate_events(_df([
        _row(action_type="de_escalate", stage_from="4", stage_to="2",
             event_direction="de_escalation"),
    ]))
    assert "multi_stage_de_escalation" in _codes(findings, gv.FLAG)
    assert _codes(findings, gv.ERROR) == set()


def test_revoke_leaving_active_stage_is_flagged_not_error():
    # action=revoke but stage_to=3 -> should be de_escalate; flag, don't reject.
    findings = gv.validate_events(_df([
        _row(action_type="revoke", stage_from="4", stage_to="3",
             event_direction="full_revocation"),
    ]))
    flags = _codes(findings, gv.FLAG)
    assert "action_stage_mismatch" in flags
    assert "direction_stage_mismatch" in flags


def test_not_chronological_is_error():
    findings = gv.validate_events(_df([
        _row(event_id="a", effective_date="2022-11-01"),
        _row(event_id="b", effective_date="2022-10-01",
             action_type="escalate", stage_from="1", stage_to="2",
             event_direction="escalation"),
    ]))
    assert "not_chronological" in _codes(findings, gv.ERROR)


def test_columns_mismatch_is_error():
    bad = pd.DataFrame([{"event_id": "x", "effective_date": "2022-10-05"}])
    findings = gv.validate_events(bad)
    assert "columns_mismatch" in _codes(findings, gv.ERROR)


def test_non_url_source_is_flag_not_error():
    findings = gv.validate_events(_df([_row(official_source="CAQM order PDF")]))
    assert "source_not_url" in _codes(findings, gv.FLAG)
    assert _codes(findings, gv.ERROR) == set()
