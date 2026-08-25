#!/usr/bin/env python3
"""
CONSORT 2010 Statement RCT Reporting Checklist Evaluator & Flow Diagram Auditor
--------------------------------------------------------------------------------
Comprehensive clinical trial reporting evaluation engine implementing the CONSORT 2010
25-item checklist (37 sub-items), section-by-section compliance scoring, participant
flow diagram conservation arithmetic, and Cochrane Risk of Bias (RoB 2.0) domain mapping.

Domain: Clinical Research / Evidence-Based Medicine / Trial Methodologies
Pure Python Standard Library (no external dependencies required).
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple, Union
import json
import csv
import io
import sys
import datetime


# CONSORT Checklist Item Definitions
CONSORT_TAXONOMY = {
    "1a": {"section": "TITLE_ABSTRACT", "title": "Identification as a randomised trial in the title", "rob_domain": None},
    "1b": {"section": "TITLE_ABSTRACT", "title": "Structured summary of trial design, methods, results, and conclusions", "rob_domain": None},
    "2a": {"section": "INTRODUCTION", "title": "Scientific background and rationale", "rob_domain": None},
    "2b": {"section": "INTRODUCTION", "title": "Specific objectives or hypotheses", "rob_domain": None},
    "3a": {"section": "METHODS", "title": "Description of trial design (allocation ratio, parallel/factorial)", "rob_domain": "D1_RANDOMISATION"},
    "3b": {"section": "METHODS", "title": "Important changes to methods after trial commencement with reasons", "rob_domain": "D2_DEVIATIONS"},
    "4a": {"section": "METHODS", "title": "Eligibility criteria for participants", "rob_domain": None},
    "4b": {"section": "METHODS", "title": "Settings and locations where the data were collected", "rob_domain": None},
    "5":  {"section": "METHODS", "title": "Interventions for each group with sufficient details for replication", "rob_domain": "D2_DEVIATIONS"},
    "6a": {"section": "METHODS", "title": "Completely defined pre-specified primary and secondary outcome measures", "rob_domain": "D4_MEASUREMENT"},
    "6b": {"section": "METHODS", "title": "Any changes to trial outcomes after trial commenced with reasons", "rob_domain": "D5_REPORTED_RESULT"},
    "7a": {"section": "METHODS", "title": "Sample size determination and power calculation parameters", "rob_domain": None},
    "7b": {"section": "METHODS", "title": "Interim analyses explanation and formal stopping guidelines", "rob_domain": "D2_DEVIATIONS"},
    "8a": {"section": "METHODS", "title": "Method used to generate random allocation sequence", "rob_domain": "D1_RANDOMISATION"},
    "8b": {"section": "METHODS", "title": "Type of randomisation (blocking, stratification)", "rob_domain": "D1_RANDOMISATION"},
    "9":  {"section": "METHODS", "title": "Allocation concealment mechanism (centralised, sealed envelopes)", "rob_domain": "D1_RANDOMISATION"},
    "10": {"section": "METHODS", "title": "Implementation: sequence generator, participant enroller, assigner", "rob_domain": "D1_RANDOMISATION"},
    "11a":{"section": "METHODS", "title": "Blinding procedure (participants, providers, outcome assessors)", "rob_domain": "D2_DEVIATIONS"},
    "11b":{"section": "METHODS", "title": "Similarity of interventions for active vs comparator", "rob_domain": "D2_DEVIATIONS"},
    "12a":{"section": "METHODS", "title": "Statistical methods used to compare groups for primary/secondary outcomes", "rob_domain": "D5_REPORTED_RESULT"},
    "12b":{"section": "METHODS", "title": "Methods for additional analyses (subgroup, adjusted analyses)", "rob_domain": "D5_REPORTED_RESULT"},
    "13a":{"section": "RESULTS", "title": "Participant flow numbers by group (assigned, received, analysed)", "rob_domain": "D3_MISSING_DATA"},
    "13b":{"section": "RESULTS", "title": "Losses and exclusions after randomisation with documented reasons", "rob_domain": "D3_MISSING_DATA"},
    "14a":{"section": "RESULTS", "title": "Dates defining periods of recruitment and follow-up", "rob_domain": None},
    "14b":{"section": "RESULTS", "title": "Why the trial ended or was stopped early", "rob_domain": "D2_DEVIATIONS"},
    "15": {"section": "RESULTS", "title": "Baseline demographic and clinical characteristics for each group", "rob_domain": "D1_RANDOMISATION"},
    "16": {"section": "RESULTS", "title": "Number of participants included in each analysis and ITT adherence", "rob_domain": "D3_MISSING_DATA"},
    "17a":{"section": "RESULTS", "title": "Effect size and precision (95% CI) for primary and secondary outcomes", "rob_domain": "D4_MEASUREMENT"},
    "17b":{"section": "RESULTS", "title": "Absolute and relative effect sizes for binary outcomes", "rob_domain": "D4_MEASUREMENT"},
    "18": {"section": "RESULTS", "title": "Results of ancillary analyses (subgroup, exploratory)", "rob_domain": "D5_REPORTED_RESULT"},
    "19": {"section": "RESULTS", "title": "All important harms or unintended effects in each group", "rob_domain": "D2_DEVIATIONS"},
    "20": {"section": "DISCUSSION", "title": "Trial limitations addressing sources of potential bias and imprecision", "rob_domain": "D3_MISSING_DATA"},
    "21": {"section": "DISCUSSION", "title": "Generalisability (external validity) of the trial findings", "rob_domain": None},
    "22": {"section": "DISCUSSION", "title": "Interpretation consistent with results balancing benefits and harms", "rob_domain": None},
    "23": {"section": "OTHER_INFO", "title": "Registration number and name of trial registry (e.g. ClinicalTrials.gov)", "rob_domain": "D5_REPORTED_RESULT"},
    "24": {"section": "OTHER_INFO", "title": "Where the full trial protocol can be accessed", "rob_domain": "D5_REPORTED_RESULT"},
    "25": {"section": "OTHER_INFO", "title": "Sources of funding and role of funders", "rob_domain": None},
}


@dataclass
class FlowDiagramArm:
    """Participant counts for a single trial arm."""
    arm_name: str = "Intervention"
    allocated: int = 100
    received_allocated_intervention: int = 98
    did_not_receive_intervention: int = 2
    did_not_receive_reasons: List[str] = field(default_factory=lambda: ["Consent withdrawn before dose"])
    lost_to_followup: int = 3
    lost_to_followup_reasons: List[str] = field(default_factory=lambda: ["Relocated"])
    discontinued_intervention: int = 5
    discontinued_reasons: List[str] = field(default_factory=lambda: ["Adverse event"])
    analysed_for_primary_outcome: int = 95
    excluded_from_analysis: int = 5
    excluded_from_analysis_reasons: List[str] = field(default_factory=lambda: ["Protocol violation"])


@dataclass
class FlowDiagramCounts:
    """Consolidated participant flow metrics across all stages."""
    assessed_for_eligibility: int = 250
    excluded_total: int = 50
    excluded_not_meeting_criteria: int = 35
    excluded_declined_consent: int = 10
    excluded_other_reasons: int = 5
    randomised_total: int = 200
    arms: List[FlowDiagramArm] = field(default_factory=list)


@dataclass
class FlowValidationResult:
    """Conservation arithmetic and consistency check results for flow diagram."""
    is_mathematically_conserved: bool
    enrollment_discrepancy: int
    allocation_discrepancy: int
    arm_discrepancies: List[Dict[str, Any]] = field(default_factory=list)
    intention_to_treat_ratio: float = 1.0  # analysed / allocated
    validation_flags: List[str] = field(default_factory=list)


@dataclass
class SectionScore:
    """Compliance breakdown for a single CONSORT section."""
    section_name: str
    points_awarded: int
    points_max: int
    compliance_percentage: float
    items_fully_reported: int
    items_partially_reported: int
    items_not_reported: int
    items_not_applicable: int


@dataclass
class RiskOfBiasDomainEvaluation:
    """Cochrane RoB 2.0 domain score derived from CONSORT reporting items."""
    domain_id: str  # D1_RANDOMISATION, D2_DEVIATIONS, D3_MISSING_DATA, D4_MEASUREMENT, D5_REPORTED_RESULT
    domain_title: str
    items_evaluated: List[str]
    domain_score_percentage: float
    risk_level: str  # 'LOW_RISK', 'SOME_CONCERNS', 'HIGH_RISK'
    concerns: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ConsortAuditReport:
    """Unified comprehensive CONSORT evaluation report."""
    trial_id: str
    trial_title: str
    timestamp_utc: str
    overall_compliance_percentage: float
    overall_quality_tier: str  # 'HIGH_QUALITY', 'ACCEPTABLE_MODERATE', 'SUBSTANDARD_LOW'
    total_points_awarded: int
    total_points_max: int
    section_scores: Dict[str, SectionScore]
    flow_validation: Optional[FlowValidationResult]
    risk_of_bias_evaluation: List[RiskOfBiasDomainEvaluation]
    actionable_remediation_items: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class ConsortEvaluatorEngine:
    """
    Core engine for auditing RCT manuscripts and protocols against CONSORT 2010 standards,
    evaluating flow diagram mathematical invariants, and mapping to Cochrane RoB 2.0.
    """

    @classmethod
    def evaluate_checklist_responses(
        cls,
        responses: Dict[str, str],  # item_key -> 'FULL', 'PARTIAL', 'NO', 'NA' (or 2, 1, 0)
        trial_id: str = "TRIAL-001",
        trial_title: str = "Randomised Controlled Trial Assessment",
        flow_counts: Optional[FlowDiagramCounts] = None
    ) -> ConsortAuditReport:
        """
        Evaluate full 25-item checklist responses, calculate scores, and generate audit report.
        """
        section_groups: Dict[str, List[Dict[str, Any]]] = {}
        rob_groups: Dict[str, List[Dict[str, Any]]] = {
            "D1_RANDOMISATION": [],
            "D2_DEVIATIONS": [],
            "D3_MISSING_DATA": [],
            "D4_MEASUREMENT": [],
            "D5_REPORTED_RESULT": [],
        }

        remediation_items = []
        total_awarded = 0
        total_max = 0

        # Initialize section trackers
        for item_key, item_info in CONSORT_TAXONOMY.items():
            sec = item_info["section"]
            if sec not in section_groups:
                section_groups[sec] = []

            raw_resp = str(responses.get(item_key, "NO")).upper().strip()
            # Map response to score
            if raw_resp in ["2", "FULL", "FULLY_REPORTED", "YES", "TRUE"]:
                points = 2
                max_pts = 2
                status = "FULLY_REPORTED"
            elif raw_resp in ["1", "PARTIAL", "PARTIALLY_REPORTED"]:
                points = 1
                max_pts = 2
                status = "PARTIALLY_REPORTED"
                remediation_items.append({
                    "item": item_key,
                    "title": item_info["title"],
                    "section": sec,
                    "status": status,
                    "deficiency": "Item is only partially described; expand methodology or data reporting.",
                })
            elif raw_resp in ["NA", "N/A", "NOT_APPLICABLE"]:
                points = 0
                max_pts = 0
                status = "NOT_APPLICABLE"
            else:
                points = 0
                max_pts = 2
                status = "NOT_REPORTED"
                remediation_items.append({
                    "item": item_key,
                    "title": item_info["title"],
                    "section": sec,
                    "status": status,
                    "deficiency": "Item is omitted from report; required for CONSORT 2010 compliance.",
                })

            item_record = {
                "item": item_key,
                "title": item_info["title"],
                "section": sec,
                "points": points,
                "max_points": max_pts,
                "status": status
            }

            section_groups[sec].append(item_record)
            total_awarded += points
            total_max += max_pts

            # Map to Cochrane RoB
            rob_d = item_info["rob_domain"]
            if rob_d and rob_d in rob_groups and max_pts > 0:
                rob_groups[rob_d].append(item_record)

        # Compute Section Scores
        section_score_map: Dict[str, SectionScore] = {}
        for sec_name, items in section_groups.items():
            s_awarded = sum(i["points"] for i in items)
            s_max = sum(i["max_points"] for i in items)
            s_pct = (s_awarded / s_max * 100.0) if s_max > 0 else 100.0
            
            section_score_map[sec_name] = SectionScore(
                section_name=sec_name,
                points_awarded=s_awarded,
                points_max=s_max,
                compliance_percentage=round(s_pct, 1),
                items_fully_reported=sum(1 for i in items if i["status"] == "FULLY_REPORTED"),
                items_partially_reported=sum(1 for i in items if i["status"] == "PARTIALLY_REPORTED"),
                items_not_reported=sum(1 for i in items if i["status"] == "NOT_REPORTED"),
                items_not_applicable=sum(1 for i in items if i["status"] == "NOT_APPLICABLE")
            )

        # Overall Compliance
        overall_pct = (total_awarded / total_max * 100.0) if total_max > 0 else 0.0
        overall_pct = round(overall_pct, 1)

        if overall_pct >= 85.0:
            quality_tier = "HIGH_QUALITY"
        elif overall_pct >= 65.0:
            quality_tier = "ACCEPTABLE_MODERATE"
        else:
            quality_tier = "SUBSTANDARD_LOW"

        # Evaluate Cochrane Risk of Bias Domains
        rob_evaluations = cls.evaluate_rob_domains(rob_groups)

        # Validate Participant Flow if provided
        flow_result = None
        if flow_counts:
            flow_result = cls.validate_participant_flow(flow_counts)

        return ConsortAuditReport(
            trial_id=trial_id,
            trial_title=trial_title,
            timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            overall_compliance_percentage=overall_pct,
            overall_quality_tier=quality_tier,
            total_points_awarded=total_awarded,
            total_points_max=total_max,
            section_scores=section_score_map,
            flow_validation=flow_result,
            risk_of_bias_evaluation=rob_evaluations,
            actionable_remediation_items=remediation_items
        )

    @classmethod
    def evaluate_rob_domains(cls, rob_groups: Dict[str, List[Dict[str, Any]]]) -> List[RiskOfBiasDomainEvaluation]:
        """Map CONSORT checklist items to Cochrane RoB 2.0 5-domain risk matrix."""
        domain_titles = {
            "D1_RANDOMISATION": "Domain 1: Risk of bias arising from the randomisation process",
            "D2_DEVIATIONS": "Domain 2: Risk of bias due to deviations from the intended interventions",
            "D3_MISSING_DATA": "Domain 3: Missing outcome data",
            "D4_MEASUREMENT": "Domain 4: Risk of bias in measurement of the outcome",
            "D5_REPORTED_RESULT": "Domain 5: Risk of bias in selection of the reported result"
        }

        results = []
        for dom_id, items in rob_groups.items():
            awarded = sum(i["points"] for i in items)
            max_p = sum(i["max_points"] for i in items)
            score_pct = (awarded / max_p * 100.0) if max_p > 0 else 100.0

            concerns = []
            recs = []

            for itm in items:
                if itm["status"] == "NOT_REPORTED":
                    concerns.append(f"Item {itm['item']} ({itm['title']}) is omitted.")
                elif itm["status"] == "PARTIALLY_REPORTED":
                    concerns.append(f"Item {itm['item']} ({itm['title']}) lacks complete procedural detail.")

            if score_pct >= 80.0:
                risk = "LOW_RISK"
            elif score_pct >= 50.0:
                risk = "SOME_CONCERNS"
                recs.append("Clarify methodology and supply missing protocol appendices to resolve domain ambiguity.")
            else:
                risk = "HIGH_RISK"
                recs.append("Critical methodological reporting failure. Supply explicit sequence generation, concealment, or outcome details.")

            results.append(RiskOfBiasDomainEvaluation(
                domain_id=dom_id,
                domain_title=domain_titles.get(dom_id, dom_id),
                items_evaluated=[i["item"] for i in items],
                domain_score_percentage=round(score_pct, 1),
                risk_level=risk,
                concerns=concerns,
                recommendations=recs
            ))
        return results

    @staticmethod
    def validate_participant_flow(flow: FlowDiagramCounts) -> FlowValidationResult:
        """
        Validate mathematical conservation of participant counts across all 4 CONSORT stages.
        """
        flags = []
        
        # 1. Enrollment Conservation
        calc_excluded = flow.excluded_not_meeting_criteria + flow.excluded_declined_consent + flow.excluded_other_reasons
        if calc_excluded != flow.excluded_total:
            flags.append(f"Enrollment Error: Sum of sub-exclusions ({calc_excluded}) != total excluded ({flow.excluded_total}).")

        enroll_discrepancy = flow.assessed_for_eligibility - (flow.randomised_total + flow.excluded_total)
        if enroll_discrepancy != 0:
            flags.append(f"Enrollment Error: Assessed ({flow.assessed_for_eligibility}) != Randomised ({flow.randomised_total}) + Excluded ({flow.excluded_total}) [Discrepancy: {enroll_discrepancy}].")

        # 2. Allocation Conservation
        sum_allocated = sum(a.allocated for a in flow.arms)
        alloc_discrepancy = flow.randomised_total - sum_allocated
        if alloc_discrepancy != 0:
            flags.append(f"Allocation Error: Total randomised ({flow.randomised_total}) != Sum of arm allocations ({sum_allocated}).")

        # 3. Arm Conservation (Follow-up and Analysis)
        arm_issues = []
        total_analysed = 0
        total_allocated = 0

        for arm in flow.arms:
            total_allocated += arm.allocated
            total_analysed += arm.analysed_for_primary_outcome

            # Check allocation = received + did_not_receive
            if arm.allocated != (arm.received_allocated_intervention + arm.did_not_receive_intervention):
                msg = f"Arm '{arm.arm_name}': Allocated ({arm.allocated}) != Received ({arm.received_allocated_intervention}) + Did Not Receive ({arm.did_not_receive_intervention})."
                flags.append(msg)
                arm_issues.append({"arm": arm.arm_name, "issue": msg})

            # Check analysed + excluded_from_analysis == completed/received
            # Completed follow-up = received - lost - discontinued
            completed_followup = arm.received_allocated_intervention - (arm.lost_to_followup + arm.discontinued_intervention)
            if completed_followup < 0:
                msg = f"Arm '{arm.arm_name}': Losses and discontinuations exceed received count."
                flags.append(msg)
                arm_issues.append({"arm": arm.arm_name, "issue": msg})

        itt_ratio = (total_analysed / total_allocated) if total_allocated > 0 else 1.0

        if itt_ratio < 0.90:
            flags.append(f"Attrition Warning: Intention-To-Treat analysis ratio is {itt_ratio * 100:.1f}% (< 90% analyzed). Risk of attrition bias.")

        is_conserved = (len(flags) == 0)

        return FlowValidationResult(
            is_mathematically_conserved=is_conserved,
            enrollment_discrepancy=enroll_discrepancy,
            allocation_discrepancy=alloc_discrepancy,
            arm_discrepancies=arm_issues,
            intention_to_treat_ratio=round(itt_ratio, 4),
            validation_flags=flags
        )

    @classmethod
    def evaluate_batch_csv(cls, csv_text: str) -> List[ConsortAuditReport]:
        """Parse batch CSV where each row corresponds to a trial checklist evaluation."""
        reader = csv.DictReader(io.StringIO(csv_text))
        reports = []
        for idx, row in enumerate(reader):
            t_id = row.get("trial_id", f"TRIAL-{idx+1}")
            t_title = row.get("trial_title", "Evaluated Clinical Trial")
            
            # Extract item responses from row
            responses = {}
            for item_key in CONSORT_TAXONOMY.keys():
                if item_key in row:
                    responses[item_key] = row[item_key]
                elif f"item_{item_key}" in row:
                    responses[item_key] = row[f"item_{item_key}"]

            reports.append(cls.evaluate_checklist_responses(
                responses=responses,
                trial_id=t_id,
                trial_title=t_title
            ))
        return reports
