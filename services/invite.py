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
    """Gửi lời mời tham gia nhóm.
    Nếu người gửi chưa có nhóm, một nhóm mới sẽ được tạo."""
    
    group_id_to_use = invite.group_id

    # Nếu không có group_id được cung cấp (lời mời đầu tiên)
    if not group_id_to_use:
        # Kiểm tra xem người mời đã ở trong nhóm nào chưa
        if is_member_of_any_group(db, sender_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bạn đã thuộc một nhóm khác và không thể tạo lời mời mới."
            )
        
        # Tạo nhóm mới và đặt người mời làm nhóm trưởng
        new_group = Group(name=f"Nhóm của sinh viên {sender_id}", leader_id=sender_id, quantity=1)
        db.add(new_group)
        db.flush()  # Để lấy ID của nhóm mới

        leader_as_member = GroupMember(group_id=new_group.id, student_id=sender_id, is_leader=True)
        db.add(leader_as_member)
        group_id_to_use = new_group.id
    else:
        # Nếu có group_id, xác thực người gửi là nhóm trưởng
        group = db.query(Group).filter(Group.id == group_id_to_use, Group.leader_id == sender_id).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ nhóm trưởng mới có quyền mời hoặc nhóm không tồn tại."
            )

    # Kiểm tra nếu người nhận đã thuộc nhóm nào đó
    if is_member_of_any_group(db, invite.receiver_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Người được mời đã thuộc nhóm khác."
        )

    # Kiểm tra nếu đã có lời mời từ nhóm này
    if has_existing_invite(db, group_id_to_use, invite.receiver_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lời mời từ nhóm này đã tồn tại."
        )

    # Tạo mới lời mời
    new_invite = Invite(
        sender_id=sender_id,
        receiver_id=invite.receiver_id,
        group_id=group_id_to_use,
        status=1,  # 1: Đang chờ
        create_datetime=datetime.utcnow()
    )
    db.add(new_invite)
    db.commit()
    db.refresh(new_invite)
    return new_invite

def accept_invite(db: Session, invite_id: UUID, receiver_id: UUID):
    """Chấp nhận lời mời tham gia nhóm"""
    # Điều kiện: Người chấp nhận không được có lời mời đang chờ do chính họ gửi đi
    sent_invites = db.query(Invite).filter(Invite.sender_id == receiver_id, Invite.status == 1).first()
    if sent_invites:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn phải hủy tất cả các lời mời đã gửi đi trước khi chấp nhận lời mời này."
        )

    # Tìm lời mời
    invite = db.query(Invite).filter(
        Invite.id == invite_id,
        Invite.receiver_id == receiver_id,
        Invite.status == 1
    ).first()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lời mời không tồn tại hoặc đã được xử lý."
        )
    
    # Điều kiện: Kiểm tra số lượng thành viên trong nhóm
    member_count = db.query(GroupMember).filter(GroupMember.group_id == invite.group_id).count()
    if member_count >= 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nhóm đã đủ số lượng thành viên (tối đa 4 người)."
        )

    # Thêm thành viên mới vào nhóm
    new_member = GroupMember(
        group_id=invite.group_id,
        student_id=invite.receiver_id,
        is_leader=False,
        join_date=datetime.utcnow()
    )
    db.add(new_member)
    
    # Cập nhật số lượng thành viên trong nhóm
    db.query(Group).filter(Group.id == invite.group_id).update({"quantity": Group.quantity + 1})

    invite.status = 2 # 2: Đã chấp nhận
    db.commit()
    return {"message": "Lời mời đã được chấp nhận."}

def revoke_invite(db: Session, invite_id: UUID, sender_id: UUID):
    """Hủy lời mời tham gia nhóm (chỉ nhóm trưởng)"""
    # Chỉ người gửi (sender_id) mới có quyền hủy
    invite = db.query(Invite).filter(Invite.id == invite_id, Invite.sender_id == sender_id).first()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy lời mời hoặc bạn không có quyền hủy."
        )
    db.delete(invite)
    db.commit()
    return {"message": "Lời mời đã bị hủy."}

def reject_invite(db: Session, invite_id: UUID, receiver_id: UUID):
    """Từ chối lời mời tham gia nhóm"""
    invite = db.query(Invite).filter(
        Invite.id == invite_id,
        Invite.receiver_id == receiver_id,
        Invite.status == 1 # Chỉ từ chối lời mời đang chờ
    ).first()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lời mời không tồn tại hoặc đã được xử lý."
        )
    invite.status = 3  # 3: Đã từ chối
    db.commit()
    return {"message": "Lời mời đã bị từ chối."}


def get_invites_by_receiver(db: Session, receiver_id: UUID):
    """Lấy danh sách lời mời của tài khoản được nhận"""
    invites = db.query(Invite).filter(
        Invite.receiver_id == receiver_id,
        Invite.status == 1  # Chỉ lấy lời mời đang chờ xử lý
    ).all()

    # Không báo lỗi nếu không có lời mời, chỉ trả về danh sách rỗng
    return invites
