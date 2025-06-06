from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.sys_role import RoleResponseTree, SysRoleCreate, SysRoleCreateWithFunctions, SysRoleResponse
from schemas.sys_role_function import SysRoleFunctionUpdate
from services.sys_role import create_role, create_role_with_functions, delete_role, get_all_roles, get_all_roles_create, get_role_with_functions, update_role
from routers.auth import PathChecker, get_current_user
from models.model import User
from services.sys_role_function import update_role_and_functions
# from utils.path_checker import PathChecker  
router = APIRouter(
    prefix="/roles",
    tags=["roles"]
)

@router.post("/", response_model=SysRoleResponse)
def create_user_role(
    role: SysRoleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return create_role(db, role, user.id)

@router.put("/{role_id}", response_model=RoleResponseTree,dependencies=[Depends(PathChecker("/put/roles/:id"))])
def update_role_full(
    role_id: int,
    update_data: SysRoleFunctionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return update_role_and_functions(db=db, role_id=role_id, update_data=update_data, user_id=str(current_user.id))

@router.delete("/{role_id}",dependencies=[Depends(PathChecker("/delete/roles/:id"))])
def delete_user_role(
    role_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return delete_role(db, role_id)


@router.get("/{role_id}", response_model=RoleResponseTree)
def get_role_with_functions_endpoint(
    role_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    API để lấy thông tin vai trò và các chức năng liên quan.
    """
    return get_role_with_functions(db, role_id)

@router.get("/assign/permission", response_model=List[RoleResponseTree])
def get_all_roles_endpoint(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    API để lấy danh sách tất cả các vai trò (roles) với thông tin các chức năng liên quan.
    """
    return get_all_roles_create(db)

@router.get("/", response_model=List[RoleResponseTree],dependencies=[Depends(PathChecker("/get/roles"))])
def get_all_roles_endpoint(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    API để lấy danh sách tất cả các vai trò (roles) với thông tin các chức năng liên quan.
    """
    return get_all_roles(db)

@router.post("/create-with-functions",dependencies=[Depends(PathChecker("/roles/create-with-functions"))], response_model=RoleResponseTree)
def create_role_with_functions_endpoint(
    data: SysRoleCreateWithFunctions,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_role_with_functions(db, data, current_user.id)








