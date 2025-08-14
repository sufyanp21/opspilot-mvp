from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from ..settings import settings


class User(BaseModel):
    user_id: str
    email: str
    roles: List[str]


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def _now_epoch() -> int:
    return int(time.time())


def create_access_token(payload: Dict[str, Any]) -> str:
    now = _now_epoch()
    body = {
        **payload,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + settings.access_token_ttl,
    }
    return jwt.encode(body, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(payload: Dict[str, Any]) -> str:
    now = _now_epoch()
    body = {
        **payload,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + settings.refresh_token_ttl,
    }
    return jwt.encode(body, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
    try:
        decoded = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if expected_type and decoded.get("type") != expected_type:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        return decoded
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    data = verify_token(token, expected_type="access")
    return User(user_id=data["sub"], email=data.get("email", ""), roles=data.get("roles", []))


def require_roles(*required_roles: str):
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if not any(r in user.roles for r in required_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return dependency



