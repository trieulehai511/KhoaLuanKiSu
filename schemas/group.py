from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional

class GroupCreate(BaseModel):
    name: str

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    leader_id: Optional[UUID] = None

class GroupMemberCreate(BaseModel):
    student_id: UUID
    is_leader: bool = False

class GroupResponse(BaseModel):
    id: UUID
    name: str
    leader_id: UUID
    class Config:
        orm_mode = True 

class GroupMemberResponse(BaseModel):
    group_id: UUID
    student_id: UUID
    is_leader: bool
    class Config:
        orm_mode = True

# Schema chi tiết cho một thành viên trong danh sách trả về
class MemberDetailResponse(BaseModel):
    user_id: UUID
    full_name: str
    student_code: str
    is_leader: bool

    class Config:
        orm_mode = True

# Schema mới cho response trả về, chứa thông tin nhóm và danh sách thành viên
class GroupWithMembersResponse(BaseModel):
    id: UUID
    name: str
    leader_id: UUID
    members: List[MemberDetailResponse]

    class Config:
        orm_mode = True