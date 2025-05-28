from sqlalchemy.orm import Session
from models.model import Group, GroupMember
from schemas.group import GroupCreate, GroupUpdate, GroupMemberCreate
from uuid import UUID
from fastapi import HTTPException, status

def create_group(db: Session, group: GroupCreate, user_id: UUID):
    """Tạo nhóm mới và đặt người tạo làm nhóm trưởng"""
    new_group = Group(name=group.name, leader_id=user_id,quantity = 1)
    db.add(new_group)
    db.commit()
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
    group = db.query(Group).filter(Group.id == group_id, Group.leader_id == leader_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ nhóm trưởng mới có quyền thêm thành viên")

    existing_member = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.student_id == member.student_id).first()
    if existing_member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Thành viên đã có trong nhóm")

    new_member = GroupMember(group_id=group_id, student_id=member.student_id, is_leader=False)
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member

def remove_member(db: Session, group_id: UUID, member_id: UUID, leader_id: UUID):
    """Xóa thành viên khỏi nhóm (chỉ nhóm trưởng)"""
    group = db.query(Group).filter(Group.id == group_id, Group.leader_id == leader_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ nhóm trưởng mới có quyền xóa thành viên")

    member = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.student_id == member_id).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thành viên không tồn tại trong nhóm")

    db.delete(member)
    db.commit()
    return {"message": "Thành viên đã bị xóa"}

def get_members(db: Session, group_id: UUID):
    """Lấy danh sách thành viên của nhóm"""
    return db.query(GroupMember).filter(GroupMember.group_id == group_id).all()

def transfer_leader(db: Session, group_id: UUID, new_leader_id: UUID, current_leader_id: UUID):
    """Chuyển quyền nhóm trưởng"""
    group = db.query(Group).filter(Group.id == group_id, Group.leader_id == current_leader_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ nhóm trưởng mới có quyền chuyển quyền")
    
    # Cập nhật trưởng nhóm
    group.leader_id = new_leader_id
    db.commit()
    return {"message": "Chuyển quyền nhóm trưởng thành công"}

