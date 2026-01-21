import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File as UploadFileType, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from .. import models, schemas
from ..dependencies import get_current_user, role_required
from ..database import get_db
from ..logger import setup_audit_logger


router = APIRouter(prefix="/files", tags=["files"])
audit_log = setup_audit_logger()
storage_dir = Path("storage")
storage_dir.mkdir(exist_ok=True)


@router.post("/send", response_model=schemas.FileUploadResponse, dependencies=[Depends(role_required("OWNER"))])
def send_file(
    client_id: int,
    upload: UploadFile = UploadFileType(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    client = db.query(models.User).filter(models.User.id == client_id, models.User.role == "CLIENT").first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    original_filename = upload.filename or "file"
    safe_name = f"{uuid.uuid4().hex}_{Path(original_filename).name}"
    target_path = storage_dir / safe_name

    with target_path.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    size_bytes = target_path.stat().st_size
    file_record = models.File(
        owner_id=user.id,
        client_id=client_id,
        original_filename=original_filename,
        stored_path=str(target_path),
        size_bytes=size_bytes,
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    audit_log.info("file_send_success user_id=%s client_id=%s file_id=%s size_bytes=%s", user.id, client_id, file_record.id, size_bytes)
    return file_record


@router.get("", response_model=list[schemas.FileOut])
def list_files(db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role == "OWNER":
        files = db.query(models.File).all()
    else:
        files = db.query(models.File).filter(models.File.client_id == user.id).all()
    return files


@router.get("/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    file_obj = db.query(models.File).filter(models.File.id == file_id).first()
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")

    if user.role != "OWNER" and file_obj.client_id != user.id:
        audit_log.info("download_denied user_id=%s file_id=%s", user.id, file_id)
        raise HTTPException(status_code=403, detail="Forbidden")

    path = Path(file_obj.stored_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing on server")

    audit_log.info("download_success user_id=%s file_id=%s", user.id, file_id)
    return FileResponse(path, filename=file_obj.original_filename, media_type="application/octet-stream")
