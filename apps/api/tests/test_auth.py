from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt


def test_health(client):
    assert client.get("/api/v1/health").json() == {"status": "ok"}
    r = client.get("/api/v1/health/ready")
    body = r.json()
    assert body["checks"]["database"]["ok"] is True
    assert body["checks"]["storage"]["ok"] is True


def test_register_login_me(client):
    r = client.post("/api/v1/auth/register", json={"email": "Carol@Example.com", "password": "correct horse battery", "locale": "ar"})
    assert r.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": "carol@example.com", "password": "correct horse battery"})
    assert login.status_code == 200
    me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"}).json()
    assert me["email"] == "carol@example.com"
    assert me["locale"] == "ar"
    assert me["role"] == "owner"


def test_duplicate_email_and_weak_password(client, alice):
    assert client.post("/api/v1/auth/register", json={"email": alice["email"], "password": "correct horse battery"}).status_code == 409
    r = client.post("/api/v1/auth/register", json={"email": "weak@example.com", "password": "short"})
    assert r.status_code == 422


def test_wrong_password_is_generic(client, alice):
    r = client.post("/api/v1/auth/login", json={"email": alice["email"], "password": "wrong password!!"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "invalid_credentials"
    r2 = client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "wrong password!!"})
    assert r2.json()["error"]["code"] == "invalid_credentials"  # no user enumeration


def test_password_is_hashed(client, alice):
    from app.db import get_sessionmaker
    from app.models import User
    from sqlalchemy import select

    with get_sessionmaker()() as db:
        u = db.scalar(select(User).where(User.email == alice["email"]))
        assert u.password_hash.startswith("$argon2id$")
        assert "correct horse" not in u.password_hash


def test_refresh_rotation_and_reuse_detection(client, alice):
    r1 = client.post("/api/v1/auth/refresh", json={"refresh_token": alice["refresh"]})
    assert r1.status_code == 200
    new_refresh = r1.json()["refresh_token"]
    assert new_refresh != alice["refresh"]
    # replaying the old token = theft signal -> family revoked
    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": alice["refresh"]})
    assert r2.status_code == 401 and r2.json()["error"]["code"] == "refresh_token_reused"
    r3 = client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert r3.status_code == 401


def test_logout_revokes(client, alice):
    assert client.post("/api/v1/auth/logout", json={"refresh_token": alice["refresh"]}).status_code == 204
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": alice["refresh"]}).status_code == 401


def test_requires_auth(client):
    assert client.get("/api/v1/me").status_code == 401
    assert client.get("/api/v1/business-cards").status_code == 401
    assert client.get("/api/v1/me", headers={"Authorization": "Bearer not-a-jwt"}).status_code == 401


def test_tampered_and_expired_tokens(client, alice):
    token = alice["headers"]["Authorization"].split()[1]
    payload = jwt.decode(token, options={"verify_signature": False})
    forged = jwt.encode(payload, "another-secret-another-secret-another-sec", algorithm="HS256")
    assert client.get("/api/v1/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401
    none_alg = jwt.encode(payload, key="", algorithm="none") if hasattr(jwt, "encode") else None
    assert client.get("/api/v1/me", headers={"Authorization": f"Bearer {none_alg}"}).status_code == 401
    payload["exp"] = datetime.now(timezone.utc) - timedelta(minutes=1)
    expired = jwt.encode(payload, "test-secret-test-secret-test-secret-1234", algorithm="HS256")
    r = client.get("/api/v1/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "token_expired"


def test_rate_limit_login(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "rate_limit_auth_per_minute", 3)
    codes = [client.post("/api/v1/auth/login", json={"email": "x@example.com", "password": "whatever-whatever"}).status_code for _ in range(5)]
    assert codes[-1] == 429


def test_update_me_phone_region(client, alice):
    r = client.patch("/api/v1/me", json={"default_phone_region": "ma", "locale": "fr"}, headers=alice["headers"])
    assert r.status_code == 200 and r.json()["default_phone_region"] == "MA"
    assert client.patch("/api/v1/me", json={"default_phone_region": "Morocco"}, headers=alice["headers"]).status_code == 422


def test_openapi_documents_business_cards(client):
    spec = client.get("/api/v1/openapi.json").json()
    paths = spec["paths"]
    for route in ("business-cards",):
        for suffix in ("", "/{doc_id}", "/{doc_id}/images", "/{doc_id}/process", "/{doc_id}/fields", "/{doc_id}/review", "/{doc_id}/export"):
            assert f"/api/v1/{route}{suffix}" in paths
    for p in ("/api/v1/health", "/api/v1/health/ready", "/api/v1/models", "/api/v1/jobs/{job_id}", "/api/v1/me"):
        assert p in paths
