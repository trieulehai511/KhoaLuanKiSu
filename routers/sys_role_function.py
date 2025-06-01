from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.model import User
from schemas.sys_role import RoleResponseTree
from schemas.sys_role_function import SysRoleFunctionCreate, SysRoleFunctionUpdate, SysRoleFunctionResponse
from services.sys_role_function import (
    create_role_functions,
    update_role_function,
    get_role_function_by_id,
    get_all_role_functions,
    delete_role_function
)
from routers.auth import get_current_user

router = APIRouter(
    prefix="/role-functions",
    tags=["role-functions"]
)

@router.post("/", response_model=RoleResponseTree)
def assign_functions_to_role_and_return_tree(
    role_function_data: SysRoleFunctionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_role_functions(db, role_function_data, current_user.id)


@router.put("/update-role/{role_id}", response_model=RoleResponseTree)
def update_role_function_endpoint(
    role_id: int,
    update_data: SysRoleFunctionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return update_role_function(db, role_id, update_data, current_user.id)


@router.get("/{role_function_id}", response_model=SysRoleFunctionResponse)
def get_role_function_endpoint(
    role_function_id: int,
    db: Session = Depends(get_db)
):
    """
    API để lấy thông tin một liên kết giữa vai trò và chức năng theo ID.
    """
    return get_role_function_by_id(db, role_function_id)

@router.get("/", response_model=List[SysRoleFunctionResponse])
def get_all_role_functions_endpoint(
    db: Session = Depends(get_db)
):
    """
    API để lấy danh sách tất cả liên kết giữa vai trò và chức năng.
    """
    return get_all_role_functions(db)

@router.delete("/{role_function_id}")
def delete_role_function_endpoint(
    role_function_id: int,
    db: Session = Depends(get_db)
):
    """
    API để xóa một liên kết giữa vai trò và chức năng theo ID.
    """
    return delete_role_function(db, role_function_id)