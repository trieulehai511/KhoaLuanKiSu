from fastapi import APIRouter, Body, Cookie, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models.model import SysFunction,SysRole, SysRoleFunction, SysUserRole, User, RefreshToken
from schemas.sysuser import AdminChangePasswordRequest, ChangePasswordRequest, UserBase, UserCreate, UserLogin, UserResponse
from auth.authentication import create_access_token, create_refresh_token,SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,REFRESH_TOKEN_EXPIRE_DAYS, ACCESS_TOKEN_EXPIRE_MINUTES
import bcrypt
import jwt 
from datetime import datetime, timedelta
from db.database import get_db
from services.sysuser import create_user
from fastapi import Request
import jwt
from jwt import decode as jwt_decode
from jwt.exceptions import ExpiredSignatureError,InvalidTokenError
router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)
import hashlib
from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def get_current_user(request: Request, db: Session = Depends(get_db)):
    # Lấy token từ header hoặc cookie
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        print("🔐 Token from header:", token)
    else:
        token = request.cookies.get("access_token")
        token = token.decode("utf-8") if isinstance(token, bytes) else token
        print("🍪 Token from cookie:", token)

    if not token:
        raise HTTPException(status_code=401, detail="Token not found")

    try:
        payload = jwt_decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": True}
        )
        print("✅ Token hợp lệ:", payload)

    except ExpiredSignatureError:
        print("🔥 Token expired — sẽ trả 410")
        raise HTTPException(status_code=410, detail="Token has expired")

    except InvalidTokenError as e:
        print(f"❌ InvalidTokenError: {type(e).__name__} - {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    # Lấy user từ DB
    user_id = payload.get("uuid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

class PathChecker:
    def __init__(self, allowed_path: str):
        self.allowed_path = allowed_path

    def __call__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        user_roles = db.query(SysUserRole.role_id)\
            .join(SysRole, SysUserRole.role_id == SysRole.id)\
            .filter(SysUserRole.user_id == user.id, SysRole.status == 1)\
            .all()

        role_ids = [r.role_id for r in user_roles]
        if not role_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn chưa được gán quyền hoặc tất cả quyền đã bị vô hiệu hóa."
            )
        function = db.query(SysFunction).filter(
            SysFunction.path == self.allowed_path,
            SysFunction.status == 1  
        ).first()

        if not function:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Đường dẫn [{self.allowed_path}] không tồn tại hoặc đã bị khóa."
            )
        allowed = db.query(SysRoleFunction).filter(
            SysRoleFunction.function_id == function.id,
            SysRoleFunction.role_id.in_(role_ids),
            SysRoleFunction.status == 1 
        ).first()

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Bạn không có quyền truy cập chức năng tại: {self.allowed_path}"
            )
        return user

# class PathChecker:
#     def __init__(self, allowed_path: str):
#         self.allowed_path = allowed_path
#     def __call__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
#         user_roles = db.query(SysUserRole).filter(SysUserRole.user_id == user.id).all()
#         role_ids = [user_role.role_id for user_role in user_roles]

#         if not role_ids:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="User has no assigned roles"
#             )
#         # Tìm chức năng (function) tương ứng với allowed_path
#         function = db.query(SysFunction).filter(SysFunction.path == self.allowed_path).first()
#         if not function:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail=f"Function for path {self.allowed_path} not defined"
#             )
#         # Kiểm tra xem vai trò của người dùng có quyền truy cập chức năng không
#         role_function = db.query(SysRoleFunction).filter(
#             SysRoleFunction.function_id == function.id,
#             SysRoleFunction.role_id.in_(role_ids)
#         ).first()
#         if not role_function:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail=f"User does not have permission to access {self.allowed_path}"
#             )

#         return user  # Trả về user để sử dụng trong endpoint

@router.post("/register", response_model=UserResponse)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.user_name == user.user_name).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this username already exists")
    try:
        db_user = create_user(db, user)

        # Xác định role_code và user_type_name
        role_map = {
            1: ("admin", "Admin"),
            2: ("user", "Student"),
            3: ("lecture", "Lecturer")
        }

        if user.user_type not in role_map:
            raise HTTPException(status_code=400, detail="Invalid user type")

        role_code, user_type_name = role_map[user.user_type]

        # Tìm role trong bảng
        default_role = db.query(SysRole).filter(SysRole.role_code == role_code).first()
        if not default_role:
            default_role = db.query(SysRole).filter(SysRole.id == 1).first()

        if default_role:
            user_role = SysUserRole(user_id=db_user.id, role_id=default_role.id)
            db.add(user_role)
            db.commit()
            db.refresh(db_user)

        # Tạo dict từ db_user và thêm user_type_name
        user_dict = db_user.__dict__.copy()
        user_dict["user_type_name"] = user_type_name

        return UserResponse(**user_dict)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
