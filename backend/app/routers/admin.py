import json
import secrets
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from fastapi.encoders import jsonable_encoder
from pydantic import Field, ValidationError
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password
from backend.app.database import get_db
from backend.app.dependencies import require_admin
from backend.app.models.student_portal import (
    Achievement,
    AssessmentAttempt,
    AssessmentQuestion,
    Certification,
    LearningMilestone,
    LearningPath,
    LearningResource,
    Notification,
    Opportunity,
    OpportunityApplication,
    PortfolioProject,
    ProjectContribution,
    ProjectTask,
    SavedOpportunity,
    SkillAssessment,
    StudentSettings,
    StudentSkill,
    SupportMessage,
    SupportTicket,
    Team,
    TeamInvitation,
    TeamMember,
    UserSession,
    WorkExperience,
)
from backend.app.models.user import (
    AuditLog,
    CompanyProfile,
    InstitutionProfile,
    InvestorProfile,
    LearningActivity,
    Role,
    User,
    UserRole,
    UserProfile,
)
from backend.app.schemas.admin import (
    AdminAssessmentQuestion,
    AdminOpportunityUpdate,
    AdminAssessmentCreate,
    AdminAssessmentUpdate,
    AdminProjectContributionCreate,
    AdminProjectContributionUpdate,
    AdminProjectTaskCreate,
    AdminSupportResponse,
    AdminStudentApplicationCreate,
    AdminStudentApplicationUpdate,
    AdminStudentCreate,
    AdminStudentNotificationCreate,
    AdminStudentNotificationUpdate,
    AdminStudentSavedOpportunityCreate,
    AdminStudentSettingsUpdate,
    AdminStudentUpdate,
    AdminTeamInvitationCreate,
    AdminTeamInvitationUpdate,
    AdminTeamMembershipCreate,
    AdminTeamMembershipUpdate,
    AdminTicketStatusUpdate,
    AdminUserUpdate,
)
from backend.app.schemas.portal import (
    AchievementCreate,
    CertificationCreate,
    LearningMilestoneCreate,
    LearningPathCreate,
    LearningResourceCreate,
    ProjectTaskUpdate,
    ProjectCreate,
    StudentSkillCreate,
    TeamCreate,
    WorkExperienceCreate,
)
from backend.app.schemas.student import LearningActivityCreate

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminLearningPathCreate(LearningPathCreate):
    status: str = Field(default="active", pattern="^(active|paused|completed)$")


class AdminLearningMilestoneCreate(LearningMilestoneCreate):
    status: str = Field(default="planned", pattern="^(planned|in_progress|completed)$")


STUDENT_RECORD_TYPES = {
    "skills": (StudentSkill, StudentSkillCreate, "user_id"),
    "learning-activities": (LearningActivity, LearningActivityCreate, "user_id"),
    "learning-paths": (LearningPath, AdminLearningPathCreate, "user_id"),
    "milestones": (LearningMilestone, AdminLearningMilestoneCreate, "user_id"),
    "resources": (LearningResource, LearningResourceCreate, "user_id"),
    "projects": (PortfolioProject, ProjectCreate, "user_id"),
    "certifications": (Certification, CertificationCreate, "user_id"),
    "achievements": (Achievement, AchievementCreate, "user_id"),
    "work-experiences": (WorkExperience, WorkExperienceCreate, "user_id"),
    "teams": (Team, TeamCreate, "owner_id"),
}


def _admin_student(db: Session, student_id: str) -> User:
    student = db.query(User).filter(User.id == student_id, User.user_type == "student").first()
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


def _validate_record(schema: type, values: dict[str, Any]) -> dict[str, Any]:
    unknown_fields = set(values) - set(schema.model_fields)
    if unknown_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unsupported fields: {', '.join(sorted(unknown_fields))}",
        )
    try:
        validated = schema.model_validate(values)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=exc.errors()) from exc
    result = validated.model_dump()
    for field in ("evidence_url", "resource_url", "github_url", "live_url", "credential_url", "url"):
        if field in result and result[field] is not None:
            result[field] = str(result[field])
    if "evidence_urls" in result:
        result["evidence_urls"] = [str(value) for value in result["evidence_urls"]]
    return result


