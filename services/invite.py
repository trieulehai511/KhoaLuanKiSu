from typing import List
from sqlalchemy.orm import Session
from models.model import Information, Invite, StudentInfo
from models.model import Group, GroupMember
from models.model import User
from schemas.invite import GroupInInviteResponse, InviteCreate, InviteDetailResponse, UserInInviteResponse
from uuid import UUID
from datetime import datetime
from fastapi import HTTPException, status

def is_member_of_any_group(db: Session, user_id: UUID):
    """Kiểm tra người dùng đã thuộc nhóm nào chưa"""
    return db.query(GroupMember).filter(GroupMember.student_id == user_id).first() is not None

def send_invite(db: Session, invite: InviteCreate, sender_id: UUID):
    """Gửi lời mời tham gia nhóm (chưa tạo nhóm)."""
    
    # --- THAY ĐỔI LOGIC KIỂM TRA QUYỀN GỬI LỜI MỜI ---
    # 1. Kiểm tra trạng thái của người gửi
    sender_membership = db.query(GroupMember).filter(GroupMember.student_id == sender_id).first()

    # Nếu người gửi đã là thành viên của một nhóm, phải đảm bảo họ là nhóm trưởng
    if sender_membership and not sender_membership.is_leader:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ nhóm trưởng mới có quyền gửi lời mời."
        )
    # Nếu sender_membership là None (chưa vào nhóm nào), hoặc là leader, thì tiếp tục.

    # 2. Người nhận không được phép ở trong nhóm nào khác
    if is_member_of_any_group(db, invite.receiver_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Người được mời đã thuộc một nhóm khác."
        )

    # 3. Kiểm tra xem lời mời đã tồn tại và đang chờ chưa
    existing_invite = db.query(Invite).filter(
        Invite.sender_id == sender_id,
        Invite.receiver_id == invite.receiver_id,
        Invite.status == 1
    ).first()
    if existing_invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn đã gửi lời mời đến người này rồi."
        )

    # 4. Tạo lời mời mà không có group_id
    new_invite = Invite(
        sender_id=sender_id,
        receiver_id=invite.receiver_id,
        group_id=None,
        status=1,
    )
    db.add(new_invite)
    db.commit()
    db.refresh(new_invite)
    return new_invite

def accept_invite(db: Session, invite_id: UUID, receiver_id: UUID):
    """Chấp nhận lời mời. Nhóm sẽ được tạo ở lần chấp nhận đầu tiên."""
    
    # --- Logic được làm lại hoàn toàn ---
    # 1. Các kiểm tra cơ bản
    # Người chấp nhận không được có lời mời đang chờ do chính họ gửi đi
    if db.query(Invite).filter(Invite.sender_id == receiver_id, Invite.status == 1).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn phải hủy tất cả các lời mời đã gửi đi trước khi chấp nhận."
        )

    # Tìm lời mời hợp lệ
    invite = db.query(Invite).filter(
        Invite.id == invite_id,
        Invite.receiver_id == receiver_id,
        Invite.status == 1
    ).first()

    if not invite:
        raise HTTPException(status_code=404, detail="Lời mời không tồn tại hoặc đã được xử lý.")

    # 2. Tìm hoặc Tạo Nhóm
    sender_id = invite.sender_id
    # Tìm xem người gửi lời mời đã có nhóm chưa
    group = db.query(Group).filter(Group.leader_id == sender_id).first()

    if not group:
        new_group = Group(name=None, leader_id=sender_id, quantity=2)
        db.add(new_group)
        db.flush()  
        leader_member = GroupMember(group_id=new_group.id, student_id=sender_id, is_leader=True)
        accepted_member = GroupMember(group_id=new_group.id, student_id=receiver_id, is_leader=False)
        db.add_all([leader_member, accepted_member])
        invite.group_id = new_group.id
        invite.status = 2 
        db.query(Invite).filter(
            Invite.sender_id == sender_id,
            Invite.status == 1
        ).update({"group_id": new_group.id})

    else:
        if group.quantity >= 4:
            raise HTTPException(status_code=400, detail="Nhóm đã đủ số lượng thành viên (tối đa 4 người).")
        new_member = GroupMember(group_id=group.id, student_id=receiver_id, is_leader=False)
        db.add(new_member)
        group.quantity += 1
        invite.group_id = group.id
        invite.status = 2

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


def get_all_invites_for_user(db: Session, user_id: UUID) -> dict:
    """Lấy tất cả lời mời đã nhận và đã gửi của một người dùng."""

    def get_user_details(db_session: Session, user_id: UUID) -> UserInInviteResponse:
        user_info = db_session.query(Information).filter(Information.user_id == user_id).first()
        student_info = db_session.query(StudentInfo).filter(StudentInfo.user_id == user_id).first()

        return UserInInviteResponse(
            id=user_id,
            full_name=f"{user_info.last_name} {user_info.first_name}" if user_info else "Không rõ",
            student_code=student_info.student_code if student_info else None
        )

    # Lấy lời mời đã nhận và sắp xếp theo ngày tạo mới nhất
    received_invites_query = db.query(Invite).filter(
        Invite.receiver_id == user_id
    ).order_by(Invite.create_datetime.desc()).all() # <-- THÊM SẮP XẾP

    received_invites_list: List[InviteDetailResponse] = []
    for invite in received_invites_query:
        group_info = db.query(Group).filter(Group.id == invite.group_id).first()
        received_invites_list.append(
            InviteDetailResponse(
                id=invite.id,
                status=invite.status,
                sender=get_user_details(db, invite.sender_id),
                receiver=get_user_details(db, invite.receiver_id),
                group=GroupInInviteResponse.from_orm(group_info) if group_info else None
            )
        )

    # Lấy lời mời đã gửi và sắp xếp theo ngày tạo mới nhất
    sent_invites_query = db.query(Invite).filter(
        Invite.sender_id == user_id
    ).order_by(Invite.create_datetime.desc()).all() # <-- THÊM SẮP XẾP

    sent_invites_list: List[InviteDetailResponse] = []
    for invite in sent_invites_query:
        group_info = db.query(Group).filter(Group.id == invite.group_id).first()
        sent_invites_list.append(
            InviteDetailResponse(
                id=invite.id,
                status=invite.status,
                sender=get_user_details(db, invite.sender_id),
                receiver=get_user_details(db, invite.receiver_id),
                group=GroupInInviteResponse.from_orm(group_info) if group_info else None
            )
        )

    return {
        "received_invites": received_invites_list,
        "sent_invites": sent_invites_list
    }

