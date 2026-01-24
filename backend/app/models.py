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


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    size_bytes = Column(BigInteger, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", back_populates="files_sent", foreign_keys=[sender_id])
    receiver = relationship("User", back_populates="files_received", foreign_keys=[receiver_id])
