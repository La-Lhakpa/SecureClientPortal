from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, models
from ..dependencies import get_current_user
from ..database import get_db


router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """List all users (for receiver dropdown)"""
    return db.query(models.User).all()
