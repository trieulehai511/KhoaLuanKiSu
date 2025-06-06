from datetime import datetime
import uuid
from fastapi import HTTPException,status
from sqlalchemy import UUID
from sqlalchemy.orm import Session
from models.model import AcademyYear, Batch, Department, Information, LecturerInfo, Major, Semester, Thesis, ThesisLecturer, User
from schemas.thesis import ThesisCreate, ThesisResponse, ThesisUpdate

def create(db: Session, thesis: ThesisCreate, lecturer_id: uuid.UUID):
    creator = db.query(User).filter(User.id == lecturer_id, User.user_type == 3).first()
    if not creator:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Người tạo không phải giảng viên")
    valid_lecturers = db.query(User).filter(User.id.in_(thesis.lecturer_ids), User.user_type == 3).all()
    if len(valid_lecturers) != len(thesis.lecturer_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Một hoặc nhiều giảng viên không hợp lệ hoặc không tồn tại"
        )
    db_thesis = Thesis(
        title=thesis.title,
        description=thesis.description,
        thesis_type=thesis.thesis_type,
        start_date=thesis.start_date,
        end_date=thesis.end_date,
        status=thesis.status,
        create_by=lecturer_id,
        create_datetime=datetime.utcnow(),
        batch_id=thesis.batch_id,
        major_id=thesis.major_id
    )
    db.add(db_thesis)
    db.commit()
    db.refresh(db_thesis)
    for l_id in thesis.lecturer_ids:
        db.add(ThesisLecturer(
            lecturer_id=l_id,
            thesis_id=db_thesis.id,
            role=1 
        ))

    db.commit()
    return get_thesis_by_id(db, db_thesis.id)

def update_thesis(db: Session, thesis_id: UUID, thesis: ThesisUpdate, user_id: UUID):
    db_thesis = db.query(Thesis).filter(Thesis.id == thesis_id).first()
    if not db_thesis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thesis not found"
        )
    if db_thesis.create_by != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: You can only update your own thesis"
        )
    update_data = thesis.dict(exclude_unset=True)
    if "batch_id" in update_data:
        batch = db.query(Batch).filter(Batch.id == update_data["batch_id"]).first()
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid batch ID"
            )

    # ✅ Nếu có lecturer_ids, kiểm tra và cập nhật
    if "lecturer_ids" in update_data:
        lecturer_ids = update_data.pop("lecturer_ids")
        # Kiểm tra tính hợp lệ
        valid_lecturers = db.query(User).filter(User.id.in_(lecturer_ids), User.user_type == 3).all()
        if len(valid_lecturers) != len(lecturer_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Một hoặc nhiều giảng viên không hợp lệ hoặc không tồn tại"
            )

        # Xoá toàn bộ giảng viên cũ
        db.query(ThesisLecturer).filter(ThesisLecturer.thesis_id == thesis_id).delete()

        # Thêm giảng viên mới
        for l_id in lecturer_ids:
            db.add(ThesisLecturer(
                lecturer_id=l_id,
                thesis_id=thesis_id,
                role=1  # Mặc định
            ))

    # Cập nhật các trường còn lại
    for key, value in update_data.items():
        setattr(db_thesis, key, value)

    db_thesis.update_datetime = datetime.utcnow()
    db.commit()
    db.refresh(db_thesis)
    return get_thesis_by_id(db, db_thesis.id)

def get_thesis_by_id(db: Session, thesis_id: UUID) -> ThesisResponse:
    thesis = db.query(Thesis).filter(Thesis.id == thesis_id).first()
    if not thesis:
        raise HTTPException(status_code=404, detail="Thesis not found")

    thesis_lecturers = db.query(ThesisLecturer).filter(ThesisLecturer.thesis_id == thesis.id).all()
    instructors = []
    for tl in thesis_lecturers:
        lecturer_info = db.query(LecturerInfo).filter(LecturerInfo.user_id == tl.lecturer_id).first()
        if lecturer_info:
            user_info = db.query(Information).filter(Information.user_id == lecturer_info.user_id).first()
            department_name = None
            if lecturer_info.department is not None:
                dept = db.query(Department).filter(Department.id == lecturer_info.department).first()
                department_name = dept.name if dept else None

            if user_info:
                instructors.append({
                    "name": f"{user_info.first_name} {user_info.last_name}",
                    "email": lecturer_info.email,
                    "department": lecturer_info.department,
                    "lecturer_code": lecturer_info.lecturer_code,
                    "department_name": department_name
                })

    batch = db.query(Batch).filter(Batch.id == thesis.batch_id).first()
    semester = db.query(Semester).filter(Semester.id == batch.semester_id).first() if batch else None
    academy_year = db.query(AcademyYear).filter(AcademyYear.id == semester.academy_year_id).first() if semester else None
    major = db.query(Major).filter(Major.id == thesis.major_id).first()
    major_name = major.name if major else "Chuyên ngành không xác định"

    return ThesisResponse(
        id=thesis.id,
        thesis_type=thesis.thesis_type,
        status=(
            "Từ chối" if thesis.status == 0 else
            "Chưa được đăng ký" if thesis.status == 1 else
            "Đã đăng ký" if thesis.status == 2 else
            "Chờ duyệt" if thesis.status == 3 else
            "Đã hoàn thành" if thesis.status == 4 else
            "Hủy đăng ký" if thesis.status == 5 else
            "Không xác định"
        ),
        name=thesis.title,
        description=thesis.description,
        start_date=thesis.start_date,
        end_date=thesis.end_date,
        reason=thesis.reason,
        instructors=instructors,
        name_thesis_type="Khóa luận" if thesis.thesis_type ==1 else "Đồ án",
        batch={
            "id": batch.id,
            "name": batch.name,
            "start_date": batch.start_date,
            "end_date": batch.end_date,
            "semester": {
                "id": semester.id,
                "name": semester.name,
                "start_date": semester.start_date,
                "end_date": semester.end_date,
                "academy_year": {
                    "id": academy_year.id,
                    "name": academy_year.name,
                    "start_date": academy_year.start_date,
                    "end_date": academy_year.end_date
                } if academy_year else None
            } if semester else None
        } if batch else None,
        major=major_name
    )

