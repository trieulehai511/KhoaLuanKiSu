from sqlalchemy.orm import Session
from models.model import SysFunction, SysRole, SysRoleFunction
from schemas.sys_role import FunctionResponseTree, RoleResponseTree
from schemas.sys_role_function import SysRoleFunctionCreate, SysRoleFunctionUpdate, SysRoleFunctionResponse
from fastapi import HTTPException, status
from datetime import datetime
from typing import List, Optional

from services.sys_role import has_assigned_child

def create_role_functions(
    db: Session,
    role_function_data: SysRoleFunctionCreate,
    user_id: str
) -> RoleResponseTree:
    # Bước 1: Lấy role
    role = db.query(SysRole).filter(SysRole.id == role_function_data.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Vai trò không tồn tại.")

    duplicated = []
    for function_id in role_function_data.function_ids:
        exists = db.query(SysRoleFunction).filter_by(
            role_id=role_function_data.role_id,
            function_id=function_id
        ).first()
        if exists:
            duplicated.append(function_id)
        else:
            db.add(SysRoleFunction(
                role_id=role_function_data.role_id,
                function_id=function_id,
                status=role_function_data.status if role_function_data.status is not None else 1,
                created_by=user_id,
                create_datetime=datetime.utcnow()
            ))

    if duplicated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Các chức năng đã được cấp quyền: {duplicated}"
        )

    db.commit()

    # Bước 3: Truy vấn tất cả function đã được cấp cho role
    function_ids = db.query(SysRoleFunction.function_id).filter_by(role_id=role.id).all()
    function_ids = [fid[0] for fid in function_ids]

    functions = db.query(SysFunction).filter(SysFunction.id.in_(function_ids)).all()

    # Bước 4: Xây dựng cây chức năng
    def build_tree(items: List[SysFunction], parent_id: Optional[int] = None) -> List[FunctionResponseTree]:
        tree = []
        for item in items:
            if item.parent_id == parent_id:
                node = FunctionResponseTree(
                    id=item.id,
                    name=item.name,
                    path=item.path,
                    type=item.type,
                    parent_id=item.parent_id,
                    description=item.description,
                    status="enabled" if item.status == 1 else "disabled",
                    is_assigned=True,  # Vì tất cả đều là function đã được cấp
                    children=[]
                )
                node.children = build_tree(items, item.id)
                tree.append(node)
        return tree

    function_tree = build_tree(functions)

    # Bước 5: Trả về thông tin role kèm cây function
    return RoleResponseTree(
        id=role.id,
        roleId=role.role_code,
        roleName=role.role_name,
        description=role.description,
        status="active" if role.status == 1 else "inactive",
        function=function_tree
    )

