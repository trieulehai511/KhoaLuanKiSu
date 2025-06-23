from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException, status
from models.model import Thesis, Group, GroupMember, ThesisCommittee, ThesisMemberScore
from schemas.score import ScoreCreate

def create_or_update_score(db: Session, score_data: ScoreCreate, evaluator_id: UUID):
    """
    Tạo mới hoặc cập nhật điểm cho một sinh viên trong một đồ án.
    Bao gồm kiểm tra quyền của người chấm điểm.
    """
    
    # 1. Kiểm tra xem đồ án có tồn tại không
    thesis = db.query(Thesis).filter(Thesis.id == score_data.thesis_id).first()
    if not thesis or not thesis.committee_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy đồ án hoặc đồ án chưa được gán cho hội đồng.")

    # 2. Kiểm tra xem người chấm (evaluator) có phải là thành viên của hội đồng của đồ án này không
    is_evaluator_in_committee = db.query(ThesisCommittee).filter(
        ThesisCommittee.committee_id == thesis.committee_id,
        ThesisCommittee.member_id == evaluator_id
    ).first()
    if not is_evaluator_in_committee:
        raise HTTPException(status_code=403, detail="Bạn không phải là thành viên của hội đồng chấm điểm đồ án này.")

    # 3. Kiểm tra xem sinh viên được chấm có thuộc nhóm làm đồ án này không
    group = db.query(Group).filter(Group.thesis_id == score_data.thesis_id).first()
    if not group:
         raise HTTPException(status_code=404, detail="Không tìm thấy nhóm thực hiện đồ án này.")
    
    is_student_in_group = db.query(GroupMember).filter(
        GroupMember.group_id == group.id,
        GroupMember.student_id == score_data.student_id
    ).first()
    if not is_student_in_group:
        raise HTTPException(status_code=400, detail="Sinh viên này không thuộc nhóm thực hiện đồ án.")

    # 4. Tìm kiếm điểm đã có để cập nhật, nếu không thì tạo mới (UPSERT)
    existing_score = db.query(ThesisMemberScore).filter(
        ThesisMemberScore.thesis_id == score_data.thesis_id,
        ThesisMemberScore.student_id == score_data.student_id,
        ThesisMemberScore.evaluator_id == evaluator_id,
        ThesisMemberScore.score_type == score_data.score_type
    ).first()

    if existing_score:
        # Nếu đã có, cập nhật điểm
        existing_score.score = score_data.score
        db.commit()
        db.refresh(existing_score)
        return existing_score
    else:
        # Nếu chưa có, tạo bản ghi điểm mới
        new_score = ThesisMemberScore(
            thesis_id=score_data.thesis_id,
            student_id=score_data.student_id,
            evaluator_id=evaluator_id, # Lấy từ user đang đăng nhập
            score=score_data.score,
            score_type=score_data.score_type
        )
        db.add(new_score)
        db.commit()
        db.refresh(new_score)
        return new_score