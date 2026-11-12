from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_and_login_flow() -> None:
    email = f"student-{uuid4()}@example.com"
    payload = {
        "full_name": "Asha Student",
        "email": email,
        "password": "StrongPass123",
        "user_type": "student",
    }

    register = client.post("/api/v1/auth/register", json=payload)
    assert register.status_code == 200, register.text
    user = register.json()
    assert user["email"] == email
    assert user["port_id"].startswith("TP")

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": payload["password"]},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    profile = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert profile.status_code == 200, profile.text
    profile_data = profile.json()
    assert profile_data["email"] == email
    assert profile_data["full_name"] == payload["full_name"]


def test_register_endpoint_allows_local_frontend_origin() -> None:
    response = client.options(
        "/api/v1/auth/register",
        headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8080"