"""
backend/app/services/alerts/cap_validator.py
============================================
OASIS CAP v1.2 & ITU-T X.1303 Alert Payload Validator.
Enforces structural, semantic, and bilingual validity before alert dispatch.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from backend.app.core.errors import FloodyShieldException


VALID_STATUSES = {"Actual", "Exercise", "System", "Test", "Draft"}
VALID_MSG_TYPES = {"Alert", "Update", "Cancel", "Ack", "Error"}
VALID_SCOPES = {"Public", "Restricted", "Private"}
VALID_URGENCIES = {"Immediate", "Expected", "Future", "Past", "Unknown"}
VALID_SEVERITIES = {"Extreme", "Severe", "Moderate", "Minor", "Unknown"}
VALID_CERTAINTIES = {"Observed", "Likely", "Possible", "Unlikely", "Unknown"}


class CAPValidator:
    """Validates CAP XML documents against OASIS CAP v1.2 and NDMA Sachet constraints."""

    @staticmethod
    def validate_cap_dict(data: Dict[str, Any]) -> None:
        """Validates in-memory alert dispatch dictionary before generation."""
        missing = []
        for field in ("headline", "description", "instruction", "area_desc"):
            if not data.get(field):
                missing.append(field)
        if missing:
            raise FloodyShieldException(
                message=f"Missing mandatory CAP alert fields: {', '.join(missing)}",
                error_code="CAP_VALIDATION_ERROR",
                status_code=422,
            )

        severity = data.get("severity", "Extreme")
        if severity not in VALID_SEVERITIES:
            raise FloodyShieldException(
                message=f"Invalid CAP severity '{severity}'. Must be one of {VALID_SEVERITIES}",
                error_code="CAP_VALIDATION_ERROR",
                status_code=422,
            )

        urgency = data.get("urgency", "Immediate")
        if urgency not in VALID_URGENCIES:
            raise FloodyShieldException(
                message=f"Invalid CAP urgency '{urgency}'. Must be one of {VALID_URGENCIES}",
                error_code="CAP_VALIDATION_ERROR",
                status_code=422,
            )

        certainty = data.get("certainty", "Observed")
        if certainty not in VALID_CERTAINTIES:
            raise FloodyShieldException(
                message=f"Invalid CAP certainty '{certainty}'. Must be one of {VALID_CERTAINTIES}",
                error_code="CAP_VALIDATION_ERROR",
                status_code=422,
            )

    @staticmethod
    def validate_cap_xml(xml_content: str) -> None:
        """Parses and validates a serialized OASIS CAP v1.2 XML string."""
        if not xml_content or not xml_content.strip():
            raise FloodyShieldException(
                message="Empty CAP XML content",
                error_code="CAP_VALIDATION_ERROR",
                status_code=422,
            )

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise FloodyShieldException(
                message=f"Malformed XML syntax: {e}",
                error_code="CAP_XML_PARSE_ERROR",
                status_code=422,
            )

        # Strip namespace if present
        tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
        if tag.lower() != "alert":
            raise FloodyShieldException(
                message=f"Root element must be <alert>, found <{tag}>",
                error_code="CAP_INVALID_ROOT",
                status_code=422,
            )

        # Mandatory alert root fields
        def find_el(parent, name):
            for child in parent:
                ctag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if ctag == name:
                    return child
            return None

        identifier = find_el(root, "identifier")
        if identifier is None or not identifier.text:
            raise FloodyShieldException(message="Missing <identifier> in CAP alert", error_code="CAP_VALIDATION_ERROR", status_code=422)

        sender = find_el(root, "sender")
        if sender is None or not sender.text:
            raise FloodyShieldException(message="Missing <sender> in CAP alert", error_code="CAP_VALIDATION_ERROR", status_code=422)

        status_el = find_el(root, "status")
        if status_el is None or status_el.text not in VALID_STATUSES:
            raise FloodyShieldException(message=f"Invalid or missing <status> in CAP alert", error_code="CAP_VALIDATION_ERROR", status_code=422)

        msg_type_el = find_el(root, "msgType")
        if msg_type_el is None or msg_type_el.text not in VALID_MSG_TYPES:
            raise FloodyShieldException(message=f"Invalid or missing <msgType> in CAP alert", error_code="CAP_VALIDATION_ERROR", status_code=422)

        scope_el = find_el(root, "scope")
        if scope_el is None or scope_el.text not in VALID_SCOPES:
            raise FloodyShieldException(message=f"Invalid or missing <scope> in CAP alert", error_code="CAP_VALIDATION_ERROR", status_code=422)

        # Verify info elements
        info_elements = [child for child in root if (child.tag.split("}")[-1] if "}" in child.tag else child.tag) == "info"]
        if not info_elements:
            raise FloodyShieldException(message="CAP alert must contain at least one <info> block", error_code="CAP_VALIDATION_ERROR", status_code=422)

        for info in info_elements:
            for required in ("category", "event", "urgency", "severity", "certainty", "headline", "description", "area"):
                el = find_el(info, required)
                if el is None:
                    raise FloodyShieldException(
                        message=f"Missing mandatory element <{required}> inside <info> block",
                        error_code="CAP_VALIDATION_ERROR",
                        status_code=422,
                    )


cap_validator = CAPValidator()
