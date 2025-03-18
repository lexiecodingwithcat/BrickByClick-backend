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


class ProjectTaskDetail(BaseModel):
    project_id: int
    task_id: int
    assignee_id: Optional[int]
    status: TaskStatus
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    actual_end_date: Optional[datetime]
    budget: float
    amount_due: float
    dependency: Optional[int]
    duration: int
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskWithProjectTask(BaseModel):
    task: TaskBase
    project_task: ProjectTaskDetail


class ProjectWithTasks(BaseModel):
    project: ProjectBase
    tasks: List[TaskWithProjectTask]

    class Config:
        from_attributes: True


class ProjectTaskCreate(BaseModel):
    name: str = Field(..., max_length=50)
    current_assignee: int = Field(default=1)
    priority: Optional[ProjectPriority] = Field(default=ProjectPriority.LOW)
    address: str = Field(..., max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    city_id: int
    province_id: int
    budget: float
    status: Optional[ProjectStatus] = Field(default=ProjectStatus.PENDING)
    start_date: Optional[datetime] = Field(default_factory=datetime.utcnow)
    estimated_duration: Optional[int] = Field(default=1)
    task_ids: Optional[List[int]] = None
    # assignee_id : Optional[int] = None
    company_id: int = Field(default=1)
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
