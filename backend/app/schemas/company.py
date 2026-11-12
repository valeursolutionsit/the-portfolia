from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CompanyProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    hiring_focus: Optional[str] = None


class CompanyProfileOut(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    user_type: str
    company_name: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    hiring_focus: Optional[str] = None
    is_active: bool
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)
