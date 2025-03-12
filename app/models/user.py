# define data table
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from app.database import Base
from sqlalchemy.sql import func
from enum import Enum as PyEnum


class Role(PyEnum):
    ADMIN = ("administrator",)
    PM = ("project manager",)
    CONTRACTOR = "contractor"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, default=1)
    first_name = Column(String(50), index=True, nullable=True)
    last_name = Column(String(50), index=True, nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(128), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    role = Column(Enum(Role), default=Role.CONTRACTOR, nullable=False)
    verification_code = Column(String(10), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
