from pydantic import BaseModel, validator
from typing import List, Optional
from uuid import UUID
from datetime import datetime
class TaskCommentBase(BaseModel):
    comment_text: Optional[str] = None
    image_base64: Optional[str] = None

class TaskCommentCreate(TaskCommentBase):
    pass

class CommenterResponse(BaseModel):
    id: UUID
    user_name: str

class TaskCommentResponse(TaskCommentBase):
    id: UUID
    commenter_id: UUID
    create_datetime: datetime
    commenter: Optional[CommenterResponse] # Trả về thông tin người comment

    class Config:
        orm_mode = True

# --- Task Schemas ---
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: int = 1
    priority: int = 2

class TaskCreate(TaskBase):
    pass

class TaskUpdateStatus(BaseModel):
    status: int

class TaskResponse(TaskBase):
    id: UUID
    mission_id: UUID
    comments: List[TaskCommentResponse] = []
    priority_text: str = "" 
    
    class Config:
        orm_mode = True
    @validator('priority_text', always=True)
    def set_priority_text(cls, v, values):
        priority_int = values.get('priority')
        if priority_int == 1:
            return "Thấp"
        if priority_int == 3:
            return "Cao"
        return "Trung bình"

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[int] = None
    priority: Optional[int] = None
    
# --- Mission Schemas ---
class MissionBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    status: int = 1

class MissionCreate(MissionBase):
    pass

class MissionResponse(MissionBase):
    id: UUID
    thesis_id: UUID
    tasks: List[TaskResponse] = []

    class Config:
        orm_mode = True

