from datetime import datetime
import uuid
from sqlalchemy import UUID, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, func
from db.database import Base

class AcademyYear(Base):
    __tablename__ ='academy_year'
    id = Column(UUID , primary_key = True, default=uuid.uuid4,index= True)
    name = Column(String, nullable=False, index=True)
    start_date = Column(DateTime, nullable= False)
    end_date = Column(DateTime, nullable=False)
    create_datetime = Column(DateTime, default=func.now())
    update_datetime = Column(DateTime, default=func.now(), onupdate=func.now())

class Semester(Base):
    __tablename__ = 'semester'
    id = Column(UUID, primary_key=True, default=uuid.uuid4, index = True)
    academy_year_id = Column(UUID , nullable = False, index=  True)
    name = Column(String, nullable=False, index=True)
    start_date = Column(DateTime , nullable=False)
    end_date = Column(DateTime, nullable=False)
    create_datetime = Column(DateTime, default=func.now())
    update_datetime = Column(DateTime, default=func.now(), onupdate=func.now())

class Batch(Base):
    __tablename__ = 'batch'
    id = Column(UUID, primary_key=True, default=uuid.uuid4, index = True)
    semester_id = Column(UUID, nullable=False, index = True)
    name = Column(String, nullable=False, index= True)
    start_date = Column(DateTime, nullable= False)
    end_date = Column(DateTime, nullable=False)
    create_datetime = Column(DateTime, default=func.now())
    status = Column(Integer)
    update_datetime = Column(DateTime, default=func.now(), onupdate=func.now())

class User(Base):
    __tablename__ = "sys_user"
    id = Column(UUID, primary_key=True, index=True)
    user_name = Column(String, index=True)
    password = Column(String, index=True)
    is_active = Column(Boolean, index=True)
    user_type = Column(Integer, index=True) # 1: Admin, 2: Student, 3: Lecturer
    create_datetime = Column(DateTime, default=func.now())
    update_datetime = Column(DateTime, default=func.now(), onupdate=func.now())

class Information(Base):
    __tablename__ = 'information'
    id = Column(UUID, primary_key=True, default=uuid.uuid4,index = True)
    user_id = Column(UUID, nullable= False, index= True)
    first_name = Column(String,nullable=False,index= True)
    last_name = Column(String, nullable=False, index=True)
    date_of_birth = Column(DateTime, nullable=False)
    gender = Column(Integer,nullable=False)
    address = Column(String, nullable=False)
    tel_phone = Column(String, nullable=False)

class StudentInfo(Base):
    __tablename__ = 'student_info'
    id = Column(UUID, primary_key=True, default=uuid.uuid4, index = True)
    user_id = Column(UUID, nullable=False)
    student_code = Column(String, nullable=False, index = True)
    class_name = Column(String, index = True)
    major_id = Column(UUID, nullable=False)
    create_datetime = Column(DateTime, default=func.now())
    update_datetime = Column(DateTime, default=func.now(), onupdate=func.now())

class LecturerInfo(Base):
    __tablename__ = 'lecturer_info'
    id = Column(UUID, primary_key=True, default=uuid.uuid4, index = True)
    user_id = Column(UUID, nullable=False)
    lecturer_code = Column(UUID, nullable=False, index = True)
    department = Column(Integer)
    title = Column(String, nullable= False)
    phone = Column(String, nullable= False)
    email = Column(String, nullable= False)
    create_datetime = Column(DateTime, default=func.now())
    update_datetime = Column(DateTime, default=func.now(), onupdate=func.now())


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID, nullable=False)
    token = Column(String, nullable=False, index=True)  # Lưu refresh token
    access_token = Column(String, nullable=True, index=True)  # Lưu access token
    expires_at = Column(DateTime, nullable=False)  # Thời gian hết hạn của refresh token
    access_expires_at = Column(DateTime, nullable=True)  # Thời gian hết hạn của access token
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

class Major(Base):
    __tablename__ ="major"
    id = Column(UUID, primary_key=True, index =True)
    name = Column(String, index =True)

class SysRole(Base):
    __tablename__ = "sys_role"
    id = Column(Integer, primary_key=True, index=True)
    role_code = Column(String, unique=True, index=True, nullable=False) # Tương ứng với 'name' cũ, là mã định danh vai trò
    role_name = Column(String, nullable=False) # Tên vai trò dễ hiểu
    description = Column(String, nullable=True) # Mô tả chi tiết về vai trò
    status = Column(Integer, nullable=True) # Trạng thái của vai trò (ví dụ: 'active', 'inactive')
    create_datetime = Column(DateTime, default=func.now())
    created_by = Column(UUID, nullable=True) # Hoặc UUID
    update_datetime = Column(DateTime, default=func.now(), onupdate=func.now())

class SysFunction(Base):
    __tablename__ = "sys_function"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False) # Tên chức năng/nhóm chức năng (ví dụ: "Quản lý người dùng", "Xem báo cáo")
    path = Column(String, nullable=True) # Đường dẫn API (ví dụ: "/users/create") hoặc mã định danh cho GROUP
    type = Column(String, nullable=False) # Loại chức năng: "GROUP" hoặc "API"
    parent_id = Column(Integer, nullable=True) # ID của chức năng cha (nếu có)
    description = Column(String, nullable=True) # Mô tả chi tiết về chức năng
    status = Column(Integer, nullable=True) # Trạng thái của chức năng (ví dụ: 'enabled', 'disabled')
    create_datetime = Column(DateTime, default=func.now())
    created_by = Column(UUID, nullable=True) # Hoặc UUID
    update_datetime = Column(DateTime, default=func.now(), onupdate=func.now())

