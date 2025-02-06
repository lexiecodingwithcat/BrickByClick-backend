from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, func, Enum
from app.database import Base
from enum import Enum as PyEnum


class TaskStatus(PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NORMAL = "normal"
    DELAYED = "delayed"


# ProjectTask model with project, task, and assignee
class ProjectTask(Base):
    __tablename__ = "project_tasks"

    project_id = Column(
        Integer, ForeignKey("projects.id"), primary_key=True, nullable=False
    )
    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True, nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    actual_end_date = Column(DateTime(timezone=True), nullable=True)
    budget = Column(Float, nullable=False)
    debt = Column(Float, nullable=False)
    dependency = Column(Integer, nullable=True)  # task id
    notes = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
