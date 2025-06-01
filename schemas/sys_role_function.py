from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class SysRoleFunctionBase(BaseModel):
    role_id: int  # ID của vai trò
    function_id: int  # ID của chức năng
    status: Optional[int] = None  # Trạng thái (ví dụ: 1: active, 0: inactive)

class SysRoleFunctionCreate(BaseModel):
    role_id: int
    function_ids: List[int]
    status: Optional[int] = None

class AssignFunctionsResponse(BaseModel):
    message: str
    role_id: int
    assigned_function_ids: List[int]

class SysRoleFunctionUpdate(BaseModel):
    role_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[int] = None
    function_ids: List[int] 

class SysRoleFunctionResponse(SysRoleFunctionBase):
    id: int 
    created_by: Optional[UUID] = None  
    create_datetime: datetime 

    class Config:
        orm_mode = True