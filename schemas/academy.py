from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class AcademyYearResponse(BaseModel):
    id: UUID
    name: str
    start_date: datetime
    end_date: datetime

    class Config:
        orm_mode = True


class SemesterResponse(BaseModel):
    id: UUID
    name: str
    start_date: datetime
    end_date: datetime

    class Config:
        orm_mode = True


class BatchResponse(BaseModel):
    id: UUID
    name: str
    start_date: datetime
    end_date: datetime

    class Config:
        orm_mode = True
