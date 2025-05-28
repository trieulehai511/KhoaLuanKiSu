from datetime import datetime
import uuid
from fastapi import HTTPException,status
from sqlalchemy import UUID
from sqlalchemy.orm import Session
from models.model import Information, LecturerInfo, Thesis, ThesisLecturer, User
from schemas.thesis import ThesisCreate, ThesisResponse, ThesisUpdate

def create(db: Session,thesis: ThesisCreate, lecturer_id: uuid.UUID):
    lecturer = db.query(User).filter(User.id == lecturer_id, User.user_type == 3).first()
    if not lecturer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lecturer not found or invalid")
    db_thesis = Thesis(
        title=thesis.title,
        description=thesis.description,
        thesis_type=thesis.thesis_type,
        start_date=thesis.start_date,
        end_date=thesis.end_date,
        status=thesis.status,
        create_by=lecturer_id,
        create_datetime=datetime.utcnow()
    )
    db.add(db_thesis)
    db.commit()
    db.refresh(db_thesis)
    return db_thesis

def update_thesis(db: Session, thesis_id: UUID, thesis: ThesisUpdate):
    """
    Cập nhật thông tin một luận văn (thesis).
    """
    db_thesis = db.query(Thesis).filter(Thesis.id == thesis_id).first()
    if not db_thesis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thesis not found"
        )

    for key, value in thesis.dict(exclude_unset=True).items():
        setattr(db_thesis, key, value)
    db_thesis.update_datetime = datetime.utcnow()

    db.commit()
    db.refresh(db_thesis)
    return db_thesis

def get_thesis_by_id(db: Session, thesis_id: UUID) -> ThesisResponse:
    """
    Lấy thông tin một luận văn (thesis) theo ID, bao gồm thông tin của tất cả giảng viên hướng dẫn.
    """
    thesis = db.query(Thesis).filter(Thesis.id == thesis_id).first()
    if not thesis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thesis not found"
        )
    thesis_lecturers = db.query(ThesisLecturer).filter(ThesisLecturer.thesis_id == thesis.id).all()
    instructors = []
    for tl in thesis_lecturers:
        lecturer_info = db.query(LecturerInfo).filter(LecturerInfo.id == tl.lecturer_id).first()
        if lecturer_info:
            # Lấy thông tin người dùng từ bảng Information
            user_info = db.query(Information).filter(Information.user_id == lecturer_info.user_id).first()
            if user_info:
                instructors.append({
                    "name": f"{user_info.first_name} {user_info.last_name}",
                    "email": lecturer_info.email,
                    "department": lecturer_info.department,
                    "phone": lecturer_info.phone
                })
    return ThesisResponse(
        id=thesis.id,
        topicNumber=thesis.thesis_type,
        status="Chưa có người đăng ký" if thesis.status == 1 else "Đã có người đăng ký",
        name=thesis.title,
        description=thesis.description,
        start_date=thesis.start_date,
        end_date=thesis.end_date,
        instructors=instructors
    )

def get_all_theses(db: Session) -> list[ThesisResponse]:
    """
    Lấy danh sách tất cả các luận văn (theses) với thông tin của tất cả giảng viên hướng dẫn.
    """
    theses = db.query(Thesis).all()
    thesis_responses = []
    for thesis in theses:
        thesis_lecturers = db.query(ThesisLecturer).filter(ThesisLecturer.thesis_id == thesis.id).all()
        instructors = []
        for tl in thesis_lecturers:
            lecturer_info = db.query(LecturerInfo).filter(LecturerInfo.id == tl.lecturer_id).first()
            if lecturer_info:
                user_info = db.query(Information).filter(Information.user_id == lecturer_info.user_id).first()
                if user_info:
                    instructors.append({
                        "name": f"{user_info.first_name} {user_info.last_name}",
                        "email": lecturer_info.email,
                        "department": lecturer_info.department,
                        "phone": lecturer_info.phone
                    })

        thesis_responses.append({
            "id": thesis.id,
            "thesis_type": thesis.thesis_type,
            "status": "Chưa có người đăng ký" if thesis.status == 1 else "Đã có người đăng ký",
            "name": thesis.title,
            "description": thesis.description,
            "start_date": thesis.start_date,
            "end_date": thesis.end_date,
            "instructors": instructors
        })

    return thesis_responses

def delete_thesis(db: Session, thesis_id: UUID):
    """
    Xóa một luận văn (thesis).
    """
    db_thesis = db.query(Thesis).filter(Thesis.id == thesis_id).first()
    if not db_thesis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thesis not found"
        )
    db.delete(db_thesis)
    db.commit()
    return {"message": "Thesis deleted successfully"}