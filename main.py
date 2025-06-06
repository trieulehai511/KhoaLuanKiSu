from fastapi import FastAPI
from db.database import Base, engine
from routers import academy, auth, group, information, invite, lecturer_profile, student_profile, sys_role, sys_role_function, sys_user_role, sysuser, thesis, function
from fastapi.middleware.cors import CORSMiddleware
import logging
from fastapi_jwt_auth import AuthJWT
from auth.authentication import SECRET_KEY

Base.metadata.create_all(bind=engine)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
app = FastAPI()


origins = [
    "http://localhost:3000",  
    "https://your-frontend-domain.com",
    "http://localhost:3039",
    "http://192.168.56.1:3039",
    "http://localhost:3040",
    "http://localhost:3041"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins= origins, 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"], 
)
# Cấu hình AuthJWT
@app.on_event("startup")
async def startup():
    AuthJWT.load_config(lambda: [
        ("authjwt_secret_key", SECRET_KEY),
        ("authjwt_token_location", ["cookies"]),  # Chỉ định token được tìm trong cookies
        ("authjwt_cookie_csrf_protect", False),   # Tắt CSRF protection cho cookies nếu không cần thiết hoặc xử lý riêng                                              # Cân nhắc bật True cho production và xử lý CSRF token
        ("authjwt_access_token_expires", 1800),   # Thời gian hết hạn của access token (30 phút)
        ("authjwt_refresh_token_expires", 604800), # Thời gian hết hạn của refresh token (7 ngày)
    ])
    logger.info("AuthJWT configured successfully")


# List các router. Thêm router nào ghi vô
list_router = [
    sysuser.router,
    auth.router,
    thesis.router,
    group.router,
    invite.router,
    information.router,
    sys_role.router,
    function.router,
    sys_user_role.router,
    sys_role_function.router,
    academy.router,
    student_profile.router,
    lecturer_profile.router
]
for router in list_router:
    app.include_router(router)