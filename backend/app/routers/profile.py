from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.profile import Profile
from app.models.user import User
from app.schemas.profile import ProfileRead, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["profile"])


def _get_or_create_profile(user: User, db: Session) -> Profile:
    profile: Profile | None = (
        db.query(Profile).filter(Profile.user_id == user.id).first()
    )
    if profile is None:
        profile = Profile(
            user_id=user.id,
            major="",
            interests=[],
            skills=[],
            experience_level="entry",
            savings=0.0,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("", response_model=ProfileRead)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileRead:
    profile = _get_or_create_profile(current_user, db)
    return ProfileRead.model_validate(profile, from_attributes=True)


@router.put("", response_model=ProfileRead)
def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileRead:
    profile = _get_or_create_profile(current_user, db)

    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    profile.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(profile)
    return ProfileRead.model_validate(profile, from_attributes=True)
