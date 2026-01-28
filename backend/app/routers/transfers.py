import secrets
import string
from datetime import datetime
from datetime import timezone
from email.utils import format_datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File as UploadFileType, Form, Header, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import func, case
from sqlalchemy.orm import Session, joinedload

from zipstream import ZipStream, ZIP_STORED

from .. import models, schemas
from ..config import get_settings
from ..database import get_db
from ..dependencies import get_current_user
from ..logger import setup_audit_logger
from ..core.security import (
    hash_access_code,
    verify_access_code,
    create_transfer_access_token,
    decode_transfer_access_token,
)


router = APIRouter(prefix="/transfers", tags=["transfers"])
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
    base = Path(name).name or "file"
    base = base.replace("\\", "_").replace("/", "_").strip().strip(".")
    return base or "file"


def _stream_to_disk(upload: UploadFile, target_path: Path) -> int:
    size = 0
    chunk_size = 1024 * 1024
    with target_path.open("wb") as out:
        while True:
            chunk = upload.file.read(chunk_size)
            if not chunk:
                break
            out.write(chunk)
            size += len(chunk)
    return size


def _validate_access_code(code: str) -> str:
    code = (code or "").strip()
    if len(code) < 6:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Access code must be at least 6 characters")
    # allow alphanumeric only (simple policy)
    if not all(ch.isalnum() for ch in code):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Access code must be alphanumeric")
    return code


def _generate_access_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    # avoid ambiguous characters
    alphabet = alphabet.replace("O", "").replace("0", "").replace("I", "").replace("1", "")
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _make_code_hint(code: str) -> str:
    # Do not store full code. Provide minimal hint (last 2 chars + length).
    if len(code) < 2:
        return f"len:{len(code)}"
    return f"len:{len(code)} ends:{code[-2:]}"


def _require_receiver_transfer_token(
    transfer_id: int,
    current_user: models.User,
    token: Optional[str],
) -> None:
    if not token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Transfer access token required")
    payload = decode_transfer_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired transfer access token")
    if str(payload.get("tid")) != str(transfer_id) or str(payload.get("rid")) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Transfer access token does not match")


