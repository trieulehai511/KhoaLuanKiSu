from typing import List
from fastapi import APIRouter, Depends, HTTPException,status 
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
from models.model import StudentInfo, User
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
def get_all_students_endpoint(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    API để lấy danh sách sinh viên cùng chuyên ngành với người dùng đang đăng nhập.
    """
    # Lấy thông tin sinh viên của người dùng đang đăng nhập để tìm chuyên ngành
    user_student_info = db.query(StudentInfo).filter(StudentInfo.user_id == current_user.id).first()

    # Nếu không tìm thấy thông tin sinh viên của người dùng, không thể lọc
    if not user_student_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông tin sinh viên của bạn."
        )

    # Lấy mã chuyên ngành của người dùng
    user_major_id = user_student_info.major_id

    # Gọi service với mã chuyên ngành để lọc
    return get_all_student_profiles(db, major_id=user_major_id)




