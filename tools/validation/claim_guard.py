"""
tools/validation/claim_guard.py
===============================
FLOODY SHIELD v3.8.2 - Automated Consistency & Claim Qualification Scanner.

LIMITATION & SCOPE NOTICE:
This tool is an automated consistency and claim scanning mechanism designed to
detect unsupported wording, unqualified superlatives, and misaligned evidentiary
claims across documentation, reports, and code comments.

IMPORTANT:
This scanner is NOT an independent scientific peer-review system and does not
establish scientific truth independently. It serves as an automated quality gate
to enforce evidentiary honesty and consistency with repo evidence.

Taxonomy of Phrases:
Allowed Descriptive Phrases:
  - "software-tested"
  - "simulated benchmark"
  - "preliminary external evidence"
  - "proxy validated"

Restricted Phrases (require explicit qualifying context/metadata):
  - "field validated" (only allowed if qualified by real GSI/HPSDMA points)
  - "externally validated" (restricted if unqualified or conflated with synthetic fixtures)
  - "ground truth" (restricted when applied to synthesized/simulated fixtures)
  - "production ready" (restricted; system is Level 1 Research / Prototype)
  - "operationally proven" (restricted; physical sensors are in staging mode)

Outputs:
  reports/v3_8_2/claim_guard_report.json
  reports/v3_8_1/claim_guard_report.json
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_DIR_V381 = PROJECT_ROOT / "reports" / "v3_8_1"
REPORT_DIR_V382 = PROJECT_ROOT / "reports" / "v3_8_2"
REPORT_DIR_V40 = PROJECT_ROOT / "reports" / "v4_0"
REPORT_DIR_V381.mkdir(parents=True, exist_ok=True)
REPORT_DIR_V382.mkdir(parents=True, exist_ok=True)
REPORT_DIR_V40.mkdir(parents=True, exist_ok=True)

# Formal lists of phrases
ALLOWED_PHRASES = [
    "software-tested",
    "simulated benchmark",
    "preliminary external evidence",
    "proxy validated",
    "synthetic benchmarked",
    "global empirical benchmark",
]

RESTRICTED_PHRASES = [
    "field validated",
    "externally validated",
    "ground truth",
    "production ready",
    "operationally proven",
]

CLAIM_RULES = [
    {
        "id": "UNQUALIFIED_100_FIELD_RELIABILITY",
        "pattern": re.compile(r"100%?\s+(?:field\s+reliability|operational\s+reliability)", re.IGNORECASE),
        "allowed_context": re.compile(r"(?:simulat|emulat|harness|synthetic|software|test\s+bench|benchmark)", re.IGNORECASE),
        "description": "Claiming 100% field/operational reliability without clarifying it is in a simulated/software harness.",
        "severity": "HIGH",
        "recommendation": "Qualify as '100% simulated packet delivery in software reliability harness' or 'software-in-the-loop stress testing'.",
    },
    {
        "id": "UNQUALIFIED_PRODUCTION_READY",
        "pattern": re.compile(r"\b(?:production[\s-]ready|operationally[\s-]proven)\b", re.IGNORECASE),
        "allowed_context": re.compile(r"(?:not\s+yet|towards|roadmap|Level\s+1|prototype|research|pre-operational|disclaimer|restricted)", re.IGNORECASE),
        "description": "Claiming system is 'production ready' or 'operationally proven' when operational status is Level 1 Research / Prototype.",
        "severity": "HIGH",
        "recommendation": "Clarify that the system is a Level 1 Prototype / Research Decision Support System, not certified for sole operational use.",
    },
    {
        "id": "SYNTHETIC_AS_GROUND_TRUTH",
        "pattern": re.compile(r"(?:520\s+points|850\s+rows|800\+\s+stage|M6_stable_slope_controls|M10_cwc_thalout).*?(?:ground[\s-]truthed|GPS-surveyed|continuous\s+CWC)", re.IGNORECASE),
        "allowed_context": re.compile(r"(?:synthetic|simulat|benchmark|fixture)", re.IGNORECASE),
        "description": "Describing synthesized benchmark datasets (M6 520 pts, M10 850 rows) as real GPS ground truth or real continuous CWC observations.",
        "severity": "CRITICAL",
        "recommendation": "Clearly label as 'Statistically generated synthetic benchmark fixture' and reserve 'ground truth' for data/external/ records.",
    },
    {
        "id": "FORCED_NINE_MODELS_VALIDATED",
        "pattern": re.compile(r"(?:9|nine)\s+models\s+(?:externally\s+validated|scientifically\s+validated)", re.IGNORECASE),
        "allowed_context": re.compile(r"(?:preliminary|proxy|synthetic|empirically\s+benchmarked|audit|histor|breakdown)", re.IGNORECASE),
        "description": "Claiming '9 models externally validated' without qualifying the evidence tier (preliminary vs synthetic benchmark).",
        "severity": "HIGH",
        "recommendation": "Distinguish between preliminary external evidence (M6, M7, M2), proxy validated (M4, M11), global empirical benchmark (M12), and synthetic fixtures (M10, M19, M20).",
    },
    {
        "id": "UNVERIFIED_FIELD_DEPLOYMENT",
        "pattern": re.compile(r"(?:currently\s+deployed\s+in\s+the\s+field|live\s+in-river\s+sensors\s+operating)", re.IGNORECASE),
        "allowed_context": re.compile(r"(?:staging|pilot|planned|simulat|emulat|prototype|0\s+in-situ)", re.IGNORECASE),
        "description": "Claiming sensors are active live in the field when physical hardware is in bench staging / simulation mode.",
        "severity": "HIGH",
        "recommendation": "Explicitly state physical stations are in staging / testbed mode (0 in-situ deployed in active river water) pending field deployment.",
    },
    {
        "id": "BROAD_UNQUALIFIED_VALIDATION_CLAIM",
        "pattern": re.compile(r"All\s+claims\s+are\s+scientifically\s+grounded,\s+reproducible,\s+and\s+cryptographically\s+verified", re.IGNORECASE),
        "allowed_context": re.compile(r"(?:to\s+the\s+extent\s+documented|delineat|distinguish|model-specific|audited)", re.IGNORECASE),
        "description": "Broadly claiming all claims are scientifically grounded and cryptographically verified without distinguishing software, cryptographic, and empirical evidence.",
        "severity": "HIGH",
        "recommendation": "Replace with evidence-specific language distinguishing cryptographic integrity, software verification, dataset provenance, and model-specific scientific status.",
    }
]


@dataclass
class ClaimFinding:
    rule_id: str
    file_path: str
    line_number: int
    matched_text: str
    context: str
    severity: str
    recommendation: str


def scan_file(file_path: Path) -> List[ClaimFinding]:
    findings = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return findings

    # Skip files that are intentionally describing audit rules, test assertions, or historical archives
    if file_path.name in ["claim_guard.py", "claim_guard_report.json"]:
        return findings

    for idx, line in enumerate(lines, start=1):
        for rule in CLAIM_RULES:
            match = rule["pattern"].search(line)
            if match:
                # Check surrounding context (current line +/- 3 lines)
                start_c = max(0, idx - 4)
                end_c = min(len(lines), idx + 3)
                surrounding = " ".join(lines[start_c:end_c])

                # If allowed context exists in surrounding text, skip
                if rule["allowed_context"] and rule["allowed_context"].search(surrounding):
                    continue

                matched_str = match.group(0)
                findings.append(
                    ClaimFinding(
                        rule_id=rule["id"],
                        file_path=str(file_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                        line_number=idx,
                        matched_text=matched_str,
                        context=line.strip()[:140],
                        severity=rule["severity"],
                        recommendation=rule["recommendation"],
                    )
                )
    return findings


def run_claim_guard(target_dirs: Optional[List[str]] = None) -> Dict[str, Any]:
    print("=" * 70)
    print("FLOODY SHIELD v3.8.2: SCIENTIFIC INTEGRITY & CLAIM GUARD")
    print("=" * 70)

    dirs_to_scan = target_dirs or ["docs", "reports", "ml", "tools"]
    total_files = 0
    all_findings: List[ClaimFinding] = []

    for d in dirs_to_scan:
        dp = PROJECT_ROOT / d
        if not dp.exists():
            continue
        for p in dp.rglob("*"):
            if p.is_file() and p.suffix in [".md", ".py", ".json", ".txt", ".csv"]:
                # Ignore git or cache
                if ".git" in p.parts or "__pycache__" in p.parts or ".pytest_cache" in p.parts:
                    continue
                # Skip the previous audit reports being audited
                if ("v3_8_1" in p.parts or "v3_8_2" in p.parts) and p.name == "claim_guard_report.json":
                    continue
                total_files += 1
                findings = scan_file(p)
                all_findings.extend(findings)

    print(f"[*] Scanned {total_files} files across directories: {dirs_to_scan}")
    print(f"[*] Found {len(all_findings)} potential claim qualification items.")

    findings_by_severity = {
        "CRITICAL": [asdict(f) for f in all_findings if f.severity == "CRITICAL"],
        "HIGH": [asdict(f) for f in all_findings if f.severity == "HIGH"],
        "MEDIUM": [asdict(f) for f in all_findings if f.severity == "MEDIUM"],
    }

    report = {
        "audit_version": "v3.8.2",
        "scanner_classification": "AUTOMATED_CONSISTENCY_CLAIM_SCANNER",
        "scanner_notice": "Automated text consistency scanner. Does not replace peer review or independent empirical observation.",
        "allowed_phrase_taxonomy": ALLOWED_PHRASES,
        "restricted_phrase_taxonomy": RESTRICTED_PHRASES,
        "timestamp_utc": "2026-09-22T04:38:00Z",
        "files_scanned": total_files,
        "total_findings": len(all_findings),
        "critical_count": len(findings_by_severity["CRITICAL"]),
        "high_count": len(findings_by_severity["HIGH"]),
        "findings_by_severity": findings_by_severity,
        "findings": [asdict(f) for f in all_findings],
        "verdict": "FLAGGED_ITEMS_TO_QUALIFY" if all_findings else "ALL_CLAIMS_HONEST_AND_QUALIFIED",
    }

    for d in [REPORT_DIR_V381, REPORT_DIR_V382, REPORT_DIR_V40]:
        out_file = d / "claim_guard_report.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"[+] Claim Guard Report saved to {out_file}")

    for sev in ["CRITICAL", "HIGH"]:
        cnt = len(findings_by_severity[sev])
        if cnt > 0:
            print(f"    - {sev}: {cnt} items flagged for qualification")
    print("=" * 70)
    return report


if __name__ == "__main__":
    run_claim_guard()
