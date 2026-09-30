"""
backend/app/database/models/audit.py
====================================
SQLAlchemy model for Tamper-Evident Append-Only Audit Logging.
Enforces human authorization boundaries and action tracking with cryptographic hash chaining.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from typing import Any, Dict, Optional
import uuid

from sqlalchemy import Column, DateTime, String, Text
from backend.app.database.session import Base


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    action = Column(String(64), nullable=False)
    actor_id = Column(String(128), nullable=False)
    actor_role = Column(String(64), nullable=False)  # e.g. COMMANDER, ANALYST, OBSERVER
    target_entity_type = Column(String(64), nullable=False)
    target_entity_id = Column(String(64), nullable=False)
    changes = Column(Text, nullable=True)
    ip_address = Column(String(64), nullable=True)

    # Cryptographic Hash Chaining for Tamper-Evidence
    previous_hash = Column(String(64), nullable=True)
    entry_hash = Column(String(64), nullable=True)

    def __init__(self, **kwargs):
        if "timestamp" not in kwargs or kwargs["timestamp"] is None:
            kwargs["timestamp"] = datetime.datetime.now(datetime.timezone.utc)
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = str(uuid.uuid4())
        super().__init__(**kwargs)

    def compute_hash(self, prev_hash: Optional[str] = None) -> str:
        """Computes SHA-256 hash over record attributes and previous hash."""
        if not self.timestamp:
            self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        if isinstance(self.timestamp, datetime.datetime):
            ts_str = self.timestamp.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            ts_str = str(self.timestamp)[:19].replace(" ", "T")
        payload = {
            "id": self.id,
            "timestamp": ts_str,
            "action": self.action,
            "actor_id": self.actor_id,
            "actor_role": self.actor_role,
            "target_entity_type": self.target_entity_type,
            "target_entity_id": self.target_entity_id,
            "changes": self.changes or "",
            "previous_hash": prev_hash or self.previous_hash or "GENESIS",
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "action": self.action,
            "actor_id": self.actor_id,
            "actor_role": self.actor_role,
            "target_entity_type": self.target_entity_type,
            "target_entity_id": self.target_entity_id,
            "changes": self.changes,
            "ip_address": self.ip_address,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
        }
