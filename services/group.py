from sqlalchemy.orm import Session
from models.model import Group, GroupMember, Information, Invite, Mission, StudentInfo, Thesis, ThesisLecturer
from schemas.group import (
    GroupCreate, GroupUpdate, GroupMemberCreate, 
    GroupWithMembersResponse, MemberDetailResponse
)
from uuid import UUID
from fastapi import HTTPException, status
from typing import List

def is_member_of_any_group(db: Session, user_id: UUID):
    """Kiểm tra người dùng đã thuộc nhóm nào chưa"""
    return db.query(GroupMember).filter(GroupMember.student_id == user_id).first() is not None

def create_group(db: Session, group: GroupCreate, user_id: UUID):
    """Tạo nhóm mới và đặt người tạo làm nhóm trưởng"""
    is_existing_member = db.query(GroupMember).filter(GroupMember.student_id == user_id).first()
    if is_existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn đã là thành viên của một nhóm khác, không thể tạo nhóm mới."
        )

    new_group = Group(name=group.name, leader_id=user_id, quantity=1)
    db.add(new_group)
    db.flush()
    db.refresh(new_group)

    group_leader = GroupMember(
        group_id=new_group.id,
        student_id=user_id,
        is_leader=True,
    )
    db.add(group_leader)
    db.commit()
    return new_group

def add_member(db: Session, group_id: UUID, member: GroupMemberCreate, leader_id: UUID):
    """Thêm thành viên vào nhóm (chỉ nhóm trưởng). Hàm này dành cho trường hợp thêm trực tiếp, không qua lời mời."""
    # 1. Kiểm tra nhóm và quyền của người gọi
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhóm.")
    if group.leader_id != leader_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ nhóm trưởng mới có quyền thêm thành viên.")

    # 2. Kiểm tra giới hạn thành viên
    if group.quantity >= 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nhóm đã đủ số lượng thành viên.")

    # 3. Kiểm tra xem người được thêm đã ở trong nhóm khác chưa
    if is_member_of_any_group(db, member.student_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Thành viên này đã ở trong một nhóm khác.")
        
    # 4. Thêm thành viên
    new_member = GroupMember(group_id=group_id, student_id=member.student_id, is_leader=False)
    db.add(new_member)
    
    # 5. Cập nhật số lượng
    group.quantity += 1
    db.commit()
    db.refresh(new_member)
    return new_member

def remove_member(db: Session, group_id: UUID, member_id: UUID, leader_id: UUID):
    """Xóa thành viên khỏi nhóm (chỉ nhóm trưởng)"""
    # 1. Kiểm tra nhóm và quyền của người gọi
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhóm.")
    if group.leader_id != leader_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ nhóm trưởng mới có quyền xóa thành viên.")

    # 2. Không cho phép xóa chính nhóm trưởng
    if member_id == leader_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể xóa nhóm trưởng. Hãy chuyển quyền trước.")

    # 3. Tìm và xóa thành viên
    member_to_remove = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.student_id == member_id
    ).first()

    if not member_to_remove:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thành viên này trong nhóm.")
    
    db.delete(member_to_remove)
    
    # 4. Cập nhật số lượng
    group.quantity -= 1
    db.commit()
    return {"message": "Xóa thành viên thành công."}

def get_members(db: Session, group_id: UUID):
    """Lấy danh sách thành viên của nhóm"""
    return db.query(GroupMember).filter(GroupMember.group_id == group_id).all()

def transfer_leader(db: Session, group_id: UUID, new_leader_id: UUID, current_leader_id: UUID):
    """Chuyển quyền nhóm trưởng"""
    # 1. Kiểm tra nhóm và quyền của người gọi
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhóm.")
    if group.leader_id != current_leader_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ nhóm trưởng hiện tại mới có thể chuyển quyền.")

    # 2. Tìm thành viên cũ và mới
    current_leader_member = db.query(GroupMember).filter(GroupMember.student_id == current_leader_id, GroupMember.group_id == group_id).first()
    new_leader_member = db.query(GroupMember).filter(GroupMember.student_id == new_leader_id, GroupMember.group_id == group_id).first()

    if not new_leader_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người được chuyển quyền không phải là thành viên của nhóm.")

    # 3. Cập nhật quyền
    current_leader_member.is_leader = False
    new_leader_member.is_leader = True
    group.leader_id = new_leader_id
    
    db.commit()
    return {"message": "Chuyển quyền nhóm trưởng thành công."}


