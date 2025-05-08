from datetime import datetime
import uuid
from sqlalchemy import UUID, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, func
from db.database import Base

class User(Base):
    __tablename__ = "sys_user"

    id = Column(UUID, primary_key=True, index=True)
    user_name = Column(String, index=True)
    password = Column(String, index=True)
    is_active = Column(Boolean, index=True)
    is_lecturer = Column(Boolean, index= True)
    major = Column(UUID, index = True)

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID, nullable=False)
    token = Column(String, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

class Major(Base):
    __tablename__ ="major"
    id = Column(UUID, primary_key=True, index =True)
    name = Column(String, index =True)

class Information(Base):
    __tablename__ = 'information'
    id = Column(UUID, primary_key=True,index =True)
    first_name = Column(String, index = True)
    last_name = Column(String, index = True)
    date_of_birth = Column(DateTime)
    gender = Column(String)
    address = Column(String)
    tel_phone = Column(String)
    user_id = Column(UUID, nullable=False)

class SysRole(Base):
    __tablename__ = "sys_role"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # admin, user, lecture
    create_datetime = Column(DateTime, default=func.now())
    update_datetime = Column(DateTime, default=func.now(), onupdate=func.now())

class SysFunction(Base):
    __tablename__ = "sys_function"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # API path, e.g., "/thesis/propose"
    create_datetime = Column(DateTime, default=func.now())
    update_datetime = Column(DateTime, default=func.now(), onupdate=func.now())

class SysUserRole(Base):
    __tablename__ = "sys_user_role"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID, nullable=False)
    role_id = Column(Integer,nullable=False)

class SysRoleFunction(Base):
    __tablename__ = "sys_role_function"
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer,nullable=False)
    function_id = Column(Integer,nullable=False)

class Thesis(Base):
    __tablename__ = "thesis"
    id = Column(UUID, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    lecturer_id = Column(UUID, nullable=False)
    create_datetime = Column(DateTime, default=func.now())
    update_datetime = Column(DateTime, default=func.now(), onupdate=func.now())
    status = Column(Integer, index=True)
    #  1: Chua co nguoi dang ki . 2 Da co nguoi dang ki. 

class Group(Base):
    __tablename__ = "group"
    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String, index=True)
    thesis_id = Column(UUID, nullable=True)  # Khóa luận được gán
    leader_id = Column(UUID, nullable=False)  # Người tạo nhóm (nhóm trưởng)
    create_datetime = Column(DateTime, default=func.now())

class GroupAdvisor(Base):
    __tablename__ = "group_advisor"
    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    group_id = Column(UUID)
    lecturer_id = Column(UUID)
    create_datetime = Column(DateTime, default=func.now())

class GroupStudent(Base):
    __tablename__ = "group_student"
    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    group_id = Column(UUID)
    student_id = Column(UUID)
    create_datetime = Column(DateTime, default=func.now())

class Invite(Base):
    __tablename__ = "invite"
    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    group_id = Column(UUID)
    sender_id = Column(UUID)  # Người gửi (nhóm trưởng)
    receiver_id = Column(UUID)  # Người nhận (thành viên)
    status = Column(Integer, default="pending")  # "pending", "accepted", "rejected"
    create_datetime = Column(DateTime, default=func.now())

class StudentScore(Base):
    __tablename__ = "student_score"
    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    group_id = Column(UUID)
    student_id = Column(UUID)
    lecturer_id = Column(UUID)
    score = Column(Float)  # Điểm của sinh viên
    score_type = Column(String)  # "process", "defense"
    create_datetime = Column(DateTime, default=func.now())








