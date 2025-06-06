from schemas.information import InformationCreate, InformationUpdate, InformationResponse
from schemas.lecturer_info import LecturerInfoCreate, LecturerInfoUpdate, LecturerInfoResponse
from pydantic import BaseModel
from uuid import UUID


class LecturerCreateProfile(BaseModel):
    information: InformationCreate
    lecturer_info: LecturerInfoCreate


class LecturerUpdateProfile(BaseModel):
    information: InformationUpdate
    lecturer_info: LecturerInfoUpdate


class LecturerFullProfile(BaseModel):
    user_id: UUID
    information: InformationResponse
    lecturer_info: LecturerInfoResponse

    class Config:
        orm_mode = True
