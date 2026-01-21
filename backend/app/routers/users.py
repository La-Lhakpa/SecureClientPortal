from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, models
from ..dependencies import get_current_user, role_required
from ..database import get_db


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=schemas.UserOut)
def read_me(user=Depends(get_current_user)):
    return user


@router.get("", response_model=list[schemas.UserOut], dependencies=[Depends(role_required("OWNER"))])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


@router.get("/clients", response_model=list[schemas.UserOut], dependencies=[Depends(role_required("OWNER"))])
def list_clients(db: Session = Depends(get_db)):
    return db.query(models.User).filter(models.User.role == "CLIENT").all()
