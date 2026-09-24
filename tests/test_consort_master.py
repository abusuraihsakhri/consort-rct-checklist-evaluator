"""Compatibility-focused integration tests for the CONSORT 2025 evaluator."""

from consort_evaluator import CONSORT_TAXONOMY, ConsortEvaluatorEngine


def test_consort_scoring_pytest():
    responses = {key: "FULL" for key in CONSORT_TAXONOMY}
    report = ConsortEvaluatorEngine.evaluate_checklist_responses(responses=responses)
    assert report.overall_compliance_percentage == 100.0
    assert report.overall_completion_percentage == 100.0
    assert report.overall_quality_tier == "HIGH_COMPLETENESS"


def test_consort_partial_pytest():
    responses = {key: "PARTIAL" for key in CONSORT_TAXONOMY}
    report = ConsortEvaluatorEngine.evaluate_checklist_responses(responses=responses)
    assert report.overall_compliance_percentage == 50.0
    assert report.reporting_completeness_band == "LOW_COMPLETENESS"
