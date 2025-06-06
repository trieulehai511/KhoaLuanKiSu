from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from services.group import (
    create_group, add_member, remove_member, get_members, transfer_leader
)
from schemas.group import GroupCreate, GroupMemberCreate, GroupMemberResponse, GroupResponse
from routers.auth import PathChecker, get_current_user
from models.model import User
from uuid import UUID

router = APIRouter(
    prefix="/group",
    tags=["group"]
)

@router.post("",response_model=GroupResponse,dependencies=[Depends(PathChecker("/group"))])
def create_new_group(group: GroupCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Tạo nhóm mới"""
    return create_group(db, group, user.id)

@router.post("/{group_id}/add-member",response_model=GroupMemberResponse)
def add_group_member(group_id: UUID, member: GroupMemberCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Thêm thành viên vào nhóm"""
    return add_member(db, group_id, member, user.id)

@router.delete("/{group_id}/remove-member/{member_id}")
def remove_group_member(group_id: UUID, member_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Xóa thành viên khỏi nhóm"""
    return remove_member(db, group_id, member_id, user.id)

@router.get("/{group_id}/members")
def list_group_members(group_id: UUID, db: Session = Depends(get_db)):
    """Lấy danh sách thành viên của nhóm"""
    return get_members(db, group_id)

@router.put("/{group_id}/transfer-leader/{new_leader_id}")
def change_group_leader(group_id: UUID, new_leader_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Chuyển quyền nhóm trưởng"""
    return transfer_leader(db, group_id, new_leader_id, user.id)
