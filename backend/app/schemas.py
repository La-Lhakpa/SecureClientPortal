from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "CLIENT"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class FileUploadResponse(BaseModel):
    id: int
    filename: str
    client_id: Optional[int]
    owner_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class FileAssign(BaseModel):
    client_id: int


class FileOut(BaseModel):
    id: int
    filename: str
    client_id: Optional[int]
    owner_id: int
    created_at: datetime

    class Config:
        orm_mode = True
