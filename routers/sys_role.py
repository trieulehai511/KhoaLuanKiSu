from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.sys_role import RoleResponseTree, SysRoleCreate, SysRoleResponse
from services.sys_role import create_role, delete_role, get_role_with_functions, update_role
from routers.auth import get_current_user
from models.model import User
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

@router.put("/{role_id}", response_model=SysRoleResponse)
def update_user_role(
    role_id: int,
    role: SysRoleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return update_role(db, role_id, role, user.id)

@router.delete("/{role_id}")
def delete_user_role(
    role_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return delete_role(db, role_id)


@router.get("/{role_id}", response_model=RoleResponseTree)
def get_role_with_functions_endpoint(
    role_id: str,
    db: Session = Depends(get_db)
):
    """
    API để lấy thông tin vai trò và các chức năng liên quan.
    """
    return get_role_with_functions(db, role_id)