def _record_lookup_id(model: type, record_id: str) -> str | int:
    if model is LearningActivity:
        try:
            return int(record_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student record not found") from exc
    return record_id


def _student_detail(student: User, db: Session) -> dict[str, Any]:
    profile = db.query(UserProfile).filter(UserProfile.user_id == student.id).first()
    records: dict[str, Any] = {}
    for resource, (model, _, owner_field) in STUDENT_RECORD_TYPES.items():
        owner_column = getattr(model, owner_field)
        records[resource] = (
            db.query(model)
            .filter(owner_column == student.id)
            .order_by(model.created_at.desc(), model.id.desc())
            .all()
        )

    team_ids = [
        row[0]
        for row in db.query(TeamMember.team_id).filter(TeamMember.user_id == student.id).all()
    ]
    team_ids.extend(team.id for team in records["teams"])
    ticket_ids = [
        row[0]
        for row in db.query(SupportTicket.id).filter(SupportTicket.user_id == student.id).all()
    ]
    records.update(
        {
            "profile": profile,
            "assessment_attempts": db.query(AssessmentAttempt).filter(
                AssessmentAttempt.user_id == student.id
            ).order_by(AssessmentAttempt.started_at.desc()).all(),
            "opportunity_applications": db.query(OpportunityApplication).filter(
                OpportunityApplication.user_id == student.id
            ).order_by(OpportunityApplication.created_at.desc()).all(),
            "saved_opportunities": db.query(SavedOpportunity).filter(
                SavedOpportunity.user_id == student.id
            ).order_by(SavedOpportunity.created_at.desc()).all(),
            "support_tickets": db.query(SupportTicket).filter(
                SupportTicket.user_id == student.id
            ).order_by(SupportTicket.updated_at.desc()).all(),
            "notifications": db.query(Notification).filter(
                Notification.user_id == student.id
            ).order_by(Notification.created_at.desc()).all(),
            "settings": db.query(StudentSettings).filter(StudentSettings.user_id == student.id).first(),
            "sessions": db.query(UserSession).filter(
                UserSession.user_id == student.id
            ).order_by(UserSession.created_at.desc()).all(),
            "team_memberships": db.query(TeamMember).filter(
                TeamMember.user_id == student.id
            ).all(),
            "team_invitations": db.query(TeamInvitation).filter(
                or_(TeamInvitation.inviter_id == student.id, TeamInvitation.invitee_id == student.id)
            ).order_by(TeamInvitation.created_at.desc()).all(),
            "project_tasks": db.query(ProjectTask).filter(
                or_(
                    ProjectTask.created_by == student.id,
                    ProjectTask.assignee_id == student.id,
                    ProjectTask.team_id.in_(team_ids),
                )
            ).order_by(ProjectTask.created_at.desc()).all(),
            "project_contributions": db.query(ProjectContribution).filter(
                ProjectContribution.user_id == student.id
            ).order_by(ProjectContribution.created_at.desc()).all(),
            "support_messages": db.query(SupportMessage).filter(
                or_(SupportMessage.sender_id == student.id, SupportMessage.ticket_id.in_(ticket_ids))
            ).order_by(SupportMessage.created_at.asc()).all(),
            "team_records": db.query(Team).filter(Team.id.in_(team_ids)).all() if team_ids else [],
        }
    )
    records["assessment_attempts"] = [
        {
            **jsonable_encoder(attempt),
            "assessment_title": db.query(SkillAssessment.title)
            .filter(SkillAssessment.id == attempt.assessment_id)
            .scalar()
            or "Assessment unavailable",
        }
        for attempt in records["assessment_attempts"]
    ]
    records["opportunity_applications"] = [
        {
            **jsonable_encoder(application),
            "opportunity_title": db.query(Opportunity.title)
            .filter(Opportunity.id == application.opportunity_id)
            .scalar()
            or "Opportunity unavailable",
        }
        for application in records["opportunity_applications"]
    ]
    records["saved_opportunities"] = [
        {
            **jsonable_encoder(saved),
            "opportunity_title": db.query(Opportunity.title)
            .filter(Opportunity.id == saved.opportunity_id)
            .scalar()
            or "Opportunity unavailable",
        }
        for saved in records["saved_opportunities"]
    ]
    records["team_memberships"] = [
        {
            **jsonable_encoder(membership),
            "team_name": db.query(Team.name).filter(Team.id == membership.team_id).scalar() or "Team unavailable",
        }
        for membership in records["team_memberships"]
    ]
    records["team_invitations"] = [
        {
            **jsonable_encoder(invitation),
            "team_name": db.query(Team.name).filter(Team.id == invitation.team_id).scalar() or "Team unavailable",
            "invitee_email": db.query(User.email).filter(User.id == invitation.invitee_id).scalar(),
        }
        for invitation in records["team_invitations"]
    ]
    records["project_tasks"] = [
        {
            **jsonable_encoder(task),
            "team_name": db.query(Team.name).filter(Team.id == task.team_id).scalar() or "Team unavailable",
            "assignee_email": db.query(User.email).filter(User.id == task.assignee_id).scalar() if task.assignee_id else None,
        }
        for task in records["project_tasks"]
    ]
    records["project_contributions"] = [
        {
            **jsonable_encoder(contribution),
            "team_name": db.query(Team.name).filter(Team.id == contribution.team_id).scalar() or "Team unavailable",
        }
        for contribution in records["project_contributions"]
    ]
    records["support_tickets"] = [
        {
            **jsonable_encoder(ticket),
            "message_count": db.query(SupportMessage.id).filter(SupportMessage.ticket_id == ticket.id).count(),
        }
        for ticket in records["support_tickets"]
    ]
    return jsonable_encoder(
        {
            "student": _user_summary(student, db),
            "profile": profile,
            "records": records,
        }
    )


def _delete_team_records(db: Session, team_id: str) -> None:
    db.query(PortfolioProject).filter(PortfolioProject.team_id == team_id).update(
        {PortfolioProject.team_id: None},
        synchronize_session=False,
    )
    db.query(ProjectTask).filter(ProjectTask.team_id == team_id).delete(synchronize_session=False)
    db.query(ProjectContribution).filter(ProjectContribution.team_id == team_id).delete(synchronize_session=False)
    db.query(TeamInvitation).filter(TeamInvitation.team_id == team_id).delete(synchronize_session=False)
    db.query(TeamMember).filter(TeamMember.team_id == team_id).delete(synchronize_session=False)


def _delete_student_records(db: Session, student: User) -> None:
    student_id = student.id
    team_ids = [row[0] for row in db.query(Team.id).filter(Team.owner_id == student_id).all()]
    member_team_rows = db.query(TeamMember.team_id).filter(
        TeamMember.user_id == student_id,
        TeamMember.team_id.notin_(team_ids) if team_ids else True,
    ).all()
    for (team_id,) in member_team_rows:
        team = db.query(Team).filter(Team.id == team_id).first()
        if team is not None:
            team.open_positions = min(team.team_size, team.open_positions + 1)
    ticket_ids = [row[0] for row in db.query(SupportTicket.id).filter(SupportTicket.user_id == student_id).all()]
    opportunity_ids = [row[0] for row in db.query(Opportunity.id).filter(Opportunity.publisher_id == student_id).all()]

    if team_ids:
        db.query(PortfolioProject).filter(PortfolioProject.team_id.in_(team_ids)).update(
            {PortfolioProject.team_id: None}, synchronize_session=False
        )
        db.query(ProjectTask).filter(ProjectTask.team_id.in_(team_ids)).delete(synchronize_session=False)
        db.query(ProjectContribution).filter(ProjectContribution.team_id.in_(team_ids)).delete(synchronize_session=False)
        db.query(TeamInvitation).filter(TeamInvitation.team_id.in_(team_ids)).delete(synchronize_session=False)
        db.query(TeamMember).filter(TeamMember.team_id.in_(team_ids)).delete(synchronize_session=False)

    db.query(ProjectTask).filter(ProjectTask.assignee_id == student_id).update(
        {ProjectTask.assignee_id: None}, synchronize_session=False
    )
    db.query(ProjectTask).filter(
        or_(ProjectTask.created_by == student_id, ProjectTask.team_id.in_(team_ids))
    ).delete(synchronize_session=False)
    db.query(ProjectContribution).filter(ProjectContribution.user_id == student_id).delete(synchronize_session=False)
    db.query(TeamMember).filter(TeamMember.user_id == student_id).delete(synchronize_session=False)
    db.query(TeamInvitation).filter(
        or_(TeamInvitation.inviter_id == student_id, TeamInvitation.invitee_id == student_id)
    ).delete(synchronize_session=False)
    db.query(Team).filter(Team.owner_id == student_id).delete(synchronize_session=False)

    db.query(SupportMessage).filter(
        or_(SupportMessage.sender_id == student_id, SupportMessage.ticket_id.in_(ticket_ids))
    ).delete(synchronize_session=False)
    db.query(SupportTicket).filter(SupportTicket.user_id == student_id).delete(synchronize_session=False)

    if opportunity_ids:
        db.query(OpportunityApplication).filter(
            OpportunityApplication.opportunity_id.in_(opportunity_ids)
        ).delete(synchronize_session=False)
        db.query(SavedOpportunity).filter(SavedOpportunity.opportunity_id.in_(opportunity_ids)).delete(
            synchronize_session=False
        )
        db.query(Opportunity).filter(Opportunity.id.in_(opportunity_ids)).delete(synchronize_session=False)
    db.query(OpportunityApplication).filter(OpportunityApplication.user_id == student_id).delete(
        synchronize_session=False
    )
    db.query(SavedOpportunity).filter(SavedOpportunity.user_id == student_id).delete(synchronize_session=False)

    db.query(AuditLog).filter(AuditLog.user_id == student_id).update(
        {AuditLog.user_id: None}, synchronize_session=False
    )
    for model in (
        AssessmentAttempt,
        StudentSkill,
        LearningMilestone,
        LearningPath,
        LearningResource,
        PortfolioProject,
        Certification,
        Achievement,
        WorkExperience,
        StudentSettings,
        Notification,
        UserSession,
    ):
        db.query(model).filter(model.user_id == student_id).delete(synchronize_session=False)
    db.query(LearningActivity).filter(LearningActivity.user_id == student_id).delete(synchronize_session=False)
    db.query(UserRole).filter(UserRole.user_id == student_id).delete(synchronize_session=False)
    db.delete(student)


def _record_admin_action(db: Session, actor: User, action: str, details: dict[str, object]) -> None:
    db.add(AuditLog(user_id=actor.id, action=action, details=json.dumps(details, sort_keys=True)))


def _is_super_admin(user: User) -> bool:
    return any(role.name.lower() in {"super-admin", "super_admin"} for role in user.roles)


def _user_summary(user: User, db: Session) -> dict[str, object]:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "user_type": user.user_type,
        "port_id": user.port_id,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
        "college_name": profile.college_name if profile else None,
        "roles": [role.name for role in user.roles],
    }


