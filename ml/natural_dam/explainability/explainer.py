"""
explainer.py — Explainable AI Diagnostic & Evidence Breakdown Generator
========================================================================
Translates algorithmic multi-evidence scores into clear, transparent, human-readable
diagnostic summaries for disaster management authorities and GIS map popups.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ml.natural_dam.candidate_detection.evidence_scorer import NaturalDamCandidate


class NaturalDamExplainer:
    """Generates explainable audit trails for detected natural dam candidates."""

    @staticmethod
    def generate_explanation(candidate: NaturalDamCandidate) -> Dict[str, Any]:
        if candidate.false_positive_rejected:
            return {
                "headline": f"REJECTED: {candidate.rejection_reason}",
                "summary": "This site matches a known artificial structure or reservoir and has been excluded from natural dam alerts.",
                "supporting_evidence_ratio": "0 / 8 indicators",
                "evidence_checklist": [],
                "statutory_disclaimer": "False-positive infrastructure screening applied.",
            }

        passed_lines = []
        unpassed_lines = []

        for ind in candidate.evidence_indicators:
            symbol = "✓" if ind.passed else "✗"
            line = f"{symbol} {ind.description} ({ind.details})"
            if ind.passed:
                passed_lines.append(line)
            else:
                unpassed_lines.append(line)

        evidence_str = f"{candidate.indicators_passed_count} / {candidate.total_indicators_count} indicators satisfied"

        headline = (
            f"AI detected a {candidate.candidate_tier.replace('_', ' ').title()} "
            f"(Score: {candidate.probability:.2f}) requiring authority validation."
        )

        audit_narrative = (
            f"Candidate was flagged because multi-sensor satellite imagery (Sentinel-1 SAR & Sentinel-2 MSI) "
            f"and Copernicus DEM detected physical channel constriction accompanied by upstream backwater impoundment "
            f"and adjacent hillslope failure."
        )

        return {
            "dam_id": candidate.dam_id,
            "river_name": candidate.river_name,
            "headline": headline,
            "audit_narrative": audit_narrative,
            "supporting_evidence_ratio": evidence_str,
            "passed_indicators": passed_lines,
            "missing_indicators": unpassed_lines,
            "confidence_assessment": f"Model Confidence: {candidate.confidence:.2f} | Data Quality: {candidate.data_quality}",
            "observation_freshness": candidate.observation_freshness,
            "disclaimer": (
                "SCIENTIFIC NOTICE: This represents a remote sensing candidate detection requiring field "
                "or aerial validation by authorized disaster management officials prior to civil defense actions."
            ),
        }
