from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException, status
from models.model import Committee, Thesis, ThesisCommittee, User
from schemas.council import CouncilCreateWithTheses

def create_council_and_assign(db: Session, council_data: CouncilCreateWithTheses, user_id: UUID):
    """
    Tạo một hội đồng mới, gán thành viên và gán các đồ án cho hội đồng đó.
    """
    # 1. Tạo hội đồng mới
    # Tìm chairman_id từ danh sách members
    chairman = next((member for member in council_data.members if member.role == 1), None)
    if not chairman:
        raise HTTPException(status_code=400, detail="Hội đồng phải có một chủ tịch (role=1).")

    new_council = Committee(
        name=council_data.name,
        chairman_id=chairman.member_id,
        meeting_time=council_data.meeting_time,
        location=council_data.location,
        note=council_data.note
    )
    db.add(new_council)
    db.flush() # Dùng flush để lấy được new_council.id trước khi commit

    # 2. Gán thành viên cho hội đồng
    for member_data in council_data.members:
        # Kiểm tra xem giảng viên có tồn tại không
        lecturer = db.query(User).filter(User.id == member_data.member_id, User.user_type == 3).first()
        if not lecturer:
            db.rollback() # Hoàn tác nếu có lỗi
            raise HTTPException(status_code=404, detail=f"Không tìm thấy giảng viên với ID: {member_data.member_id}")

        assignment = ThesisCommittee(
            committee_id=new_council.id,
            member_id=member_data.member_id,
            role=member_data.role,
            # Lưu ý: thesis_id ở đây có thể để null nếu 1 thành viên thuộc hội đồng chung
            # Hoặc bạn có thể lặp qua thesis_ids và tạo bản ghi cho từng đồ án
            thesis_id=None # Gán thành viên vào hội đồng chung
        )
        db.add(assignment)

    # 3. Gán các đồ án cho hội đồng
    if council_data.thesis_ids:
        theses_to_update = db.query(Thesis).filter(Thesis.id.in_(council_data.thesis_ids)).all()
        
        if len(theses_to_update) != len(council_data.thesis_ids):
            db.rollback()
            raise HTTPException(status_code=404, detail="Một hoặc nhiều đồ án không tồn tại.")
        
        for thesis in theses_to_update:
            if thesis.committee_id:
                db.rollback()
                raise HTTPException(status_code=400, detail=f"Đồ án '{thesis.title}' đã thuộc một hội đồng khác.")
            thesis.committee_id = new_council.id

    db.commit()
    db.refresh(new_council)
    
    return new_council