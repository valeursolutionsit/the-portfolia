from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class StudentSkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(default="technical", max_length=80)
    proficiency: str | None = Field(default=None, max_length=40)
    evidence_url: HttpUrl | None = None


class LearningRecordUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    topic: str | None = Field(default=None, max_length=255)
    description: str | None = None
    what_i_practised: str | None = None
    resource_url: HttpUrl | None = None
    evidence_url: HttpUrl | None = None
    confidence: int | None = Field(default=None, ge=1, le=5)
    status: str | None = Field(default=None, pattern="^(planned|in_progress|completed)$")
    duration_hours: int | None = Field(default=None, ge=0, le=1000)
    completed_at: datetime | None = None


class LearningPathCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    skill_name: str | None = Field(default=None, max_length=120)
    target_date: date | None = None


class LearningMilestoneCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    skill_name: str | None = Field(default=None, max_length=120)
    description: str | None = None
    target_date: date | None = None


class LearningResourceCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    url: HttpUrl
    category: str = Field(default="general", max_length=100)
    description: str | None = None


class ProjectCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    problem_statement: str | None = None
    objective: str | None = None
    technologies: list[str] = Field(default_factory=list, max_length=50)
    student_role: str | None = Field(default=None, max_length=120)
    team_members: list[str] = Field(default_factory=list, max_length=30)
    duration: str | None = Field(default=None, max_length=120)
    status: str = Field(default="in_progress", pattern="^(planned|in_progress|completed)$")
    github_url: HttpUrl | None = None
    live_url: HttpUrl | None = None
    evidence_urls: list[HttpUrl] = Field(default_factory=list, max_length=30)
    key_learnings: str | None = None
    is_public: bool = False


class CertificationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    issuer: str | None = Field(default=None, max_length=255)
    credential_url: HttpUrl | None = None
    issued_at: date | None = None


class AchievementCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    awarded_by: str | None = Field(default=None, max_length=255)
    achieved_at: date | None = None


class WorkExperienceCreate(BaseModel):
    organization: str = Field(min_length=2, max_length=255)
    role: str = Field(min_length=2, max_length=255)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class TeamCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    project_name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    required_skills: list[str] = Field(default_factory=list, max_length=50)
    team_size: int = Field(default=4, ge=2, le=100)
    open_positions: int = Field(default=1, ge=0, le=99)
    duration: str | None = Field(default=None, max_length=120)
    objectives: str | None = None


class TeamInvitationCreate(BaseModel):
    email: EmailStr


class ProjectTaskCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    assignee_id: str | None = None
    due_date: date | None = None


class ProjectTaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    assignee_id: str | None = None
    status: str | None = Field(default=None, pattern="^(todo|in_progress|done)$")
    due_date: date | None = None


class ContributionCreate(BaseModel):
    description: str = Field(min_length=2)
    evidence_url: HttpUrl | None = None


class OpportunityCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    organization: str = Field(min_length=2, max_length=255)
    category: str = Field(pattern="^(internship|job|project|competition|scholarship)$")
    description: str = Field(min_length=2)
    required_skills: list[str] = Field(default_factory=list, max_length=50)
    eligibility: str | None = None
    location: str | None = Field(default=None, max_length=255)
    work_mode: str | None = Field(default=None, max_length=40)
    compensation: str | None = Field(default=None, max_length=120)
    deadline: date | None = None
    application_url: HttpUrl | None = None
    contact_information: str | None = Field(default=None, max_length=255)


class TicketCreate(BaseModel):
    category: str = Field(pattern="^(account|profile|learning|assessments|portfolio|workspace|opportunities|technical|other)$")
    subject: str = Field(min_length=3, max_length=255)
    message: str = Field(min_length=2)


class SupportMessageCreate(BaseModel):
    message: str = Field(min_length=2)


class StudentSettingsUpdate(BaseModel):
    email_preferences: dict[str, bool] | None = None
    notification_settings: dict[str, bool] | None = None
    privacy_settings: dict[str, bool] | None = None
    profile_visibility: str | None = Field(default=None, pattern="^(private|public)$")
    deactivation_requested: bool | None = None


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class AssessmentSubmit(BaseModel):
    answers: dict[str, Any]


class OpportunityApplicationStatusUpdate(BaseModel):
    status: str = Field(pattern="^(reviewing|interview|accepted|rejected)$")


class SupportTicketStatusUpdate(BaseModel):
    status: str = Field(pattern="^(open|in_progress|closed)$")


class PublicProjectOut(BaseModel):
    id: str
    title: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    github_url: str | None = None
    live_url: str | None = None
    key_learnings: str | None = None

    model_config = ConfigDict(from_attributes=True)
