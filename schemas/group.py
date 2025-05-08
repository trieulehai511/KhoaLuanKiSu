from pydantic import BaseModel, UUID4
from typing import Optional

class GroupCreate(BaseModel):
    name: str
    thesis_id: Optional[UUID4] = None

class GroupResponse(BaseModel):
    id: UUID4
    name: str
    thesis_id: Optional[UUID4] = None
    leader_id: UUID4