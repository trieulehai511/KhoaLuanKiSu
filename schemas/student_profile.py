from uuid import UUID
from pydantic import BaseModel
from schemas.information import InformationCreate, InformationUpdate, InformationResponse
from schemas.student_info  import StudentInfoCreate, StudentInfoUpdate, StudentInfoResponse

class StudentCreateProfile(BaseModel):
    information: InformationCreate
    student_info: StudentInfoCreate

class StudentUpdateProfile(BaseModel):
    information: InformationUpdate
    student_info: StudentInfoUpdate

class StudentFullProfile(BaseModel):
    user_id: UUID
    information: InformationResponse
    student_info: StudentInfoResponse

    class Config:
        orm_mode = True
