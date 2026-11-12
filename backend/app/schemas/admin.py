from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator, model_validator

from backend.app.schemas.portal import (
    ContributionCreate,
    ProjectTaskCreate,
    StudentSettingsUpdate,
)
from backend.app.schemas.student import StudentProfileUpdate


class AdminUserUpdate(BaseModel):
    is_active: bool | None = None
    is_verified: bool | None = None


class AdminOpportunityUpdate(BaseModel):
    is_active: bool


class AdminTicketStatusUpdate(BaseModel):
    status: str = Field(pattern="^(open|in_progress|closed)$")


class AdminSupportResponse(BaseModel):
    message: str = Field(min_length=2, max_length=10000)


class AdminStudentCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    profile: StudentProfileUpdate | None = None


class AdminStudentUpdate(StudentProfileUpdate):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=12, max_length=128)
    is_active: bool | None = None
    is_verified: bool | None = None

    @model_validator(mode="after")
    def validate_student_update(self):
        if self.full_name is not None and len(self.full_name.strip()) < 2:
            raise ValueError("Full name must contain at least 2 characters")
        return self


class AdminStudentNotificationCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    message: str = Field(min_length=2)


class AdminStudentNotificationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    message: str | None = Field(default=None, min_length=2)
    is_read: bool | None = None


class AdminStudentApplicationCreate(BaseModel):
    opportunity_id: str = Field(min_length=1, max_length=36)


class AdminStudentSavedOpportunityCreate(BaseModel):
    opportunity_id: str = Field(min_length=1, max_length=36)


class AdminStudentApplicationUpdate(BaseModel):
    status: str = Field(pattern="^(submitted|reviewing|interview|accepted|rejected)$")


class AdminTeamMembershipCreate(BaseModel):
    team_id: str = Field(min_length=1, max_length=36)
    role: str = Field(default="member", min_length=1, max_length=80)


class AdminTeamMembershipUpdate(BaseModel):
    role: str = Field(min_length=1, max_length=80)


class AdminTeamInvitationCreate(BaseModel):
    team_id: str = Field(min_length=1, max_length=36)
    invitee_id: str = Field(min_length=1, max_length=36)


class AdminTeamInvitationUpdate(BaseModel):
    status: str = Field(pattern="^(pending|accepted|declined|cancelled)$")


class AdminProjectTaskCreate(ProjectTaskCreate):
    team_id: str = Field(min_length=1, max_length=36)
    status: str = Field(default="todo", pattern="^(todo|in_progress|done)$")


class AdminProjectContributionCreate(ContributionCreate):
    team_id: str = Field(min_length=1, max_length=36)


class AdminProjectContributionUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=2)
    evidence_url: HttpUrl | None = None


class AdminStudentSettingsUpdate(StudentSettingsUpdate):
    pass


class AdminAssessmentQuestion(BaseModel):
    prompt: str = Field(min_length=5, max_length=5000)
    topic: str = Field(min_length=2, max_length=120)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_option_index: int = Field(ge=0, le=3)

    @field_validator("prompt", "topic", mode="before")
    @classmethod
    def trim_question_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("options")
    @classmethod
    def validate_options(cls, options: list[str]) -> list[str]:
        normalized = [option.strip().casefold() for option in options]
        if any(not option or len(option) > 1000 for option in normalized) or len(set(normalized)) != 4:
            raise ValueError("Each question must have four distinct, non-empty options of at most 1000 characters")
        return [option.strip() for option in options]


class AdminAssessmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=2, max_length=255)
    category: str = Field(min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=5000)
    duration_minutes: int = Field(default=30, ge=1, le=300)
    is_active: bool = True
    questions: list[AdminAssessmentQuestion] = Field(min_length=30, max_length=30)

    @field_validator("title", "category", mode="before")
    @classmethod
    def trim_assessment_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("description", mode="before")
    @classmethod
    def trim_description(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value


class AdminAssessmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=2, max_length=255)
    category: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=5000)
    duration_minutes: int | None = Field(default=None, ge=1, le=300)
    is_active: bool | None = None
    questions: list[AdminAssessmentQuestion] | None = Field(default=None, min_length=30, max_length=30)

    @field_validator("title", "category", mode="before")
    @classmethod
    def trim_assessment_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("description", mode="before")
    @classmethod
    def trim_description(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value
