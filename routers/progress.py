# trieulehai511/khoaluankisu/KhoaLuanKiSu-2c2df2c1a2b0a2f6ca7e7682b68d080964b944d6/routers/progress.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from db.database import get_db
from models.model import User
from routers.auth import get_current_user
from schemas.progress import (
    MissionCreate, MissionResponse, TaskCreate, TaskResponse,
    TaskCommentCreate, TaskCommentResponse, TaskUpdateStatus
)
import services.progress as progress_service

router = APIRouter(
    prefix="/progress",
    tags=["Progress Management"]
)

@router.post("/theses/{thesis_id}/missions", response_model=MissionResponse)
def create_mission_endpoint(
    thesis_id: UUID,
    mission: MissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return progress_service.create_mission(db, mission, thesis_id, current_user.id)

@router.post("/missions/{mission_id}/tasks", response_model=TaskResponse)
def create_task_endpoint(
    mission_id: UUID,
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return progress_service.create_task(db, task, mission_id, current_user.id)

@router.get("/theses/{thesis_id}/missions", response_model=List[MissionResponse])
def get_missions_endpoint(
    thesis_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return progress_service.get_missions_for_thesis(db, thesis_id, current_user.id)

@router.patch("/tasks/{task_id}/status", response_model=TaskResponse)
def update_task_status_endpoint(
    task_id: UUID,
    status_data: TaskUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return progress_service.update_task_status(db, task_id, status_data, current_user.id)

@router.post("/tasks/{task_id}/comments", response_model=TaskCommentResponse)
def create_comment_endpoint(
    task_id: UUID,
    comment: TaskCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return progress_service.create_task_comment(db, comment, task_id, current_user.id)