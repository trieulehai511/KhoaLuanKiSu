from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.model import Information, Major, StudentInfo, User
from schemas.student_profile import StudentCreateProfile, StudentUpdateProfile, StudentFullProfile
from schemas.information import InformationResponse
from schemas.student_info import StudentInfoResponse
from uuid import UUID, uuid4

def create_student_profile(db: Session, profile_data: StudentCreateProfile, user_id):
    # Lấy thông tin user để có user_name
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Trường hợp này khó xảy ra vì user_id lấy từ token, nhưng vẫn nên kiểm tra
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")
    # Tạo thông tin cá nhân
    info = Information(
        id=uuid4(),
        user_id=user_id,
        **profile_data.information.dict()
    )
    db.add(info)

    # Tạo thông tin sinh viên
    student = StudentInfo(
        id=uuid4(),
        user_id=user_id,
        **profile_data.student_info.dict()
    )
    db.add(student)

    db.commit()
    db.refresh(info)
    db.refresh(student)

    # Truy vấn tên chuyên ngành
    major = db.query(Major).filter(Major.id == student.major_id).first()
    major_name = major.name if major else "Không rõ"

    return StudentFullProfile(
        user_id=user_id,
        user_name=user.user_name, # <-- THÊM DÒNG NÀY
        information=InformationResponse.from_orm(info),
        student_info=StudentInfoResponse(
            id=student.id,
            user_id=student.user_id,
            student_code=student.student_code,
            class_name=student.class_name,
            major_id=student.major_id,
            major_name=major_name,
            create_datetime=student.create_datetime,
            update_datetime=student.update_datetime
        )
    )



def update_student_profile(db: Session, profile_data: StudentUpdateProfile, user_id):
    # Tìm và cập nhật thông tin cá nhân
    info = db.query(Information).filter(Information.user_id == user_id).first()
    student = db.query(StudentInfo).filter(StudentInfo.user_id == user_id).first()

    if not info or not student:
        return None

    for key, value in profile_data.information.dict(exclude_unset=True).items():
        setattr(info, key, value)

    for key, value in profile_data.student_info.dict(exclude_unset=True).items():
        setattr(student, key, value)

    db.commit()
    db.refresh(info)
    db.refresh(student)

    # Lấy tên chuyên ngành
    major = db.query(Major).filter(Major.id == student.major_id).first()
    major_name = major.name if major else "Không rõ"

    # Map giới tính
    gender_map = {
        0: "Bê đê",
        1: "Nam",
        2: "Nữ"
    }
    gender_int = int(info.gender) if info.gender is not None else -1
    gender_str = gender_map.get(gender_int, "Không rõ")

    # Trả về dữ liệu đầy đủ
    return StudentFullProfile(
        user_id=user_id,
        information=InformationResponse(
            id=info.id,
            user_id=info.user_id,
            first_name=info.first_name,
            last_name=info.last_name,
            date_of_birth=info.date_of_birth,
            gender=gender_int,
            address=info.address,
            tel_phone=info.tel_phone
        ),
        student_info=StudentInfoResponse(
            id=student.id,
            user_id=student.user_id,
            student_code=student.student_code,
            class_name=student.class_name,
            major_id=student.major_id,
            major_name=major_name,
            create_datetime=student.create_datetime,
            update_datetime=student.update_datetime
        )
    )


def get_student_profile_by_user_id(db: Session, user_id):
    # Lấy thông tin từ cả 3 bảng: User, Information, StudentInfo
    user = db.query(User).filter(User.id == user_id).first()
    info = db.query(Information).filter(Information.user_id == user_id).first()
    student = db.query(StudentInfo).filter(StudentInfo.user_id == user_id).first()

    # Nếu thiếu bất kỳ thông tin nào, trả về None
    if not user or not info or not student:
        return None
        
    major = db.query(Major).filter(Major.id == student.major_id).first()
    major_name = major.name if major else "Không rõ"
    
    gender_map = {
        0: "Bê đê",
        1: "Nam",
        2: "Nữ"
    }
    gender_int = int(info.gender)
    
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
    
    student_response = StudentInfoResponse(
        id=student.id,
        user_id=student.user_id,
        student_code=student.student_code,
        class_name=student.class_name,
        major_id=student.major_id,
        major_name=major_name,
        create_datetime=student.create_datetime,
        update_datetime=student.update_datetime
    )

    # Thêm user_name vào đối tượng trả về
    return StudentFullProfile(
        user_id=user_id,
        user_name=user.user_name, # <-- THÊM DÒNG NÀY
        information=info_response,
        student_info=student_response
    )


def get_all_student_profiles(db: Session, major_id: Optional[UUID] = None, current_user_id: Optional[UUID] = None) -> list[StudentFullProfile]:
    query = db.query(StudentInfo)
    
    # Lọc theo chuyên ngành (nếu có)
    if major_id:
        query = query.filter(StudentInfo.major_id == major_id)

    # THÊM BƯỚC LỌC MỚI: Loại trừ user đang đăng nhập
    if current_user_id:
        query = query.filter(StudentInfo.user_id != current_user_id)
        
    students = query.all()
    results = []
    
    for student in students:
        # Lấy thông tin từ các bảng liên quan
        user = db.query(User).filter(User.id == student.user_id).first()
        info = db.query(Information).filter(Information.user_id == student.user_id).first()

        # Nếu không tồn tại user hoặc thông tin cá nhân, bỏ qua sinh viên này
        if not user or not info:
            continue
            
        major = db.query(Major).filter(Major.id == student.major_id).first()
        major_name = major.name if major else "Không rõ"
        
        gender_int = int(info.gender)
        
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

        student_response = StudentInfoResponse(
            id=student.id,
            user_id=student.user_id,
            student_code=student.student_code,
            class_name=student.class_name,
            major_id=student.major_id,
            major_name=major_name,
            create_datetime=student.create_datetime,
            update_datetime=student.update_datetime
        )

        results.append(StudentFullProfile(
            user_id=student.user_id,
            user_name=user.user_name,
            information=info_response,
            student_info=student_response
        ))

    return results
