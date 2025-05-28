from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class ThesisBase(BaseModel): 
    title: str
    description: str
    thesis_type: int
    start_date: datetime
    end_date: datetime
    status:  int

class ThesisCreate(ThesisBase):
    pass

class ThesisUpdate(BaseModel):
    title:  Optional[str] = None
    description:  Optional[str] = None
    thesis_type:  Optional[int] = None
    start_date: Optional[datetime] = None
    end_date:  Optional[datetime] = None
    status:  Optional[int] = None

class InstructorResponse(BaseModel):
    name: str
    email: str
    department: int
    phone: str

class ThesisResponse(BaseModel):
    id: UUID
    thesis_type: int
    status: str
    name: str
    description: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    instructors: List[InstructorResponse]

    class Config:
        orm_mode = True




