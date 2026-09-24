#!/usr/bin/env python3
"""Command-line interface for the CONSORT 2025 checklist evaluator."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Dict, Optional

from consort_evaluator import (
    CONSORT_TAXONOMY,
    METHODOLOGICAL_NOTE,
    SECTION_LABELS,
    STANDARD_VERSION,
    ConsortAuditReport,
    ConsortEvaluatorEngine,
    FlowDiagramArm,
    FlowDiagramCounts,
)


def format_report_text(report: ConsortAuditReport) -> str:
    """Format a report for terminal output."""

    lines = [
        "=" * 78,
        f"{STANDARD_VERSION} REPORTING CHECKLIST EVALUATION",
        f"Trial ID: {report.trial_id}",
        f"Title:    {report.trial_title}",
        "=" * 78,
        f"Completion: {report.overall_completion_percentage:.1f}% "
        f"({report.total_points_awarded}/{report.total_points_max} points)",
        f"Band:       {report.reporting_completeness_band.replace('_', ' ').title()}",
        "",
        "SECTION COMPLETION",
    ]

    for section_name, section in report.section_scores.items():
        label = SECTION_LABELS.get(section_name, section_name)
        lines.append(
            f"  {label:<18} {section.completion_percentage:5.1f}% "
            f"({section.points_awarded}/{section.points_max})"
        )

    if report.flow_validation is not None:
        flow = report.flow_validation
        lines.extend(
            [
                "",
                "PARTICIPANT-FLOW ARITHMETIC",
                f"  Consistent: {'yes' if flow.is_mathematically_conserved else 'no'}",
                f"  Analysis coverage: {flow.analysis_coverage_ratio * 100:.1f}% "
                "(analysed / allocated; descriptive only)",
            ]
        )
        for flag in flow.validation_flags:
            lines.append(f"  - {flag}")

    if report.actionable_remediation_items:
        lines.extend(["", "REPORTING GAPS (first 10)"])
        for item in report.actionable_remediation_items[:10]:
            lines.append(f"  - Item {item['item']}: {item['title']} [{item['status']}]")
        remaining = len(report.actionable_remediation_items) - 10
        if remaining > 0:
            lines.append(f"  - ... plus {remaining} additional gaps")

    lines.extend(["", f"Note: {METHODOLOGICAL_NOTE}", "=" * 78])
    return "\n".join(lines)


def _prompt_nonnegative_int(label: str, default: int) -> int:
    while True:
        raw = input(f"{label} [{default}]: ").strip()
        if not raw:
            return default
        try:
            value = int(raw)
        except ValueError:
            print("Enter a non-negative integer.")
            continue
        if value < 0:
            print("Enter a non-negative integer.")
            continue
        return value


def _prompt_arm(name: str, default_allocated: int) -> FlowDiagramArm:
    print(f"\n{name}")
    allocated = _prompt_nonnegative_int("  Allocated", default_allocated)
    received = _prompt_nonnegative_int("  Received allocated intervention", allocated)
    did_not_receive = _prompt_nonnegative_int(
        "  Did not receive allocated intervention", max(allocated - received, 0)
    )
    lost = _prompt_nonnegative_int("  Lost to follow-up", 0)
    discontinued = _prompt_nonnegative_int("  Discontinued intervention", 0)
    analysed = _prompt_nonnegative_int("  Analysed for primary outcome", allocated)
    excluded = _prompt_nonnegative_int("  Excluded from primary analysis", max(allocated - analysed, 0))
    return FlowDiagramArm(
        arm_name=name,
        allocated=allocated,
        received_allocated_intervention=received,
        did_not_receive_intervention=did_not_receive,
        lost_to_followup=lost,
        discontinued_intervention=discontinued,
        analysed_for_primary_outcome=analysed,
        excluded_from_analysis=excluded,
    )


def run_interactive_mode() -> ConsortAuditReport:
    """Prompt through every scored CONSORT 2025 checklist entry."""

    print(f"\n--- Interactive {STANDARD_VERSION} Checklist Evaluator ---")
    trial_id = input("Trial identifier [TRIAL-INTERACTIVE]: ").strip() or "TRIAL-INTERACTIVE"
    trial_title = input("Trial title [Evaluated Randomised Trial]: ").strip() or "Evaluated Randomised Trial"
    print("\nFor each item enter F (full), P (partial), N (not reported), or NA. Blank = N.")

    responses: Dict[str, str] = {}
    current_section = None
    for item_key, info in CONSORT_TAXONOMY.items():
        if info["section"] != current_section:
            current_section = info["section"]
            print(f"\n[{SECTION_LABELS.get(current_section, current_section)}]")
        while True:
            raw = input(f"{item_key:>3}  {info['title']} [F/P/N/NA]: ").strip() or "N"
            try:
                ConsortEvaluatorEngine.normalize_response(raw, item_key=item_key)
            except ValueError as exc:
                print(exc)
                continue
            responses[item_key] = raw
            break

    flow_counts = None
    if input("\nValidate participant-flow arithmetic? [y/N]: ").strip().lower() in {"y", "yes"}:
        assessed = _prompt_nonnegative_int("Assessed for eligibility", 250)
        excluded = _prompt_nonnegative_int("Excluded total", 50)
        not_eligible = _prompt_nonnegative_int("  Excluded: did not meet criteria", 35)
        declined = _prompt_nonnegative_int("  Excluded: declined consent", 10)
        other = _prompt_nonnegative_int("  Excluded: other reasons", max(excluded - not_eligible - declined, 0))
        randomised = _prompt_nonnegative_int("Randomised total", max(assessed - excluded, 0))
        half = randomised // 2
        arms = [_prompt_arm("Intervention", half), _prompt_arm("Comparator", randomised - half)]
        flow_counts = FlowDiagramCounts(
            assessed_for_eligibility=assessed,
            excluded_total=excluded,
            excluded_not_meeting_criteria=not_eligible,
            excluded_declined_consent=declined,
            excluded_other_reasons=other,
            randomised_total=randomised,
            arms=arms,
        )

    return ConsortEvaluatorEngine.evaluate_checklist_responses(
        responses=responses,
        trial_id=trial_id,
        trial_title=trial_title,
        flow_counts=flow_counts,
    )


def run_batch_evaluation(
    input_path: str, output_path: Optional[str] = None, json_format: bool = False
) -> None:
    """Evaluate a checklist CSV and optionally write a summary CSV or full JSON."""

    path = Path(input_path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {input_path}")

    reports = ConsortEvaluatorEngine.evaluate_batch_csv(path.read_text(encoding="utf-8"))
    if output_path:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if json_format or destination.suffix.lower() == ".json":
            destination.write_text(
                json.dumps([report.to_dict() for report in reports], indent=2), encoding="utf-8"
            )
        else:
            fields = [
                "trial_id",
                "trial_title",
                "standard_version",
                "overall_completion_percentage",
                "reporting_completeness_band",
                "total_points_awarded",
                "total_points_max",
                "actionable_remediations_count",
            ]
            with destination.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for report in reports:
                    writer.writerow(
                        {
                            "trial_id": report.trial_id,
                            "trial_title": report.trial_title,
                            "standard_version": report.standard_version,
                            "overall_completion_percentage": report.overall_completion_percentage,
                            "reporting_completeness_band": report.reporting_completeness_band,
                            "total_points_awarded": report.total_points_awarded,
                            "total_points_max": report.total_points_max,
                            "actionable_remediations_count": len(report.actionable_remediation_items),
                        }
                    )
        print(f"Processed {len(reports)} trial(s). Output written to '{destination}'.")
    elif json_format:
        print(json.dumps([report.to_dict() for report in reports], indent=2))
    else:
        for report in reports:
            print(format_report_text(report))
            print()


def _load_responses(value: str) -> Dict[str, str]:
    path = Path(value)
    try:
        if path.is_file():
            parsed = json.loads(path.read_text(encoding="utf-8"))
        else:
            parsed = json.loads(value)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not parse --responses-json: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("--responses-json must contain a JSON object mapping item keys to statuses.")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"{STANDARD_VERSION} reporting checklist evaluator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="subcommand")
    batch = subparsers.add_parser("batch", help="Evaluate multiple trial checklists from CSV")
    batch.add_argument("-i", "--input", required=True, help="Input CSV path")
    batch.add_argument("-o", "--output", help="Output CSV or JSON path")
    batch.add_argument("--json", action="store_true", help="Write/print full JSON reports")

    parser.add_argument("-i", "--interactive", action="store_true", help="Run the interactive checklist")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    parser.add_argument("--csv", help="Evaluate a batch CSV and print results")
    parser.add_argument("--trial-id", default="TRIAL-001", help="Trial identifier")
    parser.add_argument("--title", default="Evaluated Clinical Trial", help="Trial title")
    parser.add_argument("--responses-json", help="JSON object or path containing checklist responses")
    parser.add_argument("--full-compliance", action="store_true", help="Fill every item as FULL (benchmark only)")

    args = parser.parse_args()
    try:
        if args.subcommand == "batch":
            run_batch_evaluation(args.input, args.output, args.json)
            return
        if args.csv:
            run_batch_evaluation(args.csv, None, args.json)
            return
        if args.interactive:
            report = run_interactive_mode()
        else:
            if args.full_compliance:
                responses = {key: "FULL" for key in CONSORT_TAXONOMY}
            elif args.responses_json:
                responses = _load_responses(args.responses_json)
            else:
                responses = {}
            report = ConsortEvaluatorEngine.evaluate_checklist_responses(
                responses=responses,
                trial_id=args.trial_id,
                trial_title=args.title,
            )
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))

    print(report.to_json() if args.json else format_report_text(report))


if __name__ == "__main__":
    main()
