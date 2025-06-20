from datetime import datetime
from io import BytesIO
import logging
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Dict, List
from db.database import get_db
import pandas as pd
from models.model import AcademyYear, Batch, Department, Information, LecturerInfo, Major, Semester, Thesis, ThesisLecturer, User
from schemas.thesis import BatchResponse, BatchSimpleResponse, DepartmentResponse, InstructorResponse, MajorResponse, ThesisBatchUpdateRequest, ThesisBatchUpdateResponse, ThesisCreate, ThesisUpdate, ThesisResponse
from services.thesis import (
    batch_update_theses,
    create,
    get_all_batches_with_details,
    get_all_departments,
    get_all_majors,
    get_theses_by_batch_id,
    update_thesis,
    get_thesis_by_id,
    get_all_theses,
    delete_thesis
)
from pathlib import Path
from routers.auth import get_current_user
from uuid import UUID
from fastapi.responses import FileResponse
router = APIRouter(
    prefix="/theses",
    tags=["theses"]
)

@router.get("/download-template", summary="Tải file Excel mẫu")
def download_template():
    file_path = Path("static/thesis_template.xlsx")

    if not file_path.exists():
        data = {
            "STT": [],
            "TÊN ĐỀ TÀI": [],
            "NỘI DUNG YÊU CẦU": [],
            "LOẠI ĐỀ TÀI": [],
            "CHUYÊN NGÀNH": [], # <-- THÊM CỘT MỚI
            "MÃ GV HƯỚNG DẪN": [],
            "MÃ GV PHẢN BIỆN": [],
            "BỘ MÔN": [],
            "GHI CHÚ": []
        }
        df = pd.DataFrame(data)
        # Thêm một dòng ví dụ
        example_row = pd.DataFrame([{
            "STT": 1,
            "TÊN ĐỀ TÀI": "Hệ thống quản lý thư viện",
            "NỘI DUNG YÊU CẦU": "Xây dựng các chức năng chính...",
            "LOẠI ĐỀ TÀI": 2,
            "CHUYÊN NGÀNH": "Công nghệ thông tin", # Ví dụ
            "MÃ GV HƯỚNG DẪN": "GV01",
            "MÃ GV PHẢN BIỆN": "GV02",
            "BỘ MÔN": "KTPM",
            "GHI CHÚ": ""
        }])
        df = pd.concat([df, example_row], ignore_index=True)
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(file_path, index=False)

    return FileResponse(
        path=file_path,
        filename="thesis_template.xlsx",
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# Thiết lập logging
# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Định nghĩa mô hình Pydantic cho phản hồi
class ErrorItem(BaseModel):
    row: int
    title: str
    error: str

class ImportResponse(BaseModel):
    success: int
    errors: List[ErrorItem]
    imported_theses: List[ThesisResponse] = []  # Thêm trường cho danh sách đề tài vừa import

@router.post("/import-excel", response_model=ImportResponse)
def import_thesis_from_simple_excel(
    file: UploadFile = File(...),
    status: int = 1,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Import danh sách đề tài từ file Excel và trả về danh sách đề tài vừa import.
    """
    try:
        # 1. Tìm đợt mới nhất
        latest_batch = db.query(Batch).order_by(Batch.create_datetime.desc()).first()
        if not latest_batch:
            raise HTTPException(status_code=404, detail="Không tìm thấy đợt học nào trong hệ thống.")

        # 2. Đọc file Excel
        content = file.file.read()
        df = pd.read_excel(BytesIO(content), header=4)  # Header ở dòng 5 (0-based index)

        # Chuẩn hóa tên cột để khớp với file có dấu *
        df.columns = [col.strip() for col in df.columns]  # Loại bỏ khoảng trắng thừa
        column_mapping = {
            "STT": "STT",
            "TÊN ĐỀ TÀI *": "TÊN ĐỀ TÀI",
            "NỘI DUNG YÊU CẦU *": "NỘI DUNG YÊU CẦU",
            "MÃ GV HƯỚNG DẪN *": "MÃ GV HƯỚNG DẪN",
            "LOẠI ĐỀ TÀI *\n1: Khóa luận kỹ sư\n2: Đồ án tốt nghiệp": "LOẠI ĐỀ TÀI",
            "MÃ GV PHẢN BIỆN\n(Nếu loại đề tài là 2 thì có thể nhập MÃ GV PHẢN BIỆN hoặc không)": "MÃ GV PHẢN BIỆN",
            "BỘ MÔN *\n1: KTPM\n2: HTTT\n3: KHDL&TTNT\n4: MMT-ATTT": "BỘ MÔN",
            "CHUYÊN NGÀNH *\n(Chọn chuyên ngành bằng dropdown)": "CHUYÊN NGÀNH",
            "GHI CHÚ": "GHI CHÚ"
        }
        df = df.rename(columns=column_mapping)

        # Log DataFrame để kiểm tra
        logger.info(f"Đọc được {len(df)} dòng từ file Excel")
        logger.info(f"Các cột trong DataFrame: {df.columns.tolist()}")
        logger.info(f"Dữ liệu DataFrame:\n{df.to_dict(orient='records')}")
        logger.info(f"Giá trị NaN:\n{df.isna()}")

        created_count = 0
        errors = []
        newly_created_thesis_ids = []  # Lưu ID của các đề tài vừa tạo

        for i, row in df.iterrows():
            logger.info(f"Xử lý dòng {i + 6}: {row.to_dict()}")
            try:
                # 3. Bỏ qua dòng trống
                if pd.isna(row.get("STT")) or pd.isna(row.get("TÊN ĐỀ TÀI")):
                    logger.warning(f"Bỏ qua dòng {i + 6}: Thiếu STT hoặc TÊN ĐỀ TÀI. Giá trị: STT={row.get('STT')}, TÊN ĐỀ TÀI={row.get('TÊN ĐỀ TÀI')}")
                    errors.append({
                        "row": i + 6,
                        "title": row.get("TÊN ĐỀ TÀI", "<trống>"),
                        "error": "Thiếu STT hoặc TÊN ĐỀ TÀI"
                    })
                    continue

                # 4. Xử lý Chuyên ngành
                major_name_from_excel = row.get("CHUYÊN NGÀNH")
                if pd.isna(major_name_from_excel):
                    raise Exception("Cột 'CHUYÊN NGÀNH' không được để trống.")
                major_name_to_find = str(major_name_from_excel).strip().lower()
                major = db.query(Major).filter(func.lower(Major.name) == major_name_to_find).first()
                if not major:
                    raise Exception(f"Chuyên ngành '{major_name_from_excel}' không tồn tại trong cơ sở dữ liệu.")
                major_id_val = major.id

                # 5. Xử lý Giảng viên Hướng dẫn
                instructor_codes = [code.strip() for code in str(row.get("MÃ GV HƯỚNG DẪN", "")).split(',') if code.strip()]
                instructors = []
                if instructor_codes:
                    instructors = db.query(LecturerInfo).filter(LecturerInfo.lecturer_code.in_(instructor_codes)).all()
                    if len(instructors) != len(instructor_codes):
                        raise Exception(f"Một hoặc nhiều Mã GV Hướng Dẫn không tồn tại: {instructor_codes}")

                # 6. Xử lý Giảng viên Phản biện (chỉ kiểm tra nếu LOẠI ĐỀ TÀI là 2)
                reviewers = []  # Khởi tạo trước để tránh lỗi
                reviewer_codes = []
                if pd.notna(row.get("MÃ GV PHẢN BIỆN")):
                    reviewer_codes = [code.strip() for code in str(row.get("MÃ GV PHẢN BIỆN", "")).split(',') if code.strip()]
                if row.get("LOẠI ĐỀ TÀI") == 2 and reviewer_codes:
                    reviewers = db.query(LecturerInfo).filter(LecturerInfo.lecturer_code.in_(reviewer_codes)).all()
                    if len(reviewers) != len(reviewer_codes):
                        raise Exception(f"Một hoặc nhiều Mã GV Phản Biện không tồn tại: {reviewer_codes}")

                # 7. Xử lý Bộ môn
                department_id = None
                dept_input = row.get("BỘ MÔN")
                if pd.notna(dept_input):
                    dept_input_str = str(dept_input).strip()
                    try:
                        # Thử xử lý như ID
                        dept_id = int(dept_input)
                        department = db.query(Department).filter(Department.id == dept_id).first()
                    except (ValueError, TypeError):
                        # Xử lý như tên
                        department = db.query(Department).filter(func.lower(Department.name) == dept_input_str.lower()).first()
                    if not department:
                        raise Exception(f"Bộ môn '{dept_input}' không tồn tại.")
                    department_id = department.id

                # 8. Xử lý Loại đề tài
                thesis_type_from_excel = row.get("LOẠI ĐỀ TÀI")
                if pd.isna(thesis_type_from_excel):
                    raise Exception("Cột 'LOẠI ĐỀ TÀI' không được để trống.")
                try:
                    thesis_type_val = int(thesis_type_from_excel)
                    if thesis_type_val not in [1, 2]:
                        raise Exception(f"Giá trị '{thesis_type_val}' không hợp lệ cho Loại đề tài (chỉ 1 hoặc 2).")
                except (ValueError, TypeError):
                    raise Exception(f"Giá trị '{thesis_type_from_excel}' không phải là số hợp lệ cho Loại đề tài.")

                # 9. Xử lý Ghi chú
                notes_text = row.get("GHI CHÚ")
                notes_text = str(notes_text).strip() if pd.notna(notes_text) else None

                # 10. Tạo đối tượng ThesisCreate
                thesis_data = ThesisCreate(
                    title=str(row["TÊN ĐỀ TÀI"]).strip(),
                    description=str(row.get("NỘI DUNG YÊU CẦU", "")).strip(),
                    notes=notes_text,
                    thesis_type=thesis_type_val,
                    status=status,
                    major_id=major_id_val,
                    department_id=department_id,
                    batch_id=latest_batch.id,
                    start_date=latest_batch.start_date,
                    end_date=latest_batch.end_date,
                    instructor_ids=[lec.user_id for lec in instructors],
                    reviewer_ids=[rev.user_id for rev in reviewers] if reviewers else []
                )

                # 11. Gọi hàm create và lưu ID
                try:
                    created_thesis = create(db, thesis_data, user.id)
                    created_count += 1
                    newly_created_thesis_ids.append(created_thesis.id)  # Lưu ID của đề tài vừa tạo
                    logger.info(f"Đã tạo thành công đề tài: {row['TÊN ĐỀ TÀI']}")
                except Exception as create_error:
                    raise Exception(f"Lỗi khi tạo đề tài: {str(create_error)}")

            except Exception as e:
                logger.error(f"Lỗi ở dòng {i + 6}: {str(e)}")
                errors.append({
                    "row": i + 6,
                    "title": row.get("TÊN ĐỀ TÀI", "<trống>"),
                    "error": str(e)
                })

        # 12. Chuẩn bị danh sách đề tài vừa import
        imported_theses = []
        for thesis_id in newly_created_thesis_ids:
            thesis = db.query(Thesis).filter(Thesis.id == thesis_id).first()
            if thesis:
                thesis_lecturers = db.query(ThesisLecturer).filter(ThesisLecturer.thesis_id == thesis.id).all()
                instructors_list = []
                reviewers_list = []

                for tl in thesis_lecturers:
                    lecturer_info = db.query(LecturerInfo).filter(LecturerInfo.user_id == tl.lecturer_id).first()
                    if lecturer_info:
                        user_info = db.query(Information).filter(Information.user_id == lecturer_info.user_id).first()
                        department = db.query(Department).filter(Department.id == lecturer_info.department).first()

                        if user_info:
                            lecturer_details = InstructorResponse(
                                name=f"{user_info.last_name} {user_info.first_name}",
                                email=lecturer_info.email,
                                lecturer_code=lecturer_info.lecturer_code,
                                department=lecturer_info.department,
                                department_name=department.name if department else None
                            )
                            if tl.role == 1:  # Giảng viên hướng dẫn
                                instructors_list.append(lecturer_details)
                            elif tl.role == 2:  # Giảng viên phản biện
                                reviewers_list.append(lecturer_details)

                batch = db.query(Batch).filter(Batch.id == thesis.batch_id).first()
                semester = db.query(Semester).filter(Semester.id == batch.semester_id).first() if batch else None
                academy_year = db.query(AcademyYear).filter(AcademyYear.id == semester.academy_year_id).first() if semester else None
                major = db.query(Major).filter(Major.id == thesis.major_id).first()
                major_name = major.name if major else "Chuyên ngành không xác định"
                department_response = None
                if thesis.department_id:
                    department = db.query(Department).filter(Department.id == thesis.department_id).first()
                    if department:
                        department_response = DepartmentResponse.from_orm(department)

                imported_theses.append(ThesisResponse(
                    id=thesis.id,
                    thesis_type=thesis.thesis_type,
                    status=(
                        "Từ chối" if thesis.status == 0 else
                        "Chờ duyệt" if thesis.status == 1 else
                        "Đã duyệt cấp bộ môn" if thesis.status == 2 else
                        "Đã duyệt cấp khoa" if thesis.status == 3 else
                        "Chưa được đăng ký" if thesis.status == 4 else
                        "Đã được đăng ký" if thesis.status == 5 else
                        "Không xác định"
                    ),
                    reason=thesis.reason,
                    name=thesis.title,
                    description=thesis.description,
                    start_date=thesis.start_date,
                    end_date=thesis.end_date,
                    instructors=instructors_list,
                    reviewers=reviewers_list,
                    department=department_response,
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

        # 13. Trả về kết quả
        return {"success": created_count, "errors": errors, "imported_theses": imported_theses}

    except Exception as e:
        logger.error(f"Lỗi chung khi xử lý file: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Lỗi xử lý file Excel: {str(e)}")

@router.post("/", response_model=ThesisResponse)
def create_thesis_endpoint(
    thesis: ThesisCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    API để tạo mới một luận văn (thesis).
    """
    return create(db, thesis, user.id)


@router.put("/batch-update", response_model=ThesisBatchUpdateResponse)
def batch_update_theses_endpoint(
    update_request: ThesisBatchUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    API để cập nhật thông tin của nhiều đề tài trong một lần gọi.
    """
    return batch_update_theses(db, update_request, user.id)

@router.put("/{thesis_id}", response_model=ThesisResponse)
def update_thesis_endpoint(
    thesis_id: UUID,
    thesis: ThesisUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    API để cập nhật thông tin một luận văn (thesis).
    Chỉ cho phép giảng viên tạo đề tài đó được sửa.
    """
    update_thesis(db, thesis_id, thesis, user.id)
    return get_thesis_by_id(db, thesis_id)





@router.get("/{thesis_id}", response_model=ThesisResponse)
def get_thesis_by_id_endpoint(thesis_id: UUID, db: Session = Depends(get_db)):
    """
    API để lấy thông tin một luận văn (thesis) theo ID.
    """
    return get_thesis_by_id(db, thesis_id)

@router.get("/", response_model=List[ThesisResponse])
def get_all_theses_endpoint(db: Session = Depends(get_db)):
    """
    API để lấy danh sách tất cả các luận văn (theses) với thông tin của tất cả giảng viên hướng dẫn.
    """
    return get_all_theses(db)

@router.delete("/{thesis_id}")
def delete_thesis_endpoint(
    thesis_id: UUID,
    db: Session = Depends(get_db)
):
    """
    API để xóa một luận văn (thesis) theo ID.
    """
    return delete_thesis(db, thesis_id)

@router.get("/getall/major", response_model=List[MajorResponse])
def get_all_majors_endpoint(db: Session = Depends(get_db)):
    """
    API để lấy danh sách tất cả chuyên ngành (major).
    """
    return get_all_majors(db)

@router.get("/getall/department/g", response_model=List[DepartmentResponse])
def get_all_departments_endpoint(db: Session = Depends(get_db)):
    """
    API để lấy danh sách tất cả khoa (department).
    """
    return get_all_departments(db)

@router.get("/by-batch/{batch_id}", response_model=List[ThesisResponse])
def get_theses_by_batch_endpoint(batch_id: UUID, db: Session = Depends(get_db)):
    """
    API lấy danh sách luận văn theo đợt (batch_id).
    """
    return get_theses_by_batch_id(db, batch_id)


@router.get("/getall/batches", response_model=List[BatchResponse])
def get_all_batches_endpoint(db: Session = Depends(get_db)):
    """
    API lấy danh sách các đợt (batch) kèm học kỳ và năm học, sắp xếp từ mới đến cũ.
    """
    return get_all_batches_with_details(db)