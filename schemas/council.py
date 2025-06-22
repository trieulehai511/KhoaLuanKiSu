from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# Schema để định nghĩa một thành viên khi tạo hội đồng
class CouncilMemberCreate(BaseModel):
    member_id: UUID  # ID của giảng viên
    role: int       # Vai trò trong hội đồng, ví dụ: 1: Chủ tịch, 2: Ủy viên,...

# Schema chính cho request tạo hội đồng
class CouncilCreateWithTheses(BaseModel):
    name: str
    meeting_time: Optional[datetime] = None
    location: Optional[str] = None
    note: Optional[str] = None
    members: List[CouncilMemberCreate]
    thesis_ids: List[UUID]

# Schema cho response sau khi tạo thành công
class CouncilResponse(BaseModel):
    id: UUID
    name: str
    meeting_time: Optional[datetime] = None
    location: Optional[str] = None
    note: Optional[str] = None

    class Config:
        orm_mode = True