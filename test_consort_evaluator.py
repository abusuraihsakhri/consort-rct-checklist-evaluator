#!/usr/bin/env python3
"""
Comprehensive Unit Test Suite for CONSORT 2010 RCT Checklist Evaluator & Flow Auditor
Tests checklist scoring, section breakdowns, Cochrane RoB 2.0 mapping,
participant flow arithmetic, and CSV batch processing.
"""

import unittest
import json
from consort_evaluator import (
    ConsortEvaluatorEngine,
    FlowDiagramCounts,
    FlowDiagramArm,
    FlowValidationResult,
    SectionScore,
    RiskOfBiasDomainEvaluation,
    ConsortAuditReport,
    CONSORT_TAXONOMY,
)


class TestConsortChecklistScoring(unittest.TestCase):
    """Test CONSORT item response mapping and compliance percentage scoring."""

    def test_full_100_percent_compliance(self):
        responses = {k: "FULL" for k in CONSORT_TAXONOMY.keys()}
        report = ConsortEvaluatorEngine.evaluate_checklist_responses(
            responses=responses,
            trial_id="TRIAL-100",
            trial_title="Perfect Quality Trial"
        )
        self.assertEqual(report.overall_compliance_percentage, 100.0)
        self.assertEqual(report.overall_quality_tier, "HIGH_QUALITY")
        self.assertEqual(len(report.actionable_remediation_items), 0)
        self.assertEqual(report.total_points_awarded, report.total_points_max)

    def test_zero_compliance_substandard(self):
        responses = {k: "NO" for k in CONSORT_TAXONOMY.keys()}
        report = ConsortEvaluatorEngine.evaluate_checklist_responses(
            responses=responses,
            trial_id="TRIAL-0",
            trial_title="Empty Trial"
        )
        self.assertEqual(report.overall_compliance_percentage, 0.0)
        self.assertEqual(report.overall_quality_tier, "SUBSTANDARD_LOW")
        self.assertEqual(report.total_points_awarded, 0)
        self.assertEqual(len(report.actionable_remediation_items), len(CONSORT_TAXONOMY))

    def test_all_partial_compliance(self):
        responses = {k: "PARTIAL" for k in CONSORT_TAXONOMY.keys()}
        report = ConsortEvaluatorEngine.evaluate_checklist_responses(
            responses=responses,
            trial_id="TRIAL-PARTIAL",
            trial_title="Partial Trial"
        )
        self.assertEqual(report.overall_compliance_percentage, 50.0)
        self.assertEqual(report.overall_quality_tier, "SUBSTANDARD_LOW")

    def test_not_applicable_items_excluded_from_denominator(self):
        # 3b (changes to methods) and 7b (interim analyses) are NA
        responses = {k: "FULL" for k in CONSORT_TAXONOMY.keys()}
        responses["3b"] = "NA"
        responses["7b"] = "NA"
        report = ConsortEvaluatorEngine.evaluate_checklist_responses(responses=responses)
        self.assertEqual(report.overall_compliance_percentage, 100.0)
        # Total max should be 2 * (len(CONSORT_TAXONOMY) - 2)
        expected_max = 2 * (len(CONSORT_TAXONOMY) - 2)
        self.assertEqual(report.total_points_max, expected_max)

    def test_high_quality_threshold(self):
        # 88% compliance -> HIGH_QUALITY
        responses = {}
        for idx, k in enumerate(CONSORT_TAXONOMY.keys()):
            responses[k] = "FULL" if idx < 32 else "NO"
        report = ConsortEvaluatorEngine.evaluate_checklist_responses(responses=responses)
        self.assertGreaterEqual(report.overall_compliance_percentage, 85.0)
        self.assertEqual(report.overall_quality_tier, "HIGH_QUALITY")

    def test_acceptable_moderate_threshold(self):
        responses = {}
        for idx, k in enumerate(CONSORT_TAXONOMY.keys()):
            responses[k] = "FULL" if idx < 26 else "NO"
        report = ConsortEvaluatorEngine.evaluate_checklist_responses(responses=responses)
        self.assertTrue(65.0 <= report.overall_compliance_percentage < 85.0)
        self.assertEqual(report.overall_quality_tier, "ACCEPTABLE_MODERATE")


