from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

# Schema cho request body khi gửi điểm
class ScoreCreate(BaseModel):
    thesis_id: UUID
    student_id: UUID
    # Thêm ràng buộc cho điểm từ 0 đến 10
    score: float = Field(..., gt=0, le=10) 
    score_type: int

# Schema cho response sau khi chấm điểm thành công
class ScoreResponse(BaseModel):
    id: UUID
    thesis_id: UUID
    student_id: UUID
    evaluator_id: UUID
    score: float
    score_type: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True