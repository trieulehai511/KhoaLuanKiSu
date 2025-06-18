from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional

class InviteCreate(BaseModel):
    receiver_id: UUID

# --- CÁC SCHEMA MỚI ĐỂ TRẢ VỀ ---

class UserInInviteResponse(BaseModel):
    id: UUID
    full_name: str
    student_code: Optional[str] = None
    class Config:
        orm_mode = True

class GroupInInviteResponse(BaseModel):
    id: UUID
    name: Optional[str] = None
    class Config:
        orm_mode = True

class InviteDetailResponse(BaseModel):
    id: UUID
    status: int
    sender: UserInInviteResponse
    receiver: UserInInviteResponse
    group: Optional[GroupInInviteResponse]
    class Config:
        orm_mode = True

class AllInvitesResponse(BaseModel):
    received_invites: List[InviteDetailResponse]
    sent_invites: List[InviteDetailResponse]