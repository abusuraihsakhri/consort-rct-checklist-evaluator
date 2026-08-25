"""
Pytest integration test suite for consort_master.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from consort_evaluator import ConsortEvaluatorEngine, CONSORT_TAXONOMY


def test_consort_scoring_pytest():
    responses = {k: "FULL" for k in CONSORT_TAXONOMY.keys()}
    rep = ConsortEvaluatorEngine.evaluate_checklist_responses(responses=responses)
    assert rep.overall_compliance_percentage == 100.0
    assert rep.overall_quality_tier == "HIGH_QUALITY"


def test_consort_partial_pytest():
    responses = {k: "PARTIAL" for k in CONSORT_TAXONOMY.keys()}
    rep = ConsortEvaluatorEngine.evaluate_checklist_responses(responses=responses)
    assert rep.overall_compliance_percentage == 50.0
