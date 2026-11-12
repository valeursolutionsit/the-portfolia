from datetime import UTC, datetime
from sqlalchemy import func

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.dependencies import get_student_user
from backend.app.models.student_portal import (
    AssessmentAttempt,
    Opportunity,
    PortfolioProject,
    StudentSkill,
    StudentSettings,
    TeamInvitation,
    TeamMember,
)
from backend.app.models.user import LearningActivity, User, UserProfile
from backend.app.schemas.portal import LearningRecordUpdate
from backend.app.schemas.student import (
    LearningActivityCreate,
    LearningActivityOut,
    StudentProfileOut,
    StudentProfileUpdate,
)

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/me", response_model=StudentProfileOut)
def get_student_profile(current_user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    return StudentProfileOut(
        user_id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        port_id=current_user.port_id,
        user_type=current_user.user_type,
        phone=profile.phone if profile else None,
        profile_photo_url=profile.profile_photo_url if profile else None,
        date_of_birth=profile.date_of_birth if profile else None,
        gender=profile.gender if profile else None,
        address=profile.address if profile else None,
        college_name=profile.college_name if profile else None,
        university=profile.university if profile else None,
        degree=profile.degree if profile else None,
        course=profile.course if profile else None,
        department=profile.department if profile else None,
        current_year=profile.current_year if profile else None,
        graduation_year=profile.graduation_year if profile else None,
        career_interests=profile.career_interests if profile else None,
        career_objective=profile.career_objective if profile else None,
        interested_industries=profile.interested_industries if profile else None,
        preferred_job_roles=profile.preferred_job_roles if profile else None,
        career_goals=profile.career_goals if profile else None,
        technical_skills=profile.technical_skills if profile else None,
        non_technical_skills=profile.non_technical_skills if profile else None,
        languages=profile.languages if profile else None,
        linkedin_url=profile.linkedin_url if profile else None,
        github_url=profile.github_url if profile else None,
        personal_website=profile.personal_website if profile else None,
        profile_visibility=profile.profile_visibility if profile else "private",
        bio=profile.bio if profile else None,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
    )


@router.put("/me", response_model=StudentProfileOut)
def update_student_profile(
    payload: StudentProfileUpdate,
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if profile is None:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    values = payload.model_dump(exclude_unset=True)
    if "full_name" in values:
        full_name = values.pop("full_name")
        if full_name is None or len(full_name.strip()) < 2:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Full name must contain at least 2 characters")
        current_user.full_name = full_name.strip()

    for field, value in values.items():
        if field in {"profile_photo_url", "linkedin_url", "github_url", "personal_website"} and value is not None:
            value = str(value)
        setattr(profile, field, value)
    if "profile_visibility" in values:
        settings = db.query(StudentSettings).filter(StudentSettings.user_id == current_user.id).first()
        if settings is not None:
            settings.profile_visibility = values["profile_visibility"]

    db.commit()
    db.refresh(profile)
    db.refresh(current_user)
    return get_student_profile(current_user=current_user, db=db)


@router.get("/learning-activities", response_model=list[LearningActivityOut])
def list_learning_activities(current_user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    activities = (
        db.query(LearningActivity)
        .filter(LearningActivity.user_id == current_user.id)
        .order_by(LearningActivity.completed_at.desc(), LearningActivity.id.desc())
        .all()
    )
    return activities


@router.post("/learning-activities", response_model=LearningActivityOut)
def create_learning_activity(
    payload: LearningActivityCreate,
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    activity = LearningActivity(
        user_id=current_user.id,
        title=payload.title.strip(),
        category=payload.category.strip(),
        topic=payload.topic,
        description=payload.description,
        what_i_practised=payload.what_i_practised,
        resource_url=str(payload.resource_url) if payload.resource_url else None,
        evidence_url=str(payload.evidence_url) if payload.evidence_url else None,
        confidence=payload.confidence,
        status=payload.status,
        duration_hours=payload.duration_hours,
        completed_at=payload.completed_at or datetime.now(UTC),
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@router.put("/learning-activities/{activity_id}", response_model=LearningActivityOut)
def update_learning_activity(
    activity_id: int,
    payload: LearningRecordUpdate,
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    activity = (
        db.query(LearningActivity)
        .filter(LearningActivity.id == activity_id, LearningActivity.user_id == current_user.id)
        .first()
    )
    if activity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning record not found")
    values = payload.model_dump(exclude_unset=True)
    for field, value in values.items():
        if value is not None:
            setattr(activity, field, str(value) if field in {"resource_url", "evidence_url"} else value)
    db.commit()
    db.refresh(activity)
    return activity


@router.get("/dashboard")
def student_dashboard(current_user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    activities = (
        db.query(LearningActivity)
        .filter(LearningActivity.user_id == current_user.id)
        .order_by(LearningActivity.completed_at.desc())
        .limit(5)
        .all()
    )
    all_activity_count = db.query(LearningActivity).filter(LearningActivity.user_id == current_user.id).count()
    total_hours = db.query(func.coalesce(func.sum(LearningActivity.duration_hours), 0)).filter(
        LearningActivity.user_id == current_user.id
    ).scalar()
    skills = db.query(StudentSkill).filter(StudentSkill.user_id == current_user.id).all()
    profile_fields = [
        current_user.full_name,
        profile.phone if profile else None,
        profile.college_name if profile else None,
        profile.degree if profile else None,
        profile.graduation_year if profile else None,
        profile.career_objective if profile else None,
        profile.technical_skills if profile else None,
        profile.non_technical_skills if profile else None,
        profile.languages if profile else None,
        profile.profile_photo_url if profile else None,
        profile.linkedin_url if profile else None,
        profile.github_url if profile else None,
    ]
    profile_completion = round(100 * sum(bool(value) for value in profile_fields) / len(profile_fields))
    today_count = (
        db.query(LearningActivity)
        .filter(
            LearningActivity.user_id == current_user.id,
            func.date(LearningActivity.completed_at) == datetime.now(UTC).date().isoformat(),
        )
        .count()
    )
    project_count = db.query(PortfolioProject).filter(PortfolioProject.user_id == current_user.id).count()
    assessments = (
        db.query(AssessmentAttempt)
        .filter(AssessmentAttempt.user_id == current_user.id)
        .order_by(AssessmentAttempt.started_at.desc())
        .all()
    )
    teams = db.query(TeamMember.team_id).filter(TeamMember.user_id == current_user.id).distinct().count()
    invitations = db.query(TeamInvitation).filter(
        TeamInvitation.invitee_id == current_user.id, TeamInvitation.status == "pending"
    ).count()
    opportunities = (
        db.query(Opportunity)
        .filter(Opportunity.is_active.is_(True))
        .order_by(Opportunity.created_at.desc())
        .limit(5)
        .all()
    )
    recent_records = [
        {
            "type": "learning",
            "title": item.title,
            "occurred_at": item.completed_at.isoformat(),
        }
        for item in activities
    ]
    recent_records.extend(
        {
            "type": "project",
            "title": item.title,
            "occurred_at": item.created_at.isoformat(),
        }
        for item in db.query(PortfolioProject)
        .filter(PortfolioProject.user_id == current_user.id)
        .order_by(PortfolioProject.created_at.desc())
        .limit(5)
        .all()
    )
    recent_records.sort(key=lambda item: item["occurred_at"], reverse=True)
    return {
        "full_name": current_user.full_name,
        "port_id": current_user.port_id,
        "profile_photo_url": profile.profile_photo_url if profile else None,
        "profile_completion_percent": profile_completion,
        "skills": [{"name": skill.name, "category": skill.category, "proficiency": skill.proficiency} for skill in skills],
        "total_learning_activities": all_activity_count,
        "total_learning_hours": int(total_hours or 0),
        "daily_learning_activities": today_count,
        "skill_assessment_attempts": len(assessments),
        "latest_assessment_score": next((item.score for item in assessments if item.score is not None), None),
        "portfolio_project_count": project_count,
        "active_teams": teams,
        "team_invitations": invitations,
        "latest_opportunities": [
            {"id": item.id, "title": item.title, "organization": item.organization, "category": item.category}
            for item in opportunities
        ],
        "recent_activity": recent_records[:8],
    }
