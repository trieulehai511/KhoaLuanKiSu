from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class InviteCreate(BaseModel):
    receiver_id: UUID
    group_id: Optional[UUID] = None
    status: Optional[int] = 1