def _admin_assessment_detail(assessment: SkillAssessment, db: Session) -> dict[str, Any]:
    questions = (
        db.query(AssessmentQuestion)
        .filter(AssessmentQuestion.assessment_id == assessment.id)
        .all()
    )
    return {
        "id": assessment.id,
        "title": assessment.title,
        "category": assessment.category,
        "description": assessment.description,
        "duration_minutes": assessment.duration_minutes,
        "is_active": assessment.is_active,
        "created_at": assessment.created_at,
        "question_count": len(questions),
        "attempt_count": db.query(AssessmentAttempt.id)
        .filter(AssessmentAttempt.assessment_id == assessment.id)
        .count(),
        "questions": [
            {
                "id": question.id,
                "prompt": question.prompt,
                "topic": question.topic or "",
                "options": question.options,
                "correct_option_index": (
                    question.options.index(question.answer_key)
                    if question.answer_key in question.options
                    else 0
                ),
            }
            for question in questions
        ],
    }


def _save_assessment_questions(
    db: Session,
    assessment: SkillAssessment,
    questions: list[AdminAssessmentQuestion],
) -> None:
    db.query(AssessmentQuestion).filter(
        AssessmentQuestion.assessment_id == assessment.id
    ).delete(synchronize_session=False)
    for question in questions:
        db.add(
            AssessmentQuestion(
                assessment_id=assessment.id,
                prompt=question.prompt.strip(),
                question_type="multiple_choice",
                options=question.options,
                answer_key=question.options[question.correct_option_index],
                topic=question.topic.strip(),
                points=1,
            )
        )


@router.get("/assessments")
def list_admin_assessments(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    assessments = db.query(SkillAssessment).order_by(SkillAssessment.created_at.desc()).all()
    return [_admin_assessment_detail(assessment, db) for assessment in assessments]


@router.post("/assessments", status_code=status.HTTP_201_CREATED)
def create_admin_assessment(
    payload: AdminAssessmentCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    values = payload.model_dump(exclude={"questions"})
    questions = payload.questions
    values["title"] = values["title"].strip()
    values["category"] = values["category"].strip()
    if values["description"] is not None:
        values["description"] = values["description"].strip()
    assessment = SkillAssessment(**values)
    db.add(assessment)
    db.flush()
    _save_assessment_questions(db, assessment, questions)
    _record_admin_action(
        db,
        admin,
        "admin.assessment.created",
        {"assessment_id": assessment.id, "question_count": len(questions)},
    )
    db.commit()
    db.refresh(assessment)
    return _admin_assessment_detail(assessment, db)


@router.patch("/assessments/{assessment_id}")
def update_admin_assessment(
    assessment_id: str,
    payload: AdminAssessmentUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    assessment = db.query(SkillAssessment).filter(SkillAssessment.id == assessment_id).first()
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    values = payload.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="No assessment changes provided")
    questions = payload.questions if "questions" in payload.model_fields_set else None
    nullable_forbidden = {"title", "category", "duration_minutes", "is_active", "questions"}
    if any(field in values and values[field] is None for field in nullable_forbidden):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Assessment fields cannot be cleared with null",
        )
    values.pop("questions", None)
    if questions is not None and db.query(AssessmentAttempt.id).filter(
        AssessmentAttempt.assessment_id == assessment.id
    ).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Questions cannot be changed after students have started this test",
        )
    if "title" in values:
        values["title"] = values["title"].strip()
    if "category" in values:
        values["category"] = values["category"].strip()
    if values.get("description") is not None:
        values["description"] = values["description"].strip()
    for field, value in values.items():
        setattr(assessment, field, value)
    if questions is not None:
        _save_assessment_questions(db, assessment, questions)
    _record_admin_action(
        db,
        admin,
        "admin.assessment.updated",
        {"assessment_id": assessment.id, "fields": sorted(payload.model_fields_set)},
    )
    db.commit()
    db.refresh(assessment)
    return _admin_assessment_detail(assessment, db)


