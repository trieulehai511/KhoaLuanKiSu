import uuid
from fastapi import HTTPException,status
from sqlalchemy import UUID
from sqlalchemy.orm import Session
from models.model import Thesis, User
from schemas.thesis import ThesisCreate, ThesisUpdate


def create(db: Session,thesis: ThesisCreate, lecturer_id: uuid.UUID):
    lecturer = db.query(User).filter(User.id == lecturer_id, User.is_lecturer == True).first()

    if not lecturer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lecturer not found or invalid")

    db_thesis = Thesis(
        id=uuid.uuid4(),
        title = thesis.title,
        description = thesis.description,
        lecturer_id = lecturer_id,
        status = 1
    )
    db.add(db_thesis)
    db.commit()
    db.refresh(db_thesis)
    return db_thesis

def get(db: Session, thesis_id: uuid.UUID):
    thesis = db.query(Thesis).filter(Thesis.id == thesis_id).first()
    if not thesis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thesis not found")
    return thesis

def get_creator(db: Session, thesis_id: uuid.UUID):
    thesis = db.query(Thesis).filter(Thesis.id == thesis_id).first()
    if not thesis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thesis not found")
    
    # Lấy thông tin lecturer (người tạo)
    lecturer = db.query(User).filter(User.id == thesis.lecturer_id).first()
    if not lecturer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecturer not found")

    return {
        "thesis_id": thesis.id,
        "thesis_title": thesis.title,
        "creator": {
            "id": lecturer.id,
            "user_name": lecturer.user_name,
            "is_lecturer": lecturer.is_lecturer
        }
    }

def get_all(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Thesis).offset(skip).limit(limit).all()

def update(db: Session, thesis_id: uuid.UUID, thesis: ThesisUpdate, user_id: uuid.UUID):
    db_thesis = db.query(Thesis).filter(Thesis.id == thesis_id).first()
    if not db_thesis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thesis not found")
    
    # Chỉ cho phép giảng viên hoặc admin cập nhật (kiểm tra quyền trong router)
    if db_thesis.lecturer_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this thesis")

    update_data = thesis.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_thesis, key, value)
    db.commit()
    db.refresh(db_thesis)
    return db_thesis

def delete(db: Session, thesis_id: uuid.UUID, user_id: uuid.UUID):
    db_thesis = db.query(Thesis).filter(Thesis.id == thesis_id).first()
    if not db_thesis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thesis not found")
    
    # Chỉ cho phép giảng viên hoặc admin xóa (kiểm tra quyền trong router)
    if db_thesis.lecturer_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this thesis")

    db.delete(db_thesis)
    db.commit()
    return {"message": "Thesis deleted successfully"}


