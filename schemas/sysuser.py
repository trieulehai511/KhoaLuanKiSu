from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from schemas.information import InformationResponse
from schemas.lecturer_info import LecturerInfoResponse
from schemas.student_info import StudentInfoResponse

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

class LecturerAccountResponse(BaseModel):
    id: UUID
    user_name: str
    first_name: str
    last_name: str
    email: str
    department: int
    title: str
    is_active: bool
    department_name: Optional[str]

    class Config:
        orm_mode = True

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
    user_type_name: str

    class Config:
        orm_mode = True

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class AdminChangePasswordRequest(BaseModel):
    user_id: UUID
    new_password: str

class UserFullProfile(BaseModel):
    user_id: UUID
    user_name: str
    user_type: int
    user_type_name: str
    information: InformationResponse
    student_info: Optional[StudentInfoResponse] = None
    lecturer_info: Optional[LecturerInfoResponse] = None

    class Config:
        orm_mode = True
