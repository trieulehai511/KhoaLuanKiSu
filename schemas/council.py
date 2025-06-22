from pydantic import BaseModel, validator
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from schemas.thesis import InstructorResponse, MajorResponse

# Schema để định nghĩa một thành viên khi tạo hội đồng
class CouncilMemberCreate(BaseModel):
    member_id: UUID  # ID của giảng viên
    role: int       # Vai trò trong hội đồng, ví dụ: 1: Chủ tịch, 2: Ủy viên,...

# Schema chính cho request tạo hội đồng
class CouncilCreateWithTheses(BaseModel):
    major_id: UUID
    name: str
    meeting_time: Optional[datetime] = None
    location: Optional[str] = None
    note: Optional[str] = None
    members: List[CouncilMemberCreate]
    thesis_ids: List[UUID]

# 1. Tạo một schema đơn giản cho Thesis để lồng vào response
class ThesisSimpleResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    status: str
    thesis_type: int
    name_thesis_type: str # Ví dụ: "Khóa luận" hoặc "Đồ án"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    instructors: List[InstructorResponse] = [] # Danh sách giảng viên hướng dẫn

    class Config:
        orm_mode = True

# 1. Tạo schema mới để định nghĩa thông tin thành viên trong response
class CouncilMemberResponse(BaseModel):
    member_id: UUID
    name: str
    role: int
    email: str
    lecturer_code: str
    department: int
    department_name: str
    role_name: str = ""
    @validator('role_name', always=True)
    def set_role_name(cls, v, values):
        # 'values' là một dict chứa các trường khác của model
        role_id = values.get('role')
        if role_id == 1:
            return 'Chủ tịch Hội đồng'
        if role_id == 2:
            return 'Uỷ viên - Thư ký'
        if role_id == 3:
            return 'Uỷ viên'
        return "Không xác định"

# 2. Cập nhật CouncilDetailResponse để thêm danh sách thành viên
class CouncilDetailResponse(BaseModel):
    id: UUID
    name: str
    major: Optional[MajorResponse] = None
    meeting_time: Optional[datetime] = None
    location: Optional[str] = None
    note: Optional[str] = None
    members: List[CouncilMemberResponse] = []
    theses: List[ThesisSimpleResponse] = []
    # ================================

    class Config:
        orm_mode = True # Giữ lại orm_mode

# Sửa lại CouncilResponse để tương thích (nếu cần)
class CouncilResponse(BaseModel):
    id: UUID
    name: str
    major_id: UUID
    meeting_time: Optional[datetime] = None
    location: Optional[str] = None
    note: Optional[str] = None

    class Config:
        orm_mode = True