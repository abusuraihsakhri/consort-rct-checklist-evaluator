#!/usr/bin/env python3
"""
Command-Line Interface for CONSORT 2010 RCT Checklist Evaluator & Flow Auditor
Supports interactive checklists, JSON/CSV batch auditing, flow diagram arithmetic, and structured reporting.
"""

import argparse
import json
import sys
import os
from pathlib import Path

# Add parent directory to path if needed
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from consort_evaluator import (
    ConsortEvaluatorEngine,
    FlowDiagramCounts,
    FlowDiagramArm,
    ConsortAuditReport,
    CONSORT_TAXONOMY,
)


def format_report_text(report: ConsortAuditReport) -> str:
    """Format ConsortAuditReport into a human-readable clinical trial audit summary."""
    lines = []
    lines.append("=" * 80)
    lines.append("CONSORT 2010 STATEMENT RCT REPORTING AUDIT REPORT")
    lines.append(f"Trial ID: {report.trial_id:<20} Timestamp UTC: {report.timestamp_utc}")
    lines.append(f"Title:    {report.trial_title}")
    lines.append("=" * 80)

    # 1. Overall Compliance
    lines.append("\n[1] OVERALL COMPLIANCE SUMMARY")
    lines.append(f"  * Composite CONSORT Adherence: {report.overall_compliance_percentage:.1f}% ({report.total_points_awarded} / {report.total_points_max} points)")
    lines.append(f"  * Quality Tier:                >>> {report.overall_quality_tier.replace('_', ' ')} <<<")

    # 2. Sectional Compliance Breakdown
    lines.append("\n[2] SECTION-BY-SECTION COMPLIANCE BREAKDOWN")
    for sec_name, sec in report.section_scores.items():
        bar_len = int(sec.compliance_percentage / 5)
        bar = "#" * bar_len + "-" * (20 - bar_len)
        lines.append(f"  * {sec_name:<16} [{bar}] {sec.compliance_percentage:5.1f}% ({sec.points_awarded:2d}/{sec.points_max:2d} pts) [Full:{sec.items_fully_reported} Part:{sec.items_partially_reported} None:{sec.items_not_reported} NA:{sec.items_not_applicable}]")

    # 3. Cochrane RoB 2.0 Mapping
    lines.append("\n[3] COCHRANE RISK OF BIAS (RoB 2.0) MAPPING")
    for rob in report.risk_of_bias_evaluation:
        lines.append(f"  * {rob.domain_id} ({rob.domain_score_percentage:5.1f}%): >>> {rob.risk_level.replace('_', ' ')} <<<")
        lines.append(f"    {rob.domain_title}")
        if rob.concerns:
            for c in rob.concerns[:3]:
                lines.append(f"      [-] {c}")
        if rob.recommendations:
            for r in rob.recommendations:
                lines.append(f"      [*] {r}")

    # 4. Participant Flow Conservation
    if report.flow_validation:
        f = report.flow_validation
        lines.append("\n[4] CONSORT PARTICIPANT FLOW CONSERVATION ARITHMETIC")
        status = "MATHEMATICALLY CONSERVED" if f.is_mathematically_conserved else "CONSERVATION ANOMALIES DETECTED"
        lines.append(f"  * Status:                      >>> {status} <<<")
        lines.append(f"  * Intention-to-Treat Ratio:    {f.intention_to_treat_ratio * 100:.1f}% analysed of allocated")
        if f.validation_flags:
            for flag in f.validation_flags:
                lines.append(f"    [!] {flag}")

    # 5. Actionable Remediation Items
    if report.actionable_remediation_items:
        lines.append("\n[5] PRIORITY ACTIONABLE REMEDIATIONS (Missing/Partial Items)")
        for rem in report.actionable_remediation_items[:8]:
            lines.append(f"  * [Item {rem['item']:<3}] {rem['title'][:55]}... ({rem['status']})")
        if len(report.actionable_remediation_items) > 8:
            lines.append(f"  * ... plus {len(report.actionable_remediation_items) - 8} more reporting recommendations.")

    lines.append("=" * 80)
    return "\n".join(lines)


