from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.deps import Principal, audit, client_ip, get_principal
from app.errors import ApiError
from app.models import Membership, User, Workspace
from app.ratelimit import check_rate
from app.schemas import ErrorResponse, LoginIn, MeOut, MeUpdate, RefreshIn, RegisterIn, TokenOut, WorkspaceSettingsIn
from validation.contact import is_safe_url
from app.security import create_access_token, hash_password, issue_refresh_token, revoke_refresh_family, rotate_refresh_token, verify_dummy, verify_password

router = APIRouter(tags=["auth"], responses={401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}})


def _workspace_for(db: Session, user: User) -> Workspace:
    m = db.scalar(select(Membership).where(Membership.user_id == user.id).order_by(Membership.role))
    if m is None:
        raise ApiError(403, "no_workspace", "The user has no workspace.")
    return db.get(Workspace, m.workspace_id)


def _tokens(db: Session, user: User, refresh: str | None = None) -> TokenOut:
    ws = _workspace_for(db, user)
    access, ttl = create_access_token(user.id, ws.id)
    if refresh is None:
        refresh = issue_refresh_token(db, user)
        db.commit()
    return TokenOut(access_token=access, refresh_token=refresh, expires_in=ttl)


@router.get("/auth/config", summary="Public sign-in options (is self-registration open?)")
def auth_config():
    return {"registration_open": bool(get_settings().allow_registration)}


@router.post("/auth/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED, summary="Create an account and a personal workspace")
def register(body: RegisterIn, request: Request, db: Session = Depends(get_db)):
    s = get_settings()
    check_rate(f"auth:{client_ip(request)}", s.rate_limit_auth_per_minute)
    if not s.allow_registration:
        raise ApiError(403, "registration_disabled", "Self-registration is disabled.")
    if len(body.password) < s.password_min_length:
        raise ApiError(422, "weak_password", f"Password must be at least {s.password_min_length} characters.")
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise ApiError(409, "email_taken", "An account with this e-mail already exists.")
    user = User(email=email, password_hash=hash_password(body.password), display_name=body.display_name, locale=body.locale)
    db.add(user)
    db.flush()
    ws = Workspace(name=f"{body.display_name or email.split('@')[0]}'s workspace", owner_id=user.id)
    db.add(ws)
    db.flush()
    db.add(Membership(workspace_id=ws.id, user_id=user.id, role="owner"))
    audit(db, "auth.register", user=user, workspace_id=ws.id, ip=client_ip(request))
    db.commit()
    return _tokens(db, user)


@router.post("/auth/login", response_model=TokenOut, summary="Sign in")
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    check_rate(f"auth:{client_ip(request)}", get_settings().rate_limit_auth_per_minute)
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None:
        verify_dummy()
        raise ApiError(401, "invalid_credentials", "Invalid e-mail or password.")
    if not verify_password(body.password, user.password_hash) or not user.is_active:
        audit(db, "auth.login_failed", user=user, ip=client_ip(request))
        db.commit()
        raise ApiError(401, "invalid_credentials", "Invalid e-mail or password.")
    audit(db, "auth.login", user=user, ip=client_ip(request))
    db.commit()
    return _tokens(db, user)


@router.post("/auth/refresh", response_model=TokenOut, summary="Rotate the refresh token")
def refresh(body: RefreshIn, request: Request, db: Session = Depends(get_db)):
    check_rate(f"refresh:{client_ip(request)}", get_settings().rate_limit_auth_per_minute * 6)
    user, new_refresh = rotate_refresh_token(db, body.refresh_token)
    return _tokens(db, user, refresh=new_refresh)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke the refresh-token family")
def logout(body: RefreshIn, db: Session = Depends(get_db)):
    revoke_refresh_family(db, body.refresh_token)


def _android_url(ws: Workspace) -> str | None:
    return (ws.settings or {}).get("android_app_url") or get_settings().android_app_url or None


def _me_out(user: User, p: Principal) -> MeOut:
    return MeOut(id=user.id, email=user.email, display_name=user.display_name, locale=user.locale, default_phone_region=user.default_phone_region,
                 workspace_id=p.workspace.id, workspace_name=p.workspace.name, role=p.role, android_app_url=_android_url(p.workspace))


@router.get("/me", response_model=MeOut, summary="Current user and workspace")
def me(p: Principal = Depends(get_principal)):
    return _me_out(p.user, p)


@router.patch("/workspace/settings", response_model=MeOut, summary="Workspace settings (owner only): Android app link")
def update_workspace_settings(body: WorkspaceSettingsIn, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    if p.role != "owner":
        raise ApiError(403, "forbidden", "Only the workspace owner can change these settings.")
    ws = db.get(Workspace, p.workspace.id)
    settings = dict(ws.settings or {})
    raw = (body.android_app_url or "").strip()
    if raw:
        if not raw.lower().startswith("https://") or not is_safe_url(raw):
            raise ApiError(422, "invalid_url", "Use a valid https:// link.")
        settings["android_app_url"] = raw
    else:
        settings.pop("android_app_url", None)
    ws.settings = settings
    db.commit()
    p.workspace = ws
    return _me_out(p.user, p)


@router.patch("/me", response_model=MeOut, summary="Update profile preferences")
def update_me(body: MeUpdate, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    user = db.get(User, p.user.id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit()
    return _me_out(user, p)
