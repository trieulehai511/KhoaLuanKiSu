from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class LecturerInfoBase(BaseModel):
    lecturer_code: str
    department: int
    title: str
    email: str


class LecturerInfoCreate(LecturerInfoBase):
    pass 


class LecturerInfoUpdate(BaseModel):
    lecturer_code: Optional[str] = None
    department: Optional[int] = None
    title: Optional[str] = None
    email: Optional[str] = None


class LecturerInfoResponse(LecturerInfoBase):
    id: UUID
    user_id: UUID
    department_name: str
    create_datetime: datetime
    update_datetime: datetime

    class Config:
        orm_mode = True