def run_interactive_mode() -> ConsortAuditReport:
    """Prompt user interactively through key CONSORT checklist sections."""
    print("\n--- Interactive CONSORT 2010 Checklist Evaluator ---")
    trial_id = input("Trial Identifier [TRIAL-INTERACTIVE]: ").strip() or "TRIAL-INTERACTIVE"
    trial_title = input("Trial Title [Phase 3 Randomized Clinical Trial]: ").strip() or "Phase 3 Randomized Clinical Trial"

    print("\nFor each key item, enter status: [F]ully reported (2 pts), [P]artially reported (1 pt), [N]ot reported (0 pts), or [NA] (Not applicable).")
    
    responses = {}
    key_items = ["1a", "1b", "2a", "2b", "3a", "4a", "5", "6a", "7a", "8a", "8b", "9", "10", "11a", "12a", "13a", "15", "16", "17a", "19", "20", "23", "25"]

    for item_key in key_items:
        info = CONSORT_TAXONOMY[item_key]
        resp = input(f"Item {item_key:<3} ({info['section']:<12}) {info['title'][:45]} [F/p/n/na]: ").strip().upper()
        if not resp or resp.startswith("F") or resp == "2":
            responses[item_key] = "FULL"
        elif resp.startswith("P") or resp == "1":
            responses[item_key] = "PARTIAL"
        elif resp.startswith("NA"):
            responses[item_key] = "NA"
        else:
            responses[item_key] = "NO"

    # Quick flow query
    include_flow = input("\nAudit participant flow diagram numbers? (y/N): ").strip().lower() in ["y", "yes"]
    flow_obj = None
    if include_flow:
        try:
            assessed = int(input("  Assessed for eligibility: ") or "200")
            excluded = int(input("  Excluded total: ") or "40")
            randomised = int(input("  Randomised total: ") or "160")
            arm1_alloc = int(input("  Arm 1 (Intervention) allocated: ") or "80")
            arm1_analysed = int(input("  Arm 1 analysed: ") or "78")
            arm2_alloc = int(input("  Arm 2 (Control) allocated: ") or "80")
            arm2_analysed = int(input("  Arm 2 analysed: ") or "77")

            arm1 = FlowDiagramArm(arm_name="Intervention", allocated=arm1_alloc, received_allocated_intervention=arm1_alloc, analysed_for_primary_outcome=arm1_analysed)
            arm2 = FlowDiagramArm(arm_name="Control", allocated=arm2_alloc, received_allocated_intervention=arm2_alloc, analysed_for_primary_outcome=arm2_analysed)
            flow_obj = FlowDiagramCounts(
                assessed_for_eligibility=assessed,
                excluded_total=excluded,
                randomised_total=randomised,
                arms=[arm1, arm2]
            )
        except ValueError:
            print("Invalid number entered; skipping flow audit.")

    return ConsortEvaluatorEngine.evaluate_checklist_responses(
        responses=responses,
        trial_id=trial_id,
        trial_title=trial_title,
        flow_counts=flow_obj
    )


def main():
    parser = argparse.ArgumentParser(
        description="CONSORT 2010 Statement RCT Reporting Checklist & Flow Evaluator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("-i", "--interactive", action="store_true", help="Launch interactive checklist auditor")
    parser.add_argument("--json", action="store_true", help="Output results in structured JSON format")
    parser.add_argument("--csv", type=str, help="Path to batch CSV file containing trial evaluations")
    parser.add_argument("--trial-id", type=str, default="TRIAL-001", help="Trial identifier")
    parser.add_argument("--title", type=str, default="Evaluated Clinical Trial", help="Trial manuscript title")
    parser.add_argument("--responses-json", type=str, help="JSON string or file path containing item response mappings")
    parser.add_argument("--full-compliance", action="store_true", help="Benchmark: Evaluate with 100% full compliance on all items")

    args = parser.parse_args()

    if args.csv:
        if not os.path.exists(args.csv):
            print(f"Error: CSV file '{args.csv}' not found.", file=sys.stderr)
            sys.exit(1)
        with open(args.csv, "r", encoding="utf-8") as f:
            csv_text = f.read()
        reports = ConsortEvaluatorEngine.evaluate_batch_csv(csv_text)
        if args.json:
            print(json.dumps([r.to_dict() for r in reports], indent=2))
        else:
            for rep in reports:
                print(format_report_text(rep))
                print("\n")
        return

    if args.interactive:
        report = run_interactive_mode()
    else:
        responses = {}
        if args.full_compliance:
            for k in CONSORT_TAXONOMY.keys():
                responses[k] = "FULL"
        elif args.responses_json:
            if os.path.exists(args.responses_json):
                with open(args.responses_json, "r", encoding="utf-8") as f:
                    responses = json.load(f)
            else:
                try:
                    responses = json.loads(args.responses_json)
                except Exception:
                    responses = {}
        else:
            # Default moderate trial responses
            for k in ["1a", "1b", "2a", "2b", "3a", "4a", "5", "6a", "7a", "8a", "9", "11a", "12a", "13a", "15", "16", "17a", "19", "20", "22", "23", "25"]:
                responses[k] = "FULL"
            for k in ["3b", "6b", "8b", "10", "11b", "12b", "13b", "14a", "17b", "18", "21", "24"]:
                responses[k] = "PARTIAL"

        report = ConsortEvaluatorEngine.evaluate_checklist_responses(
            responses=responses,
            trial_id=args.trial_id,
            trial_title=args.title
        )

    if args.json:
        print(report.to_json())
    else:
        print(format_report_text(report))


if __name__ == "__main__":
    main()
