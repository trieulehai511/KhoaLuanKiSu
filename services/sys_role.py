from datetime import datetime
from typing import List
from fastapi import HTTPException,status
from sqlalchemy import UUID
from sqlalchemy.orm import Session
from models.model import SysRole, SysRoleFunction
from schemas.sys_role import FunctionResponseTree, RoleResponseTree, SysRoleCreate, SysRoleCreateWithFunctions
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
        status= function.status,
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
        status=role.status,
        function=tree
    )

def get_all_roles(db: Session) -> List[RoleResponseTree]:
    """
    Lấy danh sách tất cả vai trò và các chức năng liên quan dưới dạng cây.
    """
    roles = db.query(SysRole).all()
    all_functions = db.query(SysFunction).all()
    
    # Đưa toàn bộ function vào dict để tái sử dụng
    all_function_dict = {
        function.id: FunctionResponseTree(
            id=function.id,
            name=function.name,
            path=function.path,
            type=function.type,
            parent_id=function.parent_id,
            description=function.description,
            status="Hoạt động" if function.status == 1 else "Ngừng hoạt động",
            children=[]
        )
        for function in all_functions
    }

    role_responses = []

    for role in roles:
        # Lấy danh sách function_id đã được cấp cho vai trò
        role_function_ids = [
            rf.function_id for rf in db.query(SysRoleFunction)
            .filter(SysRoleFunction.role_id == role.id)
            .all()
        ]

        # Lọc ra các function object tương ứng từ dict (đã được build từ all_function_dict)
        function_nodes = {
            fid: all_function_dict[fid]
            for fid in role_function_ids if fid in all_function_dict
        }

        # Reset children (để tránh nối trùng khi lặp nhiều role)
        for fn in function_nodes.values():
            fn.children = []

        # Gắn cây quan hệ cha – con trong tập hợp function đã cấp cho role
        tree: List[FunctionResponseTree] = []
        for fn in function_nodes.values():
            if fn.parent_id and fn.parent_id in function_nodes:
                function_nodes[fn.parent_id].children.append(fn)
            else:
                tree.append(fn)

        # Trả về thông tin role với cây function
        role_responses.append(RoleResponseTree(
            id=role.id,
            roleId=role.role_code,
            roleName=role.role_name,
            description=role.description,
            status="Hoạt động" if role.status == 1 else "Ngừng hoạt động",
            function=tree
        ))

    return role_responses



def get_all_roles_create(db: Session) -> List[RoleResponseTree]:
    roles = db.query(SysRole).all()
    all_functions = db.query(SysFunction).all()

    # Gốc khởi tạo, không gán is_assigned ở đây
    base_function_data = {
        f.id: {
            "id": f.id,
            "name": f.name,
            "path": f.path,
            "type": f.type,
            "parent_id": f.parent_id,
            "description": f.description,
            "status": "Hoạt động" if f.status == 1 else "Ngừng hoạt động"
        }
        for f in all_functions
    }

    role_responses = []

    for role in roles:
        assigned_ids = set(
            rf.function_id for rf in db.query(SysRoleFunction)
            .filter(SysRoleFunction.role_id == role.id).all()
        )

        # Tạo bản sao FunctionResponseTree cho từng role (tránh ảnh hưởng lẫn nhau)
        function_dict = {
            fid: FunctionResponseTree(
                **data,
                is_assigned=(fid in assigned_ids),
                children=[]
            )
            for fid, data in base_function_data.items()
        }

        # Gắn cây
        for fn in function_dict.values():
            fn.children = []

        for fn in function_dict.values():
            if fn.parent_id and fn.parent_id in function_dict:
                function_dict[fn.parent_id].children.append(fn)

        # Lọc root node
        roots = [
            fn for fn in function_dict.values()
            if fn.parent_id is None and has_assigned_child(fn, assigned_ids)
        ]

        role_responses.append(RoleResponseTree(
            id=role.id,
            roleId=role.role_code,
            roleName=role.role_name,
            description=role.description,
            status="Hoạt động" if role.status == 1 else "Ngừng hoạt động",
            function=roots
        ))

    return role_responses


# Helper để kiểm tra xem node hoặc con nó có được cấp quyền không
def has_assigned_child(node: FunctionResponseTree, assigned_ids: set) -> bool:
    if node.id in assigned_ids:
        return True
    for child in node.children:
        if has_assigned_child(child, assigned_ids):
            return True
    return False

def get_all_roles(db: Session) -> List[RoleResponseTree]:
    """
    Lấy danh sách tất cả các vai trò (roles) với thông tin các chức năng liên quan.
    """
    # Lấy danh sách tất cả các vai trò từ cơ sở dữ liệu
    roles = db.query(SysRole).all()

    # Chuyển đổi dữ liệu thành danh sách các đối tượng RoleResponse
    role_responses = []
    for role in roles:
        # Lấy danh sách các chức năng liên quan từ bảng SysRoleFunction
        role_functions = db.query(SysRoleFunction).filter(SysRoleFunction.role_id == role.id).all()
        function_ids = [rf.function_id for rf in role_functions]

        # Lấy thông tin các chức năng từ bảng SysFunction
        functions = db.query(SysFunction).filter(SysFunction.id.in_(function_ids)).all()

        # Chuyển đổi danh sách chức năng thành cấu trúc cây
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

        # Thêm thông tin vai trò vào danh sách phản hồi
        role_responses.append(RoleResponseTree(
            id=role.id,
            roleId=role.role_code,
            roleName=role.role_name,
            description=role.description,
            status="Hoạt động" if role.status == 1 else "Ngừng hoạt động",
            function=tree
        ))

    return role_responses

def create_role_with_functions(
    db: Session,
    role_data: SysRoleCreateWithFunctions,
    user_id: str
) -> RoleResponseTree:
    existing_role = db.query(SysRole).filter(SysRole.role_code == role_data.role_code).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã role đã tồn tại"
        )

    new_role = SysRole(
        role_code=role_data.role_code,
        role_name=role_data.role_name,
        description=role_data.description,
        status=role_data.status,
        created_by=user_id,
        create_datetime=datetime.utcnow(),
        update_datetime=datetime.utcnow()
    )
    db.add(new_role)
    db.commit()
    db.refresh(new_role)

    # Gán chức năng
    for function_id in role_data.function_ids:
        db.add(SysRoleFunction(
            role_id=new_role.id,
            function_id=function_id,
            status=1,
            created_by=user_id,
            create_datetime=datetime.utcnow()
        ))

    db.commit()

    # Truy vấn lại các chức năng vừa gán
    functions = db.query(SysFunction).filter(SysFunction.id.in_(role_data.function_ids)).all()

    def build_tree(items, parent_id=None):
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
                    is_assigned=True,
                    children=[]
                )
                node.children = build_tree(items, item.id)
                tree.append(node)
        return tree

    return RoleResponseTree(
        id=new_role.id,
        roleId=new_role.role_code,
        roleName=new_role.role_name,
        description=new_role.description,
        status="Hoạt động" if new_role.status == 1 else "Ngừng hoạt động",
        function=build_tree(functions)
    )


                
