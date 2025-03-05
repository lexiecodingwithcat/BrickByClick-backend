from pydantic import BaseModel, Field

# from sqlalchemy import List
from typing import Optional, List
from app.models.project_task import TaskStatus
from datetime import datetime
from app.models.project import ProjectPriority, ProjectStatus
from app.schemas.project import ProjectBase
from app.schemas.task import TaskBase


# project detail task list : return three objs: project, task, gantt chart
class ProjectTaskBase(BaseModel):
    project: ProjectBase
    tasks: List[TaskBase]

    class Config:
        from_attributes: True


class ProjectTaskCreate(BaseModel):
    name: str = Field(..., max_length=50)
    current_assignee: Optional[int] = None
    priority: ProjectPriority = ProjectPriority.LOW
    address: str = Field(..., max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    city_id: int
    province_id: int
    budget: float
    status: ProjectStatus = ProjectStatus.PENDING
    start_date: Optional[datetime] = None
    estimated_duration: Optional[int]
    task_ids: Optional[List[int]] = None
    # assignee_id : Optional[int] = None
    company_id: Optional[int] = 1
    # note: Optional[str]=Field(...,max_length=200)

    class Config:
        from_attributes = True


class ProjectTaskUpdate(BaseModel):
    task_id: int
    name: str = Field(..., max_length=50)
    current_assignee: Optional[int] = None
    priority: ProjectPriority = ProjectPriority.LOW
    address: str = Field(..., max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    city_id: int
    province_id: int
    budget: float
    status: ProjectStatus = ProjectStatus.PENDING
    start_date: Optional[datetime] = None
    estimated_duration: Optional[int]
    assignee_id: Optional[int] = None
    company_id: Optional[int]
    note: Optional[str] = Field(..., max_length=200)

    class Config:
        from_attributes = True
