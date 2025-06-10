from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from routers.auth import get_current_user
from schemas.student_profile import (
    StudentCreateProfile,
    StudentUpdateProfile,
    StudentFullProfile,
)
from services.student_profile import (
    create_student_profile,
    get_all_student_profiles,
    update_student_profile,
    get_student_profile_by_user_id,
)
from models.model import User
from db.database import get_db


router = APIRouter(prefix="/student-profile", tags=["Student Profile"])


@router.post("/", response_model=StudentFullProfile)
def create_student_endpoint(
    profile: StudentCreateProfile,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return create_student_profile(db, profile, user.id)


@router.put("/", response_model=StudentFullProfile)
def update_student_endpoint(
    profile: StudentUpdateProfile,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return update_student_profile(db, profile, user.id)


@router.get("/", response_model=StudentFullProfile)
def get_student_profile_endpoint(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    profile = get_student_profile_by_user_id(db, user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin sinh viên")
    return profile

@router.get("/gett-all", response_model=List[StudentFullProfile])
def get_all_students_endpoint(db: Session = Depends(get_db)):
    return get_all_student_profiles(db)




