from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models.model import SysFunction,SysRole, SysRoleFunction, SysUserRole, User, RefreshToken
from schemas.sysuser import UserBase, UserCreate, UserLogin, UserResponse
from auth.authentication import create_access_token, create_refresh_token,SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,REFRESH_TOKEN_EXPIRE_DAYS, ACCESS_TOKEN_EXPIRE_MINUTES
import bcrypt
import jwt 
from datetime import datetime, timedelta
from db.database import get_db
from services.sysuser import create_user
from fastapi import Request

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Ưu tiên token từ header Authorization
    if token:
        print("Token from header:", token)  # Log token từ header
    else:
        # Nếu không có token trong header, đọc từ cookie
        token = request.cookies.get("access_token")
        print("Token from cookie:", token)  # Log token từ cookie

    # Kiểm tra nếu không có token từ cả hai nguồn
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token not found")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("Payload:", payload)  # Log payload
        user_id: str = payload.get("uuid")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired, please log in again")
    except jwt.PyJWTError as e:
        print("JWT Error:", str(e))  # Log lỗi JWT
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token, please log in again")

class PathChecker:
    def __init__(self, allowed_path: str):
        self.allowed_path = allowed_path
    def __call__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        # 1. Lấy các role_id đang hoạt động của người dùng
        user_active_roles = db.query(SysUserRole.role_id)\
            .join(SysRole, SysUserRole.role_id == SysRole.id)\
            .filter(SysUserRole.user_id == user.id, SysRole.status == 1)\
            .all() # Giả sử status == 1 là vai trò hoạt động

        role_ids = [role.role_id for role in user_active_roles]

        if not role_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no active assigned roles or no roles at all."
            )

        # 2. Tìm chức năng (function) đang hoạt động tương ứng với allowed_path
        function = db.query(SysFunction).filter(
            SysFunction.path == self.allowed_path,
            SysFunction.status == 1 # Giả sử status == 1 là chức năng hoạt động
        ).first()

        if not function:
            # Có thể lỗi do path không tồn tại, hoặc function không hoạt động
            # Cân nhắc trả về thông báo lỗi cụ thể hơn nếu muốn
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access to path {self.allowed_path} is forbidden or function is not active/defined."
            )

        # 3. Kiểm tra xem vai trò của người dùng có quyền truy cập chức năng (và quyền đó đang hoạt động)
        role_function = db.query(SysRoleFunction).filter(
            SysRoleFunction.function_id == function.id,
            SysRoleFunction.role_id.in_(role_ids),
            SysRoleFunction.status == 1 # Giả sử status == 1 là quyền gán đang hoạt động
        ).first()

        if not role_function:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have active permission to access {self.allowed_path}"
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
    # Kiểm tra người dùng đã tồn tại
    existing_user = db.query(User).filter(User.user_name == user.user_name).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this username already exists")

    # Tạo người dùng mới
    try:
        db_user = create_user(db, user)

        # Xác định vai trò dựa trên user_type
        role_name = ""
        if user.user_type == 1:
            role_name = "admin"      # Quản trị viên
        elif user.user_type == 2:
            role_name = "user"       # Sinh viên
        elif user.user_type == 3:
            role_name = "lecture"    # Giảng viên
        else:
            raise HTTPException(status_code=400, detail="Invalid user type")

        # Lấy vai trò từ bảng SysRole
        default_role = db.query(SysRole).filter(SysRole.name == role_name).first()

        # Nếu không tìm thấy role_name, gán role mặc định là "admin"
        if not default_role:
            default_role = db.query(SysRole).filter(SysRole.id == 1).first()

        # Gán vai trò mặc định cho người dùng
        if default_role:
            user_role = SysUserRole(user_id=db_user.id, role_id=default_role.id)
            db.add(user_role)
            db.commit()
            db.refresh(db_user)

        return db_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
def login(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Xử lý đăng nhập và cấp token"""
    db_user = db.query(User).filter(User.user_name == user.user_name).first()

    # Kiểm tra nếu không tìm thấy người dùng
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Kiểm tra mật khẩu
    if not bcrypt.checkpw(user.password.encode('utf-8'), db_user.password.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Thu hồi tất cả các token cũ chưa được đánh dấu
    db.query(RefreshToken).filter(
        RefreshToken.user_id == db_user.id,
        RefreshToken.is_revoked == False
    ).update({"is_revoked": True})
    db.commit()

    # Tạo access token và refresh token mới
    access_token = create_access_token(user_id=str(db_user.id), user_name=db_user.user_name)
    refresh_token = create_refresh_token(user_id=str(db_user.id), user_name=db_user.user_name)

    # Lưu token mới vào cơ sở dữ liệu
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db_refresh_token = RefreshToken(
        user_id=db_user.id,
        token=refresh_token,
        expires_at=expires_at,
        is_revoked=False
    )
    db.add(db_refresh_token)
    db.commit()

    # Lưu token vào cookie
    response.set_cookie(
        key="access_token",
        value=access_token.decode('utf-8') if isinstance(access_token, bytes) else access_token,
        httponly=True,
        secure=True,
        samesite="None",
        max_age=60 * 60  # 1 giờ
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token.decode('utf-8') if isinstance(refresh_token, bytes) else refresh_token,
        httponly=True,
        secure=True,
        samesite="None",
        max_age=7 * 24 * 60 * 60  # 7 ngày
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.post("/refresh")
def refresh_token(response: Response, refresh_token: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Làm mới access token"""
    try:
        # Giải mã token từ refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: user ID not found"
            )

        # Kiểm tra token trong cơ sở dữ liệu
        db_refresh_token = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        ).first()

        if not db_refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked refresh token"
            )

        # Tạo access token mới
        access_token = create_access_token(user_id=str(user.id), user_name=user.user_name)

        # Cập nhật token vào cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="None",
            max_age=60 * 60  # 1 giờ
        )

        return {
            "message": "Token refreshed successfully",
            "access_token": access_token
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )

@router.post("/logout", dependencies=[Depends(PathChecker("/auth/logout"))])
def logout(response: Response, refresh_token: str = Depends(oauth2_scheme), db: Session = Depends(get_db), user: User = Depends(PathChecker("/auth/logout"))):
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