class TestSectionBreakdowns(unittest.TestCase):
    """Test section-by-section scoring and item aggregation."""

    def test_section_presence(self):
        responses = {k: "FULL" for k in CONSORT_TAXONOMY.keys()}
        report = ConsortEvaluatorEngine.evaluate_checklist_responses(responses=responses)
        expected_sections = {"TITLE_ABSTRACT", "INTRODUCTION", "METHODS", "RESULTS", "DISCUSSION", "OTHER_INFO"}
        self.assertEqual(set(report.section_scores.keys()), expected_sections)

    def test_methods_section_specific_score(self):
        responses = {k: "NO" for k in CONSORT_TAXONOMY.keys()}
        # Populate only METHODS items with FULL
        for k, v in CONSORT_TAXONOMY.items():
            if v["section"] == "METHODS":
                responses[k] = "FULL"
        report = ConsortEvaluatorEngine.evaluate_checklist_responses(responses=responses)
        self.assertEqual(report.section_scores["METHODS"].compliance_percentage, 100.0)
        self.assertEqual(report.section_scores["RESULTS"].compliance_percentage, 0.0)

    def test_title_abstract_section(self):
        responses = {"1a": "FULL", "1b": "PARTIAL"}
        report = ConsortEvaluatorEngine.evaluate_checklist_responses(responses=responses)
        ta_sec = report.section_scores["TITLE_ABSTRACT"]
        self.assertEqual(ta_sec.points_awarded, 3)
        self.assertEqual(ta_sec.points_max, 4)
        self.assertEqual(ta_sec.compliance_percentage, 75.0)


class TestCochraneRiskOfBiasMapping(unittest.TestCase):
    """Test mapping of CONSORT items to Cochrane RoB 2.0 5-domain risk matrix."""

    def test_all_five_rob_domains_evaluated(self):
        responses = {k: "FULL" for k in CONSORT_TAXONOMY.keys()}
        report = ConsortEvaluatorEngine.evaluate_checklist_responses(responses=responses)
        rob_ids = [d.domain_id for d in report.risk_of_bias_evaluation]
        expected = ["D1_RANDOMISATION", "D2_DEVIATIONS", "D3_MISSING_DATA", "D4_MEASUREMENT", "D5_REPORTED_RESULT"]
        self.assertEqual(rob_ids, expected)

    def test_rob_domain_low_risk_on_full_reporting(self):
        responses = {k: "FULL" for k in CONSORT_TAXONOMY.keys()}
        report = ConsortEvaluatorEngine.evaluate_checklist_responses(responses=responses)
        for dom in report.risk_of_bias_evaluation:
            self.assertEqual(dom.risk_level, "LOW_RISK")
            self.assertEqual(dom.domain_score_percentage, 100.0)

    def test_rob_randomisation_high_risk_on_omission(self):
        # Omit randomisation items 8a, 8b, 9, 10
        responses = {k: "FULL" for k in CONSORT_TAXONOMY.keys()}
        responses["8a"] = "NO"
        responses["8b"] = "NO"
        responses["9"] = "NO"
        responses["10"] = "NO"
        report = ConsortEvaluatorEngine.evaluate_checklist_responses(responses=responses)
        d1 = next(d for d in report.risk_of_bias_evaluation if d.domain_id == "D1_RANDOMISATION")
        self.assertEqual(d1.risk_level, "HIGH_RISK")
        self.assertLess(d1.domain_score_percentage, 50.0)
        self.assertTrue(len(d1.concerns) >= 4)

    def test_rob_missing_data_domain_evaluation(self):
        responses = {k: "FULL" for k in CONSORT_TAXONOMY.keys()}
        responses["13a"] = "PARTIAL"
        responses["13b"] = "NO"
        responses["16"] = "PARTIAL"
        report = ConsortEvaluatorEngine.evaluate_checklist_responses(responses=responses)
        d3 = next(d for d in report.risk_of_bias_evaluation if d.domain_id == "D3_MISSING_DATA")
        self.assertTrue(d3.risk_level in ["SOME_CONCERNS", "HIGH_RISK"])


