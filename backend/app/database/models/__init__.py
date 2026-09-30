"""
backend/app/database/models/__init__.py
=======================================
Exposes all SQLAlchemy models for clean imports and Alembic migrations.
"""

from backend.app.database.models.user import UserModel
from backend.app.database.models.incident import IncidentModel
from backend.app.database.models.telemetry import SensorStationModel, SensorObservationModel
from backend.app.database.models.model_run import ModelRunModel
from backend.app.database.models.alert import AlertDispatchModel, AlertAcknowledgementModel
from backend.app.database.models.evacuation import EvacuationRouteModel
from backend.app.database.models.audit import AuditLogModel
from backend.app.database.models.risk import RiskStateModel, RiskZoneModel
from backend.app.database.models.ingestion import DataIngestionRunModel, DataQualityRecordModel
from backend.app.database.models.spatial import (
    InfrastructureAssetModel,
    PopulationZoneModel,
    SafeZoneModel,
)
from backend.app.database.models.device import (
    DeviceModel,
    SensorModel,
    CalibrationRecordModel,
    DeviceHeartbeatModel,
)

__all__ = [
    "UserModel",
    "IncidentModel",
    "SensorStationModel",
    "SensorObservationModel",
    "ModelRunModel",
    "AlertDispatchModel",
    "AlertAcknowledgementModel",
    "EvacuationRouteModel",
    "AuditLogModel",
    "RiskStateModel",
    "RiskZoneModel",
    "DataIngestionRunModel",
    "DataQualityRecordModel",
    "InfrastructureAssetModel",
    "PopulationZoneModel",
    "SafeZoneModel",
    "DeviceModel",
    "SensorModel",
    "CalibrationRecordModel",
    "DeviceHeartbeatModel",
]
