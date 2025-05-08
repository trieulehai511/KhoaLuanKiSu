from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.model import User
from schemas.sysuser import User as UserSchema, UserCreate
from services.sysuser import create_user
from db.database import get_db

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post("/", response_model=UserSchema)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.user_name == user.user_name).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this username already exists")
    db_user = create_user(db, user)

    return "Registed successfully"

