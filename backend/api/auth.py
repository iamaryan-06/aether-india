"""
auth.py — Authentication utilities and FastAPI dependencies for AETHER INDIA.

Implements:
  - SHA-256 + salt password hashing (identical to seed.py)
  - JWT token generation & decoding (PyJWT)
  - FastAPI Depends for get_current_user, get_current_admin, get_optional_user
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import User

load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────────
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "aether_secret_key_jwt_dev_super_safe_token_2024")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
DEMO_SALT: str = "AETHER_DEMO_SALT_2024"

security_bearer = HTTPBearer(auto_error=False)


# ── Password Hashing & Verification ───────────────────────────────────────────

def hash_password(password: str) -> str:
    """Deterministic salted SHA-256 hash matching seed.py."""
    return hashlib.sha256(f"{DEMO_SALT}:{password}".encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that a plain password matches the hashed password."""
    return hash_password(plain_password) == hashed_password


# ── JWT Token Utilities ───────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None


# ── FastAPI User Dependencies ─────────────────────────────────────────────────

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> User:
    """
    Authenticate request via Bearer token and return the User record.
    Raises 401 if missing or invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials or not credentials.credentials:
        raise credentials_exception

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    try:
        user_id_int = int(user_id)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id_int, User.is_active == True).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Authenticate that the requesting user has the 'admin' role.
    Raises 403 Forbidden if not an admin.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operations restricted to AETHER Administrators",
        )
    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Optional user dependency: returns User if valid Bearer token provided,
    otherwise returns None without raising an HTTPException.
    Used for chat endpoints that work for both authenticated and guest users.
    """
    if not credentials or not credentials.credentials:
        return None

    payload = decode_access_token(credentials.credentials)
    if not payload:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    try:
        user_id_int = int(user_id)
        return db.query(User).filter(User.id == user_id_int, User.is_active == True).first()
    except (ValueError, Exception):
        return None
