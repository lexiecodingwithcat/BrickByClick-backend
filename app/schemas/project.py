from pydantic import BaseModel, Field, model_serializer
from typing import Optional, List, Union
from datetime import datetime
from app.models.project import ProjectStatus, ProjectPriority


# schema for outputting project data
class ProjectBase(BaseModel):
    id: int
    company_id: Optional[int] = 1
    name: str = Field(..., max_length=50)
    current_assignee: Optional[int] = None
    priority: ProjectPriority
    address: str = Field(..., max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    city_id: int
    province_id: int
    budget: float
    status: ProjectStatus
    start_date: Optional[datetime] = None
    estimated_duration: Optional[int] = None
    end_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    actual_budget: Optional[float] = None

    @model_serializer(mode="plain")
    def serialize(self):
        data = self.__dict__.copy()
        if abs(data["budget"]) >= 1000:
            data["budget"] = f"{data['budget']:,.2f}"
        else:
            data["budget"] = f"{data['budget']:.2f}"
        return data

    class Config:
        from_attributes = True


# create project
class ProjectCreate(BaseModel):
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

    class Config:
        from_attributes = True


# update project
class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    current_assignee: Optional[int]
    priority: Optional[ProjectPriority] = ProjectPriority.LOW
    address: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    city_id: Optional[int]
    province_id: Optional[int]
    budget: Optional[float]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[ProjectStatus] = ProjectStatus.PENDING
    actual_end_date: Optional[Union[datetime, str]] = None

    class Config:
        from_attributes = True


# delete project
class ProjectDelete(BaseModel):
    id: int

    class Config:
        from_attributes = True
