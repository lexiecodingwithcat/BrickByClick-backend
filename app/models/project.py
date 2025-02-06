from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, func, Enum
from app.database import Base
from enum import Enum as PyEnum


# ProjectStatus is a python enumeration that represents the status of a project
class ProjectStatus(PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NORMAL = "normal"
    DELAYED = "delayed"


# Project model
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    current_assignee = Column(Integer, ForeignKey("users.id"), nullable=False)
    priority = Column(Integer, nullable=False, default=0)
    address = Column(String(100), nullable=False)
    city_id = Column(
        Integer,
        ForeignKey("cities.id"),
        nullable=False,
    )
    province_id = Column(
        Integer,
        ForeignKey("provinces.id"),
        nullable=False,
    )
    postal_code = Column(String(10), nullable=False)
    budget = Column(Float, nullable=False)
    status = Column(
        Enum(ProjectStatus), nullable=False, default=ProjectStatus.PENDING
    )  # DB Enum type
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    estimated_duration = Column(Integer, nullable=True)  # in days
    actual_end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
