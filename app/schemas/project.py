from pydantic import BaseModel
from typing import Optional
from enum import Enum as PyEnum
from datetime import datetime

class ProjectStatus(PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"

class ProjectPriority(PyEnum):
    HIGH ="high"
    MEDIUM ="medium"
    LOW = "low"

# schema for outputting project data
class ProjectBase(BaseModel):
    id:int
    company_id:int
    name:str = Field(...,max_length=50)
    current_assignee:int
    priority: ProjectPriority = ProjectPriority.LOW
    address:str = Field(...,max_length= 100)
    postal_code: Optional[str]= Field(None, max_length=10)
    city_id:int
    province_id: int
    budget:float
    status: ProjectStatus = ProjectStatus.PENDING
    start_date = datetime
    estimated_duration:Optional[int]
    end_date = datetime
    actual_end_date:Optional[datetime]= None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# create project
class ProjectCreate(BaseModel):
    name:str = Field(...,max_length=50)
    current_assignee:int
    priority: ProjectPriority = ProjectPriority.LOW
    address:str = Field(...,max_length= 100)
    postal_code: Optional[str]= Field(None, max_length=10)
    city_id:int
    province_id: int
    budget:float
    status: ProjectStatus = ProjectStatus.PENDING
    start_date = datetime
    estimated_duration:Optional[int]
    actual_end_date:Optional[datetime]= None

    class Config:
        from_attributes = True

# update project
class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    current_assignee: Optional[int]
    priority: Optional[ProjectPriority] = ProjectPriority.LOW
    address: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    budget: Optional[float]
    status: Optional[ProjectStatus] = ProjectStatus.PENDING
    actual_end_date: Optional[datetime] = None
    class Config:
        from_attributes = True

# delete project
class ProjectDelete(BaseModel):
    id:int

    class Config:
        from_attributes = True