def update_role_and_functions(
    db: Session,
    role_id: int,
    update_data: SysRoleFunctionUpdate,
    user_id: str
) -> RoleResponseTree:
    # 1. Kiểm tra vai trò tồn tại
    role = db.query(SysRole).filter(SysRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Vai trò không tồn tại.")

    # 2. ✅ Cập nhật thông tin vai trò nếu có
    if update_data.role_name is not None:
        role.role_name = update_data.role_name
    if update_data.description is not None:
        role.description = update_data.description
    if update_data.status is not None:
        role.status = update_data.status
    role.update_datetime = datetime.utcnow()

    # 3. ✅ Cập nhật chức năng (function_ids) giống logic cũ
    existing_links = db.query(SysRoleFunction).filter_by(role_id=role_id).all()
    existing_function_ids = {link.function_id for link in existing_links}
    new_function_ids = set(update_data.function_ids)

    # 3.1 Xoá những function không còn trong danh sách mới
    to_delete = existing_function_ids - new_function_ids
    if to_delete:
        db.query(SysRoleFunction).filter(
            SysRoleFunction.role_id == role_id,
            SysRoleFunction.function_id.in_(to_delete)
        ).delete(synchronize_session=False)

    # 3.2 Thêm mới những function chưa từng gán
    to_add = new_function_ids - existing_function_ids
    for fid in to_add:
        db.add(SysRoleFunction(
            role_id=role_id,
            function_id=fid,
            status=update_data.status or 1,
            created_by=user_id,
            create_datetime=datetime.utcnow()
        ))

    # 3.3 Cập nhật lại trạng thái các function vẫn giữ nguyên
    db.query(SysRoleFunction).filter(
        SysRoleFunction.role_id == role_id,
        SysRoleFunction.function_id.in_(existing_function_ids & new_function_ids)
    ).update({SysRoleFunction.status: update_data.status}, synchronize_session=False)

    db.commit()

    # 4. Dựng lại cấu trúc trả về RoleResponseTree
    function_ids = db.query(SysRoleFunction.function_id).filter_by(role_id=role.id).all()
    function_ids = [fid[0] for fid in function_ids]
    all_functions = db.query(SysFunction).all()
    assigned_ids = set(function_ids)

    function_dict = {
        f.id: FunctionResponseTree(
            id=f.id,
            name=f.name,
            path=f.path,
            type=f.type,
            parent_id=f.parent_id,
            description=f.description,
            status="Hoạt động" if f.status == 1 else "Ngừng hoạt động",
            is_assigned=(f.id in assigned_ids),
            children=[]
        )
        for f in all_functions
    }

    for fn in function_dict.values():
        if fn.parent_id and fn.parent_id in function_dict:
            function_dict[fn.parent_id].children.append(fn)

    roots = [
        fn for fn in function_dict.values()
        if fn.parent_id is None and has_assigned_child(fn, assigned_ids)
    ]

    return RoleResponseTree(
        id=role.id,
        roleId=role.role_code,
        roleName=role.role_name,
        description=role.description,
        status="Hoạt động" if role.status == 1 else "Ngừng hoạt động",
        function=roots
    )
def update_role_function(
    db: Session,
    role_id: int,
    update_data: SysRoleFunctionUpdate,
    user_id: str
) -> RoleResponseTree:
    # Kiểm tra vai trò
    role = db.query(SysRole).filter(SysRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Vai trò không tồn tại.")

    # Lấy tất cả các function hiện đang được gán cho role
    existing_links = db.query(SysRoleFunction).filter_by(role_id=role_id).all()
    existing_function_ids = {link.function_id for link in existing_links}
    new_function_ids = set(update_data.function_ids)

    # Các function cần xóa (thu hồi)
    to_delete = existing_function_ids - new_function_ids
    if to_delete:
        db.query(SysRoleFunction).filter(
            SysRoleFunction.role_id == role_id,
            SysRoleFunction.function_id.in_(to_delete)
        ).delete(synchronize_session=False)

    # Các function cần thêm mới
    to_add = new_function_ids - existing_function_ids
    for fid in to_add:
        db.add(SysRoleFunction(
            role_id=role_id,
            function_id=fid,
            status=update_data.status or 1,
            created_by=user_id,
            create_datetime=datetime.utcnow()
        ))

    # Cập nhật trạng thái các function còn lại
    db.query(SysRoleFunction).filter(
        SysRoleFunction.role_id == role_id,
        SysRoleFunction.function_id.in_(existing_function_ids & new_function_ids)
    ).update({SysRoleFunction.status: update_data.status}, synchronize_session=False)

    db.commit()

    # Trả lại kết quả giống RoleResponseTree
    function_ids = db.query(SysRoleFunction.function_id).filter_by(role_id=role.id).all()
    function_ids = [fid[0] for fid in function_ids]

    all_functions = db.query(SysFunction).all()
    assigned_ids = set(function_ids)

    # Dựng dict function
    function_dict = {
        f.id: FunctionResponseTree(
            id=f.id,
            name=f.name,
            path=f.path,
            type=f.type,
            parent_id=f.parent_id,
            description=f.description,
            status="Hoạt động" if f.status == 1 else "Ngừng hoạt động",
            is_assigned=(f.id in assigned_ids),
            children=[]
        )
        for f in all_functions
    }

    # Gắn cây cha-con
    for fn in function_dict.values():
        if fn.parent_id and fn.parent_id in function_dict:
            function_dict[fn.parent_id].children.append(fn)

    roots = [
        fn for fn in function_dict.values()
        if fn.parent_id is None and has_assigned_child(fn, assigned_ids)
    ]

    return RoleResponseTree(
        id=role.id,
        roleId=role.role_code,
        roleName=role.role_name,
        description=role.description,
        status="Hoạt động" if role.status == 1 else "Ngừng hoạt động",
        function=roots
    )


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