"""
backend/app/core/security.py
============================
Cryptographic security utilities, JWT token encoding/decoding, password hashing,
and Role-Based Access Control (RBAC) dependencies.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.database.session import get_db
from backend.app.database.models.user import UserModel
from backend.app.decision.authorization_gateway import UserRole

import bcrypt

security_bearer = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Computes bcrypt hash of a password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8")[:72], salt).decode("utf-8")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Generates a signed JWT with expiration and user claims."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT signature and expiration."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please re-authenticate.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials / invalid token signature.",
        )


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> Optional[UserModel]:
    """FastAPI dependency yielding authenticated UserModel or None if optional."""
    if not auth:
        return None

    payload = decode_access_token(auth.credentials)
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token payload.",
        )

    user = db.query(UserModel).filter_by(username=username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token not found.",
        )
    return user


def require_role(roles_or_min: Any):
    """Factory dependency enforcing minimum role in hierarchy or membership in allowed roles."""
    hierarchy = {
        UserRole.OBSERVER: 1,
        UserRole.ANALYST: 2,
        UserRole.SENIOR_INCIDENT_COMMANDER: 3,
        "OBSERVER": 1,
        "ANALYST": 2,
        "SENIOR_INCIDENT_COMMANDER": 3,
        "ADMIN": 3,
    }

    def role_checker(user: UserModel = Depends(get_current_user)):
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for this operation.",
            )
        user_role_str = (user.role or "").upper()
        user_role_enum = getattr(UserRole, user_role_str, UserRole.OBSERVER)
        user_level = hierarchy.get(user_role_enum, hierarchy.get(user_role_str, 0))

        if isinstance(roles_or_min, (list, tuple, set)):
            allowed = {r.value.upper() if hasattr(r, "value") else str(r).upper() for r in roles_or_min}
            if user_role_str in allowed or (hasattr(user_role_enum, "value") and user_role_enum.value.upper() in allowed):
                return user
            min_lvl = min((hierarchy.get(r, 99) for r in roles_or_min), default=99)
            if user_level >= min_lvl and min_lvl != 99:
                return user
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of roles {[str(r) for r in roles_or_min]}, but user possesses role {user.role}",
            )
        else:
            required_level = hierarchy.get(roles_or_min, hierarchy.get(getattr(roles_or_min, "name", str(roles_or_min)), 0))
            if user_level < required_level:
                req_name = getattr(roles_or_min, "value", str(roles_or_min))
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Operation requires role {req_name}, but user possesses role {user.role}",
                )
            return user

    return role_checker

