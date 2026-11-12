from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.dependencies import get_current_user
from backend.app.models.user import InstitutionProfile, User
from backend.app.schemas.institution import InstitutionProfileOut, InstitutionProfileUpdate

router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.get("/me", response_model=InstitutionProfileOut)
def get_institution_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(InstitutionProfile).filter(InstitutionProfile.user_id == current_user.id).first()
    return InstitutionProfileOut(
        user_id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        user_type=current_user.user_type,
        institution_name=profile.institution_name if profile else None,
        website=profile.website if profile else None,
        city=profile.city if profile else None,
        state=profile.state if profile else None,
        country=profile.country if profile else None,
        description=profile.description if profile else None,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
    )


@router.put("/me", response_model=InstitutionProfileOut)
def update_institution_profile(
    payload: InstitutionProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(InstitutionProfile).filter(InstitutionProfile.user_id == current_user.id).first()
    if profile is None:
        profile = InstitutionProfile(user_id=current_user.id)
        db.add(profile)

    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return get_institution_profile(current_user=current_user, db=db)
