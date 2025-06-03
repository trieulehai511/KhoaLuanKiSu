from typing import List
import uuid
import bcrypt
from sqlalchemy.orm import Session
from models.model import Department, Information, LecturerInfo, User
from schemas.sysuser import UserCreate, UserResponse

def create_user(db: Session, user: UserCreate):
    # Kiểm tra và gán mật khẩu mặc định nếu không phải là giảng viên
    if user.user_type == 2:
        user.password = user.user_name

    # Mã hóa mật khẩu
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    db_user = User(
        id=uuid.uuid4(),
        user_name=user.user_name,
        password=hashed_password,
        is_active=user.is_active if user.is_active is not None else True,
        user_type=user.user_type
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_all_lecturers(db: Session):
    users = db.query(User).filter(User.user_type == 3).all()
    result = []

    for user in users:
        info = db.query(Information).filter(Information.user_id == user.id).first()
        lecturer_info = db.query(LecturerInfo).filter(LecturerInfo.user_id == user.id).first()

        department_name = None
        if lecturer_info and lecturer_info.department is not None:
            dept = db.query(Department).filter(Department.id == lecturer_info.department).first()
            department_name = dept.name if dept else None

        if info and lecturer_info:
            result.append({
                "id": user.id,
                "user_name": user.user_name,
                "first_name": info.first_name,
                "last_name": info.last_name,
                "email": lecturer_info.email,
                "department": lecturer_info.department,
                "department_name": department_name,
                "title": lecturer_info.title,
                "phone": lecturer_info.phone,
                "is_active": user.is_active
            })

    return result


def get_all_users(db: Session) -> List[UserResponse]:
    """
    Lấy danh sách tất cả người dùng từ bảng sys_user.
    """
    users = db.query(User).all()
    return [UserResponse.from_orm(user) for user in users]

