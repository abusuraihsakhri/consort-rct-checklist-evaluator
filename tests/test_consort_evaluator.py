from __future__ import annotations

import csv
import json
import subprocess
import sys

import pytest

from consort_evaluator import (
    CONSORT_TAXONOMY,
    STANDARD_VERSION,
    ConsortEvaluatorEngine,
    FlowDiagramArm,
    FlowDiagramCounts,
)


def full_responses():
    return {key: "FULL" for key in CONSORT_TAXONOMY}


def test_consort_2025_has_42_scored_entries_across_30_numbered_items():
    assert len(CONSORT_TAXONOMY) == 42
    assert list(CONSORT_TAXONOMY)[:2] == ["1a", "1b"]
    assert list(CONSORT_TAXONOMY)[-2:] == ["29", "30"]
    assert {value["section"] for value in CONSORT_TAXONOMY.values()} == {
        "TITLE_ABSTRACT",
        "OPEN_SCIENCE",
        "INTRODUCTION",
        "METHODS",
        "RESULTS",
        "DISCUSSION",
    }


def test_full_reporting_is_100_percent_and_neutral_band():
    report = ConsortEvaluatorEngine.evaluate_checklist_responses(full_responses())
    assert report.standard_version == STANDARD_VERSION
    assert report.overall_completion_percentage == 100.0
    assert report.overall_compliance_percentage == 100.0
    assert report.reporting_completeness_band == "HIGH_COMPLETENESS"
    assert report.overall_quality_tier == "HIGH_COMPLETENESS"
    assert report.total_points_awarded == 84
    assert report.total_points_max == 84
    assert report.actionable_remediation_items == []
    assert report.risk_of_bias_evaluation == []


def test_empty_responses_are_not_reported_not_silently_full():
    report = ConsortEvaluatorEngine.evaluate_checklist_responses({})
    assert report.overall_completion_percentage == 0.0
    assert report.reporting_completeness_band == "LOW_COMPLETENESS"
    assert len(report.actionable_remediation_items) == 42


def test_partial_reporting_is_half_completion():
    responses = {key: "PARTIAL" for key in CONSORT_TAXONOMY}
    report = ConsortEvaluatorEngine.evaluate_checklist_responses(responses)
    assert report.overall_completion_percentage == 50.0
    assert report.reporting_completeness_band == "LOW_COMPLETENESS"


def test_na_is_excluded_from_denominator():
    responses = full_responses()
    responses["12b"] = "NA"
    responses["16b"] = "N/A"
    report = ConsortEvaluatorEngine.evaluate_checklist_responses(responses)
    assert report.overall_completion_percentage == 100.0
    assert report.total_points_max == 80


@pytest.mark.parametrize(
    "value, expected",
    [
        ("FULL", (2, 2, "FULLY_REPORTED")),
        ("f", (2, 2, "FULLY_REPORTED")),
        ("YES", (2, 2, "FULLY_REPORTED")),
        ("PARTIAL", (1, 2, "PARTIALLY_REPORTED")),
        ("p", (1, 2, "PARTIALLY_REPORTED")),
        ("NO", (0, 2, "NOT_REPORTED")),
        ("", (0, 2, "NOT_REPORTED")),
        (None, (0, 2, "NOT_REPORTED")),
        ("NA", (0, 0, "NOT_APPLICABLE")),
    ],
)
def test_response_normalization(value, expected):
    assert ConsortEvaluatorEngine.normalize_response(value, item_key="1a") == expected


def test_invalid_response_is_rejected():
    with pytest.raises(ValueError, match="Invalid checklist response for CONSORT item 1a"):
        ConsortEvaluatorEngine.evaluate_checklist_responses({"1a": "maybe"})


def test_unknown_item_key_is_rejected():
    with pytest.raises(ValueError, match="Unknown CONSORT 2025 item"):
        ConsortEvaluatorEngine.evaluate_checklist_responses({"99": "FULL"})


def test_section_scores_expose_completion_and_compatibility_alias():
    report = ConsortEvaluatorEngine.evaluate_checklist_responses({"1a": "FULL", "1b": "PARTIAL"})
    score = report.section_scores["TITLE_ABSTRACT"]
    assert score.points_awarded == 3
    assert score.points_max == 4
    assert score.completion_percentage == 75.0
    assert score.compliance_percentage == 75.0


def test_report_json_roundtrip():
    report = ConsortEvaluatorEngine.evaluate_checklist_responses(full_responses(), trial_id="T-JSON")
    data = json.loads(report.to_json())
    assert data["trial_id"] == "T-JSON"
    assert data["standard_version"] == "CONSORT 2025"
    assert data["risk_of_bias_evaluation"] == []
    assert "not official CONSORT scores" in data["methodological_note"]


