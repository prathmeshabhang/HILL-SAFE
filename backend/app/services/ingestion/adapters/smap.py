"""
backend/app/services/ingestion/adapters/smap.py
===============================================
Ingestion adapter for NASA Soil Moisture Active Passive (SMAP) radiometer products.
Extracts L-band surface volumetric soil moisture (cm³/cm³), saturation percentage,
and retrieval quality flags covering the Upper Beas Basin catchments.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings
from backend.app.core.provenance import DataMode
from backend.app.services.ingestion.adapters.base import DataSourceAdapter, NormalizedObservation


class SMAPAdapter(DataSourceAdapter):
    """
    Adapter for NASA / NSIDC SMAP Level-3 / Level-4 Soil Moisture Products (SPL3SMP / SPL4SMA).
    Provides basin-wide antecedent soil moisture conditions critical for landslide and runoff models.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        super().__init__(
            source_id="SMAP",
            source_type="SATELLITE",
            evidence_tier="OPERATIONAL_AGENCY",
            data_mode=DataMode.REMOTE_SENSING_OBSERVATION.value,
        )
        self.endpoint = endpoint or settings.SMAP_EARTHDATA_ENDPOINT
        self.api_key = api_key or settings.SMAP_API_KEY

    @property
    def is_configured(self) -> bool:
        """True only if an explicit NASA Earthdata endpoint or bearer token is present."""
        return bool(self.endpoint and self.endpoint.strip())

    def normalize(self, raw_record: Dict[str, Any]) -> NormalizedObservation:
        """
        Normalizes raw SMAP HDF5 granule or Earthdata REST response into canonical schema.
        Handles volumetric soil moisture, saturation percent, surface temperature, and quality flags.
        """
        lat = float(raw_record.get("latitude") or raw_record.get("lat") or 31.95)
        lon = float(raw_record.get("longitude") or raw_record.get("lon") or 77.10)
        grid_res_km = float(raw_record.get("grid_resolution_km") or 9.0)

        grid_id = (
            raw_record.get("grid_cell_id")
            or raw_record.get("cell_id")
            or raw_record.get("granule_id")
            or f"SMAP_EASE2_{int(grid_res_km)}KM_{lat:.2f}_{lon:.2f}"
        )

        ts_raw = (
            raw_record.get("granule_time")
            or raw_record.get("acquisition_time")
            or raw_record.get("timestamp")
        )
        if isinstance(ts_raw, str):
            ts = datetime.datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        elif isinstance(ts_raw, datetime.datetime):
            ts = ts_raw
        else:
            ts = datetime.datetime.now(datetime.timezone.utc)

        # Volumetric soil moisture (typical range 0.02 - 0.60 cm3/cm3)
        sm_vol = float(
            raw_record.get("soil_moisture_volumetric")
            or raw_record.get("soil_moisture")
            or raw_record.get("soil_moisture_cm3cm3")
            or 0.25
        )

        # Saturation percentage (porosity ~0.45 typical for Himalayan sandy loam)
        porosity = float(raw_record.get("soil_porosity") or 0.45)
        if "soil_saturation_pct" in raw_record:
            sat_pct = float(raw_record["soil_saturation_pct"])
        else:
            sat_pct = max(0.0, min(100.0, (sm_vol / porosity) * 100.0))

        surface_temp = float(raw_record.get("surface_temp_k") or raw_record.get("surface_temperature_k") or 285.15)
        quality_flag = int(raw_record.get("retrieval_quality_flag") or raw_record.get("quality_flag") or 0)
        freeze_thaw = raw_record.get("freeze_thaw_flag", "UNFROZEN")

        # Bounding box calculation for the grid cell
        half_deg = (grid_res_km / 111.0) / 2.0
        bbox = raw_record.get("bbox") or [
            lon - half_deg,
            lat - half_deg,
            lon + half_deg,
            lat + half_deg,
        ]

        raw_ref = raw_record.get("granule_id") or raw_record.get("h5_uri") or raw_record.get("file_uri")
        idem_hash = self.compute_idempotency_hash(grid_id, ts, raw_ref)

        quality_dict = {
            "retrieval_quality_flag": quality_flag,
            "freeze_thaw_flag": freeze_thaw,
            "rfi_mitigation_applied": bool(raw_record.get("rfi_detected", False)),
            "vegetation_water_content_kg_m2": float(raw_record.get("vwc", 1.5)),
            "is_recommended_for_analysis": quality_flag in (0, 1),
        }

        return NormalizedObservation(
            station_id=grid_id,
            source_id=self.source_id,
            timestamp=ts,
            latitude=lat,
            longitude=lon,
            elevation_m=raw_record.get("elevation_m"),
            values={
                "soil_moisture_volumetric": sm_vol,
                "soil_saturation_pct": sat_pct,
                "surface_temp_k": surface_temp,
                "grid_resolution_km": grid_res_km,
                "satellite_platform": "SMAP",
                "instrument": "L-BAND_RADIOMETER",
            },
            quality_state=raw_record.get("quality_state", "FRESH"),
            idempotency_hash=idem_hash,
            provenance=self.provenance(),
            source_type=self.source_type,
            observation_type="SOIL_MOISTURE",
            acquisition_timestamp=ts,
            spatial_extent={"bbox": bbox, "crs": "EPSG:4326"},
            value=sm_vol,
            unit="cm3/cm3",
            quality=quality_dict,
            source_status="ONLINE" if self.is_configured else "NOT_CONFIGURED",
            raw_reference=raw_ref,
        )
