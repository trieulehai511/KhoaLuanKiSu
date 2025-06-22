from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from db.database import get_db
from models.model import User
from routers.auth import get_current_user # Hoặc PathChecker nếu cần
from schemas.council import CouncilCreateWithTheses, CouncilResponse
import services.council as council_service

router = APIRouter(
    prefix="/councils",
    tags=["Council Management"]
)

@router.post("/", response_model=CouncilResponse, status_code=status.HTTP_201_CREATED)
def create_council_endpoint(
    council_data: CouncilCreateWithTheses,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Tạo một hội đồng mới, gán thành viên và danh sách đồ án.
    Yêu cầu quyền Admin.
    """
    # Thêm kiểm tra quyền Admin
    if current_user.user_type != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ Admin mới có quyền thực hiện hành động này.")
        
    return council_service.create_council_and_assign(db, council_data, current_user.id)