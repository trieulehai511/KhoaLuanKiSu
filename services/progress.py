from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from models.model import Thesis, ThesisLecturer, GroupMember, Mission, Task, TaskComment, User, Information
from schemas.progress import MissionCreate, TaskCreate, TaskCommentCreate, TaskUpdateStatus

# --- Helper Function to check permissions ---
def _get_user_thesis_role(db: Session, thesis_id: UUID, user_id: UUID):
    thesis = db.query(Thesis).filter(Thesis.id == thesis_id).first()
    if not thesis:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề tài.")

    # Check if user is an instructor for this thesis
    is_instructor = db.query(ThesisLecturer).filter(
        ThesisLecturer.thesis_id == thesis_id,
        ThesisLecturer.lecturer_id == user_id
    ).first()
    if is_instructor:
        return "lecturer"

    # Check if user is a student in the assigned group
    if thesis.group_id:
        is_student_in_group = db.query(GroupMember).filter(
            GroupMember.group_id == thesis.group_id,
            GroupMember.student_id == user_id
        ).first()
        if is_student_in_group:
            return "student"

    return None

# --- Service Functions ---

def create_mission(db: Session, mission_data: MissionCreate, thesis_id: UUID, user_id: UUID):
    role = _get_user_thesis_role(db, thesis_id, user_id)
    if role != "lecturer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ giảng viên hướng dẫn mới có quyền tạo nhiệm vụ.")
    
    new_mission = Mission(**mission_data.dict(), thesis_id=thesis_id)
    db.add(new_mission)
    db.commit()
    db.refresh(new_mission)
    return new_mission

def create_task(db: Session, task_data: TaskCreate, mission_id: UUID, user_id: UUID):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhiệm vụ.")
    
    role = _get_user_thesis_role(db, mission.thesis_id, user_id)
    if role != "lecturer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ giảng viên hướng dẫn mới có quyền tạo công việc.")

    new_task = Task(**task_data.dict(), mission_id=mission_id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

def get_missions_for_thesis(db: Session, thesis_id: UUID, user_id: UUID):
    if not _get_user_thesis_role(db, thesis_id, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền xem tiến độ của đề tài này.")
    
    missions = db.query(Mission).filter(Mission.thesis_id == thesis_id).all()
    # You would typically build a nested response here, this is a simplified version
    return missions

def update_task_status(db: Session, task_id: UUID, status_data: TaskUpdateStatus, user_id: UUID):
    task = db.query(Task).join(Mission).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc.")

    role = _get_user_thesis_role(db, task.mission.thesis_id, user_id)
    if role != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ sinh viên trong nhóm mới có quyền cập nhật trạng thái.")

    task.status = status_data.status
    db.commit()
    db.refresh(task)
    return task

def create_task_comment(db: Session, comment_data: TaskCommentCreate, task_id: UUID, user_id: UUID):
    task = db.query(Task).join(Mission).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc.")

    if not _get_user_thesis_role(db, task.mission.thesis_id, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền bình luận vào công việc này.")

    new_comment = TaskComment(**comment_data.dict(), task_id=task_id, commenter_id=user_id)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment