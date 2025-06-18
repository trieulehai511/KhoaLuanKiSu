from typing import List
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from services.group import (
    create_group, add_member, delete_group, get_all_groups_for_user, get_group_with_detailed_members, register_thesis_for_group, remove_member, transfer_leader, update_group_name
)
from schemas.group import GroupCreate, GroupMemberCreate, GroupMemberResponse, GroupResponse, GroupWithMembersResponse, MemberDetailResponse
from routers.auth import PathChecker, get_current_user
from models.model import User
from uuid import UUID

router = APIRouter(
    prefix="/group",
    tags=["group"]
)

@router.post("",response_model=GroupResponse)
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

@router.get("/{group_id}/members", response_model=GroupWithMembersResponse)
def list_group_members(group_id: UUID, db: Session = Depends(get_db)):
    """Lấy thông tin chi tiết của một nhóm bao gồm danh sách thành viên."""
    # Gọi hàm service mới
    return get_group_with_detailed_members(db, group_id)

@router.put("/{group_id}/transfer-leader/{new_leader_id}")
def change_group_leader(group_id: UUID, new_leader_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Chuyển quyền nhóm trưởng"""
    return transfer_leader(db, group_id, new_leader_id, user.id)

@router.get("/my-groups", response_model=List[GroupWithMembersResponse]) # Sửa thành /my-groups và List[...]
def get_my_groups_details(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Lấy thông tin chi tiết TẤT CẢ các nhóm của người dùng đang đăng nhập,
    bao gồm cả danh sách thành viên cho mỗi nhóm.
    """
    # Hàm service mới đã trả về một danh sách, nên chỉ cần return trực tiếp
    return get_all_groups_for_user(db, user_id=current_user.id)

@router.put("/{group_id}/name", response_model=GroupResponse)
def update_group_name_endpoint(
    group_id: UUID, 
    # Nhận tên mới từ body của request
    new_name: str = Body(..., embed=True), 
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    """
    API để nhóm trưởng cập nhật lại tên nhóm.
    """
    return update_group_name(db, group_id=group_id, new_name=new_name, user_id=user.id)

@router.delete("/{group_id}")
def delete_group_endpoint(
    group_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    API để nhóm trưởng xóa nhóm của mình.
    """
    return delete_group(db, group_id=group_id, user_id=user.id)

@router.post("/{group_id}/register-thesis/{thesis_id}", response_model=GroupResponse)
def register_thesis_endpoint(
    group_id: UUID,
    thesis_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    API để nhóm trưởng đăng ký một đề tài cho nhóm của mình.
    """
    return register_thesis_for_group(db, group_id=group_id, thesis_id=thesis_id, user_id=user.id)
