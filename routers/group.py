from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from services.group import create_group, update_group_thesis, get_group_by_id
from schemas.group import GroupCreate, GroupResponse
from routers.auth import PathChecker, get_current_user
from models.model import Group, User

router = APIRouter(
    prefix="/group",
    tags=["group"]
)

@router.post("/", response_model=GroupResponse)
def create_new_group(group: GroupCreate, db: Session = Depends(get_db), user: User = Depends(PathChecker("/group"))):
    """Tạo nhóm mới (chỉ dành cho nhóm trưởng)"""
    return create_group(db, group, user.id)

@router.put("/{group_id}/thesis", response_model=GroupResponse)
def update_group(group_id: str, thesis_id: str, db: Session = Depends(get_db), user: User = Depends(PathChecker("/group"))):
    """Cập nhật đề tài của nhóm"""
    return update_group_thesis(group_id, thesis_id, db)

@router.get("/{group_id}", response_model=GroupResponse)
def get_group(group_id: str, db: Session = Depends(get_db), user: User = Depends(PathChecker("/group"))):
    """Lấy thông tin nhóm theo ID"""
    return get_group_by_id(group_id, db)

@router.delete("/{group_id}")
def delete_group(group_id: str, db: Session = Depends(get_db), user: User = Depends(PathChecker("/group"))):
    """Xóa nhóm (chỉ dành cho nhóm trưởng)"""
    group = db.query(Group).filter(Group.id == group_id, Group.leader_id == user.id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Nhóm không tồn tại hoặc bạn không phải là trưởng nhóm")
    db.delete(group)
    db.commit()
    return {"message": "Nhóm đã được xóa thành công"}
