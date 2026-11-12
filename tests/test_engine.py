import json
import os
import sys
from datetime import date

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, ROOT)

from compliance_engine import REQUIRED, REVIEW, ComplianceEngine, IncidentError, add_days  # noqa: E402
from drafter import DraftingEngine  # noqa: E402

TODAY = date(2026, 11, 12)


@pytest.fixture(scope="module")
def engine():
    return ComplianceEngine()


def assess(engine, residents, data_types=("ssn",), discovery="2026-11-02", sectors=()):
    incident = {"discovery_date": discovery, "data_types": list(data_types),
                "affected_residents": residents, "sectors": list(sectors)}
    return engine.assess_incident(incident, today=TODAY)


def find(obligations, jurisdiction, who_contains):
    matches = [o for o in obligations if o["jurisdiction"] == jurisdiction and who_contains in o["who"]]
    assert len(matches) == 1, f"expected one match for {jurisdiction}/{who_contains}, got {len(matches)}"
    return matches[0]


# --- the law data file ---

def test_every_state_dc_and_puerto_rico_is_present(engine):
    assert len(engine.states) == 52
    for name in ("california", "district of columbia", "puerto rico", "wyoming"):
        assert name in engine.states


def test_law_data_is_complete_and_consistent(engine):
    for state in engine.states.values():
        assert state["law"] and state["individual_notice_text"]
        assert state["individual_notice_days"] in (None, 30, 45, 60)
        assert set(state["also_covers"]) <= {"medical", "biometric", "credentials"}
        if state["regulator"]:
            assert state["regulator_min_residents"] >= 1 and state["regulator_threshold_text"]
            assert state["regulator_timing_text"]
        else:
            assert state["regulator_min_residents"] is None and state["regulator_days"] is None
        if state["regulator_days"] is not None:
            assert state["regulator_days_counted_from"] in ("discovery", "individual_notice")


def test_2026_changes_are_in_the_data(engine):
    california, oklahoma = engine.states["california"], engine.states["oklahoma"]
    assert california["individual_notice_days"] == 30 and california["regulator_days"] == 15
    assert oklahoma["regulator_min_residents"] == 500 and oklahoma["regulator_days"] == 60
    assert "HB 381" in engine.states["delaware"]["notes"]
    assert engine.sector_rules["critical_infrastructure"]["status"] == "not_in_effect"


# --- counting days ---

def test_calendar_and_business_days():
    assert add_days(date(2026, 11, 2), 30) == date(2026, 12, 2)
    assert add_days(date(2026, 11, 2), 14, business_days=True) == date(2026, 11, 20)   # Monday + 14 weekdays
    assert add_days(date(2026, 11, 6), 1, business_days=True) == date(2026, 11, 9)     # Friday -> Monday


def test_california_deadlines(engine):
    result = assess(engine, {"California": 1200})
    assert find(result, "California", "individuals")["due"] == date(2026, 12, 2)
    attorney_general = find(result, "California", "Attorney General")
    assert attorney_general["due"] == date(2026, 12, 17)        # 15 days after the last day to notify residents
    assert attorney_general["days_left"] == 35


def test_regulator_threshold_is_respected(engine):
    assert len(assess(engine, {"California": 500})) == 1        # "more than 500": 500 does not trigger
    assert len(assess(engine, {"California": 501})) == 2
    assert len(assess(engine, {"Texas": 249})) == 1             # "250 or more"
    assert find(assess(engine, {"Texas": 250}), "Texas", "Attorney General")["due"] == date(2026, 12, 2)


def test_vermont_business_day_notice_comes_first(engine):
    result = assess(engine, {"Vermont": 12, "Texas": 300})
    assert result[0]["jurisdiction"] == "Vermont" and result[0]["due"] == date(2026, 11, 20)


def test_states_without_a_fixed_deadline_are_still_listed(engine):
    result = assess(engine, {"Massachusetts": 10})
    assert [o["due"] for o in result] == [None, None]
    assert {o["status"] for o in result} == {REQUIRED}


def test_overdue_deadlines_have_negative_days_left(engine):
    result = assess(engine, {"Florida": 10}, discovery="2026-09-01")
    assert find(result, "Florida", "individuals")["days_left"] == -42


# --- data types ---

def test_core_data_types_apply_everywhere(engine):
    for data_type in ("ssn", "driver_license", "financial"):
        assert assess(engine, {"Ohio": 5}, [data_type])[0]["status"] == REQUIRED


def test_uncovered_data_type_is_sent_to_review_not_dropped(engine):
    result = assess(engine, {"Ohio": 5}, ["medical"])           # Ohio's law is listed as core types only
    assert len(result) == 1 and result[0]["status"] == REVIEW
    assert "Confirm with counsel" in result[0]["timing"]
    assert assess(engine, {"California": 5}, ["medical"])[0]["status"] == REQUIRED


