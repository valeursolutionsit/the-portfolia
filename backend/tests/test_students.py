from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_student_profile_and_learning_activities() -> None:
    email = f"student-profile-{uuid4()}@example.com"
    payload = {
        "full_name": "Priya Student",
        "email": email,
        "password": "StrongPass123",
        "user_type": "student",
    }

    register = client.post("/api/v1/auth/register", json=payload)
    token = register.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    profile = client.get("/api/v1/students/me", headers=headers)
    assert profile.status_code == 200, profile.text
    assert profile.json()["email"] == email

    profile_update = client.put(
        "/api/v1/students/me",
        json={
            "college_name": "Anna University",
            "course": "B.E. Computer Science",
            "department": "Software Engineering",
            "graduation_year": 2027,
            "career_interests": "Full-stack development",
            "technical_skills": "Python, SQL, FastAPI",
            "bio": "Building practical products and portfolios.",
        },
        headers=headers,
    )
    assert profile_update.status_code == 200, profile_update.text
    assert profile_update.json()["college_name"] == "Anna University"

    activity = client.post(
        "/api/v1/students/learning-activities",
        json={
            "title": "Built project dashboard",
            "category": "software",
            "description": "Created a learning dashboard with evidence and project planning.",
            "duration_hours": 4,
            "evidence_url": "https://example.com/project",
        },
        headers=headers,
    )
    assert activity.status_code == 200, activity.text
    assert activity.json()["title"] == "Built project dashboard"

    activities = client.get("/api/v1/students/learning-activities", headers=headers)
    assert activities.status_code == 200, activities.text
    assert any(item["title"] == "Built project dashboard" for item in activities.json())
