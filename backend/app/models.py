from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="CLIENT")
    created_at = Column(DateTime, default=datetime.utcnow)

    files_owned = relationship("File", back_populates="owner", foreign_keys="File.owner_id")
    files_assigned = relationship("File", back_populates="client", foreign_keys="File.client_id")


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="files_owned", foreign_keys=[owner_id])
    client = relationship("User", back_populates="files_assigned", foreign_keys=[client_id])
