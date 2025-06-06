from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class StudentInfoBase(BaseModel):
    student_code: str
    class_name: Optional[str] = None
    major_id: UUID

class StudentInfoCreate(StudentInfoBase):
    pass

class StudentInfoUpdate(BaseModel):
    student_code: Optional[str] = None
    class_name: Optional[str] = None
    major_id: Optional[UUID] = None

class StudentInfoResponse(StudentInfoBase):
    id: UUID
    user_id: UUID
    create_datetime: datetime
    update_datetime: datetime
    major_name: str

    class Config:
        orm_mode = True
