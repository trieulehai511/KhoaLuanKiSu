from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class InformationBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: datetime
    gender: int  # 0: Nữ, 1: Nam
    address: str
    tel_phone: str

class InformationCreate(InformationBase):
    pass

class InformationUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[int] = None
    address: Optional[str] = None
    tel_phone: Optional[str] = None

class InformationResponse(InformationBase):
    id: UUID
    user_id: UUID

    class Config:
        orm_mode = True
