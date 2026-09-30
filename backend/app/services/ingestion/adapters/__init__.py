"""
backend/app/services/ingestion/adapters/__init__.py
===================================================
Exports all data source ingestion adapters.
"""

from backend.app.services.ingestion.adapters.base import DataSourceAdapter, NormalizedObservation
from backend.app.services.ingestion.adapters.weather import IMDAWSAdapter, GPMIMERGAdapter
from backend.app.services.ingestion.adapters.river import CWCRiverAdapter
from backend.app.services.ingestion.adapters.satellite import SentinelSceneAdapter
from backend.app.services.ingestion.adapters.iot import IoTTelemetryAdapter
from backend.app.services.ingestion.adapters.insat3ds import INSAT3DSAdapter
from backend.app.services.ingestion.adapters.smap import SMAPAdapter

__all__ = [
    "DataSourceAdapter",
    "NormalizedObservation",
    "IMDAWSAdapter",
    "GPMIMERGAdapter",
    "CWCRiverAdapter",
    "SentinelSceneAdapter",
    "IoTTelemetryAdapter",
    "INSAT3DSAdapter",
    "SMAPAdapter",
]
