"""Password hashing (Argon2id), JWT access tokens and rotating refresh tokens.

Refresh tokens are opaque random strings; only their SHA-256 is stored. Each use issues a new
token in the same *family* and marks the old one used. Presenting an already-used token is
treated as theft: the whole family is revoked (RFC 6819 §5.2.2.3 / OAuth 2.1 guidance)."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import ApiError
from app.models import RefreshToken, User

_ph = PasswordHasher()  # argon2id, library defaults (RFC 9106 low-memory profile)


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, password)
    except (VerificationError, InvalidHashError):
        return False


_DUMMY_HASH = _ph.hash("timing-equalizer-not-a-password")


def verify_dummy() -> None:
    """Spend the same time as a real verification when the user does not exist."""
    verify_password("x", _DUMMY_HASH)


def create_access_token(user_id: uuid.UUID, workspace_id: uuid.UUID) -> tuple[str, int]:
    s = get_settings()
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=s.access_token_minutes)
    payload = {"sub": str(user_id), "ws": str(workspace_id), "iat": now, "exp": exp, "type": "access", "jti": secrets.token_hex(8)}
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm), s.access_token_minutes * 60


def decode_access_token(token: str) -> dict:
    s = get_settings()
    try:
        payload = jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm], options={"require": ["exp", "sub", "type"]})
    except jwt.ExpiredSignatureError as exc:
        raise ApiError(401, "token_expired", "Access token expired.") from exc
    except jwt.PyJWTError as exc:
        raise ApiError(401, "invalid_token", "Invalid access token.") from exc
    if payload.get("type") != "access":
        raise ApiError(401, "invalid_token", "Invalid access token.")
    return payload


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_refresh_token(db: Session, user: User, family_id: uuid.UUID | None = None) -> str:
    token = secrets.token_urlsafe(48)
    db.add(
        RefreshToken(
            user_id=user.id,
            family_id=family_id or uuid.uuid4(),
            token_hash=_hash_token(token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=get_settings().refresh_token_days),
        )
    )
    return token


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def rotate_refresh_token(db: Session, token: str) -> tuple[User, str]:
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == _hash_token(token)))
    now = datetime.now(timezone.utc)
    if row is None:
        raise ApiError(401, "invalid_refresh_token", "Invalid refresh token.")
    if row.revoked_at is not None or row.used_at is not None:
        # reuse of a rotated token -> revoke the family
        db.execute(update(RefreshToken).where(RefreshToken.family_id == row.family_id, RefreshToken.revoked_at.is_(None)).values(revoked_at=now))
        db.commit()
        raise ApiError(401, "refresh_token_reused", "Refresh token reuse detected; please sign in again.")
    if _aware(row.expires_at) < now:
        raise ApiError(401, "refresh_token_expired", "Refresh token expired.")
    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        raise ApiError(401, "invalid_refresh_token", "Invalid refresh token.")
    row.used_at = now
    new = issue_refresh_token(db, user, family_id=row.family_id)
    db.commit()
    return user, new


def revoke_refresh_family(db: Session, token: str) -> None:
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == _hash_token(token)))
    if row is not None:
        db.execute(update(RefreshToken).where(RefreshToken.family_id == row.family_id, RefreshToken.revoked_at.is_(None)).values(revoked_at=datetime.now(timezone.utc)))
        db.commit()
