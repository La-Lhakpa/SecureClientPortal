import shutil
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


@router.post("/upload", response_model=schemas.FileUploadResponse, dependencies=[Depends(role_required("OWNER"))])
def upload_file(
    upload: UploadFile = UploadFileType(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    filename = upload.filename
    target_path = storage_dir / filename
    with target_path.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    file_record = models.File(
        owner_id=user.id,
        filename=filename,
        stored_path=str(target_path),
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
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
    return FileResponse(path, filename=file_obj.filename, media_type="application/octet-stream")


@router.post("/{file_id}/assign", dependencies=[Depends(role_required("OWNER"))])
def assign_file(file_id: int, payload: schemas.FileAssign, db: Session = Depends(get_db)):
    file_obj = db.query(models.File).filter(models.File.id == file_id).first()
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")

    client = db.query(models.User).filter(models.User.id == payload.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    file_obj.client_id = payload.client_id
    db.commit()
    db.refresh(file_obj)
    return {"message": "Assigned", "file_id": file_id, "client_id": payload.client_id}
