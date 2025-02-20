from pydantic import BaseModel, Field
from typing import Optional
class TaskBase(BaseModel):
    id:int
    parent_id:Optional[int] = Field(default=None)
    name: str
    sort_order:Optional[int]=0
    company_id:Optional[int]=1
    class Config:
        from_attributes= True

class TaskCreate(BaseModel):
    parent_id:Optional[int] = Field(default=None)
    name:str = Field(...,max_length=50)
    company_id:Optional[int] = 1
    sort_order:Optional[int] = 0

    class Config:
        from_attributes= True