def get_all_theses(db: Session) -> list[ThesisResponse]:
    theses = db.query(Thesis).order_by(Thesis.create_datetime.desc()).all()
    thesis_responses = []
    for thesis in theses:
        thesis_lecturers = db.query(ThesisLecturer).filter(ThesisLecturer.thesis_id == thesis.id).all()
        instructors = []
        for tl in thesis_lecturers:
            lecturer_info = db.query(LecturerInfo).filter(LecturerInfo.user_id == tl.lecturer_id).first()
            if lecturer_info:
                user_info = db.query(Information).filter(Information.user_id == lecturer_info.user_id).first()
                department_name = None
                if lecturer_info.department is not None:
                    dept = db.query(Department).filter(Department.id == lecturer_info.department).first()
                    department_name = dept.name if dept else None

                if user_info:
                    instructors.append({
                        "name": f"{user_info.first_name} {user_info.last_name}",
                        "email": lecturer_info.email,
                        "lecturer_code": lecturer_info.lecturer_code,
                        "department": lecturer_info.department,
                        "department_name": department_name
                    })

        batch = db.query(Batch).filter(Batch.id == thesis.batch_id).first()
        semester = db.query(Semester).filter(Semester.id == batch.semester_id).first() if batch else None
        academy_year = db.query(AcademyYear).filter(AcademyYear.id == semester.academy_year_id).first() if semester else None
        major = db.query(Major).filter(Major.id == thesis.major_id).first()
        major_name = major.name if major else "Chuyên ngành không xác định"

        thesis_responses.append(ThesisResponse(
            id=thesis.id,
            thesis_type=thesis.thesis_type,
            status=(
                "Từ chối" if thesis.status == 0 else
                "Chưa được đăng ký" if thesis.status == 1 else
                "Đã đăng ký" if thesis.status == 2 else
                "Chờ duyệt" if thesis.status == 3 else
                "Đã hoàn thành" if thesis.status == 4 else
                "Hủy đăng ký" if thesis.status == 5 else
                "Không xác định"
            ),
            reason=thesis.reason,
            name=thesis.title,
            description=thesis.description,
            start_date=thesis.start_date,
            end_date=thesis.end_date,
            instructors=instructors,
            name_thesis_type="Khóa luận" if thesis.thesis_type == 1 else "Đồ án",
            batch={
                "id": batch.id,
                "name": batch.name,
                "start_date": batch.start_date,
                "end_date": batch.end_date,
                "semester": {
                    "id": semester.id,
                    "name": semester.name,
                    "start_date": semester.start_date,
                    "end_date": semester.end_date,
                    "academy_year": {
                        "id": academy_year.id,
                        "name": academy_year.name,
                        "start_date": academy_year.start_date,
                        "end_date": academy_year.end_date
                    } if academy_year else None
                } if semester else None
            } if batch else None,
            major=major_name
        ))

    return thesis_responses


def delete_thesis(db: Session, thesis_id: UUID):
    """
    Xóa một luận văn (thesis).
    """
    db_thesis = db.query(Thesis).filter(Thesis.id == thesis_id).first()
    if not db_thesis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thesis not found"
        )
    db.delete(db_thesis)
    db.commit()
    return {"message": "Thesis deleted successfully"}

def get_all_majors(db: Session):
    return db.query(Major).all()

def get_all_departments(db: Session):
    return db.query(Department).all()