@router.post("/send", response_model=schemas.TransferSendResponse)
def send_transfer(
    receiver_id: int = Form(...),
    access_code: str = Form(""),
    files: List[UploadFile] = UploadFileType(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if receiver_id == user.id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot send transfer to yourself")

    receiver = db.query(models.User).filter(models.User.id == receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receiver not found")

    if not files or len(files) == 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="At least one file is required")

    generated_code: Optional[str] = None
    if access_code and access_code.strip():
        access_code = _validate_access_code(access_code)
    else:
        generated_code = _generate_access_code()
        access_code = generated_code

    access_code_hash = hash_access_code(access_code)
    code_hint = _make_code_hint(access_code)

    storage_dir = _get_storage_dir()
    written_paths: list[Path] = []

    try:
        transfer = models.Transfer(
            sender_id=user.id,
            receiver_id=receiver_id,
            access_code_hash=access_code_hash,
            code_hint=code_hint,
            status="pending",
            failed_attempts=0,
        )
        db.add(transfer)
        db.flush()  # assigns transfer.id

        for upload in files:
            if not upload:
                continue
            original = _safe_original_name(upload.filename or "file")
            stored_filename = f"{secrets.token_hex(16)}_{original}"
            target = storage_dir / stored_filename
            try:
                size_bytes = _stream_to_disk(upload, target)
            finally:
                try:
                    upload.file.close()
                except Exception:
                    pass
            written_paths.append(target)

            tf = models.TransferFile(
                transfer_id=transfer.id,
                original_filename=original,
                stored_filename=stored_filename,
                stored_path=str(target),
                size_bytes=size_bytes,
                content_type=getattr(upload, "content_type", None),
            )
            db.add(tf)

        if not written_paths:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="At least one file is required")

        db.commit()
        db.refresh(transfer)
        audit_log.info("transfer_send_success sender_id=%s receiver_id=%s transfer_id=%s file_count=%s", user.id, receiver_id, transfer.id, len(written_paths))

        resp = schemas.TransferSendResponse(
            transfer_id=transfer.id,
            receiver=schemas.UserPublic(id=receiver.id, email=receiver.email),
            file_count=len(written_paths),
            created_at=transfer.created_at,
            generated_access_code=generated_code,
        )
        return resp
    except HTTPException:
        db.rollback()
        for p in written_paths:
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass
        raise
    except Exception as e:
        db.rollback()
        for p in written_paths:
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass
        audit_log.error("transfer_send_failed sender_id=%s receiver_id=%s error=%s", user.id, receiver_id, str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send transfer")


@router.post("/{transfer_id}/verify", response_model=schemas.TransferVerifyResponse)
def verify_transfer(
    transfer_id: int,
    payload: schemas.TransferVerifyRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    transfer = db.query(models.Transfer).filter(models.Transfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

    if transfer.receiver_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if transfer.expires_at and transfer.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Transfer expired")

    if transfer.failed_attempts >= 5:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts. Try again later.")

    code = _validate_access_code(payload.access_code)
    ok = verify_access_code(code, transfer.access_code_hash)
    if not ok:
        transfer.failed_attempts += 1
        db.commit()
        audit_log.info("transfer_verify_failed transfer_id=%s receiver_id=%s attempts=%s", transfer_id, user.id, transfer.failed_attempts)
        if transfer.failed_attempts >= 5:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts. Try again later.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid code")

    transfer.status = "opened"
    transfer.opened_at = datetime.utcnow()
    transfer.failed_attempts = 0
    db.commit()

    token = create_transfer_access_token(transfer_id=transfer.id, receiver_id=user.id, expires_minutes=15)
    audit_log.info("transfer_verify_success transfer_id=%s receiver_id=%s", transfer_id, user.id)
    return schemas.TransferVerifyResponse(verified=True, transfer_access_token=token, failed_attempts=0)


@router.get("/incoming/count", response_model=schemas.IncomingCountResponse)
def incoming_count(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    # Count transfers pending that still have at least one visible file for receiver
    visible_count = func.sum(
        case((models.TransferFile.receiver_deleted_at.is_(None), 1), else_=0)
    )
    q = (
        db.query(models.Transfer.id)
        .outerjoin(models.TransferFile, models.TransferFile.transfer_id == models.Transfer.id)
        .filter(models.Transfer.receiver_id == user.id, models.Transfer.status == "pending")
        .group_by(models.Transfer.id)
        .having(visible_count > 0)
    )
    return schemas.IncomingCountResponse(count=q.count())


@router.get("/received", response_model=list[schemas.TransferListItem])
def list_received(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    # aggregate file_count without loading all files
    visible_count = func.sum(
        case((models.TransferFile.receiver_deleted_at.is_(None), 1), else_=0)
    )
    q = (
        db.query(
            models.Transfer.id.label("transfer_id"),
            models.User.email.label("sender_email"),
            models.Transfer.created_at,
            models.Transfer.status,
            visible_count.label("file_count"),
        )
        .join(models.User, models.User.id == models.Transfer.sender_id)
        .outerjoin(models.TransferFile, models.TransferFile.transfer_id == models.Transfer.id)
        .filter(models.Transfer.receiver_id == user.id)
        .group_by(models.Transfer.id, models.User.email, models.Transfer.created_at, models.Transfer.status)
        .having(visible_count > 0)
        .order_by(models.Transfer.created_at.desc())
    )
    rows = q.all()
    return [
        schemas.TransferListItem(
            transfer_id=r.transfer_id,
            sender_email=r.sender_email,
            receiver_email=user.email,
            file_count=int(r.file_count or 0),
            created_at=r.created_at,
            status=r.status,
        )
        for r in rows
    ]


@router.get("/sent", response_model=list[schemas.TransferListItem])
def list_sent(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    visible_count = func.sum(
        case((models.TransferFile.sender_deleted_at.is_(None), 1), else_=0)
    )
    q = (
        db.query(
            models.Transfer.id.label("transfer_id"),
            models.User.email.label("receiver_email"),
            models.Transfer.created_at,
            models.Transfer.status,
            visible_count.label("file_count"),
        )
        .join(models.User, models.User.id == models.Transfer.receiver_id)
        .outerjoin(models.TransferFile, models.TransferFile.transfer_id == models.Transfer.id)
        .filter(models.Transfer.sender_id == user.id)
        .group_by(models.Transfer.id, models.User.email, models.Transfer.created_at, models.Transfer.status)
        .having(visible_count > 0)
        .order_by(models.Transfer.created_at.desc())
    )
    rows = q.all()
    return [
        schemas.TransferListItem(
            transfer_id=r.transfer_id,
            sender_email=user.email,
            receiver_email=r.receiver_email,
            file_count=int(r.file_count or 0),
            created_at=r.created_at,
            status=r.status,
        )
        for r in rows
    ]


@router.get("/{transfer_id}/files", response_model=list[schemas.TransferFileOut])
def list_transfer_files(
    transfer_id: int,
    x_transfer_token: Optional[str] = Header(default=None, alias="X-Transfer-Token"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    transfer = db.query(models.Transfer).filter(models.Transfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

    # sender can access without code
    if transfer.sender_id != user.id:
        # receiver must present transfer token
        if transfer.receiver_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        _require_receiver_transfer_token(transfer_id, user, x_transfer_token)

    q = db.query(models.TransferFile).filter(models.TransferFile.transfer_id == transfer_id)
    if transfer.sender_id == user.id:
        q = q.filter(models.TransferFile.sender_deleted_at.is_(None))
    elif transfer.receiver_id == user.id:
        q = q.filter(models.TransferFile.receiver_deleted_at.is_(None))
    files = q.order_by(models.TransferFile.created_at.asc()).all()
    return files


@router.get("/{transfer_id}/files/{file_id}/download")
def download_transfer_file(
    transfer_id: int,
    file_id: int,
    x_transfer_token: Optional[str] = Header(default=None, alias="X-Transfer-Token"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    transfer = db.query(models.Transfer).filter(models.Transfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

    tf = db.query(models.TransferFile).filter(models.TransferFile.id == file_id, models.TransferFile.transfer_id == transfer_id).first()
    if not tf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if transfer.sender_id != user.id:
        if transfer.receiver_id != user.id:
            audit_log.info("transfer_download_denied user_id=%s transfer_id=%s file_id=%s", user.id, transfer_id, file_id)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        _require_receiver_transfer_token(transfer_id, user, x_transfer_token)
        # If receiver has deleted it from their portal, hide it.
        if tf.receiver_deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    else:
        # Sender-side soft delete hides it from sender portal.
        if tf.sender_deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    storage_dir = _get_storage_dir()
    path = (storage_dir / tf.stored_filename).resolve()
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File missing on server")

    audit_log.info("transfer_download_success user_id=%s transfer_id=%s file_id=%s", user.id, transfer_id, file_id)
    media_type = tf.content_type or "application/octet-stream"
    return FileResponse(path, filename=tf.original_filename, media_type=media_type)


@router.delete("/{transfer_id}/files/{file_id}")
def delete_transfer_file(
    transfer_id: int,
    file_id: int,
    x_transfer_token: Optional[str] = Header(default=None, alias="X-Transfer-Token"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    transfer = db.query(models.Transfer).filter(models.Transfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

    tf = (
        db.query(models.TransferFile)
        .filter(models.TransferFile.id == file_id, models.TransferFile.transfer_id == transfer_id)
        .first()
    )
    if not tf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    # Sender can delete without code. Receiver needs transfer token.
    if transfer.sender_id != user.id:
        if transfer.receiver_id != user.id:
            audit_log.info("transfer_delete_denied user_id=%s transfer_id=%s file_id=%s", user.id, transfer_id, file_id)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        _require_receiver_transfer_token(transfer_id, user, x_transfer_token)

    storage_dir = _get_storage_dir()
    path = (storage_dir / tf.stored_filename).resolve()

    try:
        now = datetime.utcnow()

        # Soft delete for the acting user only.
        if transfer.sender_id == user.id:
            tf.sender_deleted_at = now
        elif transfer.receiver_id == user.id:
            tf.receiver_deleted_at = now
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

        db.flush()

        # If BOTH sides deleted, we can hard-delete DB row + disk file.
        hard_deleted = False
        if tf.sender_deleted_at is not None and tf.receiver_deleted_at is not None:
            db.delete(tf)
            hard_deleted = True

        db.commit()

        if hard_deleted:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass

        # Remaining visible files for THIS user (used by UI)
        if transfer.sender_id == user.id:
            remaining_visible = (
                db.query(models.TransferFile)
                .filter(models.TransferFile.transfer_id == transfer_id, models.TransferFile.sender_deleted_at.is_(None))
                .count()
            )
        else:
            remaining_visible = (
                db.query(models.TransferFile)
                .filter(models.TransferFile.transfer_id == transfer_id, models.TransferFile.receiver_deleted_at.is_(None))
                .count()
            )

        audit_log.info(
            "transfer_delete_success user_id=%s transfer_id=%s file_id=%s hard_deleted=%s",
            user.id,
            transfer_id,
            file_id,
            hard_deleted,
        )
        return {"deleted": True, "hard_deleted": hard_deleted, "remaining_visible_files": int(remaining_visible)}
    except Exception as e:
        db.rollback()
        audit_log.error("transfer_delete_failed user_id=%s transfer_id=%s file_id=%s error=%s", user.id, transfer_id, file_id, str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete file")


@router.get("/{transfer_id}/download-all")
def download_all_zip(
    transfer_id: int,
    x_transfer_token: Optional[str] = Header(default=None, alias="X-Transfer-Token"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    transfer = db.query(models.Transfer).filter(models.Transfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

    if transfer.sender_id != user.id:
        if transfer.receiver_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        _require_receiver_transfer_token(transfer_id, user, x_transfer_token)

    q = db.query(models.TransferFile).filter(models.TransferFile.transfer_id == transfer_id)
    if transfer.sender_id == user.id:
        q = q.filter(models.TransferFile.sender_deleted_at.is_(None))
    elif transfer.receiver_id == user.id:
        q = q.filter(models.TransferFile.receiver_deleted_at.is_(None))
    files = q.all()
    if not files:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No files in transfer")

    storage_dir = _get_storage_dir()
    # Use a sized ZipStream (no compression) so Content-Length is known
    zs = ZipStream(compress_type=ZIP_STORED, sized=True)

    used_names: set[str] = set()
    for tf in files:
        p = (storage_dir / tf.stored_filename).resolve()
        if not p.exists():
            continue
        arcname = _safe_original_name(tf.original_filename)
        # dedupe filenames inside zip
        if arcname in used_names:
            base = arcname
            idx = 2
            while f"{base} ({idx})" in used_names:
                idx += 1
            arcname = f"{base} ({idx})"
        used_names.add(arcname)
        zs.add_path(str(p), arcname)

    headers = {
        "Content-Disposition": f'attachment; filename="transfer_{transfer_id}.zip"',
    }
    try:
        headers["Content-Length"] = str(len(zs))
    except TypeError:
        # Size unknown (shouldn't happen with sized=True), omit header
        pass
    if zs.last_modified:
        # Starlette expects header values as strings (RFC 1123 format)
        headers["Last-Modified"] = format_datetime(zs.last_modified.replace(tzinfo=timezone.utc), usegmt=True)
    audit_log.info("transfer_zip_download user_id=%s transfer_id=%s", user.id, transfer_id)
    return StreamingResponse(zs, media_type="application/zip", headers=headers)

