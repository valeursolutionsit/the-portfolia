from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InstitutionProfileUpdate(BaseModel):
    institution_name: Optional[str] = None
    website: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None


class InstitutionProfileOut(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    user_type: str
    institution_name: Optional[str] = None
    website: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)
