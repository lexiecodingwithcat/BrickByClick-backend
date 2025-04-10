from pydantic import BaseModel, Field
from typing import Optional, List


# Task schema
class TaskBase(BaseModel):
    id: int
    parent_id: Optional[int] = Field(default=None)
    name: str
    sort_order: Optional[int] = 0
    company_id: Optional[int] = 1

    class Config:
        from_attributes = True


# Task schema with children
class TaskWithChildren(TaskBase):
    children: List[TaskBase] = []


class TaskCreate(BaseModel):
    parent_id: Optional[int] = Field(default=None)
    name: str = Field(..., max_length=50)
    sort_order: Optional[int] = 0

    class Config:
        from_attributes = True