class TestParticipantFlowConservation(unittest.TestCase):
    """Test mathematical conservation arithmetic of CONSORT participant flow diagrams."""

    def test_perfectly_conserved_flow_diagram(self):
        arm1 = FlowDiagramArm(
            arm_name="Intervention A",
            allocated=100,
            received_allocated_intervention=100,
            did_not_receive_intervention=0,
            lost_to_followup=2,
            discontinued_intervention=3,
            analysed_for_primary_outcome=95,
            excluded_from_analysis=5
        )
        arm2 = FlowDiagramArm(
            arm_name="Placebo Control",
            allocated=100,
            received_allocated_intervention=100,
            did_not_receive_intervention=0,
            lost_to_followup=1,
            discontinued_intervention=4,
            analysed_for_primary_outcome=95,
            excluded_from_analysis=5
        )
        flow = FlowDiagramCounts(
            assessed_for_eligibility=250,
            excluded_total=50,
            excluded_not_meeting_criteria=35,
            excluded_declined_consent=10,
            excluded_other_reasons=5,
            randomised_total=200,
            arms=[arm1, arm2]
        )
        res = ConsortEvaluatorEngine.validate_participant_flow(flow)
        self.assertTrue(res.is_mathematically_conserved)
        self.assertEqual(res.enrollment_discrepancy, 0)
        self.assertEqual(res.allocation_discrepancy, 0)
        self.assertEqual(len(res.validation_flags), 0)

    def test_enrollment_sum_discrepancy(self):
        flow = FlowDiagramCounts(
            assessed_for_eligibility=300,  # 200 rand + 50 excl = 250 != 300 (diff 50)
            excluded_total=50,
            excluded_not_meeting_criteria=35,
            excluded_declined_consent=10,
            excluded_other_reasons=5,
            randomised_total=200,
            arms=[FlowDiagramArm(allocated=100, received_allocated_intervention=100, analysed_for_primary_outcome=100),
                  FlowDiagramArm(allocated=100, received_allocated_intervention=100, analysed_for_primary_outcome=100)]
        )
        res = ConsortEvaluatorEngine.validate_participant_flow(flow)
        self.assertFalse(res.is_mathematically_conserved)
        self.assertEqual(res.enrollment_discrepancy, 50)
        self.assertTrue(any("Enrollment Error" in f for f in res.validation_flags))

    def test_allocation_sum_discrepancy(self):
        flow = FlowDiagramCounts(
            assessed_for_eligibility=250,
            excluded_total=50,
            excluded_not_meeting_criteria=50,
            excluded_declined_consent=0,
            excluded_other_reasons=0,
            randomised_total=200,
            arms=[FlowDiagramArm(allocated=90, received_allocated_intervention=90, analysed_for_primary_outcome=90),
                  FlowDiagramArm(allocated=90, received_allocated_intervention=90, analysed_for_primary_outcome=90)]  # Sum = 180 != 200
        )
        res = ConsortEvaluatorEngine.validate_participant_flow(flow)
        self.assertFalse(res.is_mathematically_conserved)
        self.assertEqual(res.allocation_discrepancy, 20)

    def test_low_itt_ratio_warning(self):
        # 140 analysed of 200 allocated = 70% ITT ratio (< 90%)
        flow = FlowDiagramCounts(
            assessed_for_eligibility=250,
            excluded_total=50,
            excluded_not_meeting_criteria=50,
            excluded_declined_consent=0,
            excluded_other_reasons=0,
            randomised_total=200,
            arms=[FlowDiagramArm(allocated=100, received_allocated_intervention=100, analysed_for_primary_outcome=70),
                  FlowDiagramArm(allocated=100, received_allocated_intervention=100, analysed_for_primary_outcome=70)]
        )
        res = ConsortEvaluatorEngine.validate_participant_flow(flow)
        self.assertEqual(res.intention_to_treat_ratio, 0.70)
        self.assertTrue(any("Attrition Warning" in f for f in res.validation_flags))


