from datetime import datetime
from typing import Optional
from uuid import UUID 
from pydantic import BaseModel

class SysUserRoleBase(BaseModel):
    user_id: UUID
    role_id: int

class SysUserRoleCreate(SysUserRoleBase):
    pass

class SysUserRoleUpdate(BaseModel):
    role_id: Optional[int] = None
    user_id: Optional[UUID] = None

class SysUserRoleResponse(SysUserRoleBase):
    id: int 
    create_datetime: datetime
    created_by: Optional[UUID] = None 
    class Config:
        orm_mode = True 
