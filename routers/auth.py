from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models.model import SysFunction,SysRole, SysRoleFunction, SysUserRole, User, RefreshToken
from schemas.sysuser import UserCreate, UserLogin, User as UserSchema
from auth.authentication import create_access_token, create_refresh_token,SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,REFRESH_TOKEN_EXPIRE_DAYS, ACCESS_TOKEN_EXPIRE_MINUTES
import bcrypt
import jwt
from datetime import datetime, timedelta
from db.database import get_db
from services.sysuser import create_user

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db), response: Response = None):
    if not token and response:
        token = response.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token not found")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired, please log in again")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token, please log in again")



class PathChecker:
    def __init__(self, allowed_path: str):
        self.allowed_path = allowed_path
    def __call__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        user_roles = db.query(SysUserRole).filter(SysUserRole.user_id == user.id).all()
        role_ids = [user_role.role_id for user_role in user_roles]

        if not role_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned roles"
            )
        # Tìm chức năng (function) tương ứng với allowed_path
        function = db.query(SysFunction).filter(SysFunction.name == self.allowed_path).first()
        if not function:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Function for path {self.allowed_path} not defined"
            )
        # Kiểm tra xem vai trò của người dùng có quyền truy cập chức năng không
        role_function = db.query(SysRoleFunction).filter(
            SysRoleFunction.function_id == function.id,
            SysRoleFunction.role_id.in_(role_ids)
        ).first()
        if not role_function:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have permission to access {self.allowed_path}"
            )

        return user  # Trả về user để sử dụng trong endpoint

@router.post("/register", response_model=UserSchema)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.user_name == user.user_name).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this username already exists")
    
    db_user = create_user(db, user)
    role_name = "lecture" if user.is_lecturer else "user"
    default_role = db.query(SysRole).filter(SysRole.name == role_name).first()
    
    if default_role:
        user_role = SysUserRole(user_id=db_user.id, role_id=default_role.id)
        db.add(user_role)
        db.commit()
        
    return db_user

@router.post("/login")
def login(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Xử lý đăng nhập và cấp token"""
    db_user = db.query(User).filter(User.user_name == user.user_name).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not bcrypt.checkpw(user.password.encode('utf-8'), db_user.password.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Thu hồi tất cả refresh token cũ để đảm bảo chỉ có một phiên đăng nhập
    db.query(RefreshToken).filter(RefreshToken.user_id == db_user.id).update({"is_revoked": True})
    db.commit()
    
    # Tạo access token và refresh token
    access_token = create_access_token(user_id=str(db_user.id), user_name=db_user.user_name)
    refresh_token = create_refresh_token(user_id=str(db_user.id), user_name=db_user.user_name)
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
        value=access_token,
        httponly=True,
        secure=True,  
        samesite="None",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
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

@router.post("/refresh", dependencies=[Depends(PathChecker("/auth/refresh"))])
def refresh_token(response: Response, refresh_token: str = Depends(oauth2_scheme), db: Session = Depends(get_db), user: User = Depends(PathChecker("/auth/refresh"))):
    """Làm mới access token"""
    try:
        db_refresh_token = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        ).first()
        
        if not db_refresh_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or revoked refresh token")
        
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id or str(db_refresh_token.user_id) != user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        
        access_token = create_access_token(data={"sub": user_id})
        
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        return {"message": "Token refreshed successfully"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

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

@router.get("/me", response_model=UserSchema, dependencies=[Depends(PathChecker("/auth/me"))])
def get_current_user_info(user: User = Depends(PathChecker("/auth/me"))):
    """Lấy thông tin người dùng hiện tại"""
    return user

@router.get("/protected", dependencies=[Depends(PathChecker("/auth/protected"))])
def protected_route(user: User = Depends(PathChecker("/auth/protected"))):
    """Endpoint bảo vệ, yêu cầu xác thực"""
    return {"message": f"Hello, {user.user_name}"}