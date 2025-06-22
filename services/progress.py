from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from models.model import Thesis, ThesisLecturer, Group, GroupMember, Mission, Task, TaskComment, User, Information
from schemas.progress import MissionCreate, TaskCreate, TaskCommentCreate, TaskUpdate, TaskUpdateStatus

# --- Helper Function ---
def _get_user_thesis_role(db: Session, thesis_id: UUID, user_id: UUID):
    """Kiểm tra vai trò của người dùng (admin, giảng viên, sinh viên) đối với một đề tài."""

    # === THÊM MỚI: KIỂM TRA QUYỀN ADMIN ĐẦU TIÊN ===
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.user_type == 1:  # Giả sử 1 là user_type của Admin
        return "admin"
    # ===============================================

    thesis = db.query(Thesis).filter(Thesis.id == thesis_id).first()
    if not thesis:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề tài.")

    # Kiểm tra xem người dùng có phải là giảng viên hướng dẫn không
    is_instructor = db.query(ThesisLecturer).filter(
        ThesisLecturer.thesis_id == thesis_id,
        ThesisLecturer.lecturer_id == user_id
    ).first()
    if is_instructor:
        return "lecturer"

    # Tìm nhóm đã được gán cho đề tài này
    assigned_group = db.query(Group).filter(Group.thesis_id == thesis_id).first()

    # Nếu tìm thấy một nhóm
    if assigned_group:
        # Kiểm tra xem người dùng có phải là thành viên của nhóm đó không
        is_student_in_group = db.query(GroupMember).filter(
            GroupMember.group_id == assigned_group.id,
            GroupMember.student_id == user_id
        ).first()
        if is_student_in_group:
            return "student"

    return None

# --- Service Functions ---

# CREATE operations
def create_mission(db: Session, mission_data: MissionCreate, thesis_id: UUID, user_id: UUID):
    """Tạo một Mission mới (Lưu ý: quy trình mới không khuyến khích dùng hàm này)."""
    role = _get_user_thesis_role(db, thesis_id, user_id)
    if role != "lecturer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ giảng viên hướng dẫn mới có quyền tạo nhiệm vụ.")
    
    new_mission = Mission(**mission_data.dict(), thesis_id=thesis_id)
    db.add(new_mission)
    db.commit()
    db.refresh(new_mission)
    return new_mission

