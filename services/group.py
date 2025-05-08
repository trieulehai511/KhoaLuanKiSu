from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.model import Group
from schemas.group import GroupCreate, GroupResponse

def create_group(db: Session, group: GroupCreate, user_id: str) -> GroupResponse:
    # Kiểm tra xem nhóm đã tồn tại chưa
    existing_group = db.query(Group).filter(Group.name == group.name).first()
    if existing_group:
        raise HTTPException(status_code=400, detail="Nhóm đã tồn tại")

    # Tạo nhóm mới
    db_group = Group(
        name=group.name,
        thesis_id=group.thesis_id,
        leader_id=user_id
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    return GroupResponse(
        id=db_group.id,
        name=db_group.name,
        thesis_id=db_group.thesis_id,
        leader_id=db_group.leader_id
    )

def update_group_thesis(group_id: str, thesis_id: str, db: Session) -> GroupResponse:
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Nhóm không tồn tại")

    group.thesis_id = thesis_id
    db.commit()
    db.refresh(group)

    return GroupResponse(
        id=group.id,
        name=group.name,
        thesis_id=group.thesis_id,
        leader_id=group.leader_id
    )

def get_group_by_id(group_id: str, db: Session) -> GroupResponse:
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Nhóm không tồn tại")
    return GroupResponse(
        id=group.id,
        name=group.name,
        thesis_id=group.thesis_id,
        leader_id=group.leader_id
    )
