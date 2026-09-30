"""
backend/app/services/ingestion/adapters/base.py
===============================================
Abstract Base Class & Unified Data Contract for FLOODY SHIELD Multi-Source Ingestion.
Enforces normalization, spatial-temporal metadata preservation, provenance tagging,
and deterministic deduplication for heterogeneous field IoT and satellite feeds.
"""

from __future__ import annotations

import abc
import datetime
import hashlib
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.core.provenance import DataMode, normalize_provenance


class NormalizedObservation(BaseModel):
    """
    Authoritative normalized observation contract across all sensor and satellite feeds.
    Preserves raw source fidelity while presenting uniform fields to the ingestion pipeline.
    """
    station_id: str = Field(..., description="Unique station, sensor, scene, or grid cell identifier")
    source_id: str = Field(..., description="Data source code: INSAT_3DS, SMAP, UPPER_BEAS_IOT, IMD_AWS, CWC_RIVER, SENTINEL_COPERNICUS")
    timestamp: datetime.datetime = Field(..., description="Standardized UTC observation timestamp")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS-84 Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS-84 Longitude in decimal degrees")
    elevation_m: Optional[float] = Field(None, description="Station or terrain surface elevation in meters above MSL")
    values: Dict[str, Any] = Field(default_factory=dict, description="Normalized physical measurements and domain variables")
    quality_state: str = Field("FRESH", description="Quality state: FRESH, STALE, EXPIRED, DEGRADED, CRITICAL_ERROR")
    idempotency_hash: str = Field("", description="Deterministic SHA-256 deduplication key")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Data provenance and evidence tier metadata")

    # Enhanced Multi-Source Metadata (Phase 04A)
    source_type: str = Field("SENSOR", description="Source category: SATELLITE, RADAR, AGENCY_AWS, RIVER_GAUGE, IOT_EXTENSOMETER")
    observation_type: str = Field("PHYSICAL_MEASUREMENT", description="Measurement type: PRECIPITATION, WATER_LEVEL, SOIL_MOISTURE, DISPLACEMENT, SAR_INUNDATION")
    acquisition_timestamp: Optional[datetime.datetime] = Field(None, description="Raw sensor/satellite acquisition time before ground processing")
    spatial_extent: Optional[Dict[str, Any]] = Field(None, description="Bounding box or footprint geometry [min_lon, min_lat, max_lon, max_lat]")
    value: Optional[float] = Field(None, description="Primary scalar measurement value if applicable")
    unit: Optional[str] = Field(None, description="Statutory unit of measurement (mm/h, m, cm3/cm3, kPa, etc.)")
    quality: Dict[str, Any] = Field(default_factory=dict, description="Detailed QC metrics, retrieval flags, cloud cover percentage")
    source_status: str = Field("ONLINE", description="Source operational status: ONLINE, DEGRADED, STALE, OFFLINE, UNAVAILABLE")
    raw_reference: Optional[str] = Field(None, description="Upstream raw file URI, granule ID, or LoRa packet sequence number")
    error_info: Optional[str] = Field(None, description="Error diagnostics if record was degraded or rejected")


class DataSourceAdapter(abc.ABC):
    """
    Unified Ingestion Adapter Interface for heterogeneous telemetry and remote sensing feeds.
    Provides standard hooks for payload normalization, deduplication hashing, and provenance stamping.
    """

    def __init__(
        self,
        source_id: str,
        source_type: str = "SENSOR",
        evidence_tier: str = "CONNECTOR_IMPLEMENTED",
        data_mode: str = DataMode.REAL_AGENCY_DATA.value,
    ):
        self.source_id = source_id
        self.source_type = source_type
        self.evidence_tier = evidence_tier
        self.data_mode = data_mode

    @property
    def is_configured(self) -> bool:
        """Indicates whether production external credentials and active network endpoints exist."""
        return False

    @abc.abstractmethod
    def normalize(self, raw_record: Dict[str, Any]) -> NormalizedObservation:
        """Transforms heterogeneous raw external records into canonical internal schema."""
        pass

    def compute_idempotency_hash(
        self,
        station_id: str,
        timestamp: datetime.datetime,
        source_record_id: Optional[str] = None,
    ) -> str:
        """Computes deterministic SHA-256 hash to prevent duplicate ingestion."""
        ts_str = timestamp.isoformat() if isinstance(timestamp, datetime.datetime) else str(timestamp)
        raw_key = f"{self.source_id}:{station_id}:{ts_str}:{source_record_id or ''}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def provenance(self) -> Dict[str, Any]:
        """Returns metadata regarding data source connectivity, provenance mode, and validation tier."""
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "evidence_tier": self.evidence_tier,
            "data_mode": self.data_mode,
            "provenance": self.data_mode,
            "adapter_class": self.__class__.__name__,
            "is_configured": self.is_configured,
            "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
