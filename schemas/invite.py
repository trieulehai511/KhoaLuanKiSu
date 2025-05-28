from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class InviteCreate(BaseModel):
    receiver_id: UUID
    group_id: UUID
    status: Optional[int] = 1
