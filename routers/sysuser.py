from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.model import User
from schemas.sysuser import LecturerAccountResponse, UserBase, UserCreate, UserResponse
from services.sysuser import create_user, get_all_lecturers, get_all_users
from db.database import get_db

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post("/", response_model=UserBase)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.user_name == user.user_name).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this username already exists")
    db_user = create_user(db, user)
    return "Registed successfully"

@router.get("/", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    """
    API trả về danh sách tất cả người dùng.
    """
    return get_all_users(db)

@router.get("/lecturers", response_model=List[LecturerAccountResponse])
def get_lecturers(db: Session = Depends(get_db)):
    """
    API để lấy danh sách tất cả tài khoản là giảng viên (user_type == 3).
    """
    return get_all_lecturers(db)




