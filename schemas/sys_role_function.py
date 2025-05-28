from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class SysRoleFunctionBase(BaseModel):
    role_id: int  # ID của vai trò
    function_id: int  # ID của chức năng
    status: Optional[int] = None  # Trạng thái (ví dụ: 1: active, 0: inactive)

class SysRoleFunctionCreate(SysRoleFunctionBase):
    pass

class SysRoleFunctionUpdate(BaseModel):
    status: Optional[int] = None  

class SysRoleFunctionResponse(SysRoleFunctionBase):
    id: int 
    created_by: Optional[UUID] = None  
    create_datetime: datetime 

    class Config:
        orm_mode = True