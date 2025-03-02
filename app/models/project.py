from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, func, Enum, Interval, event
from app.database import Base
from enum import Enum as PyEnum
from sqlalchemy.orm import column_property
from datetime import timedelta


# ProjectStatus is a python enumeration that represents the status of a project
class ProjectStatus(PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"

class ProjectPriority(PyEnum):
    HIGH ="high"
    MEDIUM ="medium"
    LOW = "low"

# Project model
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable= False, default = 1)
    name = Column(String(50), nullable=False, unique=True)
    current_assignee = Column(Integer, ForeignKey("users.id"), nullable=True, default= None)
    priority = Column(Enum(ProjectPriority), nullable=False, default=ProjectPriority.LOW)
    address = Column(String(100), nullable=False)
    postal_code = Column(String(10), nullable = True)
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
    budget = Column(Float, nullable=False)
    status = Column(
        Enum(ProjectStatus), nullable=False, default=ProjectStatus.PENDING
    )  # DB Enum type
    start_date = Column(DateTime(timezone=True), nullable=True)
    estimated_duration = Column(Integer, nullable=True)  # in days
    end_date = Column(DateTime(timezone=True), nullable=True)
    actual_end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
  
@event.listens_for(Project, 'before_insert')
@event.listens_for(Project, 'before_update')
def calculate_end_date(mapper, connection, target):
    if target.start_date and target.estimated_duration:
        target.end_date = target.start_date + timedelta(days=target.estimated_duration)