
from datetime import datetime
from typing import List, Optional
from uuid import UUID as PythonUUID 
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import UUID 
from schemas.sys_user_role import SysUserRoleCreate, SysUserRoleUpdate
from models.model import SysUserRole as SysUserRoleModel

def create_user_role_assignment(db: Session, assignment: SysUserRoleCreate, current_user_id: PythonUUID) -> SysUserRoleModel:
    """
    Gán một vai trò cho một người dùng (tạo một bản ghi SysUserRole mới).
    current_user_id là ID của người dùng thực hiện hành động này (nếu assignment.created_by không được cung cấp).
    """
    # Kiểm tra xem cặp user_id và role_id đã tồn tại chưa để tránh trùng lặp (tùy chọn)
    existing_assignment = db.query(SysUserRoleModel).filter(
        SysUserRoleModel.user_id == assignment.user_id,
        SysUserRoleModel.role_id == assignment.role_id
    ).first()

    if existing_assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Người dùng này đã được gán vai trò này rồi."
        )

    

    db_assignment = SysUserRoleModel(
        user_id=assignment.user_id,
        role_id=assignment.role_id,
        created_by=current_user_id,
        create_datetime=datetime.utcnow()
    )
    try:
        db.add(db_assignment)
        db.commit()
        db.refresh(db_assignment)
    except Exception as e:
        db.rollback()
        # Log lỗi e ở đây để debug
        print(f"Database error during user-role assignment creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi gán vai trò cho người dùng trong cơ sở dữ liệu."
        )
    return db_assignment

def get_user_role_assignment_by_id(db: Session, assignment_id: int) -> Optional[SysUserRoleModel]:
    """
    Lấy thông tin một bản ghi gán quyền cụ thể bằng ID của nó.
    """
    return db.query(SysUserRoleModel).filter(SysUserRoleModel.id == assignment_id).first()

def get_assignments_for_user(db: Session, user_id: PythonUUID) -> List[SysUserRoleModel]:
    """
    Lấy danh sách tất cả các vai trò đã được gán cho một người dùng cụ thể.
    """
    return db.query(SysUserRoleModel).filter(SysUserRoleModel.user_id == user_id).all()

def get_users_for_role(db: Session, role_id: int) -> List[SysUserRoleModel]:
    """
    Lấy danh sách tất cả các người dùng đã được gán một vai trò cụ thể.
    """
    return db.query(SysUserRoleModel).filter(SysUserRoleModel.role_id == role_id).all()


def update_user_role_assignment(db: Session, assignment_id: int, assignment_update_data: SysUserRoleUpdate, current_user_id: PythonUUID) -> Optional[SysUserRoleModel]:
    """
    Cập nhật một bản ghi gán quyền hiện có.
    assignment_id là ID của bản ghi SysUserRole cần cập nhật.
    """
    db_assignment = db.query(SysUserRoleModel).filter(SysUserRoleModel.id == assignment_id).first()

    if not db_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bản ghi gán quyền không tồn tại."
        )

    update_data = assignment_update_data.model_dump(exclude_unset=True)

    if "user_id" in update_data:
        db_assignment.user_id = update_data["user_id"]
    if "role_id" in update_data:
        db_assignment.role_id = update_data["role_id"]
    if "created_by" in update_data: # Cho phép cập nhật người tạo nếu cần
        db_assignment.created_by = update_data["created_by"]
    # Nếu có các trường khác như status của assignment, cập nhật ở đây
    # if "status" in update_data:
    #     db_assignment.status = update_data["status"]

    # Kiểm tra trùng lặp nếu user_id hoặc role_id đã thay đổi (tùy chọn, nhưng nên có)
    if "user_id" in update_data or "role_id" in update_data:
        check_conflict = db.query(SysUserRoleModel).filter(
            SysUserRoleModel.user_id == db_assignment.user_id,
            SysUserRoleModel.role_id == db_assignment.role_id,
            SysUserRoleModel.id != assignment_id # Loại trừ chính bản ghi đang cập nhật
        ).first()
        if check_conflict:
            db.rollback() # Hoàn tác các thay đổi đã gán ở trên nếu có xung đột
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sau khi cập nhật, người dùng này sẽ bị trùng lặp vai trò đã có."
            )
    try:
        db.commit()
        db.refresh(db_assignment)
    except Exception as e:
        db.rollback()
        print(f"Database error during user-role assignment update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi cập nhật bản ghi gán quyền."
        )
    return db_assignment

def delete_user_role_assignment(db: Session, assignment_id: int) -> dict:
    """
    Xóa một bản ghi gán quyền (bỏ gán vai trò cho người dùng).
    assignment_id là ID của bản ghi SysUserRole cần xóa.
    """
    db_assignment = db.query(SysUserRoleModel).filter(SysUserRoleModel.id == assignment_id).first()

    if not db_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bản ghi gán quyền không tồn tại."
        )
    try:
        db.delete(db_assignment)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Database error during user-role assignment deletion: {e}")
        # Cân nhắc các lỗi do ràng buộc nếu có (mặc dù bạn nói không có)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi xóa bản ghi gán quyền."
        )
    return {"message": "Gán quyền đã được xóa thành công."}

def delete_all_assignments_for_user(db: Session, user_id: PythonUUID) -> dict:
    """
    Xóa tất cả các vai trò đã gán cho một người dùng.
    """
    assignments = db.query(SysUserRoleModel).filter(SysUserRoleModel.user_id == user_id).all()
    if not assignments:
        # Có thể không cần raise lỗi, chỉ trả về thông báo là không có gì để xóa
        return {"message": "Người dùng này không có vai trò nào được gán."}
    
    try:
        for assignment in assignments:
            db.delete(assignment)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Database error during deletion of all assignments for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xóa tất cả các vai trò của người dùng {user_id}."
        )
    return {"message": f"Tất cả các vai trò của người dùng {user_id} đã được xóa."}

def delete_all_users_for_role(db: Session, role_id: int) -> dict:
    """
    Xóa tất cả các người dùng đã được gán một vai trò cụ thể.
    """
    assignments = db.query(SysUserRoleModel).filter(SysUserRoleModel.role_id == role_id).all()
    if not assignments:
        return {"message": f"Không có người dùng nào được gán vai trò ID {role_id}."}

    try:
        for assignment in assignments:
            db.delete(assignment)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Database error during deletion of all users for role {role_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xóa tất cả người dùng của vai trò ID {role_id}."
        )
    return {"message": f"Tất cả người dùng có vai trò ID {role_id} đã được bỏ gán."}
