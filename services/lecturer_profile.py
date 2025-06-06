from models.model import Information, LecturerInfo, Department
from schemas.information import InformationResponse
from schemas.lecturer_info import LecturerInfoResponse
from schemas.lecturer_profile import LecturerFullProfile, LecturerCreateProfile, LecturerUpdateProfile
from sqlalchemy.orm import Session
from uuid import uuid4


def create_lecturer_profile(db: Session, profile_data: LecturerCreateProfile, user_id):
    info = Information(
        id=uuid4(),
        user_id=user_id,
        **profile_data.information.dict()
    )
    db.add(info)

    lecturer = LecturerInfo(
        id=uuid4(),
        user_id=user_id,
        **profile_data.lecturer_info.dict()
    )
    db.add(lecturer)

    db.commit()
    db.refresh(info)
    db.refresh(lecturer)

    department = db.query(Department).filter(Department.id == lecturer.department).first()
    dept_name = department.name if department else "Không rõ"

    return LecturerFullProfile(
        user_id=user_id,
        information=InformationResponse.from_orm(info),
        lecturer_info=LecturerInfoResponse(
            **lecturer.__dict__,
            department_name=dept_name
        )
    )


def update_lecturer_profile(db: Session, profile_data: LecturerUpdateProfile, user_id):
    info = db.query(Information).filter(Information.user_id == user_id).first()
    lecturer = db.query(LecturerInfo).filter(LecturerInfo.user_id == user_id).first()
    if not info or not lecturer:
        return None

    for key, value in profile_data.information.dict(exclude_unset=True).items():
        setattr(info, key, value)

    for key, value in profile_data.lecturer_info.dict(exclude_unset=True).items():
        setattr(lecturer, key, value)

    db.commit()
    db.refresh(info)
    db.refresh(lecturer)

    department = db.query(Department).filter(Department.id == lecturer.department).first()
    dept_name = department.name if department else "Không rõ"

    return LecturerFullProfile(
        user_id=user_id,
        information=InformationResponse.from_orm(info),
        lecturer_info=LecturerInfoResponse(
            **lecturer.__dict__,
            department_name=dept_name
        )
    )


def get_lecturer_profile_by_user_id(db: Session, user_id):
    info = db.query(Information).filter(Information.user_id == user_id).first()
    lecturer = db.query(LecturerInfo).filter(LecturerInfo.user_id == user_id).first()
    if not info or not lecturer:
        return None

    # Lấy tên khoa
    department = db.query(Department).filter(Department.id == lecturer.department).first()
    department_name = department.name if department else "Không rõ"

    # Mapping giới tính
    gender_map = {
        0: "Bê đê",
        1: "Nam",
        2: "Nữ"
    }
    gender_int = int(info.gender) if info.gender is not None else -1
    gender_str = gender_map.get(gender_int, "Không rõ")

    # Gán thông tin cá nhân
    info_response = InformationResponse(
        id=info.id,
        user_id=info.user_id,
        first_name=info.first_name,
        last_name=info.last_name,
        date_of_birth=info.date_of_birth,
        gender=gender_int,
        address=info.address,
        tel_phone=info.tel_phone
    )

    # Gán thông tin giảng viên
    lecturer_response = LecturerInfoResponse(
        id=lecturer.id,
        user_id=lecturer.user_id,
        lecturer_code=lecturer.lecturer_code,
        department=lecturer.department,
        department_name=department_name,
        title=lecturer.title,
        email=lecturer.email,
        create_datetime=lecturer.create_datetime,
        update_datetime=lecturer.update_datetime
    )

    return LecturerFullProfile(
        user_id=user_id,
        information=info_response,
        lecturer_info=lecturer_response
    )

