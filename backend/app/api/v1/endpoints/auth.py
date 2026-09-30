"""
backend/app/api/v1/endpoints/auth.py
====================================
Authentication REST endpoints: User Login, Token Issuance, and Registration.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_current_user, get_password_hash, verify_password
from backend.app.database.session import get_db
from backend.app.database.models.user import UserModel
from backend.app.database.models.audit import AuditLogModel

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Access Control"])


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8)
    role: str = Field("OBSERVER", description="OBSERVER, ANALYST, SENIOR_INCIDENT_COMMANDER")
    full_name: Optional[str] = None
    agency: Optional[str] = "HPSDMA / Civil Defense"


class UserLoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register", summary="Register new operational user")
def register_user(
    req: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Registers a new user account with hashed password and role assignment."""
    existing = db.query(UserModel).filter((UserModel.username == req.username) | (UserModel.email == req.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email is already registered.",
        )

    user = UserModel(
        id=str(uuid.uuid4()),
        username=req.username,
        email=req.email,
        hashed_password=get_password_hash(req.password),
        role=req.role.upper(),
        full_name=req.full_name,
        agency=req.agency or "HPSDMA",
    )
    db.add(user)
    db.commit()

    return {
        "status": "USER_REGISTERED",
        "user": user.to_dict(),
    }


@router.post("/login", summary="Authenticate user and obtain JWT token")
def login_user(
    req: UserLoginRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Validates user credentials and returns signed JWT access token."""
    user = db.query(UserModel).filter_by(username=req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password credentials.",
        )

    token = create_access_token({"sub": user.username, "role": user.role, "uid": user.id})

    # Log login action to audit
    audit = AuditLogModel(
        id=str(uuid.uuid4()),
        action="USER_LOGIN_SUCCESS",
        actor_id=user.username,
        actor_role=user.role,
        target_entity_type="User",
        target_entity_id=user.id,
        changes="JWT token generated",
    )
    db.add(audit)
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
    }


@router.get("/me", summary="Get authenticated user identity")
def get_current_user_profile(
    user: UserModel = Depends(get_current_user),
) -> Dict[str, Any]:
    """Returns profile of currently authenticated user."""
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return {"user": user.to_dict()}
