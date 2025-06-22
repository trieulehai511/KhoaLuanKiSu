from typing import List
from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException, status
from models.model import Committee, Department, Information, LecturerInfo, Major, Thesis, ThesisCommittee, ThesisLecturer, User
from schemas.council import CouncilCreateWithTheses, CouncilDetailResponse, CouncilMemberResponse, ThesisSimpleResponse
from schemas.thesis import InstructorResponse, MajorResponse

def create_council_and_assign(db: Session, council_data: CouncilCreateWithTheses, user_id: UUID):
    """
    Tạo một hội đồng mới, gán thành viên và gán các đồ án cho hội đồng đó.
    Hàm này được cập nhật theo model Committee mới nhất.
    """
    
    # 1. Kiểm tra chuyên ngành (major) có tồn tại không
    major = db.query(Major).filter(Major.id == council_data.major_id).first()
    if not major:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy chuyên ngành với ID: {council_data.major_id}")

    # 2. Kiểm tra và lấy thông tin chủ tịch từ danh sách thành viên
    chairman = next((member for member in council_data.members if member.role == 1), None)
    if not chairman:
        raise HTTPException(status_code=400, detail="Hội đồng phải có một chủ tịch (role=1).")

    # 3. Tạo đối tượng Committee mới
    new_council = Committee(
        major_id=council_data.major_id,
        name=council_data.name,
        chairman_id=chairman.member_id,
        meeting_time=council_data.meeting_time,
        location=council_data.location,
        note=council_data.note
    )
    db.add(new_council)
    db.flush()  # Lấy new_council.id trước khi commit cuối cùng

    # 4. Kiểm tra sự tồn tại của tất cả các đồ án và giảng viên trước khi thực hiện gán
    if not council_data.thesis_ids:
        db.rollback() # Hoàn tác việc thêm new_council nếu có lỗi
        raise HTTPException(status_code=400, detail="Phải có ít nhất một đồ án được gán cho hội đồng.")
        
    theses_to_update = db.query(Thesis).filter(Thesis.id.in_(council_data.thesis_ids)).all()
    if len(theses_to_update) != len(set(council_data.thesis_ids)):
        db.rollback()
        raise HTTPException(status_code=404, detail="Một hoặc nhiều ID đồ án không tồn tại.")

    member_ids = [member.member_id for member in council_data.members]
    lecturers = db.query(User).filter(User.id.in_(member_ids), User.user_type == 3).all()
    if len(lecturers) != len(set(member_ids)):
        db.rollback()
        raise HTTPException(status_code=404, detail="Một hoặc nhiều ID thành viên không phải là giảng viên hoặc không tồn tại.")

    # 5. Gán đồ án và thành viên cho hội đồng
    for thesis in theses_to_update:
        if thesis.committee_id:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Đồ án '{thesis.title}' đã thuộc một hội đồng khác.")
        
        # Gán committee_id cho đồ án
        thesis.committee_id = new_council.id

        # Với mỗi đồ án, gán tất cả thành viên của hội đồng vào bảng ThesisCommittee
        for member_data in council_data.members:
            assignment = ThesisCommittee(
                committee_id=new_council.id,
                thesis_id=thesis.id,
                member_id=member_data.member_id,
                role=member_data.role
            )
            db.add(assignment)
    
    # 6. Commit tất cả các thay đổi vào DB và trả về kết quả
    db.commit()
    db.refresh(new_council)
    
    return new_council

