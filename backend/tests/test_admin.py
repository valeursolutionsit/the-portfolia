from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.database import SessionLocal
from backend.app.main import app
from backend.app.models.user import Role, User

client = TestClient(app)


def register_user(user_type: str = "student") -> tuple[dict, dict[str, str]]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Admin Panel Test",
            "email": f"admin-panel-{uuid4()}@example.com",
            "password": "StrongPass123",
            "user_type": user_type,
        },
    )
    assert response.status_code == 200, response.text
    result = response.json()
    return result, {"Authorization": f"Bearer {result['access_token']}"}


def grant_admin(user_id: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        role = db.query(Role).filter(Role.name == "admin").first()
        assert user is not None
        assert role is not None
        user.user_type = "admin"
        user.roles.append(role)
        db.commit()
    finally:
        db.close()


def test_admin_panel_is_protected_and_manages_platform_records() -> None:
    assert client.get("/api/v1/admin/dashboard").status_code == 401
    student, student_headers = register_user()
    assert client.get("/api/v1/admin/dashboard", headers=student_headers).status_code == 403

    administrator, admin_headers = register_user()
    grant_admin(administrator["user_id"])

    dashboard = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert dashboard.status_code == 200, dashboard.text
    assert dashboard.json()["users_total"] >= 2

    users = client.get("/api/v1/admin/users?q=admin-panel", headers=admin_headers)
    assert users.status_code == 200, users.text
    assert any(item["id"] == student["user_id"] for item in users.json()["items"])
    updated = client.patch(
        f"/api/v1/admin/users/{student['user_id']}",
        json={"is_verified": True},
        headers=admin_headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["is_verified"] is True

    company = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Admin Managed Company",
            "email": f"managed-company-{uuid4()}@example.com",
            "password": "StrongPass123",
            "user_type": "company",
        },
    )
    assert company.status_code == 200
    opportunity_response = client.post(
        "/api/v1/opportunities",
        json={
            "title": "Admin reviewed role",
            "organization": "Admin test",
            "category": "job",
            "description": "A test opportunity",
        },
        headers={"Authorization": f"Bearer {company.json()['access_token']}"},
    )
    assert opportunity_response.status_code == 201, opportunity_response.text
    hidden = client.patch(
        f"/api/v1/admin/opportunities/{opportunity_response.json()['id']}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert hidden.status_code == 200, hidden.text
    assert hidden.json()["is_active"] is False

    ticket = client.post(
        "/api/v1/support/tickets",
        json={"category": "technical", "subject": "Admin panel support", "message": "Please review this issue"},
        headers=student_headers,
    )
    assert ticket.status_code == 201
    ticket_id = ticket.json()["id"]
    response = client.post(
        f"/api/v1/admin/support/tickets/{ticket_id}/responses",
        json={"message": "We received your request."},
        headers=admin_headers,
    )
    assert response.status_code == 201, response.text
    closed = client.patch(
        f"/api/v1/admin/support/tickets/{ticket_id}",
        json={"status": "closed"},
        headers=admin_headers,
    )
    assert closed.status_code == 200
    detail = client.get(f"/api/v1/admin/support/tickets/{ticket_id}", headers=admin_headers)
    assert detail.status_code == 200
    assert len(detail.json()["messages"]) == 2

    activity = client.get("/api/v1/admin/activity", headers=admin_headers)
    assert activity.status_code == 200
    assert any(item["action"] == "admin.support.responded" for item in activity.json()["items"])


def test_admin_registration_requires_configured_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "admin_registration_key", "test-admin-registration-key-2026")
    payload = {
        "full_name": "New Admin",
        "email": f"new-admin-{uuid4()}@example.com",
        "password": "StrongAdminPass123!",
        "registration_key": "test-admin-registration-key-2026",
    }
    response = client.post("/api/v1/auth/register-admin", json=payload)
    assert response.status_code == 200, response.text
    assert "HttpOnly" in response.headers["set-cookie"]
    profile = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {response.json()['access_token']}"},
    )
    assert profile.status_code == 200
    assert profile.json()["user_type"] == "admin"

    wrong_key = {**payload, "email": f"invalid-admin-{uuid4()}@example.com", "registration_key": "wrong-admin-registration-key"}
    rejected = client.post("/api/v1/auth/register-admin", json=wrong_key)
    assert rejected.status_code == 403
