from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.model import User
from schemas.thesis import ThesisCreate, ThesisUpdate, ThesisResponse
from services.thesis import (
    create,
    update_thesis,
    get_thesis_by_id,
    get_all_theses,
    delete_thesis
)
from routers.auth import get_current_user
from uuid import UUID

router = APIRouter(
    prefix="/theses",
    tags=["theses"]
)

@router.post("/", response_model=ThesisResponse)
def create_thesis_endpoint(
    thesis: ThesisCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    API để tạo mới một luận văn (thesis).
    """
    return create(db, thesis, user.id)

@router.put("/{thesis_id}", response_model=ThesisResponse)
def update_thesis_endpoint(
    thesis_id: UUID,
    thesis: ThesisUpdate,
    db: Session = Depends(get_db)
):
    """
    API để cập nhật thông tin một luận văn (thesis).
    """
    return update_thesis(db, thesis_id, thesis)

@router.get("/{thesis_id}", response_model=ThesisResponse)
def get_thesis_by_id_endpoint(thesis_id: UUID, db: Session = Depends(get_db)):
    """
    API để lấy thông tin một luận văn (thesis) theo ID.
    """
    return get_thesis_by_id(db, thesis_id)

@router.get("/", response_model=List[ThesisResponse])
def get_all_theses_endpoint(db: Session = Depends(get_db)):
    """
    API để lấy danh sách tất cả các luận văn (theses) với thông tin của tất cả giảng viên hướng dẫn.
    """
    return get_all_theses(db)

@router.delete("/{thesis_id}")
def delete_thesis_endpoint(
    thesis_id: UUID,
    db: Session = Depends(get_db)
):
    """
    API để xóa một luận văn (thesis) theo ID.
    """
    return delete_thesis(db, thesis_id)