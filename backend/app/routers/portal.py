from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password, verify_password
from backend.app.database import get_db
from backend.app.dependencies import get_current_user, get_opportunity_publisher, get_student_user
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
from backend.app.models.user import LearningActivity, User, UserProfile
from backend.app.schemas.portal import (
    AchievementCreate,
    AssessmentSubmit,
    CertificationCreate,
    ContributionCreate,
    LearningMilestoneCreate,
    LearningPathCreate,
    LearningResourceCreate,
    OpportunityCreate,
    OpportunityApplicationStatusUpdate,
    PasswordChange,
    ProjectCreate,
    ProjectTaskCreate,
    ProjectTaskUpdate,
    StudentSettingsUpdate,
    StudentSkillCreate,
    SupportMessageCreate,
    SupportTicketStatusUpdate,
    TeamCreate,
    TeamInvitationCreate,
    TicketCreate,
    WorkExperienceCreate,
)

router = APIRouter(tags=["student-portal"])


def _encoded(item: Any) -> Any:
    return jsonable_encoder(item)


def _team_member(db: Session, team_id: str, user_id: str) -> TeamMember:
    member = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Team membership required")
    return member


@router.get("/students/skills")
def list_skills(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    skills = db.query(StudentSkill).filter(StudentSkill.user_id == user.id).order_by(StudentSkill.name).all()
    return _encoded(skills)


@router.post("/students/skills", status_code=status.HTTP_201_CREATED)
def create_skill(payload: StudentSkillCreate, user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    skill = StudentSkill(
        user_id=user.id,
        name=payload.name.strip(),
        category=payload.category.strip().lower(),
        proficiency=payload.proficiency,
        evidence_url=str(payload.evidence_url) if payload.evidence_url else None,
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return _encoded(skill)


@router.delete("/students/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(skill_id: str, user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    skill = db.query(StudentSkill).filter(StudentSkill.id == skill_id, StudentSkill.user_id == user.id).first()
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    db.delete(skill)
    db.commit()


@router.get("/learning/paths")
def list_learning_paths(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    paths = db.query(LearningPath).filter(LearningPath.user_id == user.id).order_by(LearningPath.created_at.desc()).all()
    return _encoded(paths)


@router.post("/learning/paths", status_code=status.HTTP_201_CREATED)
def create_learning_path(payload: LearningPathCreate, user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    path = LearningPath(user_id=user.id, **payload.model_dump())
    db.add(path)
    db.commit()
    db.refresh(path)
    return _encoded(path)


@router.get("/learning/milestones")
def list_learning_milestones(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    rows = db.query(LearningMilestone).filter(LearningMilestone.user_id == user.id).order_by(LearningMilestone.created_at.desc()).all()
    return _encoded(rows)


@router.post("/learning/milestones", status_code=status.HTTP_201_CREATED)
def create_learning_milestone(payload: LearningMilestoneCreate, user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    milestone = LearningMilestone(user_id=user.id, **payload.model_dump())
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return _encoded(milestone)


@router.patch("/learning/milestones/{milestone_id}")
def complete_learning_milestone(
    milestone_id: str,
    user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    milestone = db.query(LearningMilestone).filter(
        LearningMilestone.id == milestone_id, LearningMilestone.user_id == user.id
    ).first()
    if milestone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")
    milestone.status = "completed" if milestone.status != "completed" else "planned"
    db.commit()
    db.refresh(milestone)
    return _encoded(milestone)


@router.get("/learning/resources")
def list_learning_resources(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    rows = db.query(LearningResource).filter(LearningResource.user_id == user.id).order_by(LearningResource.created_at.desc()).all()
    return _encoded(rows)


@router.post("/learning/resources", status_code=status.HTTP_201_CREATED)
def create_learning_resource(payload: LearningResourceCreate, user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    values = payload.model_dump()
    values["url"] = str(payload.url)
    resource = LearningResource(user_id=user.id, **values)
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return _encoded(resource)


@router.get("/learning/progress")
def learning_progress(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    activities = db.query(
        LearningActivity.category,
        LearningActivity.topic,
        LearningActivity.status,
        LearningActivity.duration_hours,
    ).filter(LearningActivity.user_id == user.id).all()
    by_skill: dict[str, dict[str, int]] = {}
    for activity in activities:
        skill = activity.topic or activity.category or "General"
        summary = by_skill.setdefault(skill, {"activities": 0, "completed": 0, "hours": 0, "progress_percent": 0})
        summary["activities"] += 1
        summary["completed"] += int(activity.status == "completed")
        summary["hours"] += activity.duration_hours or 0
    for summary in by_skill.values():
        summary["progress_percent"] = round(100 * summary["completed"] / summary["activities"])
    return {"by_skill": by_skill, "activities_total": len(activities)}


@router.get("/learning/timeline")
def learning_timeline(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    activities = db.query(LearningActivity).filter(
        LearningActivity.user_id == user.id
    ).order_by(LearningActivity.completed_at.desc()).all()
    milestones = db.query(LearningMilestone).filter(
        LearningMilestone.user_id == user.id
    ).order_by(LearningMilestone.created_at.desc()).all()
    items = [
        {
            "type": "learning",
            "id": activity.id,
            "title": activity.title,
            "skill": activity.topic or activity.category,
            "status": activity.status,
            "occurred_at": activity.completed_at,
        }
        for activity in activities
    ]
    items.extend(
        {
            "type": "milestone",
            "id": milestone.id,
            "title": milestone.title,
            "skill": milestone.skill_name,
            "status": milestone.status,
            "occurred_at": milestone.created_at,
        }
        for milestone in milestones
    )
    return _encoded(sorted(items, key=lambda item: item["occurred_at"], reverse=True))


@router.get("/assessments")
def assessment_catalogue(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    assessments = db.query(SkillAssessment).filter(SkillAssessment.is_active.is_(True)).order_by(SkillAssessment.category).all()
    catalogue = []
    for item in assessments:
        questions = db.query(AssessmentQuestion).filter(
            AssessmentQuestion.assessment_id == item.id
        ).all()
        if len(questions) != 30 or any(question.question_type != "multiple_choice" for question in questions):
            continue
        catalogue.append(
            {
                "id": item.id,
                "category": item.category,
                "title": item.title,
                "description": item.description,
                "duration_minutes": item.duration_minutes,
                "question_count": len(questions),
            }
        )
    return catalogue


@router.post("/assessments/{assessment_id}/attempts", status_code=status.HTTP_201_CREATED)
def start_assessment(
    assessment_id: str,
    user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    assessment = db.query(SkillAssessment).filter(
        SkillAssessment.id == assessment_id, SkillAssessment.is_active.is_(True)
    ).first()
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    questions = db.query(AssessmentQuestion).filter(
        AssessmentQuestion.assessment_id == assessment.id
    ).all()
    if len(questions) != 30 or any(question.question_type != "multiple_choice" for question in questions):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    attempt = AssessmentAttempt(user_id=user.id, assessment_id=assessment.id, answers={})
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return {
        "attempt_id": attempt.id,
        "assessment_id": assessment.id,
        "title": assessment.title,
        "duration_minutes": assessment.duration_minutes,
        "started_at": attempt.started_at,
        "questions": [
            {
                "id": question.id,
                "prompt": question.prompt,
                "question_type": question.question_type,
                "options": question.options,
                "topic": question.topic,
                "points": question.points,
            }
            for question in questions
        ],
    }


@router.post("/assessments/attempts/{attempt_id}/submit")
def submit_assessment(
    attempt_id: str,
    payload: AssessmentSubmit,
    user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    attempt = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.id == attempt_id, AssessmentAttempt.user_id == user.id
    ).first()
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment attempt not found")
    if attempt.completed_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Assessment attempt is already submitted")
    assessment = db.query(SkillAssessment).filter(SkillAssessment.id == attempt.assessment_id).first()
    now = datetime.now(UTC)
    started_at = attempt.started_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=UTC)
    if assessment and assessment.duration_minutes and now - started_at > timedelta(minutes=assessment.duration_minutes):
        questions = db.query(AssessmentQuestion).filter(AssessmentQuestion.assessment_id == assessment.id).all()
        attempt.answers = {}
        attempt.score = 0
        attempt.max_score = sum(question.points for question in questions)
        attempt.topic_scores = {
            topic: {"score": 0, "max_score": points}
            for topic, points in _topic_max_scores(questions).items()
        }
        attempt.completed_at = now
        db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Assessment time has expired; the attempt was scored")
    questions = db.query(AssessmentQuestion).filter(AssessmentQuestion.assessment_id == attempt.assessment_id).all()
    known_ids = {question.id for question in questions}
    if set(payload.answers) - known_ids:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Answers contain unknown question IDs")
    score = 0
    maximum = 0
    topic_scores: dict[str, dict[str, int]] = {}
    for question in questions:
        maximum += question.points
        topic = question.topic or "General"
        topic_scores.setdefault(topic, {"score": 0, "max_score": 0})
        topic_scores[topic]["max_score"] += question.points
        answer = payload.answers.get(question.id)
        expected = question.answer_key
        if isinstance(expected, list):
            correct = sorted(str(value) for value in (answer or [])) == sorted(str(value) for value in expected)
        else:
            correct = str(answer).strip().casefold() == str(expected).strip().casefold()
        if correct:
            score += question.points
            topic_scores[topic]["score"] += question.points
    attempt.answers = payload.answers
    attempt.score = score
    attempt.max_score = maximum
    attempt.topic_scores = topic_scores
    attempt.completed_at = now
    db.commit()
    db.refresh(attempt)
    return _encoded(attempt)


def _topic_max_scores(questions: list[AssessmentQuestion]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for question in questions:
        topic = question.topic or "General"
        totals[topic] = totals.get(topic, 0) + question.points
    return totals


@router.get("/assessments/attempts")
def list_assessment_attempts(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    attempts = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.user_id == user.id
    ).order_by(AssessmentAttempt.started_at.desc()).all()
    return [
        {
            **_encoded(item),
            "assessment_title": db.query(SkillAssessment.title).filter(SkillAssessment.id == item.assessment_id).scalar(),
        }
        for item in attempts
    ]


@router.get("/portfolios/projects")
def list_portfolio_projects(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    projects = db.query(PortfolioProject).filter(
        PortfolioProject.user_id == user.id
    ).order_by(PortfolioProject.updated_at.desc()).all()
    return _encoded(projects)


@router.post("/portfolios/projects", status_code=status.HTTP_201_CREATED)
def create_portfolio_project(payload: ProjectCreate, user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    values = payload.model_dump()
    values["github_url"] = str(payload.github_url) if payload.github_url else None
    values["live_url"] = str(payload.live_url) if payload.live_url else None
    values["evidence_urls"] = [str(url) for url in payload.evidence_urls]
    project = PortfolioProject(user_id=user.id, **values)
    db.add(project)
    db.commit()
    db.refresh(project)
    return _encoded(project)


@router.put("/portfolios/projects/{project_id}")
def update_portfolio_project(
    project_id: str,
    payload: ProjectCreate,
    user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    project = db.query(PortfolioProject).filter(
        PortfolioProject.id == project_id, PortfolioProject.user_id == user.id
    ).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio project not found")
    values = payload.model_dump()
    values["github_url"] = str(payload.github_url) if payload.github_url else None
    values["live_url"] = str(payload.live_url) if payload.live_url else None
    values["evidence_urls"] = [str(url) for url in payload.evidence_urls]
    for field, value in values.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return _encoded(project)


@router.get("/portfolios/public/{port_id}")
def public_portfolio(port_id: str, db: Session = Depends(get_db)):
    owner = db.query(User).filter(User.port_id == port_id, User.is_active.is_(True)).first()
    if owner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Public portfolio not found")
    profile = db.query(UserProfile).filter(UserProfile.user_id == owner.id).first()
    if profile is None or profile.profile_visibility != "public":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Public portfolio not found")
    settings = db.query(StudentSettings).filter(StudentSettings.user_id == owner.id).first()
    privacy = settings.privacy_settings if settings else {}
    projects = (
        db.query(PortfolioProject)
        .filter(PortfolioProject.user_id == owner.id, PortfolioProject.is_public.is_(True))
        .order_by(PortfolioProject.created_at.desc())
        .all()
        if privacy.get("privacy_show_projects", True)
        else []
    )
    skills = (
        db.query(StudentSkill).filter(StudentSkill.user_id == owner.id).all()
        if privacy.get("privacy_show_skills", False)
        else []
    )
    return {
        "full_name": owner.full_name,
        "port_id": owner.port_id,
        "bio": profile.bio,
        "skills": [{"name": skill.name, "category": skill.category, "proficiency": skill.proficiency} for skill in skills],
        "projects": [
            {
                "title": project.title,
                "description": project.description,
                "technologies": project.technologies,
                "github_url": project.github_url,
                "live_url": project.live_url,
                "key_learnings": project.key_learnings,
            }
            for project in projects
        ],
    }


@router.get("/portfolios/certifications")
def list_certifications(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    return _encoded(db.query(Certification).filter(Certification.user_id == user.id).order_by(Certification.created_at.desc()).all())


@router.post("/portfolios/certifications", status_code=status.HTTP_201_CREATED)
def add_certification(payload: CertificationCreate, user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    values = payload.model_dump()
    values["credential_url"] = str(payload.credential_url) if payload.credential_url else None
    row = Certification(user_id=user.id, **values)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _encoded(row)


@router.get("/portfolios/achievements")
def list_achievements(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    return _encoded(db.query(Achievement).filter(Achievement.user_id == user.id).order_by(Achievement.created_at.desc()).all())


@router.post("/portfolios/achievements", status_code=status.HTTP_201_CREATED)
def add_achievement(payload: AchievementCreate, user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    row = Achievement(user_id=user.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _encoded(row)


@router.get("/portfolios/experience")
def list_work_experience(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    rows = db.query(WorkExperience).filter(
        WorkExperience.user_id == user.id
    ).order_by(WorkExperience.start_date.desc()).all()
    return _encoded(rows)


@router.get("/portfolios/contributions")
def list_portfolio_contributions(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    rows = db.query(ProjectContribution).filter(
        ProjectContribution.user_id == user.id
    ).order_by(ProjectContribution.created_at.desc()).all()
    return _encoded(rows)


@router.post("/portfolios/experience", status_code=status.HTTP_201_CREATED)
def add_work_experience(payload: WorkExperienceCreate, user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    if payload.start_date and payload.end_date and payload.end_date < payload.start_date:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="End date must be on or after start date")
    row = WorkExperience(user_id=user.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _encoded(row)


@router.get("/teams")
def discover_teams(
    q: str | None = Query(default=None, max_length=120),
    skill: str | None = Query(default=None, max_length=120),
    user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    query = db.query(Team).filter(Team.status == "open")
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(or_(Team.name.ilike(pattern), Team.project_name.ilike(pattern), Team.description.ilike(pattern)))
    rows = query.order_by(Team.created_at.desc()).all()
    if skill:
        skill_key = skill.casefold()
        rows = [team for team in rows if any(skill_key in item.casefold() for item in (team.required_skills or []))]
    return _encoded(rows)


@router.post("/teams", status_code=status.HTTP_201_CREATED)
def create_team(payload: TeamCreate, user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    team = Team(owner_id=user.id, **payload.model_dump())
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=user.id, role="owner"))
    db.add(
        PortfolioProject(
            user_id=user.id,
            team_id=team.id,
            title=payload.project_name,
            description=payload.description,
            status="in_progress",
        )
    )
    db.commit()
    db.refresh(team)
    return _encoded(team)


@router.get("/teams/mine")
def list_my_teams(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    memberships = db.query(TeamMember).filter(TeamMember.user_id == user.id).all()
    team_ids = [member.team_id for member in memberships]
    teams = db.query(Team).filter(Team.id.in_(team_ids)).order_by(Team.created_at.desc()).all() if team_ids else []
    return _encoded(teams)


@router.post("/teams/{team_id}/invitations", status_code=status.HTTP_201_CREATED)
def invite_to_team(
    team_id: str,
    payload: TeamInvitationCreate,
    user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    _team_member(db, team_id, user.id)
    invitee = db.query(User).filter(User.email == payload.email.strip().lower(), User.is_active.is_(True)).first()
    if invitee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student account not found")
    if invitee.user_type != "student":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invitations can only be sent to students")
    if team.open_positions <= 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Team has no open positions")
    if db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == invitee.id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student is already on this team")
    invitation = TeamInvitation(team_id=team_id, inviter_id=user.id, invitee_id=invitee.id)
    db.add(invitation)
    db.add(
        Notification(
            user_id=invitee.id,
            title="Team invitation",
            message=f"{user.full_name} invited you to join {team.name}.",
        )
    )
    db.commit()
    db.refresh(invitation)
    return _encoded(invitation)


@router.get("/teams/invitations")
def list_team_invitations(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    rows = db.query(TeamInvitation).filter(
        TeamInvitation.invitee_id == user.id
    ).order_by(TeamInvitation.created_at.desc()).all()
    return [
        {
            **_encoded(row),
            "team_name": db.query(Team.name).filter(Team.id == row.team_id).scalar(),
        }
        for row in rows
    ]


@router.post("/teams/invitations/{invitation_id}/accept")
def accept_team_invitation(
    invitation_id: str,
    user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    invitation = db.query(TeamInvitation).filter(
        TeamInvitation.id == invitation_id, TeamInvitation.invitee_id == user.id
    ).first()
    if invitation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    if invitation.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invitation is no longer pending")
    team = db.query(Team).filter(Team.id == invitation.team_id).first()
    if team is None or team.status != "open":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Team is not accepting members")
    member_count = db.query(TeamMember).filter(TeamMember.team_id == team.id).count()
    if member_count >= team.team_size or team.open_positions <= 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Team has reached its size limit")
    invitation.status = "accepted"
    team.open_positions -= 1
    db.add(TeamMember(team_id=team.id, user_id=user.id))
    db.commit()
    return {"message": "Invitation accepted"}


@router.get("/teams/{team_id}/tasks")
def list_team_tasks(team_id: str, user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    _team_member(db, team_id, user.id)
    return _encoded(db.query(ProjectTask).filter(ProjectTask.team_id == team_id).order_by(ProjectTask.created_at.desc()).all())


@router.post("/teams/{team_id}/tasks", status_code=status.HTTP_201_CREATED)
def create_team_task(
    team_id: str,
    payload: ProjectTaskCreate,
    user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    _team_member(db, team_id, user.id)
    if payload.assignee_id:
        _team_member(db, team_id, payload.assignee_id)
    task = ProjectTask(team_id=team_id, created_by=user.id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return _encoded(task)


@router.patch("/teams/{team_id}/tasks/{task_id}")
def update_team_task(
    team_id: str,
    task_id: str,
    payload: ProjectTaskUpdate,
    user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    _team_member(db, team_id, user.id)
    task = db.query(ProjectTask).filter(ProjectTask.id == task_id, ProjectTask.team_id == team_id).first()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    values = payload.model_dump(exclude_unset=True)
    if values.get("assignee_id"):
        _team_member(db, team_id, values["assignee_id"])
    for field, value in values.items():
        if value is not None:
            setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return _encoded(task)


@router.get("/teams/{team_id}/contributions")
def list_contributions(team_id: str, user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    _team_member(db, team_id, user.id)
    return _encoded(
        db.query(ProjectContribution)
        .filter(ProjectContribution.team_id == team_id)
        .order_by(ProjectContribution.created_at.desc())
        .all()
    )


@router.post("/teams/{team_id}/contributions", status_code=status.HTTP_201_CREATED)
def add_contribution(
    team_id: str,
    payload: ContributionCreate,
    user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    _team_member(db, team_id, user.id)
    row = ProjectContribution(
        team_id=team_id,
        user_id=user.id,
        description=payload.description,
        evidence_url=str(payload.evidence_url) if payload.evidence_url else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _encoded(row)


@router.get("/opportunities")
def browse_opportunities(
    q: str | None = Query(default=None, max_length=150),
    category: str | None = Query(default=None, max_length=40),
    skill: str | None = Query(default=None, max_length=120),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Opportunity).filter(Opportunity.is_active.is_(True))
    if category:
        query = query.filter(Opportunity.category == category)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(or_(Opportunity.title.ilike(pattern), Opportunity.organization.ilike(pattern), Opportunity.description.ilike(pattern)))
    rows = query.order_by(Opportunity.created_at.desc()).all()
    if skill:
        skill_key = skill.casefold()
        rows = [row for row in rows if any(skill_key in item.casefold() for item in (row.required_skills or []))]
    return _encoded(rows)


@router.post("/opportunities", status_code=status.HTTP_201_CREATED)
def publish_opportunity(
    payload: OpportunityCreate,
    user: User = Depends(get_opportunity_publisher),
    db: Session = Depends(get_db),
):
    values = payload.model_dump()
    values["application_url"] = str(payload.application_url) if payload.application_url else None
    opportunity = Opportunity(publisher_id=user.id, **values)
    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)
    return _encoded(opportunity)


@router.post("/opportunities/{opportunity_id}/save", status_code=status.HTTP_201_CREATED)
def save_opportunity(opportunity_id: str, user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id, Opportunity.is_active.is_(True)).first()
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    saved = db.query(SavedOpportunity).filter(
        SavedOpportunity.user_id == user.id, SavedOpportunity.opportunity_id == opportunity.id
    ).first()
    if saved is not None:
        return _encoded(saved)
    saved = SavedOpportunity(user_id=user.id, opportunity_id=opportunity.id)
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return _encoded(saved)


@router.get("/opportunities/saved")
def list_saved_opportunities(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    rows = db.query(SavedOpportunity).filter(SavedOpportunity.user_id == user.id).order_by(SavedOpportunity.created_at.desc()).all()
    return [
        {"saved": _encoded(row), "opportunity": _encoded(db.query(Opportunity).filter(Opportunity.id == row.opportunity_id).first())}
        for row in rows
    ]


@router.post("/opportunities/{opportunity_id}/apply", status_code=status.HTTP_201_CREATED)
def apply_opportunity(opportunity_id: str, user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id, Opportunity.is_active.is_(True)).first()
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    application = db.query(OpportunityApplication).filter(
        OpportunityApplication.user_id == user.id, OpportunityApplication.opportunity_id == opportunity.id
    ).first()
    if application is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already applied")
    application = OpportunityApplication(user_id=user.id, opportunity_id=opportunity.id)
    db.add(application)
    db.commit()
    db.refresh(application)
    return _encoded(application)


@router.patch("/opportunities/applications/{application_id}")
def update_application_status(
    application_id: str,
    payload: OpportunityApplicationStatusUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = db.query(OpportunityApplication).filter(OpportunityApplication.id == application_id).first()
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    opportunity = db.query(Opportunity).filter(Opportunity.id == application.opportunity_id).first()
    is_admin = user.user_type in {"admin", "super-admin"} or any(
        role.name.lower() in {"admin", "super-admin", "super_admin"} for role in user.roles
    )
    if not is_admin and (opportunity is None or opportunity.publisher_id != user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the publisher can update this application")
    application.status = payload.status
    db.commit()
    db.refresh(application)
    return _encoded(application)


@router.get("/opportunities/applications")
def list_applications(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    rows = db.query(OpportunityApplication).filter(
        OpportunityApplication.user_id == user.id
    ).order_by(OpportunityApplication.created_at.desc()).all()
    return [
        {"application": _encoded(row), "opportunity": _encoded(db.query(Opportunity).filter(Opportunity.id == row.opportunity_id).first())}
        for row in rows
    ]


@router.get("/support/tickets")
def list_tickets(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    rows = db.query(SupportTicket).filter(SupportTicket.user_id == user.id).order_by(SupportTicket.updated_at.desc()).all()
    return _encoded(rows)


@router.post("/support/tickets", status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    ticket = SupportTicket(user_id=user.id, category=payload.category, subject=payload.subject)
    db.add(ticket)
    db.flush()
    db.add(SupportMessage(ticket_id=ticket.id, sender_id=user.id, message=payload.message))
    db.commit()
    db.refresh(ticket)
    return _encoded(ticket)


@router.get("/support/tickets/{ticket_id}")
def get_ticket(ticket_id: str, user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    ticket = db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id, SupportTicket.user_id == user.id
    ).first()
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")
    messages = db.query(SupportMessage).filter(
        SupportMessage.ticket_id == ticket.id
    ).order_by(SupportMessage.created_at.asc()).all()
    return {"ticket": _encoded(ticket), "messages": _encoded(messages)}


@router.post("/support/tickets/{ticket_id}/messages", status_code=status.HTTP_201_CREATED)
def add_ticket_message(
    ticket_id: str,
    payload: SupportMessageCreate,
    user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    ticket = db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id, SupportTicket.user_id == user.id
    ).first()
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")
    if ticket.status == "closed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ticket is closed")
    message = SupportMessage(ticket_id=ticket.id, sender_id=user.id, message=payload.message)
    ticket.updated_at = datetime.now(UTC)
    db.add(message)
    db.commit()
    db.refresh(message)
    return _encoded(message)


@router.post("/support/tickets/{ticket_id}/responses", status_code=status.HTTP_201_CREATED)
def add_support_response(
    ticket_id: str,
    payload: SupportMessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_support = user.user_type in {"admin", "super-admin"} or any(
        role.name.lower() in {"admin", "super-admin", "super_admin", "support"} for role in user.roles
    )
    if not is_support:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Support staff access required")
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")
    message = SupportMessage(ticket_id=ticket.id, sender_id=user.id, message=payload.message)
    ticket.status = "in_progress"
    ticket.updated_at = datetime.now(UTC)
    db.add(message)
    db.add(
        Notification(
            user_id=ticket.user_id,
            title="Support ticket updated",
            message=f"A support response was added to '{ticket.subject}'.",
        )
    )
    db.commit()
    db.refresh(message)
    return _encoded(message)


@router.patch("/support/tickets/{ticket_id}/status")
def update_ticket_status(
    ticket_id: str,
    payload: SupportTicketStatusUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_support = user.user_type in {"admin", "super-admin"} or any(
        role.name.lower() in {"admin", "super-admin", "super_admin", "support"} for role in user.roles
    )
    if not is_support:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Support staff access required")
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")
    ticket.status = payload.status
    ticket.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(ticket)
    return _encoded(ticket)


@router.get("/students/notifications")
def list_notifications(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    rows = db.query(Notification).filter(
        Notification.user_id == user.id
    ).order_by(Notification.created_at.desc()).limit(100).all()
    return _encoded(rows)


@router.patch("/students/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    row = db.query(Notification).filter(
        Notification.id == notification_id, Notification.user_id == user.id
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    row.is_read = True
    db.commit()
    db.refresh(row)
    return _encoded(row)


@router.get("/students/settings")
def get_student_settings(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    settings = db.query(StudentSettings).filter(StudentSettings.user_id == user.id).first()
    if settings is None:
        settings = StudentSettings(user_id=user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return _encoded(settings)


@router.put("/students/settings")
def update_student_settings(
    payload: StudentSettingsUpdate,
    user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    settings = db.query(StudentSettings).filter(StudentSettings.user_id == user.id).first()
    if settings is None:
        settings = StudentSettings(user_id=user.id)
        db.add(settings)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(settings, field, value)
    if payload.profile_visibility is not None:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if profile is None:
            profile = UserProfile(user_id=user.id)
            db.add(profile)
        profile.profile_visibility = payload.profile_visibility
    db.commit()
    db.refresh(settings)
    return _encoded(settings)


@router.put("/students/password")
def change_password(
    payload: PasswordChange,
    user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="New password must be different")
    user.password_hash = hash_password(payload.new_password)
    for session in db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.revoked_at.is_(None),
    ).all():
        session.revoked_at = datetime.now(UTC)
    db.commit()
    return {"message": "Password changed successfully. Please sign in again."}


@router.get("/students/sessions")
def list_active_sessions(user: User = Depends(get_student_user), db: Session = Depends(get_db)):
    now = datetime.now(UTC)
    sessions = db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.revoked_at.is_(None),
    ).order_by(UserSession.created_at.desc()).all()
    active_sessions = []
    for session in sessions:
        expiry = session.expires_at
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=UTC)
        if expiry > now:
            active_sessions.append(session)
    return _encoded(active_sessions)


@router.delete("/students/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_session(
    session_id: str,
    user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == user.id,
        UserSession.revoked_at.is_(None),
    ).first()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active session not found")
    session.revoked_at = datetime.now(UTC)
    db.commit()
