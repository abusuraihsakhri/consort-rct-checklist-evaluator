"""
CONSORT 2010 Statement RCT Reporting Checklist Evaluator Package
"""
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

__version__ = "2.0.0"
__all__ = [
    "ConsortEvaluatorEngine",
    "FlowDiagramCounts",
    "FlowDiagramArm",
    "FlowValidationResult",
    "SectionScore",
    "RiskOfBiasDomainEvaluation",
    "ConsortAuditReport",
    "CONSORT_TAXONOMY",
]