class SysUserRole(Base):
    __tablename__ = "sys_user_role"
    id = Column(Integer, primary_key=True, index=True) # Khóa chính của bảng liên kết
    user_id = Column(UUID,  nullable=False) # Khóa ngoại tới bảng người dùng (sys_user)
    role_id = Column(Integer,  nullable=False) # Khóa ngoại tới bảng vai trò (sys_role)
    created_by = Column(UUID, nullable=True) # Hoặc UUID tùy theo kiểu id người dùng
    create_datetime = Column(DateTime, default=func.now())


class SysRoleFunction(Base):
    __tablename__ = "sys_role_function"
    id = Column(Integer, primary_key=True, index=True) # Khóa chính của bảng liên kết
    role_id = Column(Integer, ForeignKey("sys_role.id"), nullable=False) # Khóa ngoại tới bảng vai trò (sys_role)
    function_id = Column(Integer, ForeignKey("sys_function.id"), nullable=False) # Khóa ngoại tới bảng chức năng (sys_function)
    status = Column(Integer, nullable=True)
    created_by = Column(UUID, nullable=True) # Hoặc UUID
    create_datetime = Column(DateTime, default=func.now())

# class SysRole(Base):
#     __tablename__ = "sys_role"
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, unique=True, index=True)  # admin, user, lecture
#     create_datetime = Column(DateTime, default=func.now())
#     update_datetime = Column(DateTime, default=func.now(), onupdate=func.now())

# class SysFunction(Base):
#     __tablename__ = "sys_function"
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, unique=True, index=True)  # API path, e.g., "/thesis/propose"
#     create_datetime = Column(DateTime, default=func.now())
#     update_datetime = Column(DateTime, default=func.now(), onupdate=func.now())

# class SysUserRole(Base):
#     __tablename__ = "sys_user_role"
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(UUID, nullable=False)
#     role_id = Column(Integer,nullable=False)

# class SysRoleFunction(Base):
#     __tablename__ = "sys_role_function"
#     id = Column(Integer, primary_key=True, index=True)
#     role_id = Column(Integer,nullable=False)
#     function_id = Column(Integer,nullable=False)

class Thesis(Base):
    __tablename__ = "thesis"
    id = Column(UUID, primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    thesis_type = Column(Integer, nullable=False)
    create_by  = Column(UUID, nullable=False)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    create_datetime = Column(DateTime, default=func.now())
    update_datetime = Column(DateTime, default=func.now(), onupdate=func.now())
    status = Column(Integer, index=True)
    #  1: Chua co nguoi dang ki . 2 Da co nguoi dang ki. 

class ThesisLecturer(Base):
    __tablename__ = 'thesis_lecturer'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    lecturer_id = Column(UUID, nullable=False)
    thesis_id = Column(UUID, nullable=False)
    role = Column(Integer)
    create_datetime = Column(DateTime, default=func.now())

class ScoreType(Base):
    __tablename__ = 'score_type'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String)

class Group(Base):
    __tablename__ = "group"
    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String, index=True)
    leader_id = Column(UUID, nullable=False)  # Người tạo nhóm (nhóm trưởng)
    quantity = Column(Integer, nullable=False)
    create_datetime = Column(DateTime, default=func.now())
    update_datetime = Column(DateTime, default=func.now(), onupdate=func.now())

class GroupMember(Base):
    __tablename__ = "group_member"
    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    group_id = Column(UUID)
    student_id = Column(UUID)
    is_leader = Column(Boolean, nullable=True)
    join_date  = Column(DateTime, default=func.now())

class ThesisGroup(Base):
    __tablename__ = 'thesis_group'
    id = Column(UUID , primary_key=True,default=uuid.uuid4)
    thesis_id = Column(UUID, nullable=False)
    group_id = Column(UUID, nullable=False)
    
class Invite(Base):
    __tablename__ = 'invite'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    sender_id  = Column(UUID, nullable=False)
    receiver_id  = Column(UUID, nullable=False)
    group_id = Column(UUID, nullable=False)
    status = Column(Integer) #  1.Dang cho 2. Duoc chap nhan 3. Tu choi
    create_datetime = Column(DateTime, default=func.now())
    update_datetime = Column(DateTime, default=func.now(), onupdate=func.now())

class ThesisCommittee(Base):
    __tablename__ = 'thesis_committee'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    thesis_id  = Column(UUID, nullable=False)
    member_id  = Column(UUID, nullable=False)
    role = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())

class ThesisMemberScore(Base):
    __tablename__ = "thesis_member_score"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thesis_id = Column(UUID(as_uuid=True))
    student_id = Column(UUID(as_uuid=True))
    evaluator_id = Column(UUID(as_uuid=True))
    score = Column(Float, nullable=False)
    score_type = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())











