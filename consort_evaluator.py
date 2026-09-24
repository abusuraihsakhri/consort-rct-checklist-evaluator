#!/usr/bin/env python3
"""CONSORT 2025 reporting checklist evaluator and participant-flow validator.

The scoring implemented here is a repository-defined completion aid. CONSORT 2025 does
not prescribe a numeric manuscript score, and checklist completion is not a Cochrane
RoB 2 risk-of-bias assessment.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional
import csv
import datetime
import io
import json


STANDARD_VERSION = "CONSORT 2025"
STANDARD_URL = "https://www.bmj.com/content/389/bmj-2024-081123"
METHODOLOGICAL_NOTE = (
    "The percentage and completeness bands are repository-defined reporting aids, not "
    "official CONSORT scores, trial-quality ratings, or Cochrane RoB 2 judgements."
)


CONSORT_TAXONOMY: Dict[str, Dict[str, str]] = {
    "1a": {"section": "TITLE_ABSTRACT", "title": "Identify the study as a randomised trial in the title"},
    "1b": {"section": "TITLE_ABSTRACT", "title": "Provide a structured summary of trial design, methods, results, and conclusions"},
    "2": {"section": "OPEN_SCIENCE", "title": "Report trial registry name, registration identifier or URL, and registration date"},
    "3": {"section": "OPEN_SCIENCE", "title": "State where the trial protocol and statistical analysis plan can be accessed"},
    "4": {"section": "OPEN_SCIENCE", "title": "State where and how de-identified participant data, code, and other materials can be accessed"},
    "5a": {"section": "OPEN_SCIENCE", "title": "Report sources of financial and other support and the role of funders or sponsors"},
    "5b": {"section": "OPEN_SCIENCE", "title": "Report financial and other conflicts of interest of manuscript authors"},
    "6": {"section": "INTRODUCTION", "title": "Describe the scientific background and rationale"},
    "7": {"section": "INTRODUCTION", "title": "State specific objectives or hypotheses relating to benefits and harms"},
    "8": {"section": "METHODS", "title": "Describe patient and/or public involvement in trial design, conduct, or reporting"},
    "9": {"section": "METHODS", "title": "Describe trial design, allocation ratio, and framework (for example superiority or non-inferiority)"},
    "10": {"section": "METHODS", "title": "Report important changes after trial commencement, including non-prespecified outcomes or analyses, with reasons"},
    "11": {"section": "METHODS", "title": "Describe settings and locations where the trial was conducted"},
    "12a": {"section": "METHODS", "title": "Report eligibility criteria for participants"},
    "12b": {"section": "METHODS", "title": "If applicable, report eligibility criteria for sites and individuals delivering interventions"},
    "13": {"section": "METHODS", "title": "Describe intervention and comparator in enough detail for replication and link additional materials if relevant"},
    "14": {"section": "METHODS", "title": "Define prespecified primary and secondary outcomes, including measurement, analysis metric, aggregation, and time point"},
    "15": {"section": "METHODS", "title": "Describe how harms and other unintended effects were defined and assessed"},
    "16a": {"section": "METHODS", "title": "Explain sample-size determination and all supporting assumptions"},
    "16b": {"section": "METHODS", "title": "Explain interim analyses and stopping guidelines, if applicable"},
    "17a": {"section": "METHODS", "title": "State who generated the random allocation sequence and how it was generated"},
    "17b": {"section": "METHODS", "title": "Describe the type of randomisation and any restrictions such as stratification or blocking"},
    "18": {"section": "METHODS", "title": "Describe the mechanism used to conceal allocation until assignment"},
    "19": {"section": "METHODS", "title": "Describe implementation of randomisation and who had access to the allocation sequence"},
    "20a": {"section": "METHODS", "title": "State who was blinded after assignment to interventions"},
    "20b": {"section": "METHODS", "title": "If blinding was used, describe how it was achieved and the similarity of interventions"},
    "21a": {"section": "METHODS", "title": "Describe statistical methods for primary and secondary outcomes, including harms"},
    "21b": {"section": "METHODS", "title": "Define who was included in each analysis and in which randomised group"},
    "21c": {"section": "METHODS", "title": "Describe how missing data were handled in the analysis"},
    "21d": {"section": "METHODS", "title": "Describe additional analyses and distinguish prespecified from post-hoc analyses"},
    "22a": {"section": "RESULTS", "title": "For each group, report numbers randomised, receiving intended intervention, and analysed"},
    "22b": {"section": "RESULTS", "title": "For each group, report losses and exclusions after randomisation with reasons"},
    "23a": {"section": "RESULTS", "title": "Report dates defining recruitment and follow-up periods"},
    "23b": {"section": "RESULTS", "title": "Explain why the trial ended or was stopped, if applicable"},
    "24a": {"section": "RESULTS", "title": "Describe how intervention and comparator were actually administered, including adherence and fidelity where relevant"},
    "24b": {"section": "RESULTS", "title": "Report concomitant care received during the trial for each group"},
    "25": {"section": "RESULTS", "title": "Provide baseline demographic and clinical characteristics for each group"},
    "26": {"section": "RESULTS", "title": "For each primary and secondary outcome, report analysed and available-data counts, group results, effect estimates, and precision"},
    "27": {"section": "RESULTS", "title": "Report all important harms or unintended effects in each group"},
    "28": {"section": "RESULTS", "title": "Report ancillary analyses and distinguish prespecified from post-hoc analyses"},
    "29": {"section": "DISCUSSION", "title": "Interpret results consistently with the evidence, balancing benefits and harms and considering other evidence"},
    "30": {"section": "DISCUSSION", "title": "Discuss trial limitations, including potential bias, imprecision, generalisability, and multiplicity where relevant"},
}

SECTION_LABELS = {
    "TITLE_ABSTRACT": "Title & abstract",
    "OPEN_SCIENCE": "Open science",
    "INTRODUCTION": "Introduction",
    "METHODS": "Methods",
    "RESULTS": "Results",
    "DISCUSSION": "Discussion",
}

_FULL_VALUES = {"2", "FULL", "FULLY_REPORTED", "YES", "TRUE", "Y", "F"}
_PARTIAL_VALUES = {"1", "PARTIAL", "PARTIALLY_REPORTED", "P"}
_NO_VALUES = {"0", "NO", "NOT_REPORTED", "N", "FALSE"}
_NA_VALUES = {"NA", "N/A", "NOT_APPLICABLE", "NOT APPLICABLE"}


@dataclass
class FlowDiagramArm:
    """Participant counts for one trial arm."""
    arm_name: str = "Intervention"
    allocated: int = 100
    received_allocated_intervention: int = 98
    did_not_receive_intervention: int = 2
    did_not_receive_reasons: List[str] = field(default_factory=list)
    lost_to_followup: int = 3
    lost_to_followup_reasons: List[str] = field(default_factory=list)
    discontinued_intervention: int = 5
    discontinued_reasons: List[str] = field(default_factory=list)
    analysed_for_primary_outcome: int = 95
    excluded_from_analysis: int = 5
    excluded_from_analysis_reasons: List[str] = field(default_factory=list)


@dataclass
class FlowDiagramCounts:
    """Participant-flow counts across enrolment, allocation, follow-up, and analysis."""
    assessed_for_eligibility: int = 250
    excluded_total: int = 50
    excluded_not_meeting_criteria: int = 35
    excluded_declined_consent: int = 10
    excluded_other_reasons: int = 5
    randomised_total: int = 200
    arms: List[FlowDiagramArm] = field(default_factory=list)


@dataclass
class FlowValidationResult:
    """Arithmetic and internal-consistency checks for reported participant flow."""
    is_mathematically_conserved: bool
    enrollment_discrepancy: int
    allocation_discrepancy: int
    arm_discrepancies: List[Dict[str, Any]] = field(default_factory=list)
    analysis_coverage_ratio: float = 0.0
    intention_to_treat_ratio: float = 0.0
    validation_flags: List[str] = field(default_factory=list)


@dataclass
class SectionScore:
    """Repository-defined reporting completion summary for one checklist section."""
    section_name: str
    points_awarded: int
    points_max: int
    completion_percentage: float
    compliance_percentage: float
    items_fully_reported: int
    items_partially_reported: int
    items_not_reported: int
    items_not_applicable: int


@dataclass
class RiskOfBiasDomainEvaluation:
    """Deprecated v2 compatibility type; v3 does not populate this type."""
    domain_id: str
    domain_title: str
    items_evaluated: List[str]
    domain_score_percentage: float
    risk_level: str
    concerns: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ConsortAuditReport:
    """Structured CONSORT 2025 reporting-completeness report."""
    trial_id: str
    trial_title: str
    standard_version: str
    timestamp_utc: str
    overall_completion_percentage: float
    overall_compliance_percentage: float
    reporting_completeness_band: str
    overall_quality_tier: str
    total_points_awarded: int
    total_points_max: int
    section_scores: Dict[str, SectionScore]
    flow_validation: Optional[FlowValidationResult]
    risk_of_bias_evaluation: List[RiskOfBiasDomainEvaluation]
    actionable_remediation_items: List[Dict[str, Any]]
    methodological_note: str = METHODOLOGICAL_NOTE

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class ConsortEvaluatorEngine:
    """Evaluate CONSORT 2025 reporting completion and participant-flow arithmetic."""

    @staticmethod
    def normalize_response(value: Any, *, item_key: str = "") -> tuple[int, int, str]:
        if value is None or (isinstance(value, str) and not value.strip()):
            raw = "NO"
        else:
            raw = str(value).upper().strip()

        if raw in _FULL_VALUES:
            return 2, 2, "FULLY_REPORTED"
        if raw in _PARTIAL_VALUES:
            return 1, 2, "PARTIALLY_REPORTED"
        if raw in _NO_VALUES:
            return 0, 2, "NOT_REPORTED"
        if raw in _NA_VALUES:
            return 0, 0, "NOT_APPLICABLE"

        prefix = f" for CONSORT item {item_key}" if item_key else ""
        raise ValueError(
            f"Invalid checklist response{prefix}: {value!r}. "
            "Use FULL, PARTIAL, NO, or NA."
        )

    @classmethod
    def evaluate_checklist_responses(
        cls,
        responses: Dict[str, Any],
        trial_id: str = "TRIAL-001",
        trial_title: str = "Randomised Controlled Trial Assessment",
        flow_counts: Optional[FlowDiagramCounts] = None,
    ) -> ConsortAuditReport:
        unknown_items = sorted(set(responses) - set(CONSORT_TAXONOMY))
        if unknown_items:
            raise ValueError(f"Unknown CONSORT 2025 item key(s): {', '.join(unknown_items)}")

        section_groups: Dict[str, List[Dict[str, Any]]] = {}
        remediation_items: List[Dict[str, Any]] = []
        total_awarded = 0
        total_max = 0

        for item_key, item_info in CONSORT_TAXONOMY.items():
            section = item_info["section"]
            section_groups.setdefault(section, [])
            points, max_points, status = cls.normalize_response(
                responses.get(item_key), item_key=item_key
            )

            if status in {"PARTIALLY_REPORTED", "NOT_REPORTED"}:
                remediation_items.append(
                    {
                        "item": item_key,
                        "title": item_info["title"],
                        "section": section,
                        "status": status,
                        "deficiency": (
                            "Reporting is incomplete; add the information required by this CONSORT 2025 item."
                            if status == "PARTIALLY_REPORTED"
                            else "This CONSORT 2025 reporting item was not reported."
                        ),
                    }
                )

            item_record = {
                "item": item_key,
                "title": item_info["title"],
                "section": section,
                "points": points,
                "max_points": max_points,
                "status": status,
            }
            section_groups[section].append(item_record)
            total_awarded += points
            total_max += max_points

        section_score_map: Dict[str, SectionScore] = {}
        for section_name, items in section_groups.items():
            awarded = sum(item["points"] for item in items)
            maximum = sum(item["max_points"] for item in items)
            percentage = round((awarded / maximum * 100.0) if maximum else 100.0, 1)
            section_score_map[section_name] = SectionScore(
                section_name=section_name,
                points_awarded=awarded,
                points_max=maximum,
                completion_percentage=percentage,
                compliance_percentage=percentage,
                items_fully_reported=sum(i["status"] == "FULLY_REPORTED" for i in items),
                items_partially_reported=sum(i["status"] == "PARTIALLY_REPORTED" for i in items),
                items_not_reported=sum(i["status"] == "NOT_REPORTED" for i in items),
                items_not_applicable=sum(i["status"] == "NOT_APPLICABLE" for i in items),
            )

        overall = round((total_awarded / total_max * 100.0) if total_max else 0.0, 1)
        if overall >= 85.0:
            band = "HIGH_COMPLETENESS"
        elif overall >= 65.0:
            band = "MODERATE_COMPLETENESS"
        else:
            band = "LOW_COMPLETENESS"

        flow_result = cls.validate_participant_flow(flow_counts) if flow_counts else None

        return ConsortAuditReport(
            trial_id=str(trial_id),
            trial_title=str(trial_title),
            standard_version=STANDARD_VERSION,
            timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            overall_completion_percentage=overall,
            overall_compliance_percentage=overall,
            reporting_completeness_band=band,
            overall_quality_tier=band,
            total_points_awarded=total_awarded,
            total_points_max=total_max,
            section_scores=section_score_map,
            flow_validation=flow_result,
            risk_of_bias_evaluation=[],
            actionable_remediation_items=remediation_items,
        )

    @classmethod
    def evaluate_rob_domains(cls, _rob_groups: Dict[str, List[Dict[str, Any]]]) -> List[RiskOfBiasDomainEvaluation]:
        """Deprecated compatibility method; deliberately returns no RoB 2 judgements."""
        return []

    @staticmethod
    def _count_is_valid(value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0

    @classmethod
    def validate_participant_flow(cls, flow: FlowDiagramCounts) -> FlowValidationResult:
        """Check reported participant-flow counts for arithmetic consistency."""
        flags: List[str] = []
        arm_issues: List[Dict[str, Any]] = []

        top_level = {
            "assessed_for_eligibility": flow.assessed_for_eligibility,
            "excluded_total": flow.excluded_total,
            "excluded_not_meeting_criteria": flow.excluded_not_meeting_criteria,
            "excluded_declined_consent": flow.excluded_declined_consent,
            "excluded_other_reasons": flow.excluded_other_reasons,
            "randomised_total": flow.randomised_total,
        }
        for name, value in top_level.items():
            if not cls._count_is_valid(value):
                flags.append(f"Invalid count: {name} must be a non-negative integer (got {value!r}).")

        calc_excluded = (
            flow.excluded_not_meeting_criteria
            + flow.excluded_declined_consent
            + flow.excluded_other_reasons
        )
        if calc_excluded != flow.excluded_total:
            flags.append(
                f"Enrollment mismatch: exclusion subcategories sum to {calc_excluded}, "
                f"but excluded_total is {flow.excluded_total}."
            )

        enrollment_discrepancy = flow.assessed_for_eligibility - (
            flow.randomised_total + flow.excluded_total
        )
        if enrollment_discrepancy:
            flags.append(
                f"Enrollment mismatch: assessed ({flow.assessed_for_eligibility}) != "
                f"randomised ({flow.randomised_total}) + excluded ({flow.excluded_total}); "
                f"difference {enrollment_discrepancy}."
            )

        sum_allocated = sum(arm.allocated for arm in flow.arms)
        allocation_discrepancy = flow.randomised_total - sum_allocated
        if allocation_discrepancy:
            flags.append(
                f"Allocation mismatch: randomised ({flow.randomised_total}) != "
                f"sum of arm allocations ({sum_allocated}); difference {allocation_discrepancy}."
            )

        total_analysed = 0
        total_allocated = 0
        for index, arm in enumerate(flow.arms, start=1):
            arm_name = arm.arm_name or f"Arm {index}"
            counts = {
                "allocated": arm.allocated,
                "received_allocated_intervention": arm.received_allocated_intervention,
                "did_not_receive_intervention": arm.did_not_receive_intervention,
                "lost_to_followup": arm.lost_to_followup,
                "discontinued_intervention": arm.discontinued_intervention,
                "analysed_for_primary_outcome": arm.analysed_for_primary_outcome,
                "excluded_from_analysis": arm.excluded_from_analysis,
            }
            for name, value in counts.items():
                if not cls._count_is_valid(value):
                    msg = f"Arm '{arm_name}': {name} must be a non-negative integer (got {value!r})."
                    flags.append(msg)
                    arm_issues.append({"arm": arm_name, "issue": msg})

            total_allocated += arm.allocated
            total_analysed += arm.analysed_for_primary_outcome

            if arm.allocated != arm.received_allocated_intervention + arm.did_not_receive_intervention:
                msg = (
                    f"Arm '{arm_name}': allocated ({arm.allocated}) != received "
                    f"({arm.received_allocated_intervention}) + did not receive "
                    f"({arm.did_not_receive_intervention})."
                )
                flags.append(msg)
                arm_issues.append({"arm": arm_name, "issue": msg})

            if arm.analysed_for_primary_outcome > arm.allocated:
                msg = (
                    f"Arm '{arm_name}': analysed ({arm.analysed_for_primary_outcome}) "
                    f"exceeds allocated ({arm.allocated})."
                )
                flags.append(msg)
                arm_issues.append({"arm": arm_name, "issue": msg})

            if arm.excluded_from_analysis > arm.allocated:
                msg = (
                    f"Arm '{arm_name}': excluded from analysis ({arm.excluded_from_analysis}) "
                    f"exceeds allocated ({arm.allocated})."
                )
                flags.append(msg)
                arm_issues.append({"arm": arm_name, "issue": msg})

            if arm.analysed_for_primary_outcome + arm.excluded_from_analysis > arm.allocated:
                msg = (
                    f"Arm '{arm_name}': analysed + excluded from analysis "
                    f"({arm.analysed_for_primary_outcome + arm.excluded_from_analysis}) "
                    f"exceeds allocated ({arm.allocated})."
                )
                flags.append(msg)
                arm_issues.append({"arm": arm_name, "issue": msg})

        analysis_ratio = (total_analysed / total_allocated) if total_allocated > 0 else 0.0
        analysis_ratio = round(analysis_ratio, 4)

        return FlowValidationResult(
            is_mathematically_conserved=not flags,
            enrollment_discrepancy=enrollment_discrepancy,
            allocation_discrepancy=allocation_discrepancy,
            arm_discrepancies=arm_issues,
            analysis_coverage_ratio=analysis_ratio,
            intention_to_treat_ratio=analysis_ratio,
            validation_flags=flags,
        )

    @classmethod
    def evaluate_batch_csv(cls, csv_text: str) -> List[ConsortAuditReport]:
        """Evaluate a CSV where each row is one CONSORT 2025 checklist."""
        reader = csv.DictReader(io.StringIO(csv_text))
        if reader.fieldnames is None:
            raise ValueError("CSV input is missing a header row.")

        reports: List[ConsortAuditReport] = []
        for row_number, row in enumerate(reader, start=2):
            trial_id = (row.get("trial_id") or f"TRIAL-{row_number - 1}").strip()
            trial_title = (row.get("trial_title") or "Evaluated Clinical Trial").strip()
            responses: Dict[str, Any] = {}
            for item_key in CONSORT_TAXONOMY:
                if item_key in row:
                    responses[item_key] = row[item_key]
                elif f"item_{item_key}" in row:
                    responses[item_key] = row[f"item_{item_key}"]

            try:
                report = cls.evaluate_checklist_responses(
                    responses=responses,
                    trial_id=trial_id,
                    trial_title=trial_title,
                )
            except ValueError as exc:
                raise ValueError(f"CSV row {row_number}: {exc}") from exc
            reports.append(report)

        return reports
