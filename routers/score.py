from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from db.database import get_db
from models.model import User
from routers.auth import get_current_user
from schemas.score import ScoreCreate, ScoreResponse
import services.score as score_service

router = APIRouter(
    prefix="/scores",
    tags=["Scoring"]
)

@router.post("/", response_model=ScoreResponse, status_code=status.HTTP_201_CREATED)
def create_score_endpoint(
    score_data: ScoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    API để một thành viên hội đồng chấm điểm cho một sinh viên.
    Nếu điểm đã tồn tại, API sẽ cập nhật lại điểm.
    """
    # Người chấm điểm chính là người dùng đang đăng nhập
    return score_service.create_or_update_score(db, score_data, current_user.id)