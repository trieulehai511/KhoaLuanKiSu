from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from services.invite import get_invites_by_receiver, reject_invite, send_invite, accept_invite, revoke_invite
from schemas.invite import InviteCreate
from routers.auth import PathChecker, get_current_user
from models.model import User
from uuid import UUID

router = APIRouter(
    prefix="/invite",
    tags=["invite"]
)


@router.post("/send")
def create_invite(invite: InviteCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Gửi lời mời tham gia nhóm"""
    return send_invite(db, invite, user.id)

@router.post("/accept/{invite_id}")
def accept_group_invite(invite_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Chấp nhận lời mời tham gia nhóm"""
    return accept_invite(db, invite_id, user.id)

@router.post("/revoke/{invite_id}")
def revoke_group_invite(invite_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Hủy lời mời tham gia nhóm"""
    return revoke_invite(db, invite_id, user.id)

@router.post("/reject/{invite_id}")
def reject_group_invite(invite_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Từ chối lời mời tham gia nhóm"""
    return reject_invite(db, invite_id, user.id)

@router.get("/my-invites")
def list_my_invites(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Lấy danh sách lời mời của người dùng hiện tại"""
    return get_invites_by_receiver(db, user.id)
