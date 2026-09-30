from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import ApiError
from app.models import AuditEvent, Membership, User, Workspace
from app.security import decode_access_token

bearer = HTTPBearer(auto_error=False)


@dataclass
class Principal:
    user: User
    workspace: Workspace
    role: str


def get_principal(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> Principal:
    if creds is None or creds.scheme.lower() != "bearer":
        raise ApiError(401, "unauthorized", "Authentication required.")
    payload = decode_access_token(creds.credentials)
    try:
        user_id = uuid.UUID(payload["sub"])
        ws_id = uuid.UUID(payload["ws"])
    except (KeyError, ValueError) as exc:
        raise ApiError(401, "invalid_token", "Invalid access token.") from exc
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise ApiError(401, "invalid_token", "Invalid access token.")
    member = db.scalar(select(Membership).where(Membership.user_id == user_id, Membership.workspace_id == ws_id))
    if member is None:
        raise ApiError(403, "forbidden", "No access to this workspace.")
    ws = db.get(Workspace, ws_id)
    return Principal(user=user, workspace=ws, role=member.role)


def require_editor(p: Principal = Depends(get_principal)) -> Principal:
    if p.role not in ("owner", "editor"):
        raise ApiError(403, "forbidden", "Read-only access.")
    return p


def client_ip(request: Request) -> str:
    # nginx sets X-Real-IP; the API is not exposed directly in Docker deployments
    return request.headers.get("x-real-ip") or (request.client.host if request.client else "unknown")


def audit(db: Session, action: str, *, user: User | None = None, workspace_id: uuid.UUID | None = None, target_type: str | None = None, target_id: str | None = None, ip: str | None = None, **details) -> None:
    db.add(AuditEvent(action=action, user_id=user.id if user else None, workspace_id=workspace_id, target_type=target_type, target_id=target_id, ip=ip, details=details or None))
