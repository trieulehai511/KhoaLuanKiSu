import uuid
import bcrypt
from sqlalchemy.orm import Session
from models.model import User
from schemas.sysuser import UserCreate


def create_user(db: Session, user: UserCreate):
    # Nếu không phải lecturer, gán password bằng user_name
    if not user.is_lecturer:
        user.password = user.user_name  
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Tạo đối tượng người dùng
    db_user = User(
        id=uuid.uuid4(),
        user_name=user.user_name,
        password=hashed_password,
        is_active=user.is_active if user.is_active is not None else True,
        is_lecturer=user.is_lecturer if user.is_lecturer is not None else False,
        major=user.major
    )

    # Thêm vào cơ sở dữ liệu
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

