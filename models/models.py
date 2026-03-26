from database import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Table,
)
from datetime import datetime
from sqlalchemy.orm import relationship

note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    # refresh_token = Column(String, nullable=True, unique=True)
    # refresh_token_expires = Column(DateTime, nullable=True)
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    user = relationship("User", back_populates="notes")
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    tags = relationship("Tag", secondary="note_tags", back_populates="notes")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)

    notes = relationship("Note", secondary="note_tags", back_populates="tags")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    revoked = Column(Boolean, default=False)

    user = relationship("User", back_populates="refresh_tokens")