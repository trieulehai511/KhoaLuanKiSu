from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from services.thesis import create, get, get_all, update, delete, get_creator
from schemas.thesis import ThesisCreate, ThesisUpdate
from routers.auth import PathChecker, get_current_user
from models.model import User
from uuid import UUID

router = APIRouter(
    prefix="/thesis",
    tags=["thesis"]
)

@router.post("")
def create_thesis(thesis: ThesisCreate, db: Session = Depends(get_db), user: User = Depends(PathChecker("/thesis"))):
    """Tạo đề tài mới (chỉ dành cho giảng viên)"""
    return create(db, thesis, user.id)

@router.get("")
def get_all_theses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: User = Depends(PathChecker("/thesis"))):
    """Lấy danh sách tất cả đề tài"""
    return get_all(db, skip, limit)

@router.get("/{thesis_id}")
def get_thesis(thesis_id: UUID, db: Session = Depends(get_db), user: User = Depends(PathChecker("/thesis"))):
    """Lấy thông tin đề tài theo ID"""
    return get(db, thesis_id)

@router.get("/creator/{thesis_id}")
def get_thesis_creator(thesis_id: UUID, db: Session = Depends(get_db), user: User = Depends(PathChecker("/thesis"))):
    """Lấy thông tin người tạo đề tài"""
    return get_creator(db, thesis_id)

@router.put("/{thesis_id}")
def update_thesis(thesis_id: UUID, thesis: ThesisUpdate, db: Session = Depends(get_db), user: User = Depends(PathChecker("/thesis"))):
    """Cập nhật thông tin đề tài"""
    return update(db, thesis_id, thesis, user.id)

@router.delete("/{thesis_id}")
def delete_thesis(thesis_id: UUID, db: Session = Depends(get_db), user: User = Depends(PathChecker("/thesis"))):
    """Xóa đề tài"""
    return delete(db, thesis_id, user.id)
