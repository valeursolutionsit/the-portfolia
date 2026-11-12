from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.dependencies import get_current_user
from backend.app.models.user import InvestorProfile, User
from backend.app.schemas.investor import InvestorProfileOut, InvestorProfileUpdate

router = APIRouter(prefix="/investors", tags=["investors"])


@router.get("/me", response_model=InvestorProfileOut)
def get_investor_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(InvestorProfile).filter(InvestorProfile.user_id == current_user.id).first()
    return InvestorProfileOut(
        user_id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        user_type=current_user.user_type,
        investor_name=profile.investor_name if profile else None,
        organization_name=profile.organization_name if profile else None,
        focus_areas=profile.focus_areas if profile else None,
        stage=profile.stage if profile else None,
        location=profile.location if profile else None,
        bio=profile.bio if profile else None,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
    )


@router.put("/me", response_model=InvestorProfileOut)
def update_investor_profile(
    payload: InvestorProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(InvestorProfile).filter(InvestorProfile.user_id == current_user.id).first()
    if profile is None:
        profile = InvestorProfile(user_id=current_user.id)
        db.add(profile)

    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return get_investor_profile(current_user=current_user, db=db)