def create_task_for_thesis(db: Session, task_data: TaskCreate, thesis_id: UUID, user_id: UUID):
    """Tạo Task mới cho một Thesis. Tự động tìm Mission duy nhất của Thesis đó."""
    
    role = _get_user_thesis_role(db, thesis_id, user_id)
    
    # === SỬA ĐIỀU KIỆN KIỂM TRA TẠI ĐÂY ===
    if role not in ["lecturer", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ giảng viên hướng dẫn hoặc admin mới có quyền tạo công việc.")
    # =====================================

    mission = db.query(Mission).filter(Mission.thesis_id == thesis_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Không tìm thấy Mission cho đề tài này. Đề tài có thể chưa được nhóm nào đăng ký.")

    new_task = Task(**task_data.dict(), mission_id=mission.id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

def create_task(db: Session, task_data: TaskCreate, mission_id: UUID, user_id: UUID):
    """Tạo Task mới cho một Mission cụ thể (Lưu ý: quy trình mới không khuyến khích dùng hàm này)."""
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

def create_task_comment(db: Session, comment_data: TaskCommentCreate, task_id: UUID, user_id: UUID):
    """Tạo một bình luận mới cho một Task."""
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

# READ operations
def get_tasks_for_thesis(db: Session, thesis_id: UUID, user_id: UUID):
    """Lấy danh sách tất cả Task của một Thesis, có kiểm tra quyền."""
    
    # 1. Kiểm tra quyền truy cập của người dùng đối với đề tài này
    role = _get_user_thesis_role(db, thesis_id, user_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền xem các công việc của đề tài này.")

    # 2. Tìm nhiệm vụ (mission) duy nhất của đề tài
    mission = db.query(Mission).filter(Mission.thesis_id == thesis_id).first()
    
    # Nếu không có mission (ví dụ: đề tài chưa được nhóm đăng ký), trả về danh sách rỗng
    if not mission:
        return []

    # 3. Lấy tất cả các task thuộc về mission đó, sắp xếp theo độ ưu tiên và ngày tạo
    tasks = db.query(Task).filter(Task.mission_id == mission.id).order_by(Task.priority.desc(), Task.create_datetime.asc()).all()
    
    return tasks

def get_missions_for_thesis(db: Session, thesis_id: UUID, user_id: UUID):
    """Lấy danh sách các Mission của một đề tài."""
    if not _get_user_thesis_role(db, thesis_id, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền xem tiến độ của đề tài này.")
    
    missions = db.query(Mission).filter(Mission.thesis_id == thesis_id).all()
    return missions

def get_task_by_id(db: Session, task_id: UUID, user_id: UUID):
    """Lấy thông tin chi tiết của một Task."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc.")

    mission = db.query(Mission).filter(Mission.id == task.mission_id).first()
    if not mission:
        raise HTTPException(status_code=500, detail="Lỗi nội bộ: Không tìm thấy nhiệm vụ của công việc này.")

    if not _get_user_thesis_role(db, mission.thesis_id, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền xem công việc này.")

    return task

# UPDATE operations
def update_task_status(db: Session, task_id: UUID, status_data: TaskUpdateStatus, user_id: UUID):
    """Cập nhật trạng thái của một Task (phiên bản không dùng JOIN)."""
    
    # === PHẦN SỬA LỖI ===

    # 1. Lấy thông tin Task trước tiên
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc.")

    # 2. Dùng task.mission_id để lấy thông tin Mission
    mission = db.query(Mission).filter(Mission.id == task.mission_id).first()
    if not mission:
        # Lỗi này cho thấy dữ liệu không nhất quán (task tồn tại nhưng mission thì không)
        raise HTTPException(status_code=500, detail="Lỗi dữ liệu: Không tìm thấy nhiệm vụ của công việc này.")
    # 3. Dùng mission.thesis_id để kiểm tra quyền như cũ
    # role = _get_user_thesis_role(db, mission.thesis_id, user_id)
    # if role != "student":
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ sinh viên trong nhóm mới có quyền cập nhật trạng thái.")
    # ====================
    # Cập nhật trạng thái và lưu lại
    task.status = status_data.status
    db.commit()
    db.refresh(task)
    return task

def update_task(db: Session, task_id: UUID, task_data: TaskUpdate, user_id: UUID):
    """Cập nhật thông tin chi tiết của một Task."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc.")

    # Kiểm tra quyền (chỉ giảng viên hoặc admin)
    mission = db.query(Mission).filter(Mission.id == task.mission_id).first()
    if not mission:
        raise HTTPException(status_code=500, detail="Lỗi dữ liệu: Không tìm thấy nhiệm vụ của công việc này.")
    
    role = _get_user_thesis_role(db, mission.thesis_id, user_id)
    if role not in ["lecturer", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền sửa công việc này.")

    # Cập nhật các trường được gửi lên
    update_data = task_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    db.commit()
    db.refresh(task)
    return task

def delete_task(db: Session, task_id: UUID, user_id: UUID):
    """Xóa một Task và các comment liên quan."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc.")

    # Kiểm tra quyền (chỉ giảng viên hoặc admin)
    mission = db.query(Mission).filter(Mission.id == task.mission_id).first()
    if not mission:
        raise HTTPException(status_code=500, detail="Lỗi dữ liệu: Không tìm thấy nhiệm vụ của công việc này.")

    role = _get_user_thesis_role(db, mission.thesis_id, user_id)
    if role not in ["lecturer", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền xóa công việc này.")

    # Xóa các comment liên quan trước
    db.query(TaskComment).filter(TaskComment.task_id == task_id).delete(synchronize_session=False)

    # Xóa task
    db.delete(task)
    db.commit()

    return {"message": "Đã xóa công việc thành công."}