class TestSerializationAndBatch(unittest.TestCase):
    """Test report dictionary conversion, JSON serialization, and CSV batch processing."""

    def test_json_serialization_roundtrip(self):
        responses = {k: "FULL" for k in CONSORT_TAXONOMY.keys()}
        report = ConsortEvaluatorEngine.evaluate_checklist_responses(
            responses=responses,
            trial_id="TRIAL-JSON-01",
            trial_title="JSON Serialization Test Trial"
        )
        d = report.to_dict()
        self.assertEqual(d["trial_id"], "TRIAL-JSON-01")
        self.assertIn("section_scores", d)
        self.assertIn("risk_of_bias_evaluation", d)

        json_str = report.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["overall_compliance_percentage"], 100.0)

    def test_batch_csv_evaluation(self):
        csv_sample = (
            "trial_id,trial_title,1a,1b,2a,2b,3a,4a,5,6a,7a,8a,9,11a,12a,13a,15,16,17a,19,20,23,25\n"
            "T-1,Trial Alpha,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL\n"
            "T-2,Trial Beta,NO,NO,NO,NO,NO,NO,NO,NO,NO,NO,NO,NO,NO,NO,NO,NO,NO,NO,NO,NO,NO\n"
        )
        reports = ConsortEvaluatorEngine.evaluate_batch_csv(csv_sample)
        self.assertEqual(len(reports), 2)
        self.assertEqual(reports[0].trial_id, "T-1")
        self.assertGreater(reports[0].overall_compliance_percentage, 50.0)
        self.assertEqual(reports[1].trial_id, "T-2")
        self.assertEqual(reports[1].overall_compliance_percentage, 0.0)

    def test_format_report_text_helper(self):
        from cli import format_report_text
        responses = {k: "FULL" for k in CONSORT_TAXONOMY.keys()}
        report = ConsortEvaluatorEngine.evaluate_checklist_responses(
            responses=responses,
            trial_id="TRIAL-TXT",
            trial_title="Formatted Text Audit"
        )
        txt = format_report_text(report)
        self.assertIn("CONSORT 2010 STATEMENT RCT REPORTING AUDIT REPORT", txt)
        self.assertIn("OVERALL COMPLIANCE SUMMARY", txt)
        self.assertIn("SECTION-BY-SECTION COMPLIANCE BREAKDOWN", txt)

    def test_alternative_response_string_formats(self):
        # Test "YES", "TRUE", "2", "1", "0"
        responses = {
            "1a": "YES",
            "1b": "TRUE",
            "2a": "2",
            "2b": "1",
            "3a": "0"
        }
        report = ConsortEvaluatorEngine.evaluate_checklist_responses(responses=responses)
        self.assertEqual(report.section_scores["TITLE_ABSTRACT"].compliance_percentage, 100.0)
        self.assertEqual(report.section_scores["INTRODUCTION"].points_awarded, 3)

    def test_arm_losses_exceed_received_flag(self):
        # Allocated 50, received 50, lost 60 -> invalid negative completion
        arm = FlowDiagramArm(
            arm_name="High-Loss Arm",
            allocated=50,
            received_allocated_intervention=50,
            lost_to_followup=60,
            analysed_for_primary_outcome=10
        )
        flow = FlowDiagramCounts(
            assessed_for_eligibility=100,
            excluded_total=50,
            excluded_not_meeting_criteria=50,
            randomised_total=50,
            arms=[arm]
        )
        res = ConsortEvaluatorEngine.validate_participant_flow(flow)
        self.assertFalse(res.is_mathematically_conserved)
        self.assertTrue(any("Losses and discontinuations exceed" in f for f in res.validation_flags))

    def test_discussion_and_other_info_sections(self):
        responses = {
            "20": "FULL",
            "21": "FULL",
            "22": "FULL",
            "23": "FULL",
            "24": "FULL",
            "25": "FULL"
        }
        report = ConsortEvaluatorEngine.evaluate_checklist_responses(responses=responses)
        self.assertEqual(report.section_scores["DISCUSSION"].compliance_percentage, 100.0)
        self.assertEqual(report.section_scores["OTHER_INFO"].compliance_percentage, 100.0)

    def test_actionable_remediation_details(self):
        responses = {"1a": "NO", "1b": "PARTIAL"}
        report = ConsortEvaluatorEngine.evaluate_checklist_responses(responses=responses)
        self.assertTrue(len(report.actionable_remediation_items) >= 2)
        items = [r["item"] for r in report.actionable_remediation_items]
        self.assertIn("1a", items)
        self.assertIn("1b", items)


if __name__ == "__main__":
    unittest.main()