def test_unknown_place_is_sent_to_review(engine):
    result = assess(engine, {"Calfornia": 5})
    assert result[0]["status"] == REVIEW and "not in the dataset" in result[0]["timing"]


def test_missing_counts_send_threshold_questions_to_review(engine):
    incident = {"timestamp": "2026-11-02T09:30:00", "data_types": ["ssn"], "affected_locations": ["California", "New York"]}
    result = engine.assess_incident(incident, today=TODAY)       # the older incident format still works
    assert find(result, "California", "Attorney General")["status"] == REVIEW
    assert find(result, "New York", "Attorney General")["status"] == REQUIRED   # any breach


# --- sector rules ---

def test_hipaa_thresholds(engine):
    small = assess(engine, {"Ohio": 40}, sectors=["healthcare"])
    assert [o["who"] for o in small if o["jurisdiction"].startswith("HIPAA")] == ["Affected individuals"]
    large = assess(engine, {"Ohio": 600}, sectors=["healthcare"])
    assert find(large, "HIPAA Breach Notification Rule", "HHS")["due"] == date(2027, 1, 1)
    assert len([o for o in large if o["jurisdiction"].startswith("HIPAA")]) == 3


def test_sec_and_circia(engine):
    result = assess(engine, {"Ohio": 40}, sectors=["public_company", "critical_infrastructure"])
    sec = next(o for o in result if o["jurisdiction"].startswith("SEC"))
    assert sec["due"] == date(2026, 11, 6)                       # 4 business days after Monday Nov 2
    circia = next(o for o in result if o["jurisdiction"].startswith("CIRCIA"))
    assert circia["status"] == "Not yet in effect" and circia["due"] is None


# --- bad input ---

@pytest.mark.parametrize("incident, message", [
    ({"data_types": ["ssn"], "affected_residents": {"Ohio": 1}}, "discovery_date"),
    ({"discovery_date": "11/02/2026", "data_types": ["ssn"], "affected_residents": {"Ohio": 1}}, "YYYY-MM-DD"),
    ({"discovery_date": "2026-11-02", "data_types": [], "affected_residents": {"Ohio": 1}}, "data_types"),
    ({"discovery_date": "2026-11-02", "data_types": ["dna"], "affected_residents": {"Ohio": 1}}, "Unknown data type"),
    ({"discovery_date": "2026-11-02", "data_types": ["ssn"], "affected_residents": {"Ohio": "many"}}, "whole number"),
    ({"discovery_date": "2026-11-02", "data_types": ["ssn"], "affected_residents": {}}, "affected_residents"),
    ({"discovery_date": "2026-11-02", "data_types": ["ssn"], "affected_residents": {"Ohio": 1}, "sectors": ["retail"]}, "Unknown sector"),
])
def test_bad_incident_files_get_a_clear_message(engine, incident, message):
    with pytest.raises(IncidentError, match=message):
        engine.assess_incident(incident)


# --- HTML output ---

def test_report_and_letter_are_written_and_escape_input(engine, tmp_path):
    incident = {"id": "INC-<script>alert(1)</script>", "company_name": "A & B <b>Co</b>", "discovery_date": "2026-11-02",
                "data_types": ["ssn", "medical"], "affected_residents": {"California": 1200, "Ohio": 3, "Massachusetts": 2},
                "sectors": ["critical_infrastructure"]}
    obligations = engine.assess_incident(incident, today=TODAY)
    drafter = DraftingEngine()
    report = open(drafter.write_report(incident, obligations, engine.meta, str(tmp_path), today=TODAY), encoding="utf-8").read()
    letter = open(drafter.draft_consumer_notice(incident, str(tmp_path), engine.meta, today=TODAY), encoding="utf-8").read()

    assert "<script>" not in report and "&lt;script&gt;" in report
    assert "<b>Co</b>" not in letter and "A &amp; B" in letter
    for expected in ("2026-12-02", "20 days left", "Cal. Civ. Code", "not legal advice", "no fixed number of days",
                     "not in effect yet", "does not cover"):
        assert expected in report
    for expected in ("DRAFT", "Social Security number", "Medical or health insurance information", "November 12, 2026"):
        assert expected in letter


def test_run_script_with_the_example(tmp_path, monkeypatch):
    import run

    monkeypatch.chdir(tmp_path)
    assert run.main([]) == 0
    assert sorted(os.listdir(tmp_path / "output")) == ["draft_consumer_notice.html", "report.html"]
    assert run.main(["missing.json"]) == 2
    (tmp_path / "bad.json").write_text("{not json", encoding="utf-8")
    assert run.main(["bad.json"]) == 2
    (tmp_path / "incomplete.json").write_text(json.dumps({"data_types": ["ssn"]}), encoding="utf-8")
    assert run.main(["incomplete.json"]) == 2
