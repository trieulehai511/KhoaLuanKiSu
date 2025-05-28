
from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel
from uuid import UUID

class SysRoleBase(BaseModel):
    role_code: str
    role_name: str
    description: str
    status: int
    
class SysRoleCreate(SysRoleBase):
    pass

class SysRoleUpdate(SysRoleBase):
    role_code: Optional[str] = None
    role_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[int] = None

class SysRoleResponse(SysRoleBase):
    id: int
    create_datetime: datetime
    created_by: Optional[UUID] = None
    update_datetime: datetime

    class Config:
        orm_mode = True


class FunctionResponseTree(BaseModel):
    id: int
    name: str
    path: Optional[str] = None
    type: str
    parent_id: Optional[int] = None
    description: Optional[str] = None
    status: str
    children: Optional[List["FunctionResponseTree"]] = []

    class Config:
        orm_mode = True


class RoleResponseTree(BaseModel):
    id: int
    roleId: str
    roleName: str
    description: Optional[str] = None
    status: str
    function: List[FunctionResponseTree]

    class Config:
        orm_mode = True


