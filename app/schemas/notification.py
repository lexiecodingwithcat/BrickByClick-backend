from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class NotificationBase(BaseModel):
    title: str = Field(..., max_length=100)
    content: Optional[str] = Field(default=None)
    project_id: int = Field(default=0)
    task_id: int = Field(default=0)
    to_user_id: int = Field(default=0)
    created_at: datetime
    updated_at: datetime


class NotificationCreate(BaseModel):
    title: str = Field(..., max_length=100)
    content: Optional[str] = Field(default=None)
    task_id: int = Field(default=0)
    to_user_id: int = Field(default=0)

    class Config:
        from_attributes = True
