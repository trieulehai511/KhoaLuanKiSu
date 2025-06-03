from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from models.model import AcademyYear, Semester, Batch


def get_all_academy_years(db: Session) -> List[AcademyYear]:
    return db.query(AcademyYear).order_by(AcademyYear.start_date).all()


def get_semesters_by_academy_year(db: Session, academy_year_id: UUID) -> List[Semester]:
    semesters = db.query(Semester).filter(Semester.academy_year_id == academy_year_id).all()
    if not semesters:
        raise HTTPException(status_code=404, detail="Không tìm thấy học kỳ cho năm học này")
    return semesters


def get_batches_by_semester(db: Session, semester_id: UUID) -> List[Batch]:
    batches = db.query(Batch).filter(Batch.semester_id == semester_id).all()
    if not batches:
        raise HTTPException(status_code=404, detail="Không tìm thấy đợt cho học kỳ này")
    return batches
