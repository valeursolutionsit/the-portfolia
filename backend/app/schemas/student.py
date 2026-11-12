from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class StudentProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    profile_photo_url: Optional[HttpUrl] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    college_name: Optional[str] = None
    university: Optional[str] = None
    degree: Optional[str] = None
    course: Optional[str] = None
    department: Optional[str] = None
    current_year: Optional[str] = None
    graduation_year: Optional[int] = None
    career_interests: Optional[str] = None
    career_objective: Optional[str] = None
    interested_industries: Optional[str] = None
    preferred_job_roles: Optional[str] = None
    career_goals: Optional[str] = None
    technical_skills: Optional[str] = None
    non_technical_skills: Optional[str] = None
    languages: Optional[str] = None
    linkedin_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    personal_website: Optional[HttpUrl] = None
    profile_visibility: str = Field(default="private", pattern="^(private|public)$")
    bio: Optional[str] = None


class StudentProfileOut(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    port_id: Optional[str] = None
    user_type: str
    phone: Optional[str] = None
    profile_photo_url: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    college_name: Optional[str] = None
    university: Optional[str] = None
    degree: Optional[str] = None
    course: Optional[str] = None
    department: Optional[str] = None
    current_year: Optional[str] = None
    graduation_year: Optional[int] = None
    career_interests: Optional[str] = None
    career_objective: Optional[str] = None
    interested_industries: Optional[str] = None
    preferred_job_roles: Optional[str] = None
    career_goals: Optional[str] = None
    technical_skills: Optional[str] = None
    non_technical_skills: Optional[str] = None
    languages: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    personal_website: Optional[str] = None
    profile_visibility: str = "private"
    bio: Optional[str] = None
    is_active: bool
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)


class LearningActivityCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    category: str = Field(default="general", max_length=100)
    topic: Optional[str] = None
    description: Optional[str] = None
    what_i_practised: Optional[str] = None
    resource_url: Optional[HttpUrl] = None
    evidence_url: Optional[HttpUrl] = None
    confidence: Optional[int] = Field(default=None, ge=1, le=5)
    status: str = Field(default="completed", pattern="^(planned|in_progress|completed)$")
    duration_hours: int = Field(default=0, ge=0)
    completed_at: Optional[datetime] = None


class LearningActivityOut(BaseModel):
    id: int
    title: str
    category: str
    topic: Optional[str] = None
    description: Optional[str] = None
    what_i_practised: Optional[str] = None
    resource_url: Optional[str] = None
    evidence_url: Optional[str] = None
    confidence: Optional[int] = None
    status: str
    duration_hours: int
    completed_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
