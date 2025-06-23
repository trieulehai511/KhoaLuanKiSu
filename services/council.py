from typing import List
from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException, status
from models.model import Committee, Department, Information, LecturerInfo, Major, Thesis, ThesisCommittee, ThesisLecturer, User
from schemas.council import CouncilCreateWithTheses, CouncilDetailResponse, CouncilMemberResponse, CouncilUpdate, ThesisSimpleResponse
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
    Lấy danh sách tất cả các hội đồng, kèm theo các đồ án (với thông tin chi tiết) 
    và thành viên (với thông tin chi tiết) tương ứng.
    PHIÊN BẢN KHÔNG SỬ DỤNG JOIN, TỐI ƯU HÓA TRUY VẤN.
    """
    # 1. Lấy tất cả các hội đồng
    councils = db.query(Committee).order_by(Committee.create_datetime.desc()).all()
    if not councils:
        return []

    # 2. Thu thập tất cả các ID cần thiết trong một lần duyệt
    council_ids = {c.id for c in councils}
    
    theses_in_councils = db.query(Thesis).filter(Thesis.committee_id.in_(council_ids)).all()
    thesis_ids = {t.id for t in theses_in_councils}
    
    council_major_ids = {c.major_id for c in councils if c.major_id}
    thesis_major_ids = {t.major_id for t in theses_in_councils}
    all_major_ids = council_major_ids.union(thesis_major_ids)

    assignments = db.query(ThesisCommittee).filter(ThesisCommittee.committee_id.in_(council_ids)).all()
    member_user_ids = {a.member_id for a in assignments}

    instructor_assignments = db.query(ThesisLecturer).filter(ThesisLecturer.thesis_id.in_(thesis_ids), ThesisLecturer.role == 1).all()
    instructor_user_ids = {i.lecturer_id for i in instructor_assignments}
    
    all_user_ids = member_user_ids.union(instructor_user_ids)

    # 3. Truy vấn tất cả dữ liệu chi tiết trong vài câu query lớn
    all_user_infos = db.query(Information).filter(Information.user_id.in_(all_user_ids)).all()
    all_lecturer_details = db.query(LecturerInfo).filter(LecturerInfo.user_id.in_(all_user_ids)).all()
    all_department_ids = {lec.department for lec in all_lecturer_details if lec.department}
    all_departments = db.query(Department).filter(Department.id.in_(all_department_ids)).all()
    all_majors = db.query(Major).filter(Major.id.in_(all_major_ids)).all()

    # 4. Tạo các "map" để tra cứu dữ liệu nhanh trong Python
    info_map = {info.user_id: f"{info.last_name} {info.first_name}" for info in all_user_infos}
    lecturer_map = {lec.user_id: lec for lec in all_lecturer_details}
    department_map = {dept.id: dept.name for dept in all_departments}
    major_map = {m.id: m for m in all_majors}
    council_role_map = {1: 'Chủ tịch Hội đồng', 2: 'Uỷ viên - Thư ký', 3: 'Uỷ viên'}
    status_map = {0: "Từ chối", 1: "Chờ duyệt", 2: "Đã duyệt cấp bộ môn", 3: "Đã duyệt cấp khoa", 4: "Chưa được đăng ký", 5: "Đã được đăng ký"}

    # 5. Xây dựng cấu trúc response hoàn chỉnh
    final_results = []
    for council in councils:
        # Lọc và tạo danh sách đồ án cho hội đồng hiện tại
        theses_list = []
        current_theses = [t for t in theses_in_councils if t.committee_id == council.id]
        for thesis in current_theses:
            # Lọc và tạo danh sách GVHD cho đồ án hiện tại
            instructor_list = []
            current_instructors_assign = [i for i in instructor_assignments if i.thesis_id == thesis.id]
            for inst_assign in current_instructors_assign:
                lecturer_info = lecturer_map.get(inst_assign.lecturer_id)
                if lecturer_info:
                    dept_name = department_map.get(lecturer_info.department, "Không xác định")
                    instructor_list.append(InstructorResponse(
                        id=inst_assign.lecturer_id,
                        name=info_map.get(inst_assign.lecturer_id, "N/A"),
                        email=lecturer_info.email,
                        lecturer_code=lecturer_info.lecturer_code,
                        department=lecturer_info.department,
                        department_name=dept_name
                    ))
            
            major_for_thesis = major_map.get(thesis.major_id)
            theses_list.append(ThesisSimpleResponse(
                id=thesis.id,
                title=thesis.title,
                description=thesis.description,
                major_id=thesis.major_id,
                major_name=major_for_thesis.name if major_for_thesis else "Không xác định",
                status=status_map.get(thesis.status, "Không xác định"),
                thesis_type=thesis.thesis_type,
                name_thesis_type="Khóa luận" if thesis.thesis_type == 1 else "Đồ án",
                start_date=thesis.start_date,
                end_date=thesis.end_date,
                instructors=instructor_list
            ))

        # Lọc và tạo danh sách thành viên cho hội đồng hiện tại
        members_list = []
        unique_members = {assign.member_id: assign for assign in assignments if assign.committee_id == council.id}.values()
        for member_assign in unique_members:
            lecturer_details = lecturer_map.get(member_assign.member_id)
            department_name = department_map.get(lecturer_details.department, "Không xác định") if lecturer_details else "Không xác định"
            
            members_list.append(CouncilMemberResponse(
                member_id=member_assign.member_id,
                name=info_map.get(member_assign.member_id, "Không rõ"),
                role=member_assign.role,
                role_name=council_role_map.get(member_assign.role, "Không xác định"),
                email=lecturer_details.email if lecturer_details else "N/A",
                lecturer_code=lecturer_details.lecturer_code if lecturer_details else "N/A",
                department=lecturer_details.department if lecturer_details else 0,
                department_name=department_name
            ))

        # Lấy thông tin chuyên ngành của hội đồng từ map
        major_obj = major_map.get(council.major_id)
        major_res = MajorResponse(id=major_obj.id, name=major_obj.name) if major_obj else None

        # Tạo đối tượng response cuối cùng cho một hội đồng
        final_results.append(CouncilDetailResponse(
            id=council.id,
            name=council.name,
            major=major_res,
            meeting_time=council.meeting_time,
            location=council.location,
            note=council.note,
            theses=theses_list,
            members=members_list
        ))
        
    return final_results

def update_council(db: Session, council_id: UUID, council_data: CouncilUpdate):
    """
    Cập nhật thông tin của một hội đồng.
    """
    # 1. Tìm hội đồng cần cập nhật
    council = db.query(Committee).filter(Committee.id == council_id).first()
    if not council:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội đồng.")

    update_data = council_data.dict(exclude_unset=True)

    # 2. Cập nhật các trường thông tin đơn giản
    simple_fields = ["name", "major_id", "meeting_time", "location", "note"]
    for field in simple_fields:
        if field in update_data:
            setattr(council, field, update_data[field])

    # 3. Cập nhật danh sách thành viên (xóa cũ, thêm mới)
    if "members" in update_data:
        # Xóa tất cả thành viên cũ của hội đồng
        db.query(ThesisCommittee).filter(ThesisCommittee.committee_id == council_id).delete(synchronize_session=False)
        # Thêm lại danh sách thành viên mới
        for member_data in council_data.members:
            # Lặp qua các đồ án đang thuộc hội đồng để gán thành viên
            theses_in_council = db.query(Thesis).filter(Thesis.committee_id == council_id).all()
            for thesis in theses_in_council:
                assignment = ThesisCommittee(
                    committee_id=council.id,
                    thesis_id=thesis.id,
                    member_id=member_data.member_id,
                    role=member_data.role
                )
                db.add(assignment)

    # 4. Cập nhật danh sách đồ án (xóa cũ, thêm mới)
    if "thesis_ids" in update_data:
        # Gỡ tất cả đồ án cũ ra khỏi hội đồng
        db.query(Thesis).filter(Thesis.committee_id == council_id).update({"committee_id": None})
        # Gán danh sách đồ án mới vào hội đồng
        db.query(Thesis).filter(Thesis.id.in_(council_data.thesis_ids)).update({"committee_id": council_id})

    db.commit()
    db.refresh(council)
    return council

def delete_council(db: Session, council_id: UUID):
    """
    Xóa một hội đồng và các liên kết của nó.
    """
    # 1. Tìm hội đồng cần xóa
    council = db.query(Committee).filter(Committee.id == council_id).first()
    if not council:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội đồng.")

    # 2. Gỡ tất cả đồ án ra khỏi hội đồng này (set committee_id = null)
    # Dùng synchronize_session=False để tối ưu cho việc cập nhật hàng loạt
    db.query(Thesis).filter(Thesis.committee_id == council_id).update(
        {"committee_id": None}, synchronize_session=False
    )

    # 3. Xóa tất cả các bản ghi gán thành viên thuộc hội đồng này
    db.query(ThesisCommittee).filter(ThesisCommittee.committee_id == council_id).delete(
        synchronize_session=False
    )

    # 4. Xóa chính hội đồng đó
    db.delete(council)

    # 5. Lưu tất cả thay đổi
    db.commit()
    
    return {"message": "Đã xóa hội đồng thành công."}