from sqlalchemy.orm import Session
from models.model import SysRoleFunction
from schemas.sys_role_function import SysRoleFunctionCreate, SysRoleFunctionUpdate, SysRoleFunctionResponse
from fastapi import HTTPException, status
from datetime import datetime
from typing import List

def create_role_function(db: Session, role_function: SysRoleFunctionCreate, user_id: str) -> SysRoleFunctionResponse:
    """
    Tạo mới một liên kết giữa vai trò và chức năng.
    """
    # Kiểm tra xem liên kết đã tồn tại chưa
    existing_link = db.query(SysRoleFunction).filter(
        SysRoleFunction.role_id == role_function.role_id,
        SysRoleFunction.function_id == role_function.function_id
    ).first()
    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role-Function link already exists"
        )

    # Tạo mới liên kết
    db_role_function = SysRoleFunction(
        role_id=role_function.role_id,
        function_id=role_function.function_id,
        status=role_function.status if role_function.status is not None else 1,  # Mặc định là active
        created_by=user_id,
        create_datetime=datetime.utcnow()
    )
    db.add(db_role_function)
    db.commit()
    db.refresh(db_role_function)
    return SysRoleFunctionResponse.from_orm(db_role_function)

def update_role_function(db: Session, role_function_id: int, role_function: SysRoleFunctionUpdate) -> SysRoleFunctionResponse:
    """
    Cập nhật trạng thái của liên kết giữa vai trò và chức năng.
    """
    db_role_function = db.query(SysRoleFunction).filter(SysRoleFunction.id == role_function_id).first()
    if not db_role_function:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role-Function link not found"
        )

    # Cập nhật trạng thái
    for key, value in role_function.dict(exclude_unset=True).items():
        setattr(db_role_function, key, value)
    db.commit()
    db.refresh(db_role_function)
    return SysRoleFunctionResponse.from_orm(db_role_function)

def get_role_function_by_id(db: Session, role_function_id: int) -> SysRoleFunctionResponse:
    """
    Lấy thông tin liên kết giữa vai trò và chức năng theo ID.
    """
    db_role_function = db.query(SysRoleFunction).filter(SysRoleFunction.id == role_function_id).first()
    if not db_role_function:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role-Function link not found"
        )
    return SysRoleFunctionResponse.from_orm(db_role_function)

def get_all_role_functions(db: Session) -> List[SysRoleFunctionResponse]:
    """
    Lấy danh sách tất cả liên kết giữa vai trò và chức năng.
    """
    role_functions = db.query(SysRoleFunction).all()
    return [SysRoleFunctionResponse.from_orm(role_function) for role_function in role_functions]

def delete_role_function(db: Session, role_function_id: int):
    """
    Xóa một liên kết giữa vai trò và chức năng.
    """
    db_role_function = db.query(SysRoleFunction).filter(SysRoleFunction.id == role_function_id).first()
    if not db_role_function:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role-Function link not found"
        )
    db.delete(db_role_function)
    db.commit()
    return {"message": "Role-Function link deleted successfully"}