from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from pydantic import ConfigDict


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "CLIENT"


class UserLogin(BaseModel):
    # Allow login by username OR email
    username_or_email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class FileUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    original_filename: str
    client_id: Optional[int]
    owner_id: int
    size_bytes: int
    created_at: datetime


class FileAssign(BaseModel):
    client_id: int


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    original_filename: str
    client_id: Optional[int]
    owner_id: int
    size_bytes: int
    created_at: datetime
