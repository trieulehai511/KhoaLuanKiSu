from typing import List
from uuid import UUID as PythonUUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from models.model import User
from routers.auth import get_current_user
from schemas.sys_user_role import SysUserRoleCreate, SysUserRoleResponse, SysUserRoleUpdate
from services.sys_user_role import create_user_role_assignment, delete_all_assignments_for_user, delete_all_users_for_role, delete_user_role_assignment, get_assignments_for_user, get_user_role_assignment_by_id, get_users_for_role, update_user_role_assignment


router = APIRouter(
    prefix="/user-roles",
    tags=["User Roles Management"]
)

@router.post("/", response_model=SysUserRoleResponse, status_code=status.HTTP_201_CREATED)
def assign_role_to_user_endpoint(
    assignment_data: SysUserRoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Gán một vai trò cho một người dùng.
    """

    created_assignment = create_user_role_assignment(db=db, assignment=assignment_data, current_user_id= current_user.id)
    return created_assignment


@router.get("/{assignment_id}", response_model=SysUserRoleResponse)
def read_user_role_assignment_endpoint(
    assignment_id: int,
    db: Session = Depends(get_db)
):
    """
    Lấy thông tin một bản ghi gán quyền cụ thể bằng ID của nó.
    """
    db_assignment = get_user_role_assignment_by_id(db=db, assignment_id=assignment_id)
    if db_assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bản ghi gán quyền không được tìm thấy.")
    return db_assignment

@router.get("/user/{user_id}", response_model=List[SysUserRoleResponse])
def read_assignments_for_user_endpoint(
    user_id: PythonUUID,
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách tất cả các vai trò đã được gán cho một người dùng cụ thể.
    """
    assignments = get_assignments_for_user(db=db, user_id=user_id)
    return assignments

@router.get("/role/{role_id}", response_model=List[SysUserRoleResponse])
def read_users_for_role_endpoint(
    role_id: int,
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách tất cả các người dùng đã được gán một vai trò cụ thể.
    (Thực ra trả về danh sách các bản ghi SysUserRole, từ đó có thể suy ra user_id)
    """
    assignments = get_users_for_role(db=db, role_id=role_id)
    return assignments

@router.put("/{assignment_id}", response_model=SysUserRoleResponse)
def update_user_role_assignment_endpoint(
    assignment_id: int,
    assignment_update_data: SysUserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Có thể cần để ghi log ai cập nhật
):
    """
    Cập nhật một bản ghi gán quyền hiện có.
    """
    updated_assignment = update_user_role_assignment(
        db=db,
        assignment_id=assignment_id,
        assignment_update_data=assignment_update_data,
        current_user_id=current_user.id # Truyền ID người dùng hiện tại
    )
    if updated_assignment is None: # Service nên raise HTTPException nếu không tìm thấy
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bản ghi gán quyền không được tìm thấy để cập nhật.")
    return updated_assignment

@router.delete("/{assignment_id}", status_code=status.HTTP_200_OK)
def delete_user_role_assignment_endpoint(
    assignment_id: int,
    db: Session = Depends(get_db)
    # current_user: User = Depends(get_current_user) # Có thể cần để kiểm tra quyền xóa
):
    """
    Xóa một bản ghi gán quyền (bỏ gán vai trò cho người dùng).
    """
    result = delete_user_role_assignment(db=db, assignment_id=assignment_id)
    # Service đã raise HTTPException nếu không tìm thấy, nên ở đây chỉ cần trả về result
    return result

@router.delete("/user/{user_id}/all", status_code=status.HTTP_200_OK)
def delete_all_assignments_for_user_endpoint(
    user_id: PythonUUID,
    db: Session = Depends(get_db)
    # current_user: User = Depends(get_current_user) # Kiểm tra quyền
):
    """
    Xóa tất cả các vai trò đã gán cho một người dùng.
    """
    result = delete_all_assignments_for_user(db=db, user_id=user_id)
    return result

@router.delete("/role/{role_id}/all-users", status_code=status.HTTP_200_OK)
def delete_all_users_for_role_endpoint(
    role_id: int,
    db: Session = Depends(get_db)
    # current_user: User = Depends(get_current_user) # Kiểm tra quyền
):
    """
    Xóa tất cả các người dùng đã được gán một vai trò cụ thể (tức là bỏ gán vai trò này cho tất cả user).
    """
    result = delete_all_users_for_role(db=db, role_id=role_id)
    return result