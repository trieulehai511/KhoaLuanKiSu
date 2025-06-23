from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from db.database import get_db
from models.model import User
from routers.auth import get_current_user # Hoặc PathChecker nếu cần
from schemas.council import CouncilCreateWithTheses, CouncilDetailResponse, CouncilResponse, CouncilUpdate
import services.council as council_service

router = APIRouter(
    prefix="/councils",
    tags=["Council Management"]
)
@router.get("/", response_model=List[CouncilDetailResponse])
def get_all_councils_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lấy danh sách tất cả hội đồng và các đồ án tương ứng.
    Yêu cầu quyền Admin hoặc Giảng viên.
    """
    # Thêm kiểm tra quyền
    if current_user.user_type not in [1, 3]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Admin hoặc Giảng viên mới có quyền xem danh sách hội đồng."
        )
    return council_service.get_all_councils_with_theses(db)

# =================================
@router.post("/", response_model=CouncilResponse, status_code=status.HTTP_201_CREATED)
def create_council_endpoint(
    council_data: CouncilCreateWithTheses,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Tạo một hội đồng mới, gán thành viên và danh sách đồ án.
    Yêu cầu quyền Admin hoặc Giảng viên.
    """
    # === SỬA LẠI ĐIỀU KIỆN KIỂM TRA TẠI ĐÂY ===
    # Cho phép user_type là 1 (Admin) hoặc 3 (Giảng viên)
    if current_user.user_type not in [1, 3]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Admin hoặc Giảng viên mới có quyền thực hiện hành động này."
        )
    # ==========================================
        
    return council_service.create_council_and_assign(db, council_data, current_user.id)

@router.put("/{council_id}", response_model=CouncilResponse)
def update_council_endpoint(
    council_id: UUID,
    council_data: CouncilUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cập nhật thông tin hội đồng (yêu cầu quyền Admin hoặc Giảng viên)."""
    if current_user.user_type not in [1, 3]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Admin hoặc Giảng viên mới có quyền thực hiện hành động này."
        )
    return council_service.update_council(db, council_id, council_data)

@router.delete("/{council_id}", status_code=status.HTTP_200_OK)
def delete_council_endpoint(
    council_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Xóa một hội đồng (chỉ Admin).
    """
    # Chỉ Admin (user_type = 1) mới có quyền xóa
    if current_user.user_type != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Admin mới có quyền thực hiện hành động này."
        )
    return council_service.delete_council(db, council_id)