from sqlalchemy.orm import Session
from models.model import Invite
from models.model import Group, GroupMember
from models.model import User
from schemas.invite import InviteCreate
from uuid import UUID
from datetime import datetime
from fastapi import HTTPException, status

def is_member_of_any_group(db: Session, user_id: UUID):
    """Kiểm tra người dùng đã thuộc nhóm nào chưa"""
    return db.query(GroupMember).filter(GroupMember.student_id == user_id).first() is not None

def has_existing_invite(db: Session, group_id: UUID, receiver_id: UUID):
    """Kiểm tra xem đã có lời mời từ nhóm này chưa"""
    return db.query(Invite).filter(
        Invite.group_id == group_id,
        Invite.receiver_id == receiver_id,
        Invite.status == 1
    ).first() is not None

def send_invite(db: Session, invite: InviteCreate, sender_id: UUID):
    """Gửi lời mời tham gia nhóm"""
    # Kiểm tra quyền của người gửi (người dùng hiện tại)
    group = db.query(Group).filter(Group.id == invite.group_id, Group.leader_id == sender_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ nhóm trưởng mới có quyền mời"
        )

    # Kiểm tra nếu người nhận đã thuộc nhóm nào đó
    if is_member_of_any_group(db, invite.receiver_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Người được mời đã thuộc nhóm khác"
        )

    # Kiểm tra nếu đã có lời mời từ nhóm này
    if has_existing_invite(db, invite.group_id, invite.receiver_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lời mời từ nhóm này đã tồn tại"
        )

    # Tạo mới lời mời
    new_invite = Invite(
        sender_id=sender_id,  # Lấy từ người dùng hiện tại
        receiver_id=invite.receiver_id,
        group_id=invite.group_id,
        status=1,
        create_datetime=datetime.utcnow()
    )
    db.add(new_invite)
    db.commit()
    db.refresh(new_invite)
    return new_invite

def accept_invite(db: Session, invite_id: UUID, receiver_id: UUID):
    """Chấp nhận lời mời tham gia nhóm"""
    invite = db.query(Invite).filter(
        Invite.id == invite_id,
        Invite.receiver_id == receiver_id,
        Invite.status == 1
    ).first()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lời mời không tồn tại hoặc đã được xử lý"
        )
    new_member = GroupMember(
        group_id=invite.group_id,
        student_id=invite.receiver_id,
        is_leader=False,
        join_date=datetime.utcnow()
    )
    db.add(new_member)
    invite.status = 2
    db.commit()
    return {"message": "Lời mời đã được chấp nhận"}

def revoke_invite(db: Session, invite_id: UUID, sender_id: UUID):
    """Hủy lời mời tham gia nhóm (chỉ nhóm trưởng)"""
    invite = db.query(Invite).filter(Invite.id == invite_id, Invite.sender_id == sender_id).first()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy lời mời hoặc không có quyền hủy"
        )
    db.delete(invite)
    db.commit()
    return {"message": "Lời mời đã bị hủy"}

def reject_invite(db: Session, invite_id: UUID, receiver_id: UUID):
    """Từ chối lời mời tham gia nhóm"""
    invite = db.query(Invite).filter(
        Invite.id == invite_id,
        Invite.receiver_id == receiver_id,
        Invite.status == "pending"
    ).first()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lời mời không tồn tại hoặc đã được xử lý"
        )
    invite.status = 3  # Đã từ chối
    db.commit()
    return {"message": "Lời mời đã bị từ chối"}


def get_invites_by_receiver(db: Session, receiver_id: UUID):
    """Lấy danh sách lời mời của tài khoản được nhận"""
    invites = db.query(Invite).filter(
        Invite.receiver_id == receiver_id,
        Invite.status == 1  # Chỉ lấy lời mời đang chờ xử lý
    ).all()

    if not invites:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không có lời mời nào"
        )
    return invites
