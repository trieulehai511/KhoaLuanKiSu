from typing import Optional
from pydantic import BaseModel
from uuid import UUID  # Sử dụng UUID từ Python, không phải SQLAlchemy

class UserBase(BaseModel):
    user_name: str
    password: str
    is_active: bool
    is_lecturer: bool
    major: UUID  # Sử dụng UUID từ Python

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    user_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_lecturer: Optional[bool] = None
    major: Optional[UUID] = None

class UserLogin(BaseModel):
    user_name: str
    password: str
    
class UserCreate(BaseModel):
    user_name: str
    password: str
    is_active: bool = True
    is_lecturer: bool = False
    major: UUID = None

class User(BaseModel):
    id: UUID
    user_name: str
    is_active: bool
    is_lecturer: bool
    major: UUID = None

    class Config:
        orm_mode = True