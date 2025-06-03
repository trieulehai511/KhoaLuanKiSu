import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr


class LecturerInfoBase(BaseModel):
    lecturer_code: str
    department: int
    title: str
    phone: str
    email: EmailStr

class LecturerInfoCreate(LecturerInfoBase):
    user_id: UUID

class LecturerInfoUpdate(BaseModel):
    lecturer_code: Optional[str]
    department: Optional[int]
    title: Optional[str]
    phone: Optional[str]
    email: Optional[EmailStr]

class LecturerInfoResponse(LecturerInfoBase):
    id: UUID
    user_id: UUID
    create_datetime: datetime
    update_datetime: datetime

    class Config:
        orm_mode = True