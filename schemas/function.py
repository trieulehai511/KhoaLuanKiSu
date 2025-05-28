from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class FunctionBase(BaseModel):
    name: str  # Tên chức năng (ví dụ: "Quản lý người dùng")
    path: Optional[str] = None  # Đường dẫn API hoặc mã định danh cho GROUP
    type: str  # Loại chức năng: "GROUP" hoặc "API"
    parent_id: Optional[int] = None  # ID của chức năng cha (nếu có)
    description: Optional[str] = None  # Mô tả chức năng
    status: Optional[int] = None  # Trạng thái của chức năng (ví dụ: 'enabled', 'disabled')

class FunctionCreate(FunctionBase):
    pass

class FunctionUpdate(BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None
    type: Optional[str] = None
    parent_id: Optional[int] = None
    description: Optional[str] = None
    status: Optional[int] = None

class FunctionResponse(BaseModel):
    id: int
    name: str
    path: Optional[str] = None
    type: str
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None  # Thêm trường parent_name
    description: Optional[str] = None
    status: str
    create_datetime: datetime
    update_datetime: datetime
    children: Optional[List["FunctionResponse"]] = []

    class Config:
        orm_mode = True