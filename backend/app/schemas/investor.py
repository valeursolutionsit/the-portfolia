from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InvestorProfileUpdate(BaseModel):
    investor_name: Optional[str] = None
    organization_name: Optional[str] = None
    focus_areas: Optional[str] = None
    stage: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None


class InvestorProfileOut(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    user_type: str
    investor_name: Optional[str] = None
    organization_name: Optional[str] = None
    focus_areas: Optional[str] = None
    stage: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)
