"""Tests for Production Authentication and Role-Based Access Control (RBAC)."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from apps.api.auth import AuthUser, Role, require_role
from apps.api.config import Settings, get_settings
from apps.api.main import create_app


def test_auth_disabled_local_mode() -> None:
    """In default local/demo mode (auth_enabled=False), requests succeed."""
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["auth_enabled"] is False
    assert data["role"] == "admin"
    assert data["current_user"] == "local-dev-user"


def test_auth_enabled_unauthenticated_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When auth is enabled, missing credentials must return HTTP 401."""
    from apps.api import config

    mock_settings = Settings(
        auth_enabled=True,
        admin_api_key="secret-admin-key",
        analyst_api_key="secret-analyst-key",
        viewer_api_key="secret-viewer-key",
        demo_auth_token="demo-token",
    )
    monkeypatch.setattr(config, "get_settings", lambda: mock_settings)

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: mock_settings
    client = TestClient(app)

    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "WWW-Authenticate" in resp.headers


def test_auth_enabled_invalid_credentials_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When auth is enabled, invalid credentials must return HTTP 401."""
    from apps.api import config

    mock_settings = Settings(
        auth_enabled=True,
        admin_api_key="secret-admin-key",
        analyst_api_key="secret-analyst-key",
    )
    monkeypatch.setattr(config, "get_settings", lambda: mock_settings)

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: mock_settings
    client = TestClient(app)

    resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer invalid-token"}
    )
    assert resp.status_code == 401


def test_auth_enabled_bearer_token_authenticated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When auth is enabled, valid Bearer token returns user profile."""
    from apps.api import config

    mock_settings = Settings(
        auth_enabled=True,
        admin_api_key="secret-admin-key",
        analyst_api_key="secret-analyst-key",
    )
    monkeypatch.setattr(config, "get_settings", lambda: mock_settings)

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: mock_settings
    client = TestClient(app)

    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer secret-analyst-key"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["auth_enabled"] is True
    assert data["role"] == "analyst"
    assert data["current_user"] == "analyst-user"


def test_auth_enabled_api_key_header_authenticated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When auth is enabled, valid X-API-Key header returns user profile."""
    from apps.api import config

    mock_settings = Settings(
        auth_enabled=True,
        admin_api_key="secret-admin-key",
    )
    monkeypatch.setattr(config, "get_settings", lambda: mock_settings)

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: mock_settings
    client = TestClient(app)

    resp = client.get("/api/v1/auth/me", headers={"X-API-Key": "secret-admin-key"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "admin"
    assert data["current_user"] == "admin-service"


def test_rbac_role_hierarchy_permission() -> None:
    """Test RBAC role level comparison and permission satisfaction."""
    admin = AuthUser(username="admin", role=Role.ADMIN)
    analyst = AuthUser(username="analyst", role=Role.ANALYST)
    viewer = AuthUser(username="viewer", role=Role.VIEWER)

    # Admin satisfies all roles
    assert admin.role.has_permission(Role.VIEWER) is True
    assert admin.role.has_permission(Role.ANALYST) is True
    assert admin.role.has_permission(Role.ADMIN) is True

    # Analyst satisfies viewer and analyst
    assert analyst.role.has_permission(Role.VIEWER) is True
    assert analyst.role.has_permission(Role.ANALYST) is True
    assert analyst.role.has_permission(Role.ADMIN) is False

    # Viewer only satisfies viewer
    assert viewer.role.has_permission(Role.VIEWER) is True
    assert viewer.role.has_permission(Role.ANALYST) is False
    assert viewer.role.has_permission(Role.ADMIN) is False


def test_rbac_role_restriction_dependency_raises_403() -> None:
    """Test that require_role raises HTTP 403 when role is insufficient."""
    analyst = AuthUser(username="analyst", role=Role.ANALYST)
    admin_checker = require_role(Role.ADMIN)

    with pytest.raises(HTTPException) as exc_info:
        admin_checker(analyst)

    assert exc_info.value.status_code == 403
    assert "Operation requires 'admin' role privileges" in str(exc_info.value.detail)
