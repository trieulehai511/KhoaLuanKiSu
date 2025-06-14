from sqlalchemy.orm import Session
from models.model import Group, GroupMember, Information, StudentInfo
from schemas.group import (
    GroupCreate, GroupUpdate, GroupMemberCreate, 
    GroupWithMembersResponse, MemberDetailResponse
)
from uuid import UUID
from fastapi import HTTPException, status
from typing import List

def create_group(db: Session, group: GroupCreate, user_id: UUID):
    """Tạo nhóm mới và đặt người tạo làm nhóm trưởng"""
    # Điều kiện: Kiểm tra xem người dùng đã thuộc nhóm nào chưa
    is_existing_member = db.query(GroupMember).filter(GroupMember.student_id == user_id).first()
    if is_existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn đã là thành viên của một nhóm khác, không thể tạo nhóm mới."
        )

    new_group = Group(name=group.name, leader_id=user_id, quantity=1)
    db.add(new_group)
    db.flush()
    db.refresh(new_group)

    group_leader = GroupMember(
        group_id=new_group.id,
        student_id=user_id,
        is_leader=True,
    )
    db.add(group_leader)
    db.commit()
    return new_group

def add_member(db: Session, group_id: UUID, member: GroupMemberCreate, leader_id: UUID):
    """Thêm thành viên vào nhóm (chỉ nhóm trưởng)"""
    # ... (giữ nguyên logic gốc của bạn) ...
    pass

def remove_member(db: Session, group_id: UUID, member_id: UUID, leader_id: UUID):
    """Xóa thành viên khỏi nhóm (chỉ nhóm trưởng)"""
    # ... (giữ nguyên logic gốc của bạn) ...
    pass

def get_members(db: Session, group_id: UUID):
    """Lấy danh sách thành viên của nhóm"""
    return db.query(GroupMember).filter(GroupMember.group_id == group_id).all()

def transfer_leader(db: Session, group_id: UUID, new_leader_id: UUID, current_leader_id: UUID):
    """Chuyển quyền nhóm trưởng"""
    # ... (giữ nguyên logic gốc của bạn) ...
    pass

def get_all_groups_for_user(db: Session, user_id: UUID) -> List[GroupWithMembersResponse]:
    """
    Lấy thông tin TẤT CẢ các nhóm và danh sách thành viên của một user cụ thể.
    """
    user_memberships = db.query(GroupMember).filter(GroupMember.student_id == user_id).all()

    if not user_memberships:
        return []

    all_groups_list: List[GroupWithMembersResponse] = []
    
    for membership in user_memberships:
        group_id = membership.group_id
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            continue

        all_members_in_group = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()

        member_details_list: List[MemberDetailResponse] = []
        for member in all_members_in_group:
            student_user_id = member.student_id
            info = db.query(Information).filter(Information.user_id == student_user_id).first()
            student_info = db.query(StudentInfo).filter(StudentInfo.user_id == student_user_id).first()

            if info and student_info:
                member_obj = MemberDetailResponse(
                    user_id=student_user_id,
                    full_name=f"{info.last_name} {info.first_name}",
                    student_code=student_info.student_code,
                    is_leader=member.is_leader or False
                )
                member_details_list.append(member_obj)

        group_obj = GroupWithMembersResponse(
            id=group.id,
            name=group.name,
            leader_id=group.leader_id,
            members=member_details_list
        )
        all_groups_list.append(group_obj)

    return all_groups_list