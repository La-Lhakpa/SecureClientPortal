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
    # Check if username already exists
    existing_username = db.query(models.User).filter(models.User.username == user_in.username).first()
    if existing_username:
        audit_log.info("register_failed username=%s reason=username_exists", user_in.username)
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email already exists
    existing_email = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing_email:
        audit_log.info("register_failed email=%s reason=email_exists", user_in.email)
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = models.User(
        username=user_in.username,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role.upper(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    audit_log.info("register_success user_id=%s username=%s role=%s", user.id, user.username, user.role)
    return user


@router.post("/login", response_model=schemas.Token)
def login(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    # Try to find user by username first, then by email
    user = db.query(models.User).filter(
        (models.User.username == user_in.username_or_email) | 
        (models.User.email == user_in.username_or_email)
    ).first()
    
    if not user or not verify_password(user_in.password, user.password_hash):
        audit_log.info("login_failed username_or_email=%s", user_in.username_or_email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    token = create_access_token({"sub": str(user.id), "role": user.role})
    audit_log.info("login_success user_id=%s username=%s", user.id, user.username)
    return schemas.Token(access_token=token)
