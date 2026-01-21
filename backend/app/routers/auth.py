from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import schemas, models
from ..database import get_db
from ..security import verify_password, get_password_hash, create_access_token
from ..logger import setup_audit_logger


router = APIRouter(prefix="/auth", tags=["auth"])
audit_log = setup_audit_logger()


@router.post("/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role.upper(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
def login(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    audit_log.info("login_success user_id=%s", user.id)
    return schemas.Token(access_token=token)
