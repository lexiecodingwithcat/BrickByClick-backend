from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, func, Enum
from app.database import Base
from enum import Enum as PyEnum


class TaskStatus(PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"


# ProjectTask model with project, task, and assignee
class ProjectTask(Base):
    __tablename__ = "project_tasks"

    project_id = Column(
        Integer, ForeignKey("projects.id"), primary_key=True, nullable=False
    )
    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True, nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    actual_end_date = Column(DateTime(timezone=True), nullable=True)
    budget = Column(Float, nullable=False)
    amount_due = Column(Float, nullable=False, default=0)
    dependency = Column(Integer, nullable=True)  # task id
    duration = Column(Integer, nullable=False, default=1)  # duration in days
    notes = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
