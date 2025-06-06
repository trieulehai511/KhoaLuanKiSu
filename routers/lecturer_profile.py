from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.lecturer_profile import (
    LecturerCreateProfile,
    LecturerUpdateProfile,
    LecturerFullProfile,
)
from services.lecturer_profile import (
    create_lecturer_profile,
    update_lecturer_profile,
    get_lecturer_profile_by_user_id,
)
from models.model import User
from db.database import get_db
from routers.auth import get_current_user

router = APIRouter(prefix="/lecturer-profile", tags=["Lecturer Profile"])


@router.post("/", response_model=LecturerFullProfile)
def create_lecturer_endpoint(
    profile: LecturerCreateProfile,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return create_lecturer_profile(db, profile, user.id)


@router.put("/", response_model=LecturerFullProfile)
def update_lecturer_endpoint(
    profile: LecturerUpdateProfile,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return update_lecturer_profile(db, profile, user.id)


@router.get("/", response_model=LecturerFullProfile)
def get_lecturer_profile_endpoint(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    profile = get_lecturer_profile_by_user_id(db, user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin giảng viên.")
    return profile
