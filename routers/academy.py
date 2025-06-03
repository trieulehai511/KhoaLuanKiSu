from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from db.database import get_db
from models.model import User
from routers.auth import get_current_user
from schemas.academy import (
    AcademyYearResponse,
    SemesterResponse,
    BatchResponse
)
from services.academy import (
    get_all_academy_years,
    get_semesters_by_academy_year,
    get_batches_by_semester
)

router = APIRouter(
    prefix="/academy",
    tags=["Academy"]
)


@router.get("/years", response_model=List[AcademyYearResponse])
def get_all_years_endpoint(db: Session = Depends(get_db),  user: User = Depends(get_current_user)):
    return get_all_academy_years(db)


@router.get("/years/{academy_year_id}/semesters", response_model=List[SemesterResponse])
def get_semesters_by_year_endpoint(academy_year_id: UUID, db: Session = Depends(get_db),  user: User = Depends(get_current_user)):
    return get_semesters_by_academy_year(db, academy_year_id)


@router.get("/semesters/{semester_id}/batches", response_model=List[BatchResponse])
def get_batches_by_semester_endpoint(semester_id: UUID, db: Session = Depends(get_db),  user: User = Depends(get_current_user)):
    return get_batches_by_semester(db, semester_id)
