from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.database import SessionLocal
from backend.app.main import app
from backend.app.models.student_portal import AssessmentQuestion, SkillAssessment
from backend.app.models.user import Role, User

client = TestClient(app)


def register_user() -> tuple[dict, dict[str, str]]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Assessment Workflow",
            "email": f"assessment-{uuid4()}@example.com",
            "password": "StrongPass123",
            "user_type": "student",
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


def test_admin_creates_and_manages_backend_scored_30_question_test() -> None:
    student, student_headers = register_user()
    admin, admin_headers = register_user()
    grant_admin(admin["user_id"])

    questions = [
        {
            "prompt": f"Question {number}: which option is correct?",
            "topic": f"Topic {(number - 1) // 10 + 1}",
            "options": [f"Correct {number}", f"Wrong {number} B", f"Wrong {number} C", f"Wrong {number} D"],
            "correct_option_index": 0,
        }
        for number in range(1, 31)
    ]
    payload = {
        "title": f"Admin authored test {uuid4()}",
        "category": "Programming",
        "description": "A complete backend-scored skills test.",
        "duration_minutes": 45,
        "questions": questions,
    }

    client.cookies.clear()
    assert client.get("/api/v1/admin/assessments").status_code == 401
    assert client.get("/api/v1/admin/assessments", headers=student_headers).status_code == 403
    assert client.post(
        "/api/v1/admin/assessments",
        json={**payload, "questions": questions[:29]},
        headers=admin_headers,
    ).status_code == 422

    created = client.post("/api/v1/admin/assessments", json=payload, headers=admin_headers)
    assert created.status_code == 201, created.text
    assessment = created.json()
    assessment_id = assessment["id"]
    assert assessment["question_count"] == 30
    assert len(assessment["questions"]) == 30
    assert assessment["questions"][0]["correct_option_index"] == 0

    catalogue = client.get("/api/v1/assessments", headers=student_headers)
    assert catalogue.status_code == 200
    student_test = next(item for item in catalogue.json() if item["id"] == assessment_id)
    assert student_test["question_count"] == 30
    assert "answer" not in str(student_test).casefold()

    db = SessionLocal()
    try:
        legacy = SkillAssessment(category="legacy", title=f"Legacy one-question {uuid4()}")
        db.add(legacy)
        db.flush()
        db.add(
            AssessmentQuestion(
                assessment_id=legacy.id,
                prompt="Incomplete test",
                question_type="multiple_choice",
                options=["A", "B", "C", "D"],
                answer_key="A",
            )
        )
        db.commit()
        legacy_id = legacy.id
    finally:
        db.close()
    refreshed_catalogue = client.get("/api/v1/assessments", headers=student_headers)
    assert legacy_id not in {item["id"] for item in refreshed_catalogue.json()}
    assert client.post(
        f"/api/v1/assessments/{legacy_id}/attempts",
        headers=student_headers,
    ).status_code == 404

    started = client.post(f"/api/v1/assessments/{assessment_id}/attempts", headers=student_headers)
    assert started.status_code == 201, started.text
    attempt = started.json()
    assert len(attempt["questions"]) == 30
    assert all("answer_key" not in question and "correct_option_index" not in question for question in attempt["questions"])

    answers = {question["id"]: question["options"][0] for question in attempt["questions"]}
    submitted = client.post(
        f"/api/v1/assessments/attempts/{attempt['attempt_id']}/submit",
        json={"answers": answers},
        headers=student_headers,
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["score"] == 30
    assert submitted.json()["max_score"] == 30
    assert set(submitted.json()["topic_scores"]) == {"Topic 1", "Topic 2", "Topic 3"}

    question_edit = client.patch(
        f"/api/v1/admin/assessments/{assessment_id}",
        json={"questions": questions},
        headers=admin_headers,
    )
    assert question_edit.status_code == 409
    title_update = client.patch(
        f"/api/v1/admin/assessments/{assessment_id}",
        json={"title": "Updated title"},
        headers=admin_headers,
    )
    assert title_update.status_code == 200
    assert title_update.json()["title"] == "Updated title"
    assert client.delete(
        f"/api/v1/admin/assessments/{assessment_id}",
        headers=admin_headers,
    ).status_code == 409

    deactivated = client.patch(
        f"/api/v1/admin/assessments/{assessment_id}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert deactivated.status_code == 200
    assert assessment_id not in {item["id"] for item in client.get(
        "/api/v1/assessments", headers=student_headers
    ).json()}

    removable = client.post(
        "/api/v1/admin/assessments",
        json={**payload, "title": f"Unattempted test {uuid4()}"},
        headers=admin_headers,
    )
    assert removable.status_code == 201, removable.text
    removed = client.delete(
        f"/api/v1/admin/assessments/{removable.json()['id']}",
        headers=admin_headers,
    )
    assert removed.status_code == 204
