from sqlalchemy.orm import Session
from models.model import Information
from schemas.information import InformationCreate, InformationUpdate
from uuid import UUID
from fastapi import HTTPException, status

def create_information(db: Session, info: InformationCreate, user_id: UUID):
    """Tạo thông tin người dùng hiện tại"""
    new_info = Information(user_id=user_id, **info.dict())
    db.add(new_info)
    db.commit()
    db.refresh(new_info)
    return new_info

def get_information(db: Session, info_id: UUID):
    """Lấy thông tin theo ID"""
    information = db.query(Information).filter(Information.id == info_id).first()
    if not information:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thông tin không tồn tại"
        )
    return information

def update_information(db: Session, info_id: UUID, info_update: InformationUpdate):
    """Cập nhật thông tin người dùng"""
    information = db.query(Information).filter(Information.id == info_id).first()
    if not information:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thông tin không tồn tại"
        )
    for key, value in info_update.dict(exclude_unset=True).items():
        setattr(information, key, value)
    db.commit()
    db.refresh(information)
    return information

def delete_information(db: Session, info_id: UUID):
    """Xóa thông tin người dùng"""
    information = db.query(Information).filter(Information.id == info_id).first()
    if not information:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thông tin không tồn tại"
        )
    db.delete(information)
    db.commit()
    return {"message": "Thông tin đã bị xóa"}


