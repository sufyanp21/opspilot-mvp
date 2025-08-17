from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .audit.log_helper import auditlog
from .db import get_session_optional
from .security.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    User,
)


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    email: str
    roles: list[str]


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db=Depends(get_session_optional)) -> Any:
    # Demo: Accept two static users via env/seed in future; here we allow any email with password "demo".
    if payload.password != "demo":
        auditlog(db, action="auth_failure", actor_email=payload.email, details={"reason": "bad_password"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    # Assign roles by email suffix for demo; admin if endswith "+admin" before domain
    roles = ["analyst"]
    if "+admin@" in payload.email:
        roles.append("admin")
    subject = {"sub": payload.email, "email": payload.email, "roles": roles}
    access = create_access_token(subject)
    refresh = create_refresh_token(subject)
    if db is not None:
        auditlog(db, action="auth_success", actor_email=payload.email, details={"roles": roles})
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user from token.
    """
    return {"email": current_user.email, "roles": current_user.roles}


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db=Depends(get_session_optional)) -> Any:
    data = verify_token(payload.refresh_token, expected_type="refresh")
    subject = {"sub": data["sub"], "email": data.get("email"), "roles": data.get("roles", [])}
    access = create_access_token(subject)
    refresh = create_refresh_token(subject)
    if db is not None:
        auditlog(db, action="auth_refresh", actor_email=subject.get("email"))
    return TokenResponse(access_token=access, refresh_token=refresh)


