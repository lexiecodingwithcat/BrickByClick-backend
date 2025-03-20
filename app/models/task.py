from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from app.database import Base


# Task model with parent, user can add tasks
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable= True, default=1)
    parent_id = Column(
        Integer, ForeignKey("tasks.id"), nullable=True, default=None
    )  # parent task id
    name = Column(String(50), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)  # sort order of the task
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
