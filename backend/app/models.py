from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)  # Nullable for Google OAuth users
    created_at = Column(DateTime, default=datetime.utcnow)

    files_sent = relationship("File", back_populates="sender", foreign_keys="File.sender_id")
    files_received = relationship("File", back_populates="receiver", foreign_keys="File.receiver_id")
    transfers_sent = relationship("Transfer", back_populates="sender", foreign_keys="Transfer.sender_id")
    transfers_received = relationship("Transfer", back_populates="receiver", foreign_keys="Transfer.receiver_id")


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)  # uuid-based safe filename
    stored_path = Column(String, nullable=False)
    size_bytes = Column(BigInteger, nullable=False, default=0)
    content_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", back_populates="files_sent", foreign_keys=[sender_id])
    receiver = relationship("User", back_populates="files_received", foreign_keys=[receiver_id])


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    access_code_hash = Column(String, nullable=False)
    code_hint = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending", index=True)
    opened_at = Column(DateTime, nullable=True)
    failed_attempts = Column(Integer, nullable=False, default=0)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    sender = relationship("User", back_populates="transfers_sent", foreign_keys=[sender_id])
    receiver = relationship("User", back_populates="transfers_received", foreign_keys=[receiver_id])
    files = relationship("TransferFile", back_populates="transfer", cascade="all, delete-orphan")


class TransferFile(Base):
    __tablename__ = "transfer_files"

    id = Column(Integer, primary_key=True, index=True)
    transfer_id = Column(Integer, ForeignKey("transfers.id"), nullable=False, index=True)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    size_bytes = Column(BigInteger, nullable=False, default=0)
    content_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    # Soft-delete per side: hide from sender/receiver portal only
    sender_deleted_at = Column(DateTime, nullable=True, index=True)
    receiver_deleted_at = Column(DateTime, nullable=True, index=True)

    transfer = relationship("Transfer", back_populates="files")
