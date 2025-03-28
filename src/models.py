from datetime import datetime

from sqlalchemy import Column, String, TIMESTAMP, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(UUID, primary_key=True, index=True)
    email = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    registered_at = Column(TIMESTAMP, default=datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)
    is_premium = Column(Boolean, default=False)
    links = relationship("Link", back_populates="owner")


class Link(Base):
    __tablename__ = "link"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    short_code = Column(String, nullable=False, index=True, unique=True)
    original_url = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True)
    clicks = Column(Integer, default=0)
    last_accessed = Column(DateTime, nullable=True)
    owner_id = Column(UUID, ForeignKey("user.id"), nullable=True)
    owner = relationship("User", back_populates="links")


class Query(Base):
    __tablename__ = "query"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    link_id = Column(Integer, nullable=False, index=True)
    user_id = Column(UUID, index=True)
    short_code = Column(String, nullable=False, index=True)
    original_link = Column(String, nullable=False, index=True)
    accessed_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)