@router.delete("/assessments/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_assessment(
    assessment_id: str,
    response: Response,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    assessment = db.query(SkillAssessment).filter(SkillAssessment.id == assessment_id).first()
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    if db.query(AssessmentAttempt.id).filter(AssessmentAttempt.assessment_id == assessment.id).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A test with student attempts cannot be deleted; deactivate it instead",
        )
    assessment_id = assessment.id
    db.query(AssessmentQuestion).filter(
        AssessmentQuestion.assessment_id == assessment.id
    ).delete(synchronize_session=False)
    db.delete(assessment)
    _record_admin_action(db, admin, "admin.assessment.deleted", {"assessment_id": assessment_id})
    db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/dashboard")
def admin_dashboard(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user_counts = dict(
        db.query(User.user_type, func.count(User.id))
        .group_by(User.user_type)
        .all()
    )
    latest_users = db.query(User).order_by(User.created_at.desc()).limit(8).all()
    latest_logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(10).all()
    return {
        "users_total": db.query(User).count(),
        "users_active": db.query(User).filter(User.is_active.is_(True)).count(),
        "students_total": user_counts.get("student", 0),
        "companies_total": user_counts.get("company", 0),
        "institutions_total": user_counts.get("college_admin", 0),
        "investors_total": user_counts.get("investor", 0),
        "pending_verification": db.query(User).filter(
            User.user_type.in_(["college_admin", "company", "investor"]),
            User.is_verified.is_(False),
        ).count(),
        "opportunities_active": db.query(Opportunity).filter(Opportunity.is_active.is_(True)).count(),
        "applications_total": db.query(OpportunityApplication).count(),
        "support_open": db.query(SupportTicket).filter(SupportTicket.status.in_(["open", "in_progress"])).count(),
        "projects_total": db.query(PortfolioProject).count(),
        "teams_total": db.query(Team).count(),
        "learning_records_total": db.query(LearningActivity).count(),
        "assessment_attempts_total": db.query(AssessmentAttempt).count(),
        "users_by_type": user_counts,
        "recent_users": [_user_summary(user, db) for user in latest_users],
        "recent_activity": [
            {
                "id": item.id,
                "actor": db.query(User.full_name).filter(User.id == item.user_id).scalar() if item.user_id else "System",
                "action": item.action,
                "details": item.details,
                "created_at": item.created_at,
            }
            for item in latest_logs
        ],
    }


@router.get("/users")
def list_users(
    q: str | None = Query(default=None, max_length=150),
    user_type: str | None = Query(default=None, max_length=64),
    is_active: bool | None = None,
    is_verified: bool | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(or_(User.full_name.ilike(pattern), User.email.ilike(pattern), User.port_id.ilike(pattern)))
    if user_type:
        query = query.filter(User.user_type == user_type)
    if is_active is not None:
        query = query.filter(User.is_active.is_(is_active))
    if is_verified is not None:
        query = query.filter(User.is_verified.is_(is_verified))
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    return {"items": [_user_summary(user, db) for user in users], "total": total, "offset": offset, "limit": limit}


@router.get("/students")
def list_admin_students(
    q: str | None = Query(default=None, max_length=150),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User).filter(User.user_type == "student")
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(User.full_name.ilike(pattern), User.email.ilike(pattern), User.port_id.ilike(pattern))
        )
    total = query.count()
    students = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "items": [_user_summary(student, db) for student in students],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.post("/students", status_code=status.HTTP_201_CREATED)
def create_admin_student(
    payload: AdminStudentCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    email = str(payload.email).lower().strip()
    if db.query(User.id).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    role = db.query(Role).filter(Role.name == "student").first()
    if role is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Student role is not configured")
    while True:
        port_id = f"TP{str(datetime.now(UTC).year)[-2:]}{secrets.randbelow(90000) + 10000}"
        if not db.query(User.id).filter(User.port_id == port_id).first():
            break
    student = User(
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        is_active=True,
        is_verified=False,
        port_id=port_id,
        user_type="student",
    )
    student.roles.append(role)
    db.add(student)
    profile_values = payload.profile.model_dump(exclude_unset=True, exclude={"full_name"}) if payload.profile else {}
    if profile_values:
        for field in ("profile_photo_url", "linkedin_url", "github_url", "personal_website"):
            if profile_values.get(field) is not None:
                profile_values[field] = str(profile_values[field])
        db.add(UserProfile(user=student, **profile_values))
    db.flush()
    _record_admin_action(db, admin, "admin.student.created", {"student_id": student.id})
    db.commit()
    db.refresh(student)
    return _student_detail(student, db)


@router.get("/students/{student_id}")
def get_admin_student(
    student_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return _student_detail(_admin_student(db, student_id), db)


@router.patch("/students/{student_id}")
def update_admin_student(
    student_id: str,
    payload: AdminStudentUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    student = _admin_student(db, student_id)
    values = payload.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="No student changes provided")

    email = values.pop("email", None)
    if email is not None:
        email = str(email).lower().strip()
        conflict = db.query(User.id).filter(User.email == email, User.id != student.id).first()
        if conflict:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        student.email = email
    password = values.pop("password", None)
    if password is not None:
        student.password_hash = hash_password(password)
        db.query(UserSession).filter(
            UserSession.user_id == student.id,
            UserSession.revoked_at.is_(None),
        ).update({UserSession.revoked_at: datetime.now(UTC)}, synchronize_session=False)
    is_active = values.pop("is_active", None)
    if is_active is not None:
        student.is_active = is_active
        if not is_active:
            db.query(UserSession).filter(
                UserSession.user_id == student.id,
                UserSession.revoked_at.is_(None),
            ).update({UserSession.revoked_at: datetime.now(UTC)}, synchronize_session=False)
    is_verified = values.pop("is_verified", None)
    if is_verified is not None:
        student.is_verified = is_verified
    full_name = values.pop("full_name", None)
    if full_name is not None:
        student.full_name = full_name.strip()

    profile_values = values
    if profile_values:
        profile = db.query(UserProfile).filter(UserProfile.user_id == student.id).first()
        if profile is None:
            profile = UserProfile(user_id=student.id)
            db.add(profile)
        for field in ("profile_photo_url", "linkedin_url", "github_url", "personal_website"):
            if profile_values.get(field) is not None:
                profile_values[field] = str(profile_values[field])
        for field, value in profile_values.items():
            setattr(profile, field, value)
        if "profile_visibility" in profile_values:
            student_settings = db.query(StudentSettings).filter(StudentSettings.user_id == student.id).first()
            if student_settings is None:
                student_settings = StudentSettings(user_id=student.id)
                db.add(student_settings)
            student_settings.profile_visibility = profile_values["profile_visibility"]
    changed_fields = [*payload.model_fields_set]
    _record_admin_action(
        db,
        admin,
        "admin.student.updated",
        {"student_id": student.id, "fields": sorted(changed_fields)},
    )
    db.commit()
    db.refresh(student)
    return _student_detail(student, db)


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_student(
    student_id: str,
    response: Response,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    student = _admin_student(db, student_id)
    student_summary = {"student_id": student.id, "email": student.email}
    _delete_student_records(db, student)
    _record_admin_action(db, admin, "admin.student.deleted", student_summary)
    db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/students/{student_id}/records/{resource}", status_code=status.HTTP_201_CREATED)
def create_admin_student_record(
    student_id: str,
    resource: str,
    payload: dict[str, Any] = Body(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    student = _admin_student(db, student_id)
    config = STUDENT_RECORD_TYPES.get(resource)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student record type not supported")
    model, schema, owner_field = config
    values = _validate_record(schema, payload)
    if model is LearningActivity and values.get("completed_at") is None:
        values["completed_at"] = datetime.now(UTC)
    if model is Team:
        values["owner_id"] = student.id
    else:
        values["user_id"] = student.id
    record = model(**values)
    db.add(record)
    db.flush()
    record_id = record.id
    if model is Team:
        db.add(TeamMember(team_id=record.id, user_id=student.id, role="owner"))
        db.add(
            PortfolioProject(
                user_id=student.id,
                team_id=record.id,
                title=record.project_name,
                description=record.description,
                status="in_progress",
            )
        )
    _record_admin_action(
        db,
        admin,
        "admin.student_record.created",
        {"student_id": student.id, "record_type": resource, "record_id": record_id},
    )
    db.commit()
    db.refresh(record)
    return jsonable_encoder(record)


@router.patch("/students/{student_id}/records/{resource}/{record_id}")
def update_admin_student_record(
    student_id: str,
    resource: str,
    record_id: str,
    payload: dict[str, Any] = Body(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    student = _admin_student(db, student_id)
    config = STUDENT_RECORD_TYPES.get(resource)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student record type not supported")
    model, schema, owner_field = config
    owner_column = getattr(model, owner_field)
    record = db.query(model).filter(model.id == _record_lookup_id(model, record_id), owner_column == student.id).first()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student record not found")
    allowed_fields = set(schema.model_fields)
    unknown_fields = set(payload) - allowed_fields
    if unknown_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unsupported fields: {', '.join(sorted(unknown_fields))}",
        )
    existing = {field: getattr(record, field) for field in allowed_fields}
    values = _validate_record(schema, {**existing, **payload})
    for field in payload:
        setattr(record, field, values[field])
    _record_admin_action(
        db,
        admin,
        "admin.student_record.updated",
        {"student_id": student.id, "record_type": resource, "record_id": record.id, "fields": sorted(payload)},
    )
    db.commit()
    db.refresh(record)
    return jsonable_encoder(record)


@router.delete("/students/{student_id}/records/{resource}/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_student_record(
    student_id: str,
    resource: str,
    record_id: str,
    response: Response,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    student = _admin_student(db, student_id)
    config = STUDENT_RECORD_TYPES.get(resource)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student record type not supported")
    model, _, owner_field = config
    owner_column = getattr(model, owner_field)
    record = db.query(model).filter(model.id == _record_lookup_id(model, record_id), owner_column == student.id).first()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student record not found")
    if model is Team:
        _delete_team_records(db, record.id)
    record_key = record.id
    db.delete(record)
    _record_admin_action(
        db,
        admin,
        "admin.student_record.deleted",
        {"student_id": student.id, "record_type": resource, "record_id": record_key},
    )
    db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/students/{student_id}/activities/{activity_type}", status_code=status.HTTP_201_CREATED)
def create_admin_student_activity(
    student_id: str,
    activity_type: str,
    payload: dict[str, Any] = Body(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    student = _admin_student(db, student_id)
    if activity_type == "notifications":
        values = _validate_record(AdminStudentNotificationCreate, payload)
        activity = Notification(user_id=student.id, **values)
    elif activity_type == "applications":
        values = _validate_record(AdminStudentApplicationCreate, payload)
        opportunity = db.query(Opportunity).filter(Opportunity.id == values["opportunity_id"]).first()
        if opportunity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
        if db.query(OpportunityApplication.id).filter(
            OpportunityApplication.user_id == student.id,
            OpportunityApplication.opportunity_id == opportunity.id,
        ).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student already applied to this opportunity")
        activity = OpportunityApplication(user_id=student.id, opportunity_id=opportunity.id)
    elif activity_type == "saved-opportunities":
        values = _validate_record(AdminStudentSavedOpportunityCreate, payload)
        opportunity = db.query(Opportunity).filter(Opportunity.id == values["opportunity_id"]).first()
        if opportunity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
        if db.query(SavedOpportunity.id).filter(
            SavedOpportunity.user_id == student.id,
            SavedOpportunity.opportunity_id == opportunity.id,
        ).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Opportunity is already saved")
        activity = SavedOpportunity(user_id=student.id, opportunity_id=opportunity.id)
    elif activity_type == "team-memberships":
        values = _validate_record(AdminTeamMembershipCreate, payload)
        team = db.query(Team).filter(Team.id == values["team_id"]).first()
        if team is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
        if db.query(TeamMember.id).filter(
            TeamMember.team_id == team.id, TeamMember.user_id == student.id
        ).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student is already a team member")
        member_count = db.query(TeamMember.id).filter(TeamMember.team_id == team.id).count()
        if member_count >= team.team_size:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Team has reached its size limit")
        activity = TeamMember(team_id=team.id, user_id=student.id, role=values["role"])
        team.open_positions = max(0, team.open_positions - 1)
    elif activity_type == "project-tasks":
        values = _validate_record(AdminProjectTaskCreate, payload)
        team_id = values.pop("team_id")
        team = db.query(Team).filter(Team.id == team_id).first()
        if team is None or (
            team.owner_id != student.id
            and not db.query(TeamMember.id).filter(
                TeamMember.team_id == team.id, TeamMember.user_id == student.id
            ).first()
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student team not found")
        assignee_id = values.pop("assignee_id", None)
        if assignee_id and not db.query(TeamMember.id).filter(
            TeamMember.team_id == team.id, TeamMember.user_id == assignee_id
        ).first():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Assignee must belong to the team")
        activity = ProjectTask(team_id=team.id, created_by=student.id, assignee_id=assignee_id, **values)
    elif activity_type == "project-contributions":
        values = _validate_record(AdminProjectContributionCreate, payload)
        team = db.query(Team).filter(Team.id == values["team_id"]).first()
        if team is None or (
            team.owner_id != student.id
            and not db.query(TeamMember.id).filter(
                TeamMember.team_id == team.id, TeamMember.user_id == student.id
            ).first()
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student team not found")
        team_id = values.pop("team_id")
        activity = ProjectContribution(team_id=team_id, user_id=student.id, **values)
    elif activity_type == "team-invitations":
        values = _validate_record(AdminTeamInvitationCreate, payload)
        team = db.query(Team).filter(Team.id == values["team_id"]).first()
        invitee = _admin_student(db, values["invitee_id"])
        if team is None or (
            team.owner_id != student.id
            and not db.query(TeamMember.id).filter(
                TeamMember.team_id == team.id, TeamMember.user_id == student.id
            ).first()
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student team not found")
        if team.open_positions <= 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Team has no open positions")
        if db.query(TeamMember.id).filter(
            TeamMember.team_id == team.id, TeamMember.user_id == invitee.id
        ).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student is already on this team")
        activity = TeamInvitation(team_id=team.id, inviter_id=student.id, invitee_id=invitee.id)
        db.add(Notification(
            user_id=invitee.id,
            title="Team invitation",
            message=f"{student.full_name} invited you to join {team.name}.",
        ))
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student activity type not supported")

    db.add(activity)
    db.flush()
    activity_id = activity.id
    _record_admin_action(
        db,
        admin,
        "admin.student_activity.created",
        {"student_id": student.id, "activity_type": activity_type, "activity_id": activity_id},
    )
    db.commit()
    db.refresh(activity)
    return jsonable_encoder(activity)


@router.patch("/students/{student_id}/activities/{activity_type}/{activity_id}")
def update_admin_student_activity(
    student_id: str,
    activity_type: str,
    activity_id: str,
    payload: dict[str, Any] = Body(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    student = _admin_student(db, student_id)
    updated_fields: list[str]
    if activity_type == "notifications":
        activity = db.query(Notification).filter(
            Notification.id == activity_id, Notification.user_id == student.id
        ).first()
        schema = AdminStudentNotificationUpdate
        if activity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        values = _validate_record(schema, payload)
        updated_fields = list(payload)
        for field in updated_fields:
            setattr(activity, field, values[field])
    elif activity_type == "applications":
        activity = db.query(OpportunityApplication).filter(
            OpportunityApplication.id == activity_id, OpportunityApplication.user_id == student.id
        ).first()
        if activity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        values = _validate_record(AdminStudentApplicationUpdate, payload)
        activity.status = values["status"]
        updated_fields = ["status"]
    elif activity_type == "team-memberships":
        activity = db.query(TeamMember).filter(
            TeamMember.id == activity_id, TeamMember.user_id == student.id
        ).first()
        if activity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team membership not found")
        values = _validate_record(AdminTeamMembershipUpdate, payload)
        activity.role = values["role"]
        updated_fields = ["role"]
    elif activity_type == "team-invitations":
        activity = db.query(TeamInvitation).filter(
            TeamInvitation.id == activity_id,
            or_(TeamInvitation.inviter_id == student.id, TeamInvitation.invitee_id == student.id),
        ).first()
        if activity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team invitation not found")
        values = _validate_record(AdminTeamInvitationUpdate, payload)
        previous_status = activity.status
        next_status = values["status"]
        team = db.query(Team).filter(Team.id == activity.team_id).first()
        if next_status == "accepted" and previous_status != "accepted":
            member_count = db.query(TeamMember.id).filter(TeamMember.team_id == activity.team_id).count()
            if team is None or team.status != "open" or team.open_positions <= 0 or member_count >= team.team_size:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Team cannot accept another member")
            if not db.query(TeamMember.id).filter(
                TeamMember.team_id == activity.team_id, TeamMember.user_id == activity.invitee_id
            ).first():
                db.add(TeamMember(team_id=activity.team_id, user_id=activity.invitee_id))
                team.open_positions -= 1
        elif previous_status == "accepted" and next_status != "accepted":
            db.query(TeamMember).filter(
                TeamMember.team_id == activity.team_id, TeamMember.user_id == activity.invitee_id
            ).delete(synchronize_session=False)
            if team is not None:
                team.open_positions = min(team.team_size, team.open_positions + 1)
        activity.status = next_status
        updated_fields = ["status"]
    elif activity_type == "project-tasks":
        activity = db.query(ProjectTask).filter(ProjectTask.id == activity_id).first()
        if activity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project task not found")
        team = db.query(Team).filter(Team.id == activity.team_id).first()
        if team is None or (
            team.owner_id != student.id
            and not db.query(TeamMember.id).filter(
                TeamMember.team_id == team.id, TeamMember.user_id == student.id
            ).first()
            and activity.assignee_id != student.id
            and activity.created_by != student.id
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project task not found")
        values = _validate_record(ProjectTaskUpdate, payload)
        if values.get("assignee_id") and not db.query(TeamMember.id).filter(
            TeamMember.team_id == activity.team_id, TeamMember.user_id == values["assignee_id"]
        ).first():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Assignee must belong to the team")
        updated_fields = list(payload)
        for field in updated_fields:
            setattr(activity, field, values[field])
    elif activity_type == "project-contributions":
        activity = db.query(ProjectContribution).filter(
            ProjectContribution.id == activity_id, ProjectContribution.user_id == student.id
        ).first()
        if activity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project contribution not found")
        values = _validate_record(AdminProjectContributionUpdate, payload)
        updated_fields = list(payload)
        for field in updated_fields:
            setattr(activity, field, values[field])
    elif activity_type == "support-tickets":
        activity = db.query(SupportTicket).filter(
            SupportTicket.id == activity_id, SupportTicket.user_id == student.id
        ).first()
        if activity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")
        values = _validate_record(AdminTicketStatusUpdate, payload)
        activity.status = values["status"]
        activity.updated_at = datetime.now(UTC)
        updated_fields = ["status"]
    elif activity_type == "settings":
        if activity_id != student.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student settings not found")
        activity = db.query(StudentSettings).filter(StudentSettings.user_id == student.id).first()
        values = _validate_record(AdminStudentSettingsUpdate, payload)
        if activity is None:
            activity = StudentSettings(user_id=student.id)
            db.add(activity)
        updated_fields = list(payload)
        for field in updated_fields:
            setattr(activity, field, values[field])
        if values.get("profile_visibility") is not None:
            profile = db.query(UserProfile).filter(UserProfile.user_id == student.id).first()
            if profile is None:
                profile = UserProfile(user_id=student.id)
                db.add(profile)
            profile.profile_visibility = values["profile_visibility"]
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student activity type not supported")

    _record_admin_action(
        db,
        admin,
        "admin.student_activity.updated",
        {
            "student_id": student.id,
            "activity_type": activity_type,
            "activity_id": activity_id,
            "fields": sorted(updated_fields),
        },
    )
    db.commit()
    db.refresh(activity)
    return jsonable_encoder(activity)


@router.delete("/students/{student_id}/activities/{activity_type}/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_student_activity(
    student_id: str,
    activity_type: str,
    activity_id: str,
    response: Response,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    student = _admin_student(db, student_id)
    model_map = {
        "assessment-attempts": (AssessmentAttempt, AssessmentAttempt.user_id),
        "applications": (OpportunityApplication, OpportunityApplication.user_id),
        "saved-opportunities": (SavedOpportunity, SavedOpportunity.user_id),
        "notifications": (Notification, Notification.user_id),
        "sessions": (UserSession, UserSession.user_id),
        "team-memberships": (TeamMember, TeamMember.user_id),
        "team-invitations": (TeamInvitation, None),
        "project-tasks": (ProjectTask, None),
        "project-contributions": (ProjectContribution, ProjectContribution.user_id),
        "support-tickets": (SupportTicket, SupportTicket.user_id),
    }
    if activity_type == "settings":
        if activity_id != student.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student settings not found")
        record = db.query(StudentSettings).filter(StudentSettings.user_id == student.id).first()
    else:
        entry = model_map.get(activity_type)
        if entry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student activity type not supported")
        model, owner_column = entry
        query = db.query(model).filter(model.id == activity_id)
        if activity_type == "team-invitations":
            query = query.filter(or_(TeamInvitation.inviter_id == student.id, TeamInvitation.invitee_id == student.id))
        elif activity_type == "project-tasks":
            student_team_ids = db.query(Team.id).outerjoin(
                TeamMember, TeamMember.team_id == Team.id
            ).filter(or_(Team.owner_id == student.id, TeamMember.user_id == student.id))
            query = query.filter(
                or_(
                    ProjectTask.created_by == student.id,
                    ProjectTask.assignee_id == student.id,
                    ProjectTask.team_id.in_(student_team_ids),
                )
            )
        else:
            query = query.filter(owner_column == student.id)
        record = query.first()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student activity not found")

    if activity_type == "sessions" and record.revoked_at is None:
        record.revoked_at = datetime.now(UTC)
    elif activity_type == "team-memberships":
        team = db.query(Team).filter(Team.id == record.team_id).first()
        db.delete(record)
        if team is not None and team.owner_id != student.id:
            team.open_positions = min(team.team_size, team.open_positions + 1)
    elif activity_type == "team-invitations" and record.status == "accepted":
        team = db.query(Team).filter(Team.id == record.team_id).first()
        db.query(TeamMember).filter(
            TeamMember.team_id == record.team_id,
            TeamMember.user_id == record.invitee_id,
        ).delete(synchronize_session=False)
        if team is not None:
            team.open_positions = min(team.team_size, team.open_positions + 1)
        db.delete(record)
    else:
        if activity_type == "support-tickets":
            db.query(SupportMessage).filter(SupportMessage.ticket_id == record.id).delete(synchronize_session=False)
        db.delete(record)

    _record_admin_action(
        db,
        admin,
        "admin.student_activity.deleted",
        {"student_id": student.id, "activity_type": activity_type, "activity_id": activity_id},
    )
    db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.patch("/users/{user_id}")
def update_user(
    user_id: str,
    payload: AdminUserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    values = payload.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="No user changes provided")

    is_admin = any(role.name.lower() in {"admin", "super-admin", "super_admin"} for role in user.roles)
    if is_admin and not _is_super_admin(admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only a super-admin can manage admin accounts")
    if user.id == admin.id and values.get("is_active") is False:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You cannot deactivate your own account")
    if is_admin and values.get("is_active") is False:
        active_admins = (
            db.query(User)
            .join(User.roles)
            .filter(
                Role.name.in_(["admin", "super-admin", "super_admin"]),
                User.is_active.is_(True),
            )
            .count()
        )
        if active_admins <= 1:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot deactivate the last active administrator")

    for field, value in values.items():
        setattr(user, field, value)
    _record_admin_action(
        db,
        admin,
        "admin.user.updated",
        {"user_id": user.id, "changes": values},
    )
    db.commit()
    db.refresh(user)
    return _user_summary(user, db)


@router.get("/organizations")
def list_organizations(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    organizations: list[dict[str, object]] = []
    for model, name_field in (
        (InstitutionProfile, InstitutionProfile.institution_name),
        (CompanyProfile, CompanyProfile.company_name),
        (InvestorProfile, InvestorProfile.organization_name),
    ):
        rows = db.query(model, User).join(User, model.user_id == User.id).order_by(model.created_at.desc()).all()
        kind = {
            InstitutionProfile: "college_admin",
            CompanyProfile: "company",
            InvestorProfile: "investor",
        }[model]
        for profile, user in rows:
            organizations.append(
                {
                    "user_id": user.id,
                    "user_type": kind,
                    "name": getattr(profile, name_field.key) or user.full_name,
                    "email": user.email,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "created_at": profile.created_at,
                }
            )
    organizations.sort(key=lambda item: item["created_at"], reverse=True)
    return jsonable_encoder(organizations)


@router.get("/opportunities")
def list_admin_opportunities(
    q: str | None = Query(default=None, max_length=150),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Opportunity)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(or_(Opportunity.title.ilike(pattern), Opportunity.organization.ilike(pattern)))
    rows = query.order_by(Opportunity.created_at.desc()).limit(200).all()
    return [
        {
            **jsonable_encoder(item),
            "publisher_email": db.query(User.email).filter(User.id == item.publisher_id).scalar(),
        }
        for item in rows
    ]


@router.patch("/opportunities/{opportunity_id}")
def moderate_opportunity(
    opportunity_id: str,
    payload: AdminOpportunityUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    opportunity.is_active = payload.is_active
    _record_admin_action(
        db,
        admin,
        "admin.opportunity.moderated",
        {"opportunity_id": opportunity.id, "is_active": opportunity.is_active},
    )
    db.commit()
    db.refresh(opportunity)
    return jsonable_encoder(opportunity)


@router.get("/support/tickets")
def list_admin_tickets(
    ticket_status: str | None = Query(default=None, alias="status", pattern="^(open|in_progress|closed)$"),
    q: str | None = Query(default=None, max_length=150),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(SupportTicket).join(User, SupportTicket.user_id == User.id)
    if ticket_status:
        query = query.filter(SupportTicket.status == ticket_status)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(or_(SupportTicket.subject.ilike(pattern), User.email.ilike(pattern)))
    rows = query.order_by(SupportTicket.updated_at.desc()).limit(200).all()
    return [
        {
            **jsonable_encoder(ticket),
            "user_email": db.query(User.email).filter(User.id == ticket.user_id).scalar(),
            "message_count": db.query(SupportMessage).filter(SupportMessage.ticket_id == ticket.id).count(),
        }
        for ticket in rows
    ]


@router.get("/support/tickets/{ticket_id}")
def admin_ticket_detail(
    ticket_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")
    messages = db.query(SupportMessage).filter(
        SupportMessage.ticket_id == ticket.id
    ).order_by(SupportMessage.created_at.asc()).all()
    return {
        "ticket": {
            **jsonable_encoder(ticket),
            "user_email": db.query(User.email).filter(User.id == ticket.user_id).scalar(),
        },
        "messages": [
            {
                **jsonable_encoder(message),
                "sender_name": db.query(User.full_name).filter(User.id == message.sender_id).scalar(),
            }
            for message in messages
        ],
    }


@router.post("/support/tickets/{ticket_id}/responses", status_code=status.HTTP_201_CREATED)
def admin_respond_to_ticket(
    ticket_id: str,
    payload: AdminSupportResponse,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")
    message = SupportMessage(ticket_id=ticket.id, sender_id=admin.id, message=payload.message)
    ticket.status = "in_progress"
    notification = Notification(
        user_id=ticket.user_id,
        title="Support ticket updated",
        message=f"An administrator responded to '{ticket.subject}'.",
    )
    db.add_all([message, notification])
    _record_admin_action(db, admin, "admin.support.responded", {"ticket_id": ticket.id})
    db.commit()
    db.refresh(message)
    return jsonable_encoder(message)


@router.patch("/support/tickets/{ticket_id}")
def moderate_ticket_status(
    ticket_id: str,
    payload: AdminTicketStatusUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")
    ticket.status = payload.status
    _record_admin_action(
        db,
        admin,
        "admin.support.status_changed",
        {"ticket_id": ticket.id, "status": ticket.status},
    )
    db.commit()
    db.refresh(ticket)
    return jsonable_encoder(ticket)


@router.get("/activity")
def admin_activity(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    total = db.query(AuditLog).count()
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "items": [
            {
                "id": item.id,
                "actor": db.query(User.full_name).filter(User.id == item.user_id).scalar() if item.user_id else "System",
                "action": item.action,
                "details": item.details,
                "created_at": item.created_at,
            }
            for item in rows
        ],
        "total": total,
        "offset": offset,
        "limit": limit,
    }
