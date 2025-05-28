from typing import Optional
from pydantic import BaseModel
from uuid import UUID

# Schema cơ bản của User
class UserBase(BaseModel):
    user_name: str
    password: str
    is_active: bool = True
    user_type: int  # 1: Student, 2: Lecturer, 3: Admin

# Schema tạo mới người dùng
class UserCreate(UserBase):
    pass

# Schema cập nhật người dùng
class UserUpdate(BaseModel):
    user_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    user_type: Optional[int] = None

# Schema đăng nhập người dùng
class UserLogin(BaseModel):
    user_name: str
    password: str

# Schema phản hồi thông tin người dùng
class UserResponse(BaseModel):
    id: UUID
    user_name: str
    is_active: bool
    user_type: int  # 1: Student, 2: Lecturer, 3: Admin

    class Config:
        orm_mode = True
