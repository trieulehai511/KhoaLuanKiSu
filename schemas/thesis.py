from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class ThesisCreate(BaseModel):
    title: str
    description: Optional[str] = None
    
class ThesisUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[int] = None

class Thesis(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    lecturer_id: UUID
    create_datetime: datetime
    update_datetime: datetime
    status: int
    class Config:
        from_attributes = True  # Cho phép ánh xạ từ ORM model
