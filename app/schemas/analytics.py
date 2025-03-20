from pydantic import BaseModel
from typing import List, Optional


class ProjectDurationResponse(BaseModel):
    name: str
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None


class ProjectBudgetResponse(BaseModel):
    name: str
    budget: float


class TaskBudgetResponse(BaseModel):
    task_name: str
    budget: float


class TaskDurationResponse(BaseModel):
    task_name: str
    duration: int


class ProjectSummaryResponse(BaseModel):
    project_name: str
    total_budget: float
    estimated_duration: Optional[int]
    actual_duration: Optional[int]
    completion: float
    task_budgets: List[TaskBudgetResponse]
    task_durations: List[TaskDurationResponse]
