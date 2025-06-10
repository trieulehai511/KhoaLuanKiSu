from datetime import datetime
from io import BytesIO
from fastapi import APIRouter, Depends, File, Form, Path, UploadFile
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
import pandas as pd
from models.model import Department, LecturerInfo, User
from schemas.thesis import BatchResponse, BatchSimpleResponse, DepartmentResponse, MajorResponse, ThesisCreate, ThesisUpdate, ThesisResponse
from services.thesis import (
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
from routers.auth import get_current_user
from uuid import UUID
from fastapi.responses import FileResponse
router = APIRouter(
    prefix="/theses",
    tags=["theses"]
)

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



@router.get("/download-template", summary="Tải file Excel mẫu")
def download_template():
    file_path = Path("static/thesis_template.xlsx")
    if not file_path.exists():
        data = {
            "STT": [1],
            "TÊN ĐỀ TÀI": ["Hệ thống quản lý thư viện"],
            "NỘI DUNG YÊU CẦU": ["Xây dựng chức năng quản lý mượn trả"],
            "MÃ GIẢNG VIÊN": ["GV001"],
            "GIÁO VIÊN HƯỚNG DẪN": ["Nguyễn Văn A"],
            "EMAIL": ["vana@huit.edu.vn"],
            "BỘ MÔN": ["KTPM"],
            "GHI CHÚ": [""]
        }
        df = pd.DataFrame(data)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(file_path, index=False)

    return FileResponse(
        path=file_path,
        filename="thesis_template.xlsx",
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@router.post("/import--excel")
def import_thesis_from_simple_excel(
    file: UploadFile = File(...),
    batch_id: UUID = Form(...),
    major_id: UUID = Form(...),
    thesis_type: int = Form(...),
    status: int = Form(...),
    start_date: datetime = Form(...),
    end_date: datetime = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    content = file.file.read()
    df = pd.read_excel(BytesIO(content), header=4)  # Header ở dòng 5

    created = 0
    errors = []

    for i, row in df.iterrows():
        try:
            if not isinstance(row.get("STT"), (int, float)):
                raise Exception("STT không hợp lệ")

            if pd.isna(row.get("TÊN ĐỀ TÀI")) or pd.isna(row.get("NỘI DUNG YÊU CẦU")):
                raise Exception("Tên đề tài hoặc nội dung không được để trống")

            dept_name = str(row.get("BỘ MÔN")).strip()
            department = db.query(Department).filter(Department.name == dept_name).first()
            if not department:
                raise Exception(f"Bộ môn '{dept_name}' không tồn tại")

            ma_gv_list = [code.strip() for code in str(row.get("MÃ GIẢNG VIÊN")).split(",") if code.strip()]
            lecturers = db.query(LecturerInfo).filter(LecturerInfo.lecturer_code.in_(ma_gv_list)).all()
            if len(lecturers) != len(ma_gv_list):
                raise Exception("Một hoặc nhiều mã giảng viên không tồn tại")

            if pd.notna(row.get("GIÁO VIÊN HƯỚNG DẪN")):
                input_name = str(row.get("GIÁO VIÊN HƯỚNG DẪN")).strip().lower()
                if not any(input_name in lec.email.lower() or input_name in lec.lecturer_code.lower() for lec in lecturers):
                    raise Exception("Tên giảng viên không khớp với mã đã nhập")

            thesis_data = ThesisCreate(
                title=row["TÊN ĐỀ TÀI"],
                description=row["NỘI DUNG YÊU CẦU"],
                thesis_type=thesis_type,
                start_date=start_date,
                end_date=end_date,
                status=status,
                batch_id=batch_id,
                major_id=major_id,
                lecturer_ids=[lec.user_id for lec in lecturers]
            )

            create(db, thesis_data, user.id)
            created += 1

        except Exception as e:
            errors.append({
                "row": i + 5,
                "title": row.get("TÊN ĐỀ TÀI", "<trống>"),
                "error": str(e)
            })

    return {"success": created, "errors": errors}

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