def get_all_councils_with_theses(db: Session) -> List[CouncilDetailResponse]:
    """
    Lấy danh sách tất cả các hội đồng, kèm theo các đồ án và thành viên (với thông tin chi tiết) tương ứng.
    PHIÊN BẢN KHÔNG SỬ DỤNG JOIN.
    """
    # 1. Lấy tất cả các hội đồng
    councils = db.query(Committee).order_by(Committee.create_datetime.desc()).all()
    if not councils:
        return []

    # 2. Thu thập các ID cần thiết
    council_ids = {c.id for c in councils}
    major_ids = {c.major_id for c in councils if c.major_id}
    theses_in_councils = db.query(Thesis).filter(Thesis.committee_id.in_(council_ids)).all()
    thesis_ids = {t.id for t in theses_in_councils}
    assignments = db.query(ThesisCommittee).filter(ThesisCommittee.committee_id.in_(council_ids)).all()
    member_user_ids = {a.member_id for a in assignments}
    instructor_assignments = db.query(ThesisLecturer).filter(ThesisLecturer.thesis_id.in_(thesis_ids), ThesisLecturer.role == 1).all()
    instructor_user_ids = {i.lecturer_id for i in instructor_assignments}
    
    # 3. Lấy tất cả dữ liệu chi tiết liên quan
    all_user_ids = member_user_ids.union(instructor_user_ids)
    all_user_infos = db.query(Information).filter(Information.user_id.in_(all_user_ids)).all()
    all_lecturer_details = db.query(LecturerInfo).filter(LecturerInfo.user_id.in_(all_user_ids)).all()
    all_department_ids = {lec.department for lec in all_lecturer_details if lec.department}
    all_departments = db.query(Department).filter(Department.id.in_(all_department_ids)).all()
    majors = db.query(Major).filter(Major.id.in_(major_ids)).all()

    # 4. Tạo các "map" để tra cứu dữ liệu nhanh
    info_map = {info.user_id: f"{info.last_name} {info.first_name}" for info in all_user_infos}
    lecturer_map = {lec.user_id: lec for lec in all_lecturer_details}
    department_map = {dept.id: dept.name for dept in all_departments}
    major_map = {m.id: m for m in majors}

    # 5. Xây dựng cấu trúc response hoàn chỉnh
    final_results = []
    # ... (phần status_map giữ nguyên)
    status_map = {0: "Từ chối", 1: "Chờ duyệt", 2: "Đã duyệt cấp bộ môn", 3: "Đã duyệt cấp khoa", 4: "Chưa được đăng ký", 5: "Đã được đăng ký"}


    for council in councils:
        # --- Phần lấy thông tin đồ án và GVHD giữ nguyên ---
        theses_list = []
        current_theses = [t for t in theses_in_councils if t.committee_id == council.id]
        for thesis in current_theses:
            instructor_list = []
            current_instructors_assign = [i for i in instructor_assignments if i.thesis_id == thesis.id]
            for inst_assign in current_instructors_assign:
                lecturer_info = lecturer_map.get(inst_assign.lecturer_id)
                if lecturer_info:
                    dept_name = department_map.get(lecturer_info.department, "Không xác định")
                    instructor_list.append(InstructorResponse(
                        name=info_map.get(inst_assign.lecturer_id, "N/A"),
                        email=lecturer_info.email,
                        lecturer_code=lecturer_info.lecturer_code,
                        department=lecturer_info.department,
                        department_name=dept_name
                    ))
            
            theses_list.append(ThesisSimpleResponse(
                id=thesis.id, title=thesis.title, description=thesis.description,
                status=status_map.get(thesis.status, "Không xác định"),
                thesis_type=thesis.thesis_type, name_thesis_type="Khóa luận" if thesis.thesis_type == 1 else "Đồ án",
                start_date=thesis.start_date, end_date=thesis.end_date,
                instructors=instructor_list
            ))

        # === CẬP NHẬT LOGIC LẤY THÔNG TIN THÀNH VIÊN HỘI ĐỒNG ===
        members_list = []
        unique_members = {assign.member_id: assign for assign in assignments if assign.committee_id == council.id}.values()
        for member_assign in unique_members:
            lecturer_details = lecturer_map.get(member_assign.member_id)
            department_name = department_map.get(lecturer_details.department, "Không xác định") if lecturer_details else "Không xác định"
            
            members_list.append(CouncilMemberResponse(
                member_id=member_assign.member_id,
                name=info_map.get(member_assign.member_id, "Không rõ"),
                role=member_assign.role,
                email=lecturer_details.email if lecturer_details else "N/A",
                lecturer_code=lecturer_details.lecturer_code if lecturer_details else "N/A",
                department=lecturer_details.department if lecturer_details else 0,
                department_name=department_name
            ))
        # =======================================================

        major_obj = major_map.get(council.major_id)
        major_res = MajorResponse(id=major_obj.id, name=major_obj.name) if major_obj else None

        final_results.append(CouncilDetailResponse(
            id=council.id, name=council.name, major=major_res,
            meeting_time=council.meeting_time, location=council.location,
            note=council.note, theses=theses_list, members=members_list
        ))
        
    return final_results