def conserved_flow():
    return FlowDiagramCounts(
        assessed_for_eligibility=250,
        excluded_total=50,
        excluded_not_meeting_criteria=35,
        excluded_declined_consent=10,
        excluded_other_reasons=5,
        randomised_total=200,
        arms=[
            FlowDiagramArm(
                arm_name="Intervention",
                allocated=100,
                received_allocated_intervention=98,
                did_not_receive_intervention=2,
                analysed_for_primary_outcome=95,
                excluded_from_analysis=5,
            ),
            FlowDiagramArm(
                arm_name="Comparator",
                allocated=100,
                received_allocated_intervention=100,
                did_not_receive_intervention=0,
                analysed_for_primary_outcome=93,
                excluded_from_analysis=7,
            ),
        ],
    )


def test_flow_conservation_and_analysis_coverage():
    result = ConsortEvaluatorEngine.validate_participant_flow(conserved_flow())
    assert result.is_mathematically_conserved
    assert result.validation_flags == []
    assert result.enrollment_discrepancy == 0
    assert result.allocation_discrepancy == 0
    assert result.analysis_coverage_ratio == 0.94
    assert result.intention_to_treat_ratio == 0.94


def test_low_analysis_coverage_is_not_turned_into_bias_judgement():
    flow = conserved_flow()
    flow.arms[0].analysed_for_primary_outcome = 40
    flow.arms[0].excluded_from_analysis = 60
    flow.arms[1].analysed_for_primary_outcome = 40
    flow.arms[1].excluded_from_analysis = 60
    result = ConsortEvaluatorEngine.validate_participant_flow(flow)
    assert result.analysis_coverage_ratio == 0.4
    assert not any("bias" in flag.lower() or "itt" in flag.lower() for flag in result.validation_flags)


def test_flow_detects_enrollment_and_allocation_mismatches():
    flow = conserved_flow()
    flow.assessed_for_eligibility = 260
    flow.randomised_total = 210
    result = ConsortEvaluatorEngine.validate_participant_flow(flow)
    assert not result.is_mathematically_conserved
    assert result.enrollment_discrepancy == 0
    assert result.allocation_discrepancy == 10
    assert any("Allocation mismatch" in flag for flag in result.validation_flags)


def test_flow_detects_bad_exclusion_subtotals():
    flow = conserved_flow()
    flow.excluded_other_reasons = 10
    result = ConsortEvaluatorEngine.validate_participant_flow(flow)
    assert not result.is_mathematically_conserved
    assert any("exclusion subcategories" in flag for flag in result.validation_flags)


def test_flow_detects_arm_analysis_over_allocation():
    flow = conserved_flow()
    flow.arms[0].analysed_for_primary_outcome = 101
    result = ConsortEvaluatorEngine.validate_participant_flow(flow)
    assert not result.is_mathematically_conserved
    assert any("analysed (101) exceeds allocated" in flag for flag in result.validation_flags)


def test_flow_detects_negative_count():
    flow = conserved_flow()
    flow.arms[0].lost_to_followup = -1
    result = ConsortEvaluatorEngine.validate_participant_flow(flow)
    assert not result.is_mathematically_conserved
    assert any("non-negative integer" in flag for flag in result.validation_flags)


def test_batch_csv_evaluation_accepts_partial_header():
    text = "trial_id,trial_title,1a,1b\nT1,Trial One,FULL,PARTIAL\n"
    reports = ConsortEvaluatorEngine.evaluate_batch_csv(text)
    assert len(reports) == 1
    assert reports[0].trial_id == "T1"
    assert reports[0].section_scores["TITLE_ABSTRACT"].completion_percentage == 75.0


def test_batch_csv_reports_invalid_value_with_row_number():
    text = "trial_id,trial_title,1a\nT1,Trial One,MAYBE\n"
    with pytest.raises(ValueError, match="CSV row 2"):
        ConsortEvaluatorEngine.evaluate_batch_csv(text)


def test_rob_compatibility_method_returns_no_judgements():
    assert ConsortEvaluatorEngine.evaluate_rob_domains({"D1": []}) == []


def test_cli_full_benchmark_json():
    result = subprocess.run(
        [sys.executable, "cli.py", "--full-compliance", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["overall_completion_percentage"] == 100.0
    assert data["standard_version"] == "CONSORT 2025"


def test_cli_invalid_json_fails_loudly():
    result = subprocess.run(
        [sys.executable, "cli.py", "--responses-json", "{not-json}"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "Could not parse --responses-json" in result.stderr


def test_cli_batch_smoke(tmp_path):
    output = tmp_path / "summary.csv"
    result = subprocess.run(
        [sys.executable, "cli.py", "batch", "-i", "sample.csv", "-o", str(output)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    with output.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3
    assert rows[0]["standard_version"] == "CONSORT 2025"
    assert rows[0]["reporting_completeness_band"] == "HIGH_COMPLETENESS"


def test_cli_batch_json_smoke(tmp_path):
    output = tmp_path / "full.json"
    result = subprocess.run(
        [sys.executable, "cli.py", "batch", "-i", "sample.csv", "-o", str(output), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    rows = json.loads(output.read_text(encoding="utf-8"))
    assert len(rows) == 3
    assert rows[0]["risk_of_bias_evaluation"] == []
