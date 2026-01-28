from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from pydantic import ConfigDict


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v
    
    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleToken(BaseModel):
    id_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    created_at: datetime


class UserPublic(BaseModel):
    """
    Public user fields safe for recipient dropdowns.
    """
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr


class TransferSendResponse(BaseModel):
    transfer_id: int
    receiver: UserPublic
    file_count: int
    created_at: datetime
    generated_access_code: Optional[str] = None


class TransferVerifyRequest(BaseModel):
    access_code: str


class TransferVerifyResponse(BaseModel):
    verified: bool
    transfer_access_token: Optional[str] = None
    failed_attempts: Optional[int] = None


class TransferListItem(BaseModel):
    transfer_id: int
    sender_email: EmailStr
    receiver_email: EmailStr
    file_count: int
    created_at: datetime
    status: str


class TransferFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    transfer_id: int
    original_filename: str
    size_bytes: int
    content_type: Optional[str] = None
    created_at: datetime


class IncomingCountResponse(BaseModel):
    count: int


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class FileUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    original_filename: str
    sender_id: int
    receiver_id: int
    size_bytes: int
    content_type: Optional[str] = None
    stored_filename: Optional[str] = None
    sender: Optional[UserPublic] = None
    receiver: Optional[UserPublic] = None
    created_at: datetime


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    original_filename: str
    sender_id: int
    receiver_id: int
    size_bytes: int
    content_type: Optional[str] = None
    stored_filename: Optional[str] = None
    sender: Optional[UserPublic] = None
    receiver: Optional[UserPublic] = None
    created_at: datetime
