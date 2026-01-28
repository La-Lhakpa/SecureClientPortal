from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from .. import schemas, models
from ..dependencies import get_current_user
from ..database import get_db


router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[schemas.UserPublic])
def list_users(
    q: str | None = Query(default=None, description="Optional email search query"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """
    List users for recipient dropdown.
    Excludes the currently authenticated user.
    Returns only public fields (id, email).
    """
    query = db.query(models.User).filter(models.User.id != user.id)

    if q:
        q_norm = q.strip()
        if q_norm:
            query = query.filter(models.User.email.ilike(f"%{q_norm}%"))

    return query.order_by(models.User.email.asc()).all()
