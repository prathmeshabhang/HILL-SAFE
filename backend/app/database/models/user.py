"""
backend/app/database/models/user.py
===================================
SQLAlchemy model for Users, Roles, and Authentication Credentials.
Enforces Role-Based Access Control (RBAC) and stores hashed passwords.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict
import uuid

from sqlalchemy import Boolean, Column, DateTime, String
from backend.app.database.session import Base


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(64), nullable=False, unique=True, index=True)
    email = Column(String(128), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="OBSERVER")  # OBSERVER, ANALYST, SENIOR_INCIDENT_COMMANDER, ADMIN
    full_name = Column(String(128), nullable=True)
    agency = Column(String(128), nullable=False, default="HPSDMA / Kullu Civil Defense")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "full_name": self.full_name,
            "agency": self.agency,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
