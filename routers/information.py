from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.information import InformationCreate, InformationUpdate, InformationResponse
from models.model import User
from routers.auth import get_current_user, PathChecker
from services.information import create_information, get_information, update_information, delete_information
from uuid import UUID

router = APIRouter(
    prefix="/information",
    tags=["Information"]
)

@router.post("/", response_model=InformationResponse, dependencies=[Depends(PathChecker("/information"))])
def create_user_information(info: InformationCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Tạo thông tin người dùng (user_id lấy từ tài khoản đang đăng nhập)"""
    return create_information(db, info, user.id)

@router.get("/{info_id}", response_model=InformationResponse, dependencies=[Depends(PathChecker("/information"))])
def get_user_information(info_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Lấy thông tin người dùng theo ID"""
    return get_information(db, info_id)

@router.put("/{info_id}", response_model=InformationResponse, dependencies=[Depends(PathChecker("/information"))])
def update_user_information(info_id: UUID, info: InformationUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Cập nhật thông tin người dùng"""
    return update_information(db, info_id, info)

@router.delete("/{info_id}", dependencies=[Depends(PathChecker("/information"))])
def delete_user_information(info_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Xóa thông tin người dùng"""
    return delete_information(db, info_id)
