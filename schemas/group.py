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

class GroupMemberResponse(BaseModel):
    group_id: UUID
    student_id: UUID
    is_leader: bool
