from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_institution_company_and_investor_profiles() -> None:
    for user_type, payload_name, endpoint in [
        ("college_admin", "Campus Admin", "/api/v1/institutions/me"),
        ("company", "Hiring Company", "/api/v1/companies/me"),
        ("investor", "Angel Investor", "/api/v1/investors/me"),
    ]:
        email = f"{user_type}-{uuid4()}@example.com"
        register = client.post(
            "/api/v1/auth/register",
            json={
                "full_name": payload_name,
                "email": email,
                "password": "StrongPass123",
                "user_type": user_type,
            },
        )
        assert register.status_code == 200, register.text
        token = register.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        update = client.put(
            endpoint,
            json={
                "institution_name": "Madras Institute of Technology",
                "company_name": "Portfolia Labs",
                "investor_name": "Asha Investor",
                "organization_name": "North Star Ventures",
                "focus_areas": "AI, SaaS, climate tech",
                "location": "Chennai",
            },
            headers=headers,
        )
        assert update.status_code == 200, update.text
        assert update.json()["email"] == email