def get_all_groups_for_user(db: Session, user_id: UUID) -> List[GroupWithMembersResponse]:
    """
    Lấy thông tin TẤT CẢ các nhóm và danh sách thành viên của một user cụ thể.
    """
    user_memberships = db.query(GroupMember).filter(GroupMember.student_id == user_id).all()

    if not user_memberships:
        return []

    all_groups_list: List[GroupWithMembersResponse] = []
    
    for membership in user_memberships:
        group_id = membership.group_id
        # Đối tượng group ở đây đã chứa thông tin thesis_id
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            continue

        all_members_in_group = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()

        member_details_list: List[MemberDetailResponse] = []
        for member in all_members_in_group:
            student_user_id = member.student_id
            info = db.query(Information).filter(Information.user_id == student_user_id).first()
            student_info = db.query(StudentInfo).filter(StudentInfo.user_id == student_user_id).first()

            if info and student_info:
                member_obj = MemberDetailResponse(
                    user_id=student_user_id,
                    full_name=f"{info.last_name} {info.first_name}",
                    student_code=student_info.student_code,
                    is_leader=member.is_leader or False
                )
                member_details_list.append(member_obj)

        group_obj = GroupWithMembersResponse(
            id=group.id,
            name=group.name,
            leader_id=group.leader_id,
            members=member_details_list,
            # THÊM DỮ LIỆU VÀO ĐÂY
            thesis_id=group.thesis_id
        )
        all_groups_list.append(group_obj)

    return all_groups_list

def get_supervised_groups_by_lecturer(db: Session, lecturer_id: UUID) -> List[GroupWithMembersResponse]:
    """Lấy tất cả các nhóm mà một giảng viên đang hướng dẫn."""
    
    # 1. Tìm tất cả các đề tài mà giảng viên này đang hướng dẫn (role=1)
    supervised_theses_query = db.query(ThesisLecturer.thesis_id).filter(
        ThesisLecturer.lecturer_id == lecturer_id,
        ThesisLecturer.role == 1
    ).distinct()
    
    supervised_thesis_ids = [item[0] for item in supervised_theses_query.all()]

    if not supervised_thesis_ids:
        return []

    # 2. Từ danh sách đề tài, tìm các nhóm tương ứng
    groups = db.query(Group).filter(Group.thesis_id.in_(supervised_thesis_ids)).all()
    
    # 3. Lấy thông tin chi tiết cho từng nhóm
    results = []
    for group in groups:
        # Tái sử dụng hàm đã có để lấy chi tiết nhóm
        group_details = get_group_with_detailed_members(db, group.id)
        if group_details:
            results.append(group_details)
            
    return results

def get_all_groups_for_admin(db: Session) -> List[GroupWithMembersResponse]:
    """Lấy tất cả các nhóm trong hệ thống."""
    all_groups = db.query(Group).order_by(Group.create_datetime.desc()).all()
    
    results = []
    for group in all_groups:
        group_details = get_group_with_detailed_members(db, group.id)
        if group_details:
            results.append(group_details)
            
    return results

def update_group_name(db: Session, group_id: UUID, new_name: str, user_id: UUID):
    """Cập nhật tên của một nhóm (chỉ nhóm trưởng)"""
    # 1. Tìm nhóm trong CSDL
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhóm.")

    # 2. Kiểm tra quyền: người thực hiện phải là nhóm trưởng
    if group.leader_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ nhóm trưởng mới có quyền đổi tên nhóm.")

    # 3. Cập nhật tên mới
    group.name = new_name
    db.commit()
    db.refresh(group)
    
    return group

def get_detailed_members_of_group(db: Session, group_id: UUID) -> List[MemberDetailResponse]:
    """Lấy danh sách thành viên chi tiết của một nhóm."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhóm.")

    all_members_in_group = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    
    member_details_list: List[MemberDetailResponse] = []
    for member in all_members_in_group:
        student_user_id = member.student_id
        info = db.query(Information).filter(Information.user_id == student_user_id).first()
        student_info = db.query(StudentInfo).filter(StudentInfo.user_id == student_user_id).first()

        if info and student_info:
            member_obj = MemberDetailResponse(
                user_id=student_user_id,
                full_name=f"{info.last_name} {info.first_name}",
                student_code=student_info.student_code,
                is_leader=member.is_leader or False
            )
            member_details_list.append(member_obj)
            
    return member_details_list

# HÀM MỚI ĐỂ GỘP THÔNG TIN NHÓM VÀ THÀNH VIÊN
def get_group_with_detailed_members(db: Session, group_id: UUID) -> GroupWithMembersResponse:
    """Lấy thông tin chi tiết của nhóm và danh sách thành viên của nó."""
    # 1. Lấy thông tin cơ bản của nhóm (đã chứa thesis_id)
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhóm.")
        
    # 2. Lấy danh sách thành viên chi tiết
    members_list = get_detailed_members_of_group(db, group_id)
    
    # 3. Tạo đối tượng trả về hoàn chỉnh
    response = GroupWithMembersResponse(
        id=group.id,
        name=group.name,
        leader_id=group.leader_id,
        thesis_id=group.thesis_id,
        members=members_list
    )
    
    return response


def delete_group(db: Session, group_id: UUID, user_id: UUID):
    """Xóa một nhóm và các thông tin liên quan (chỉ nhóm trưởng)"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhóm.")

    if group.leader_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ nhóm trưởng mới có quyền xóa nhóm.")

    if group.thesis_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể xóa nhóm đã được gán vào đề tài.")

    # ... (phần còn lại của logic xóa giữ nguyên) ...
    db.query(Invite).filter(Invite.group_id == group_id).delete(synchronize_session=False)
    db.query(GroupMember).filter(GroupMember.group_id == group_id).delete(synchronize_session=False)
    db.delete(group)
    db.commit()
    
    return {"message": "Đã xóa nhóm thành công."}

