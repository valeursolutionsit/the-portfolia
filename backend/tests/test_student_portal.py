import re
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.database import SessionLocal
from backend.app.main import app
from backend.app.models.student_portal import AssessmentQuestion, SkillAssessment

client = TestClient(app)


def register_user(user_type: str = "student") -> tuple[dict, dict[str, str]]:
    email = f"{user_type}-{uuid4()}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Portal Test User",
            "email": email,
            "password": "StrongPass123",
            "user_type": user_type,
        },
    )
    assert response.status_code == 200, response.text
    result = response.json()
    return result, {"Authorization": f"Bearer {result['access_token']}"}


def test_student_portal_modules_are_persisted_and_isolated() -> None:
    student, headers = register_user()
    assert re.fullmatch(r"TP\d{7}", student["port_id"])

    profile = client.put(
        "/api/v1/students/me",
        json={
            "full_name": "Portal Student",
            "career_objective": "Build useful software",
            "profile_visibility": "public",
        },
        headers=headers,
    )
    assert profile.status_code == 200, profile.text
    assert profile.json()["port_id"] == student["port_id"]

    skill = client.post(
        "/api/v1/students/skills",
        json={"name": "Python", "category": "technical", "proficiency": "intermediate"},
        headers=headers,
    )
    assert skill.status_code == 201, skill.text

    learning = client.post(
        "/api/v1/students/learning-activities",
        json={
            "title": "Practised API design",
            "category": "backend",
            "topic": "FastAPI",
            "description": "Learned request validation",
            "what_i_practised": "Built a small endpoint",
            "duration_hours": 2,
            "confidence": 4,
            "status": "in_progress",
        },
        headers=headers,
    )
    assert learning.status_code == 200, learning.text
    updated = client.put(
        f"/api/v1/students/learning-activities/{learning.json()['id']}",
        json={"status": "completed", "duration_hours": 3},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "completed"
    progress = client.get("/api/v1/learning/progress", headers=headers)
    assert progress.status_code == 200
    assert progress.json()["by_skill"]["FastAPI"]["progress_percent"] == 100

    catalogue = client.get("/api/v1/assessments", headers=headers)
    assert catalogue.status_code == 200, catalogue.text
    db = SessionLocal()
    try:
        assessment_record = SkillAssessment(
            category="Python",
            title=f"Python fundamentals {uuid4()}",
            description="Admin-authored MCQ test",
            duration_minutes=30,
        )
        db.add(assessment_record)
        db.flush()
        questions = [
            AssessmentQuestion(
                assessment_id=assessment_record.id,
                prompt="Which Python value is immutable?" if number == 0 else f"Python test question {number}",
                question_type="multiple_choice",
                options=["list", "dict", "tuple", "set"] if number == 0 else [
                    f"Correct {number}",
                    f"Wrong {number} B",
                    f"Wrong {number} C",
                    f"Wrong {number} D",
                ],
                answer_key="tuple" if number == 0 else f"Correct {number}",
                topic="Data types" if number == 0 else f"Topic {number // 10 + 1}",
                points=1,
            )
            for number in range(30)
        ]
        db.add_all(questions)
        db.commit()
        assessment_id = assessment_record.id
    finally:
        db.close()
    catalogue = client.get("/api/v1/assessments", headers=headers)
    assessment = next(item for item in catalogue.json() if item["id"] == assessment_id)
    attempt = client.post(f"/api/v1/assessments/{assessment['id']}/attempts", headers=headers)
    assert attempt.status_code == 201, attempt.text
    assert len(attempt.json()["questions"]) == 30
    assert all("answer_key" not in question for question in attempt.json()["questions"])
    answers = {
        question["id"]: "tuple" if question["prompt"] == "Which Python value is immutable?" else "Not an answer"
        for question in attempt.json()["questions"]
    }
    result = client.post(
        f"/api/v1/assessments/attempts/{attempt.json()['attempt_id']}/submit",
        json={"answers": answers},
        headers=headers,
    )
    assert result.status_code == 200, result.text
    assert result.json()["score"] == 1
    assert result.json()["max_score"] == 30

    project = client.post(
        "/api/v1/portfolios/projects",
        json={
            "title": "Portfolio API",
            "description": "A project with a real persisted record",
            "technologies": ["Python", "FastAPI"],
            "is_public": True,
        },
        headers=headers,
    )
    assert project.status_code == 201, project.text
    public = client.get(f"/api/v1/portfolios/public/{student['port_id']}")
    assert public.status_code == 200, public.text
    assert public.json()["projects"][0]["title"] == "Portfolio API"

    second_student, second_headers = register_user()
    denied = client.put(
        f"/api/v1/portfolios/projects/{project.json()['id']}",
        json={"title": "Hijacked", "status": "planned"},
        headers=second_headers,
    )
    assert denied.status_code == 404

    team = client.post(
        "/api/v1/teams",
        json={
            "name": "Portal Team",
            "project_name": "Collaboration workspace",
            "required_skills": ["Python"],
            "team_size": 3,
            "open_positions": 1,
        },
        headers=headers,
    )
    assert team.status_code == 201, team.text
    invitation = client.post(
        f"/api/v1/teams/{team.json()['id']}/invitations",
        json={"email": second_student["email"]},
        headers=headers,
    )
    assert invitation.status_code == 201, invitation.text
    accepted = client.post(
        f"/api/v1/teams/invitations/{invitation.json()['id']}/accept",
        headers=second_headers,
    )
    assert accepted.status_code == 200, accepted.text
    task = client.post(
        f"/api/v1/teams/{team.json()['id']}/tasks",
        json={"title": "Build API", "assignee_id": second_student["user_id"]},
        headers=headers,
    )
    assert task.status_code == 201, task.text
    contribution = client.post(
        f"/api/v1/teams/{team.json()['id']}/contributions",
        json={"description": "Implemented request validation"},
        headers=second_headers,
    )
    assert contribution.status_code == 201, contribution.text

    company, company_headers = register_user("company")
    opportunity = client.post(
        "/api/v1/opportunities",
        json={
            "title": "Backend internship",
            "organization": "Portfolia Labs",
            "category": "internship",
            "description": "Work on APIs",
            "required_skills": ["Python"],
        },
        headers=company_headers,
    )
    assert opportunity.status_code == 201, opportunity.text
    applications = client.post(
        f"/api/v1/opportunities/{opportunity.json()['id']}/apply",
        headers=headers,
    )
    assert applications.status_code == 201, applications.text
    status_update = client.patch(
        f"/api/v1/opportunities/applications/{applications.json()['id']}",
        json={"status": "reviewing"},
        headers=company_headers,
    )
    assert status_update.status_code == 200
    assert status_update.json()["status"] == "reviewing"
    assert company["user_id"] == opportunity.json()["publisher_id"]

    ticket = client.post(
        "/api/v1/support/tickets",
        json={"category": "technical", "subject": "Portal issue", "message": "I need help"},
        headers=headers,
    )
    assert ticket.status_code == 201, ticket.text
    denied_ticket = client.get(f"/api/v1/support/tickets/{ticket.json()['id']}", headers=second_headers)
    assert denied_ticket.status_code == 404

    settings = client.put(
        "/api/v1/students/settings",
        json={
            "profile_visibility": "public",
            "notification_settings": {"notify_team": True},
            "privacy_settings": {"privacy_show_skills": True},
        },
        headers=headers,
    )
    assert settings.status_code == 200, settings.text
    sessions = client.get("/api/v1/students/sessions", headers=headers)
    assert sessions.status_code == 200, sessions.text
    assert sessions.json()


def test_browser_auth_uses_http_only_cookie() -> None:
    with TestClient(app) as browser:
        response = browser.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Cookie Student",
                "email": f"cookie-{uuid4()}@example.com",
                "password": "StrongPass123",
                "user_type": "student",
            },
        )
        assert response.status_code == 200
        cookie = response.headers.get("set-cookie", "")
        assert "HttpOnly" in cookie
        assert browser.get("/api/v1/students/me").status_code == 200
