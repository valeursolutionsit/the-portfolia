import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint

from backend.app.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class StudentSkill(Base):
    __tablename__ = "student_skills"

    id = Column(String(36), primary_key=True, default=new_id)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    category = Column(String(80), nullable=False, default="technical")
    proficiency = Column(String(40), nullable=True)
    evidence_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)


class LearningMilestone(Base):
    __tablename__ = "learning_milestones"

    id = Column(String(36), primary_key=True, default=new_id)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    skill_name = Column(String(120), nullable=True)
    description = Column(Text, nullable=True)
    target_date = Column(Date, nullable=True)
    status = Column(String(30), nullable=False, default="planned")
    created_at = Column(DateTime, nullable=False, default=utc_now)


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(String(36), primary_key=True, default=new_id)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    skill_name = Column(String(120), nullable=True)
    status = Column(String(30), nullable=False, default="active")
    target_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class LearningResource(Base):
    __tablename__ = "learning_resources"

    id = Column(String(36), primary_key=True, default=new_id)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    category = Column(String(100), nullable=False, default="general")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class PortfolioProject(Base):
    __tablename__ = "portfolio_projects"

    id = Column(String(36), primary_key=True, default=new_id)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    problem_statement = Column(Text, nullable=True)
    objective = Column(Text, nullable=True)
    technologies = Column(JSON, nullable=False, default=list)
    student_role = Column(String(120), nullable=True)
    team_members = Column(JSON, nullable=False, default=list)
    duration = Column(String(120), nullable=True)
    status = Column(String(40), nullable=False, default="in_progress")
    github_url = Column(String(500), nullable=True)
    live_url = Column(String(500), nullable=True)
    evidence_urls = Column(JSON, nullable=False, default=list)
    key_learnings = Column(Text, nullable=True)
    is_public = Column(Boolean, nullable=False, default=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)


class Certification(Base):
    __tablename__ = "certifications"

    id = Column(String(36), primary_key=True, default=new_id)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    issuer = Column(String(255), nullable=True)
    credential_url = Column(String(500), nullable=True)
    issued_at = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(String(36), primary_key=True, default=new_id)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    awarded_by = Column(String(255), nullable=True)
    achieved_at = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class WorkExperience(Base):
    __tablename__ = "work_experiences"

    id = Column(String(36), primary_key=True, default=new_id)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class SkillAssessment(Base):
    __tablename__ = "skill_assessments"

    id = Column(String(36), primary_key=True, default=new_id)
    category = Column(String(80), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id = Column(String(36), primary_key=True, default=new_id)
    assessment_id = Column(String(36), ForeignKey("skill_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    question_type = Column(String(40), nullable=False, default="multiple_choice")
    options = Column(JSON, nullable=False, default=list)
    answer_key = Column(JSON, nullable=False)
    topic = Column(String(120), nullable=True)
    points = Column(Integer, nullable=False, default=1)


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id = Column(String(36), primary_key=True, default=new_id)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(String(36), ForeignKey("skill_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    answers = Column(JSON, nullable=False, default=dict)
    score = Column(Integer, nullable=True)
    max_score = Column(Integer, nullable=True)
    topic_scores = Column(JSON, nullable=True)
    started_at = Column(DateTime, nullable=False, default=utc_now)
    completed_at = Column(DateTime, nullable=True)


class Team(Base):
    __tablename__ = "teams"

    id = Column(String(36), primary_key=True, default=new_id)
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    project_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    required_skills = Column(JSON, nullable=False, default=list)
    team_size = Column(Integer, nullable=False, default=4)
    open_positions = Column(Integer, nullable=False, default=1)
    duration = Column(String(120), nullable=True)
    objectives = Column(Text, nullable=True)
    status = Column(String(40), nullable=False, default="open")
    created_at = Column(DateTime, nullable=False, default=utc_now)


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (UniqueConstraint("team_id", "user_id", name="uq_team_member_user"),)

    id = Column(String(36), primary_key=True, default=new_id)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(80), nullable=False, default="member")
    joined_at = Column(DateTime, nullable=False, default=utc_now)


class TeamInvitation(Base):
    __tablename__ = "team_invitations"

    id = Column(String(36), primary_key=True, default=new_id)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    inviter_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    invitee_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=utc_now)


class ProjectTask(Base):
    __tablename__ = "project_tasks"

    id = Column(String(36), primary_key=True, default=new_id)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assignee_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="todo")
    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class ProjectContribution(Base):
    __tablename__ = "project_contributions"

    id = Column(String(36), primary_key=True, default=new_id)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    evidence_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(String(36), primary_key=True, default=new_id)
    publisher_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    organization = Column(String(255), nullable=False)
    category = Column(String(40), nullable=False, index=True)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, nullable=False, default=list)
    eligibility = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    work_mode = Column(String(40), nullable=True)
    compensation = Column(String(120), nullable=True)
    deadline = Column(Date, nullable=True)
    application_url = Column(String(500), nullable=True)
    contact_information = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class OpportunityApplication(Base):
    __tablename__ = "opportunity_applications"
    __table_args__ = (UniqueConstraint("opportunity_id", "user_id", name="uq_opportunity_application_user"),)

    id = Column(String(36), primary_key=True, default=new_id)
    opportunity_id = Column(String(36), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(40), nullable=False, default="submitted")
    created_at = Column(DateTime, nullable=False, default=utc_now)


class SavedOpportunity(Base):
    __tablename__ = "saved_opportunities"
    __table_args__ = (UniqueConstraint("opportunity_id", "user_id", name="uq_saved_opportunity_user"),)

    id = Column(String(36), primary_key=True, default=new_id)
    opportunity_id = Column(String(36), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(String(36), primary_key=True, default=new_id)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(80), nullable=False)
    subject = Column(String(255), nullable=False)
    status = Column(String(30), nullable=False, default="open")
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id = Column(String(36), primary_key=True, default=new_id)
    ticket_id = Column(String(36), ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=new_id)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(String(36), primary_key=True, default=new_id)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    user_agent = Column(String(500), nullable=True)


class StudentSettings(Base):
    __tablename__ = "student_settings"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    email_preferences = Column(JSON, nullable=False, default=dict)
    notification_settings = Column(JSON, nullable=False, default=dict)
    privacy_settings = Column(JSON, nullable=False, default=dict)
    profile_visibility = Column(String(20), nullable=False, default="private")
    deactivation_requested = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)