def get_group_by_thesis_id(db: Session, thesis_id: UUID):
    """
    Lấy thông tin chi tiết của nhóm dựa vào ID của đề tài mà nhóm đó đã đăng ký.
    """
    # 1. Tìm nhóm trong CSDL dựa trên thesis_id
    group = db.query(Group).filter(Group.thesis_id == thesis_id).first()
    
    # 2. Nếu không tìm thấy nhóm, báo lỗi 404
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy nhóm nào đã đăng ký cho đề tài này."
        )
        
    # 3. Nếu tìm thấy, tái sử dụng hàm đã có để lấy thông tin chi tiết của nhóm
    return get_group_with_detailed_members(db, group.id)

def register_thesis_for_group(db: Session, group_id: UUID, thesis_id: UUID, user_id: UUID):
    """Đăng ký một đề tài cho nhóm (chỉ nhóm trưởng)"""
    
    # 1. Kiểm tra nhóm và quyền nhóm trưởng
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhóm.")
    if group.leader_id != user_id:
        raise HTTPException(status_code=403, detail="Chỉ nhóm trưởng mới có quyền đăng ký đề tài.")
    if group.thesis_id:
        raise HTTPException(status_code=400, detail="Nhóm này đã đăng ký đề tài khác.")

    # 2. Kiểm tra đề tài và trạng thái của nó
    thesis_to_register = db.query(Thesis).filter(Thesis.id == thesis_id).first()
    if not thesis_to_register:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề tài.")
    
    # --- THÊM ĐIỀU KIỆN KIỂM TRA STATUS = 4 ---
    if thesis_to_register.status != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Đề tài này không ở trạng thái sẵn sàng để đăng ký."
        )
    # --------------------------------------------
    
    # 3. Kiểm tra xem đề tài đã có nhóm nào đăng ký chưa
    is_thesis_taken = db.query(Group).filter(Group.thesis_id == thesis_id).first()
    if is_thesis_taken:
        raise HTTPException(status_code=400, detail="Đề tài này đã được nhóm khác đăng ký.")

    # === LOGIC KIỂM TRA RÀNG BUỘC THÀNH VIÊN ĐÃ ĐƯỢC VIẾT LẠI (KHÔNG DÙNG JOIN) ===
    
    # Lấy ID của các sinh viên trong nhóm đang đăng ký
    members_in_group = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    student_ids = [member.student_id for member in members_in_group]

    # Tìm tất cả các nhóm mà các sinh viên này đang là thành viên
    all_memberships = db.query(GroupMember).filter(GroupMember.student_id.in_(student_ids)).all()
    all_group_ids = {membership.group_id for membership in all_memberships}

    # Từ các nhóm đó, lấy ra danh sách các đề tài đã được đăng ký
    groups_with_theses = db.query(Group).filter(Group.id.in_(all_group_ids), Group.thesis_id.isnot(None)).all()
    existing_thesis_ids = {g.thesis_id for g in groups_with_theses}
    
    # Kiểm tra xem có đề tài nào trong danh sách đã đăng ký trùng đợt và loại với đề tài hiện tại không
    if existing_thesis_ids:
        conflicting_registration = db.query(Thesis).filter(
            Thesis.id.in_(existing_thesis_ids),
            Thesis.batch_id == thesis_to_register.batch_id,
            Thesis.thesis_type == thesis_to_register.thesis_type
        ).first()

        if conflicting_registration:
            # Nếu có, tìm ra sinh viên vi phạm để báo lỗi cụ thể
            conflicting_group = db.query(Group).filter(Group.thesis_id == conflicting_registration.id).first()
            conflicting_member_record = db.query(GroupMember).filter(
                GroupMember.group_id == conflicting_group.id,
                GroupMember.student_id.in_(student_ids)
            ).first()
            
            conflicting_student_id = conflicting_member_record.student_id
            student_info = db.query(Information).filter(Information.user_id == conflicting_student_id).first()
            student_name = f"{student_info.last_name} {student_info.first_name}" if student_info else f"ID: {conflicting_student_id}"
            thesis_type_name = "Khóa luận" if thesis_to_register.thesis_type == 1 else "Đồ án"
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Đăng ký thất bại. Thành viên '{student_name}' đã đăng ký một {thesis_type_name} khác trong đợt này."
            )
    # =================================================================================

    # Tự động tạo mission nếu chưa có
    existing_mission = db.query(Mission).filter(Mission.thesis_id == thesis_id).first()
    if not existing_mission:
        default_mission = Mission(
            thesis_id=thesis_id,
            title=f"Tiến độ thực hiện: {thesis_to_register.title}",
            description="Các công việc cần thực hiện cho đề tài.",
            start_date=thesis_to_register.start_date,
            end_date=thesis_to_register.end_date,
            status=1 # 1: Chưa bắt đầu
        )
        db.add(default_mission)

    # Cập nhật thông tin và lưu
    group.thesis_id = thesis_id
    thesis_to_register.status = 5 # Chuyển trạng thái thành "Đã đăng ký"
    
    db.commit()
    db.refresh(group)
    return group