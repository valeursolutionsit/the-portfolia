from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.database import SessionLocal
from backend.app.main import app
from backend.app.models.student_portal import (
    AssessmentAttempt,
    Opportunity,
    PortfolioProject,
    SkillAssessment,
    StudentSkill,
    Team,
)
from backend.app.models.user import LearningActivity, UserProfile
from backend.app.models.user import Role, User

client = TestClient(app)


def register(email: str, user_type: str = "student") -> tuple[dict, dict[str, str]]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Student Admin Workflow",
            "email": email,
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


def test_admin_student_crud_manages_profile_and_student_records() -> None:
    admin, admin_headers = register(f"workflow-admin-{uuid4()}@example.com")
    grant_admin(admin["user_id"])

    student_email = f"managed-student-{uuid4()}@example.com"
    created = client.post(
        "/api/v1/admin/students",
        json={
            "full_name": "Managed Student",
            "email": student_email,
            "password": "StrongStudentPass123!",
            "profile": {"college_name": "Portfolia University", "graduation_year": 2028},
        },
        headers=admin_headers,
    )
    assert created.status_code == 201, created.text
    student_id = created.json()["student"]["id"]
    assert created.json()["student"]["user_type"] == "student"
    assert created.json()["profile"]["college_name"] == "Portfolia University"

    student_list = client.get("/api/v1/admin/students?q=Managed%20Student", headers=admin_headers)
    assert student_list.status_code == 200, student_list.text
    assert any(student["id"] == student_id for student in student_list.json()["items"])

    updated = client.patch(
        f"/api/v1/admin/students/{student_id}",
        json={
            "full_name": "Updated Student",
            "email": f"updated-student-{uuid4()}@example.com",
            "password": "UpdatedStrongPass456!",
            "is_verified": True,
            "college_name": "Updated University",
            "technical_skills": "Python, SQL",
        },
        headers=admin_headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["student"]["full_name"] == "Updated Student"
    assert updated.json()["student"]["is_verified"] is True
    assert updated.json()["profile"]["college_name"] == "Updated University"
    student_login = client.post(
        "/api/v1/auth/login",
        json={"email": updated.json()["student"]["email"], "password": "UpdatedStrongPass456!"},
    )
    assert student_login.status_code == 200, student_login.text
    skill = client.post(
        f"/api/v1/admin/students/{student_id}/records/skills",
        json={"name": "Python", "category": "technical", "proficiency": "advanced"},
        headers=admin_headers,
    )
    assert skill.status_code == 201, skill.text
    skill_id = skill.json()["id"]
    renamed = client.patch(
        f"/api/v1/admin/students/{student_id}/records/skills/{skill_id}",
        json={"proficiency": "expert"},
        headers=admin_headers,
    )
    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["proficiency"] == "expert"

    activity = client.post(
        f"/api/v1/admin/students/{student_id}/records/learning-activities",
        json={"title": "Completed API exercise", "category": "programming", "duration_hours": 3},
        headers=admin_headers,
    )
    assert activity.status_code == 201, activity.text
    assert activity.json()["completed_at"] is not None

    project = client.post(
        f"/api/v1/admin/students/{student_id}/records/projects",
        json={"title": "Portfolio app", "technologies": ["Python", "FastAPI"], "is_public": True},
        headers=admin_headers,
    )
    assert project.status_code == 201, project.text
    team = client.post(
        f"/api/v1/admin/students/{student_id}/records/teams",
        json={"name": "Project team", "project_name": "Portfolio app", "team_size": 4},
        headers=admin_headers,
    )
    assert team.status_code == 201, team.text
    team_id = team.json()["id"]

    notification = client.post(
        f"/api/v1/admin/students/{student_id}/activities/notifications",
        json={"title": "Admin notice", "message": "Activity control test"},
        headers=admin_headers,
    )
    assert notification.status_code == 201, notification.text
    notification_id = notification.json()["id"]
    updated_notification = client.patch(
        f"/api/v1/admin/students/{student_id}/activities/notifications/{notification_id}",
        json={"is_read": True},
        headers=admin_headers,
    )
    assert updated_notification.status_code == 200
    assert updated_notification.json()["is_read"] is True

    settings = client.patch(
        f"/api/v1/admin/students/{student_id}/activities/settings/{student_id}",
        json={"profile_visibility": "public", "notification_settings": {"email": False}},
        headers=admin_headers,
    )
    assert settings.status_code == 200, settings.text
    assert settings.json()["profile_visibility"] == "public"

    other_student, _ = register(f"workflow-peer-{uuid4()}@example.com")
    db = SessionLocal()
    try:
        opportunity = Opportunity(
            publisher_id=admin["user_id"],
            title="Managed opportunity",
            organization="Portfolia",
            category="internship",
            description="A test opportunity",
        )
        assessment = SkillAssessment(category="testing", title="Managed assessment")
        db.add_all([opportunity, assessment])
        db.flush()
        attempt = AssessmentAttempt(
            user_id=student_id,
            assessment_id=assessment.id,
            answers={},
            score=1,
            max_score=2,
        )
        db.add(attempt)
        db.commit()
        opportunity_id = opportunity.id
        assessment_attempt_id = attempt.id
    finally:
        db.close()

    application = client.post(
        f"/api/v1/admin/students/{student_id}/activities/applications",
        json={"opportunity_id": opportunity_id},
        headers=admin_headers,
    )
    assert application.status_code == 201, application.text
    application_id = application.json()["id"]
    application_update = client.patch(
        f"/api/v1/admin/students/{student_id}/activities/applications/{application_id}",
        json={"status": "interview"},
        headers=admin_headers,
    )
    assert application_update.status_code == 200
    assert application_update.json()["status"] == "interview"

    saved = client.post(
        f"/api/v1/admin/students/{student_id}/activities/saved-opportunities",
        json={"opportunity_id": opportunity_id},
        headers=admin_headers,
    )
    assert saved.status_code == 201, saved.text

    invitation = client.post(
        f"/api/v1/admin/students/{student_id}/activities/team-invitations",
        json={"team_id": team_id, "invitee_id": other_student["user_id"]},
        headers=admin_headers,
    )
    assert invitation.status_code == 201, invitation.text
    invitation_id = invitation.json()["id"]
    accepted_invitation = client.patch(
        f"/api/v1/admin/students/{student_id}/activities/team-invitations/{invitation_id}",
        json={"status": "accepted"},
        headers=admin_headers,
    )
    assert accepted_invitation.status_code == 200
    cancelled_invitation = client.patch(
        f"/api/v1/admin/students/{student_id}/activities/team-invitations/{invitation_id}",
        json={"status": "cancelled"},
        headers=admin_headers,
    )
    assert cancelled_invitation.status_code == 200

    task = client.post(
        f"/api/v1/admin/students/{student_id}/activities/project-tasks",
        json={"team_id": team_id, "title": "Admin managed task"},
        headers=admin_headers,
    )
    assert task.status_code == 201, task.text
    task_id = task.json()["id"]
    task_update = client.patch(
        f"/api/v1/admin/students/{student_id}/activities/project-tasks/{task_id}",
        json={"status": "done"},
        headers=admin_headers,
    )
    assert task_update.status_code == 200
    assert task_update.json()["status"] == "done"

    contribution = client.post(
        f"/api/v1/admin/students/{student_id}/activities/project-contributions",
        json={"team_id": team_id, "description": "Test contribution"},
        headers=admin_headers,
    )
    assert contribution.status_code == 201, contribution.text
    contribution_id = contribution.json()["id"]
    contribution_update = client.patch(
        f"/api/v1/admin/students/{student_id}/activities/project-contributions/{contribution_id}",
        json={"description": "Reviewed contribution"},
        headers=admin_headers,
    )
    assert contribution_update.status_code == 200
    assert contribution_update.json()["description"] == "Reviewed contribution"

    db = SessionLocal()
    try:
        session_id = db.query(User.id).filter(User.id == student_id).scalar()
        assert session_id == student_id
    finally:
        db.close()
    detail_before_revoke = client.get(f"/api/v1/admin/students/{student_id}", headers=admin_headers).json()
    session_id = detail_before_revoke["records"]["sessions"][0]["id"]
    revoked_session = client.delete(
        f"/api/v1/admin/students/{student_id}/activities/sessions/{session_id}",
        headers=admin_headers,
    )
    assert revoked_session.status_code == 204
    assert client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {student_login.json()['access_token']}"},
    ).status_code == 401

    detail = client.get(f"/api/v1/admin/students/{student_id}", headers=admin_headers)
    assert detail.status_code == 200, detail.text
    records = detail.json()["records"]
    assert len(records["skills"]) == 1
    assert len(records["learning-activities"]) == 1
    assert len(records["projects"]) == 2
    assert len(records["teams"]) == 1
    assert len(records["assessment_attempts"]) == 1
    assert len(records["opportunity_applications"]) == 1
    assert len(records["saved_opportunities"]) == 1
    assert len(records["notifications"]) >= 1
    assert records["settings"]["profile_visibility"] == "public"

    record_cases = [
        ("learning-paths", {"title": "Python path", "skill_name": "Python"}, "title", "Python foundations"),
        ("milestones", {"title": "Finish Python basics", "skill_name": "Python"}, "status", "completed"),
        ("resources", {"title": "Python docs", "url": "https://docs.python.org/"}, "title", "Official Python documentation"),
        ("certifications", {"name": "Python basics", "issuer": "Portfolia"}, "name", "Python certificate"),
        ("achievements", {"title": "Hackathon finalist", "awarded_by": "Portfolia"}, "title", "Regional finalist"),
        ("work-experiences", {"organization": "Portfolia", "role": "Developer intern"}, "role", "Software intern"),
    ]
    for resource, record_payload, update_field, update_value in record_cases:
        response = client.post(
            f"/api/v1/admin/students/{student_id}/records/{resource}",
            json=record_payload,
            headers=admin_headers,
        )
        assert response.status_code == 201, f"{resource}: {response.text}"
        record_id = response.json()["id"]
        response = client.patch(
            f"/api/v1/admin/students/{student_id}/records/{resource}/{record_id}",
            json={update_field: update_value},
            headers=admin_headers,
        )
        assert response.status_code == 200, f"{resource}: {response.text}"
        assert response.json()[update_field] == update_value
        response = client.delete(
            f"/api/v1/admin/students/{student_id}/records/{resource}/{record_id}",
            headers=admin_headers,
        )
        assert response.status_code == 204, f"{resource}: {response.text}"

    unsupported = client.post(
        f"/api/v1/admin/students/{student_id}/records/skills",
        json={"name": "Unsafe", "role": "admin"},
        headers=admin_headers,
    )
    assert unsupported.status_code == 422

    deleted_record = client.delete(
        f"/api/v1/admin/students/{student_id}/records/skills/{skill_id}",
        headers=admin_headers,
    )
    assert deleted_record.status_code == 204
    assert client.delete(
        f"/api/v1/admin/students/{student_id}/activities/notifications/{notification_id}",
        headers=admin_headers,
    ).status_code == 204
    assert client.delete(
        f"/api/v1/admin/students/{student_id}/activities/applications/{application_id}",
        headers=admin_headers,
    ).status_code == 204
    assert client.delete(
        f"/api/v1/admin/students/{student_id}/activities/saved-opportunities/{saved.json()['id']}",
        headers=admin_headers,
    ).status_code == 204
    assert client.delete(
        f"/api/v1/admin/students/{student_id}/activities/team-invitations/{invitation_id}",
        headers=admin_headers,
    ).status_code == 204
    assert client.delete(
        f"/api/v1/admin/students/{student_id}/activities/project-tasks/{task_id}",
        headers=admin_headers,
    ).status_code == 204
    assert client.delete(
        f"/api/v1/admin/students/{student_id}/activities/project-contributions/{contribution_id}",
        headers=admin_headers,
    ).status_code == 204
    assert client.delete(
        f"/api/v1/admin/students/{student_id}/activities/assessment-attempts/{assessment_attempt_id}",
        headers=admin_headers,
    ).status_code == 204
    assert client.delete(
        f"/api/v1/admin/students/{student_id}/activities/settings/{student_id}",
        headers=admin_headers,
    ).status_code == 204
    assert client.get(f"/api/v1/admin/students/{student_id}", headers=admin_headers).json()["records"]["skills"] == []

    deleted = client.delete(f"/api/v1/admin/students/{student_id}", headers=admin_headers)
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/admin/students/{student_id}", headers=admin_headers).status_code == 404
    db = SessionLocal()
    try:
        for model in (PortfolioProject, StudentSkill, LearningActivity, UserProfile, Team):
            owner_field = model.user_id if hasattr(model, "user_id") else model.owner_id
            assert db.query(model).filter(owner_field == student_id).count() == 0
    finally:
        db.close()
    audit = client.get("/api/v1/admin/activity?limit=100", headers=admin_headers)
    assert audit.status_code == 200
    actions = [item["action"] for item in audit.json()["items"]]
    assert "admin.student.created" in actions
    assert "admin.student.updated" in actions
    assert "admin.student.deleted" in actions
    assert "admin.student_activity.updated" in actions
    assert "admin.student_activity.deleted" in actions
