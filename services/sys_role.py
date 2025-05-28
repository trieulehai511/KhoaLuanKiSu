from datetime import datetime
from fastapi import HTTPException,status
from sqlalchemy import UUID
from sqlalchemy.orm import Session
from models.model import SysRole, SysRoleFunction
from schemas.sys_role import FunctionResponseTree, RoleResponseTree, SysRoleCreate
from sqlalchemy.orm import Session
from models.model import SysRole, SysFunction
from fastapi import HTTPException, status

def create_role(db: Session, role: SysRoleCreate, user_id: UUID):
        existing_role = db.query(SysRole).filter(SysRole.role_code == role.role_code).first()
        if existing_role:
                raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã role này đã tồn tại rồi"
        )

        db_role = SysRole(
                role_code = role.role_code,
                role_name = role.role_name,
                description = role.description,
                created_by=user_id,
                status = role.status,
                create_datetime=datetime.utcnow(),
                update_datetime=datetime.utcnow()
        )
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
        return db_role


def update_role(db: Session, role_id: int, role: SysRoleCreate, user_id: UUID):
    # Kiểm tra xem vai trò có tồn tại không
    db_role = db.query(SysRole).filter(SysRole.id == role_id).first()
    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role không có"
        )
    db_role.role_code = role.role_code or db_role.role_code
    db_role.role_name = role.role_name or db_role.role_name
    db_role.description = role.description or db_role.description
    db_role.status = role.status if role.status is not None else db_role.status
    db_role.update_datetime = datetime.utcnow()

    db.commit()
    db.refresh(db_role)
    return db_role

def delete_role(db: Session, role_id: int):
    db_role = db.query(SysRole).filter(SysRole.id == role_id).first()
    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role không có"
        )
    # Xóa vai trò
    db.delete(db_role)
    db.commit()
    return {"message": "Role deleted successfully"}

def get_role_with_functions(db: Session, role_id: int) -> RoleResponseTree:
    """
    Lấy thông tin vai trò (role) và các chức năng (functions) liên quan.
    """
    role = db.query(SysRole).filter(SysRole.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    role_functions = db.query(SysRoleFunction).filter(SysRoleFunction.role_id == role_id).all()
    function_ids = [rf.function_id for rf in role_functions]
    functions = db.query(SysFunction).filter(SysFunction.id.in_(function_ids)).all()

    function_dict = {function.id: FunctionResponseTree(
        id=function.id,
        name=function.name,
        path=function.path,
        type=function.type,
        parent_id=function.parent_id,
        description=function.description,
        status="Hoạt động" if function.status == 1 else "Ngừng hoạt động",
        children=[]
    ) for function in functions}

    tree = []
    for function in function_dict.values():
        if function.parent_id is None:
            tree.append(function)
        else:
            parent = function_dict.get(function.parent_id)
            if parent:
                parent.children.append(function)

    return RoleResponseTree(
        id=role.id,
        roleId=role.role_code,
        roleName=role.role_name,
        description=role.description,
        status="Hoạt động" if role.status == 1 else "Ngừng hoạt động",
        function=tree
    )





                
