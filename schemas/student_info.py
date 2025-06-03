import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
class StudentInfoBase(BaseModel):
    student_code: str
    class_name: Optional[str]
    major_id: UUID

class StudentInfoCreate(StudentInfoBase):
    user_id: UUID

class StudentInfoUpdate(BaseModel):
    student_code: Optional[str]
    class_name: Optional[str]
    major_id: Optional[UUID]

class StudentInfoResponse(StudentInfoBase):
    id: UUID
    user_id: UUID
    create_datetime: datetime
    update_datetime: datetime

    class Config:
        orm_mode = True