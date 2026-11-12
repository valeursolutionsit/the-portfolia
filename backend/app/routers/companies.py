from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.dependencies import get_current_user
from backend.app.models.user import CompanyProfile, User
from backend.app.schemas.company import CompanyProfileOut, CompanyProfileUpdate

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/me", response_model=CompanyProfileOut)
def get_company_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(CompanyProfile).filter(CompanyProfile.user_id == current_user.id).first()
    return CompanyProfileOut(
        user_id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        user_type=current_user.user_type,
        company_name=profile.company_name if profile else None,
        website=profile.website if profile else None,
        industry=profile.industry if profile else None,
        company_size=profile.company_size if profile else None,
        location=profile.location if profile else None,
        description=profile.description if profile else None,
        hiring_focus=profile.hiring_focus if profile else None,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
    )


@router.put("/me", response_model=CompanyProfileOut)
def update_company_profile(
    payload: CompanyProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(CompanyProfile).filter(CompanyProfile.user_id == current_user.id).first()
    if profile is None:
        profile = CompanyProfile(user_id=current_user.id)
        db.add(profile)

    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return get_company_profile(current_user=current_user, db=db)
