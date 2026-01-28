import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File as UploadFileType, HTTPException, status, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from .. import models, schemas
from ..dependencies import get_current_user
from ..database import get_db
from ..logger import setup_audit_logger
from ..config import get_settings


router = APIRouter(prefix="/files", tags=["files"])
audit_log = setup_audit_logger()


def _get_storage_dir() -> Path:
    settings = get_settings()
    backend_root = Path(__file__).resolve().parents[2]  # .../backend/app/routers -> .../backend
    storage_dir = Path(settings.storage_dir)
    if not storage_dir.is_absolute():
        storage_dir = backend_root / storage_dir
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


def _safe_original_name(name: str) -> str:
    # Never trust user-provided filename; keep only basename and strip odd chars
    base = Path(name).name or "file"
    # Basic sanitization: replace path separators and control chars
    base = base.replace("\\", "_").replace("/", "_").strip().strip(".")
    return base or "file"


def _stream_to_disk(upload: UploadFile, target_path: Path) -> int:
    # Stream upload to disk in chunks, return size_bytes
    size = 0
    chunk_size = 1024 * 1024  # 1MB
    with target_path.open("wb") as out:
        while True:
            chunk = upload.file.read(chunk_size)
            if not chunk:
                break
            out.write(chunk)
            size += len(chunk)
    return size


@router.post("/send", response_model=schemas.FileUploadResponse)
def send_file(
    receiver_id: int = Form(...),
    file: UploadFile = UploadFileType(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Send a file to another user"""
    # Server-side enforcement: cannot send to yourself
    if receiver_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot send file to yourself",
        )

    # Validate receiver exists
    receiver = db.query(models.User).filter(models.User.id == receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receiver not found")

    if not file:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="File is required")

    storage_dir = _get_storage_dir()
    original_filename = _safe_original_name(file.filename or "file")
    stored_filename = f"{uuid.uuid4().hex}_{original_filename}"
    target_path = storage_dir / stored_filename

    try:
        size_bytes = _stream_to_disk(file, target_path)
    finally:
        try:
            file.file.close()
        except Exception:
            pass

    content_type = getattr(file, "content_type", None)
    file_record = models.File(
        sender_id=user.id,
        receiver_id=receiver_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        stored_path=str(target_path),
        size_bytes=size_bytes,
        content_type=content_type,
    )
    db.add(file_record)
    db.commit()
    # Reload with relationships for response
    file_record = (
        db.query(models.File)
        .options(joinedload(models.File.sender), joinedload(models.File.receiver))
        .filter(models.File.id == file_record.id)
        .first()
    )
    audit_log.info("file_send_success sender_id=%s receiver_id=%s file_id=%s size_bytes=%s", user.id, receiver_id, file_record.id, size_bytes)
    return file_record


@router.get("/sent", response_model=list[schemas.FileOut])
def list_sent_files(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """List files sent by current user"""
    files = (
        db.query(models.File)
        .options(joinedload(models.File.sender), joinedload(models.File.receiver))
        .filter(models.File.sender_id == user.id)
        .order_by(models.File.created_at.desc())
        .all()
    )
    return files


@router.get("/received", response_model=list[schemas.FileOut])
def list_received_files(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """List files received by current user"""
    files = (
        db.query(models.File)
        .options(joinedload(models.File.sender), joinedload(models.File.receiver))
        .filter(models.File.receiver_id == user.id)
        .order_by(models.File.created_at.desc())
        .all()
    )
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

    storage_dir = _get_storage_dir()
    # Prefer stored_filename for safe path resolution; fallback to stored_path for legacy rows
    if getattr(file_obj, "stored_filename", None):
        path = (storage_dir / file_obj.stored_filename).resolve()
        if not path.is_relative_to(storage_dir.resolve()):
            raise HTTPException(status_code=404, detail="File missing on server")
    else:
        path = Path(file_obj.stored_path).resolve()

    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="File missing on server")

    audit_log.info("download_success user_id=%s file_id=%s", user.id, file_id)
    media_type = file_obj.content_type or "application/octet-stream"
    return FileResponse(path, filename=file_obj.original_filename, media_type=media_type)