def login(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Xử lý đăng nhập và cấp token"""
    db_user = db.query(User).filter(User.user_name == user.user_name).first()

    if not db_user or not bcrypt.checkpw(user.password.encode('utf-8'), db_user.password.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    db.query(RefreshToken).filter(
        RefreshToken.user_id == db_user.id,
        RefreshToken.is_revoked == False
    ).update({"is_revoked": True})
    db.commit()
    access_token = create_access_token(user_id=str(db_user.id),user_type = db_user.user_type, user_name=db_user.user_name,db=db)
    refresh_token = create_refresh_token(user_id=str(db_user.id), user_name=db_user.user_name)
    
    hashed_refresh_token = hashlib.sha256(refresh_token).hexdigest()
    access_expires_at = datetime.utcnow() + timedelta(seconds=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    db_refresh_token = RefreshToken(
        user_id=db_user.id,
        token=hashed_refresh_token,
        access_token=access_token,
        expires_at=refresh_expires_at,
        access_expires_at=access_expires_at,
        is_revoked=False
    )
    db.add(db_refresh_token)
    db.commit()
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,      
        samesite="None",    
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES*60+600
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token.decode('utf-8') if isinstance(refresh_token, bytes) else refresh_token,
        httponly=True,
        secure=True,
        samesite="None",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60 
    )
    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token
    }

@router.post("/refresh")
def refresh_token(
    response: Response,
    refresh_token_from_request: str = Cookie(None, alias="refresh_token"),
    db: Session = Depends(get_db)
):
    if not refresh_token_from_request:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )

    try:
        payload = jwt_decode(
            refresh_token_from_request,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": True}
        )
        user_id = payload.get("uuid")
        user_name = payload.get("name")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token payload")

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token has expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    hashed_input_token = hashlib.sha256(refresh_token_from_request.encode()).hexdigest()
    db_refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == hashed_input_token,
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()

    if not db_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, revoked, or expired refresh token"
        )

    user = db.query(User).filter(User.id == db_refresh_token.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    access_token = create_access_token(
        user_id=str(user.id),
        user_name=user.user_name,
        user_type=user.user_type,
        db=db 
    )
    access_expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    db_refresh_token.access_token = access_token
    db_refresh_token.access_expires_at = access_expires_at

    extend_refresh = False
    if db_refresh_token.expires_at - datetime.utcnow() < timedelta(days=1):
        new_refresh_token = create_refresh_token(user_id=str(user.id), user_name=user.user_name)
        db_refresh_token.token = hashlib.sha256(new_refresh_token.encode()).hexdigest()
        db_refresh_token.expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        extend_refresh = True

    db.commit()

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="None",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60 + 600
    )

    if extend_refresh:
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="None",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )

    return {
        "message": "Token refreshed successfully",
        "access_token": access_token
    }

@router.post("/logout" )
def logout(response: Response, refresh_token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Xử lý đăng xuất"""
    db_refresh_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if db_refresh_token:
        db_refresh_token.is_revoked = True
        db.commit()
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse, dependencies=[Depends(PathChecker("/auth/me"))])
def get_current_user_info(user: User = Depends(PathChecker("/auth/me"))):
    """Lấy thông tin người dùng hiện tại"""
    return user

@router.get("/protected", dependencies=[Depends(PathChecker("/auth/protected"))])
def protected_route(user: User = Depends(PathChecker("/auth/protected"))):
    """Endpoint bảo vệ, yêu cầu xác thực"""
    return {"message": f"Hello, {user.user_name}"}

@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    db_user = db.query(User).filter(User.id == user.id).first()
    if not db_user or not bcrypt.checkpw(data.old_password.encode('utf-8'), db_user.password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Old password is incorrect")

    hashed_new_password = bcrypt.hashpw(data.new_password.encode('utf-8'), bcrypt.gensalt()).decode("utf-8")
    db_user.password = hashed_new_password
    db.commit()
    return {"message": "Password updated successfully"}

#   dependencies=[Depends(PathChecker(""))]
@router.post("/admin-change-password",dependencies=[Depends(PathChecker("/auth/admin-change-password"))])
def admin_change_password(
    data: AdminChangePasswordRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    db_user = db.query(User).filter(User.id == data.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = bcrypt.hashpw(data.new_password.encode('utf-8'), bcrypt.gensalt()).decode("utf-8")
    db_user.password = hashed_password
    db.commit()
    return {"message": f"Password updated for user {db_user.user_name}"}
