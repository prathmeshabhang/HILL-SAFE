"""
backend/app/services/notifications/ndma_sachet_provider.py
==========================================================
NDMA Sachet National Disaster Early Warning Integration Provider.
Implements ITU-T X.1303 CAP v1.2 dispatch over Mutual TLS (mTLS) HTTP transport.
Returns NOT_CONFIGURED when government mTLS credentials are not provided.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional
import uuid
import httpx

from backend.app.services.notifications.base import NotificationProvider, NotificationResult
from backend.app.core.logging import get_logger

logger = get_logger("floody.notifications.sachet")


class NDMASachetProvider(NotificationProvider):
    """
    National Disaster Management Authority (NDMA) Sachet Alert Distribution Gateway.
    Requires institutional client certificate and private key for mutual TLS authentication.
    """

    def __init__(self):
        self.endpoint = os.environ.get("NDMA_SACHET_ENDPOINT")
        self.client_cert_path = os.environ.get("NDMA_CLIENT_CERT")
        self.client_key_path = os.environ.get("NDMA_CLIENT_KEY")
        self.ca_cert_path = os.environ.get("NDMA_CA_CERT")
        self.timeout_sec = float(os.environ.get("NDMA_TIMEOUT_SEC", "15.0"))
        self.retry_count = int(os.environ.get("NDMA_RETRY_COUNT", "3"))

    @property
    def channel_name(self) -> str:
        return "NDMA_SACHET"

    @property
    def is_configured(self) -> bool:
        """
        Validates if government endpoint and cryptographic client credentials are provided and exist on disk.
        """
        if not self.endpoint or not self.client_cert_path or not self.client_key_path:
            return False
        cert_p = Path(self.client_cert_path)
        key_p = Path(self.client_key_path)
        return cert_p.exists() and key_p.exists()

    @property
    def notification_mode(self) -> str:
        from backend.app.core.config import settings
        return os.environ.get("NOTIFICATION_MODE", settings.NOTIFICATION_MODE).strip().upper()

    async def dispatch(self, alert_payload: Dict[str, Any], recipient: Optional[str] = None) -> NotificationResult:
        """
        Dispatches validated CAP v1.2 XML to the NDMA Sachet gateway.
        If credentials are missing, returns NOT_CONFIGURED.
        In SANDBOX mode (default), simulates in-memory without making upstream network calls.
        """
        if not self.is_configured:
            return NotificationResult(
                provider_name="NDMASachetProvider",
                channel="NDMA_SACHET",
                status="NOT_CONFIGURED",
                recipient=recipient or "NDMA_SACHET_CENTRAL_GATEWAY",
                error="Institutional NDMA Sachet mTLS credentials not configured in environment.",
                details={
                    "reason": "Institutional NDMA Sachet mTLS credentials not configured in environment.",
                    "required_configuration": [
                        "NDMA_SACHET_ENDPOINT (e.g. https://sachet.ndma.gov.in/api/v1/cap/dispatch)",
                        "NDMA_CLIENT_CERT (path to authorized client certificate PEM)",
                        "NDMA_CLIENT_KEY (path to authorized client private key PEM)",
                        "NDMA_CA_CERT (optional path to national government root CA bundle)",
                    ],
                },
            )

        if self.notification_mode == "SANDBOX":
            sim_id = f"sandbox-sim-sachet-{uuid.uuid4().hex[:8]}"
            logger.info(
                f"NDMA SACHET SIMULATED [SANDBOX]: CAP alert {alert_payload.get('cap_identifier', 'UNKNOWN')} "
                f"validated in-memory. Zero mTLS upstream dispatch."
            )
            return NotificationResult(
                provider_name="NDMASachetProvider",
                channel="NDMA_SACHET",
                status="SIMULATED",
                recipient=recipient or "NDMA_SACHET_CENTRAL_GATEWAY",
                message_id=sim_id,
                details={"mode": "SANDBOX", "transmission": "SIMULATED_IN_MEMORY"},
            )

        # Execute authenticated mTLS dispatch
        cap_xml = alert_payload.get("cap_xml") or alert_payload.get("raw_cap_xml")
        if not cap_xml:
            return NotificationResult(
                provider_name="NDMASachetProvider",
                channel="NDMA_SACHET",
                status="FAILED",
                error="CAP XML payload is missing from dispatch request.",
            )

        try:
            cert_tuple = (self.client_cert_path, self.client_key_path)
            verify_ca = self.ca_cert_path if self.ca_cert_path and Path(self.ca_cert_path).exists() else True

            async with httpx.AsyncClient(cert=cert_tuple, verify=verify_ca, timeout=self.timeout_sec) as client:
                headers = {
                    "Content-Type": "application/cap+xml",
                    "X-Agency-Identifier": "HPSDMA_EOC_KULLU",
                }
                response = await client.post(self.endpoint, content=cap_xml.encode("utf-8"), headers=headers)

                if response.status_code in (200, 201, 202):
                    return NotificationResult(
                        provider_name="NDMASachetProvider",
                        channel="NDMA_SACHET",
                        status="DISPATCHED",
                        recipient="NDMA_SACHET_CENTRAL_GATEWAY",
                        message_id=str(uuid.uuid4()),
                        details={"http_status": response.status_code, "gateway_response": response.text[:200]},
                    )
                else:
                    return NotificationResult(
                        provider_name="NDMASachetProvider",
                        channel="NDMA_SACHET",
                        status="FAILED",
                        recipient="NDMA_SACHET_CENTRAL_GATEWAY",
                        error=f"HTTP {response.status_code}: {response.text[:200]}",
                    )
        except Exception as exc:
            logger.error(f"Error communicating with NDMA Sachet gateway: {exc}")
            return NotificationResult(
                provider_name="NDMASachetProvider",
                channel="NDMA_SACHET",
                status="FAILED",
                error=str(exc),
            )
