from typing import List, Optional
import uuid
import bcrypt
from sqlalchemy import UUID
from sqlalchemy.orm import Session
from models.model import Department, Information, LecturerInfo, Major, StudentInfo, User
from schemas.information import InformationResponse
from schemas.lecturer_info import LecturerInfoResponse
from schemas.student_info import StudentInfoResponse
from schemas.sysuser import UserCreate, UserFullProfile, UserResponse

def create_user(db: Session, user: UserCreate):
    if user.user_type == 2:
        user.password = user.user_name
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
                "is_active": user.is_active
            })

    return result


def get_all_users(db: Session) -> List[UserResponse]:
    """
    Lấy danh sách tất cả người dùng từ bảng sys_user.
    """
    users = db.query(User).order_by(User.create_datetime.desc()).all()
    user_type_map = {
        1: "ADMIN",
        2: "Sinh viên",
        3: "Giảng viên",
        4: "Hội đồng"
    }

    response = []
    for user in users:
        user_type_name = user_type_map.get(user.user_type, "Không rõ")
        response.append(
            UserResponse(
                id=user.id,
                user_name=user.user_name,
                is_active=user.is_active,
                user_type=user.user_type,
                user_type_name=user_type_name
            )
        )
    return response

def get_user_full_profile_by_id(db: Session, user_id: UUID) -> Optional[UserFullProfile]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    info = db.query(Information).filter(Information.user_id == user_id).first()
    if not info:
        return None

    # gender_map = {
    #     0: "Bê đê",
    #     1: "Nam",
    #     2: "Nữ"
    # }
    # gender_str = gender_map.get(info.gender, "Không rõ")

    info_response = InformationResponse(
        id=info.id,
        user_id=info.user_id,
        first_name=info.first_name,
        last_name=info.last_name,
        date_of_birth=info.date_of_birth,
        gender=info.gender,
        address=info.address,
        tel_phone=info.tel_phone
    )

    student_info = None
    lecturer_info = None

    if user.user_type == 2:  # Student
        student = db.query(StudentInfo).filter(StudentInfo.user_id == user_id).first()
        major = db.query(Major).filter(Major.id == student.major_id).first() if student else None
        student_info = StudentInfoResponse(
            id=student.id,
            user_id=student.user_id,
            student_code=student.student_code,
            class_name=student.class_name,
            major_id=student.major_id,
            major_name=major.name if major else "Không rõ",
            create_datetime=student.create_datetime,
            update_datetime=student.update_datetime
        )

    elif user.user_type == 3:  # Lecturer
        lecturer = db.query(LecturerInfo).filter(LecturerInfo.user_id == user_id).first()
        department = db.query(Department).filter(Department.id == lecturer.department).first() if lecturer else None
        lecturer_info = LecturerInfoResponse(
            id=lecturer.id,
            user_id=lecturer.user_id,
            lecturer_code=lecturer.lecturer_code,
            department=lecturer.department,
            department_name=department.name if department else "Không rõ",
            title=lecturer.title,
            email=lecturer.email,
            create_datetime=lecturer.create_datetime,
            update_datetime=lecturer.update_datetime
        )

    return UserFullProfile(
        user_id=user.id,
        user_name=user.user_name,
        user_type=user.user_type,
        user_type_name={
            1: "Admin", 2: "Sinh viên", 3: "Giảng viên", 4: "Hội đồng"
        }.get(user.user_type, "Không rõ"),
        information=info_response,
        student_info=student_info,
        lecturer_info=lecturer_info
    )
