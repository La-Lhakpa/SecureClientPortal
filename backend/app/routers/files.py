import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File as UploadFileType, HTTPException, status, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from .. import models, schemas
from ..dependencies import get_current_user
from ..database import get_db
from ..logger import setup_audit_logger


router = APIRouter(prefix="/files", tags=["files"])
audit_log = setup_audit_logger()
storage_dir = Path("storage")
storage_dir.mkdir(exist_ok=True)


@router.post("/send", response_model=schemas.FileUploadResponse)
def send_file(
    receiver_id: int = Form(...),
    file: UploadFile = UploadFileType(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Send a file to another user"""
    receiver = db.query(models.User).filter(models.User.id == receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    
    if receiver_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot send file to yourself")

    original_filename = file.filename or "file"
    safe_name = f"{uuid.uuid4().hex}_{Path(original_filename).name}"
    target_path = storage_dir / safe_name

    with target_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    size_bytes = target_path.stat().st_size
    file_record = models.File(
        sender_id=user.id,
        receiver_id=receiver_id,
        original_filename=original_filename,
        stored_path=str(target_path),
        size_bytes=size_bytes,
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    audit_log.info("file_send_success sender_id=%s receiver_id=%s file_id=%s size_bytes=%s", user.id, receiver_id, file_record.id, size_bytes)
    return file_record


@router.get("/sent", response_model=list[schemas.FileOut])
def list_sent_files(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """List files sent by current user"""
    files = db.query(models.File).filter(models.File.sender_id == user.id).all()
    return files


@router.get("/received", response_model=list[schemas.FileOut])
def list_received_files(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """List files received by current user"""
    files = db.query(models.File).filter(models.File.receiver_id == user.id).all()
    return files


@router.get("/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Download a file (only if user is sender or receiver)"""
    file_obj = db.query(models.File).filter(models.File.id == file_id).first()
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")

    # Only allow download if user is sender or receiver
    if file_obj.sender_id != user.id and file_obj.receiver_id != user.id:
        audit_log.info("download_denied user_id=%s file_id=%s", user.id, file_id)
        raise HTTPException(status_code=403, detail="Forbidden")

    path = Path(file_obj.stored_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing on server")

    audit_log.info("download_success user_id=%s file_id=%s", user.id, file_id)
    return FileResponse(path, filename=file_obj.original_filename, media_type="application/octet-stream")
