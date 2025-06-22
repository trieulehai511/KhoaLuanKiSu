from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from db.database import get_db
from models.model import User
from routers.auth import get_current_user
from schemas.progress import (
    MissionResponse, TaskCreate, TaskResponse,
    TaskCommentCreate, TaskCommentResponse, TaskUpdate, TaskUpdateStatus
)
import services.progress as progress_service

router = APIRouter(
    prefix="/progress",
    tags=["Progress Management"]
)

@router.post("/theses/{thesis_id}/tasks", response_model=TaskResponse)
def create_task_for_thesis_endpoint(
    thesis_id: UUID,
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tạo một công việc (Task) mới trực tiếp cho một đề tài (Thesis)."""
    return progress_service.create_task_for_thesis(db, task, thesis_id, current_user.id)

@router.get("/theses/{thesis_id}/missions", response_model=List[MissionResponse])
def get_missions_endpoint(
    thesis_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return progress_service.get_missions_for_thesis(db, thesis_id, current_user.id)

@router.get("/theses/{thesis_id}/tasks", response_model=List[TaskResponse])
def get_tasks_for_thesis_endpoint(
    thesis_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lấy danh sách tất cả công việc (Task) của một đề tài (Thesis)."""
    return progress_service.get_tasks_for_thesis(db, thesis_id, current_user.id)

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

@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task_endpoint(
    task_id: UUID,
    task_update_data: TaskUpdate, # Sử dụng schema mới
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cập nhật thông tin của một công việc (chỉ giảng viên hoặc admin)."""
    return progress_service.update_task(db, task_id, task_update_data, current_user.id)

@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task_by_id_endpoint(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lấy thông tin chi tiết của một công việc (Task) theo ID.
    Cả giảng viên và sinh viên trong đề tài đều có thể xem.
    """
    return progress_service.get_task_by_id(db, task_id, current_user.id)

@router.delete("/tasks/{task_id}", status_code=status.HTTP_200_OK)
def delete_task_endpoint(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Xóa một công việc (chỉ giảng viên hoặc admin)."""
    return progress_service.delete_task(db, task_id, current_user.id)