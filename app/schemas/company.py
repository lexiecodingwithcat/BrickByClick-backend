from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CompanyBase(BaseModel):
    name: str = Field(..., max_length=100)
    address: Optional[str] = Field(default=None)
    postal_code: Optional[str] = Field(default=None)
    phone_number: Optional[str] = Field(default=None)
    city_id: Optional[int] = Field(default=0)
    province_id: Optional[int] = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CompanyCreate(BaseModel):
    name: str = Field(..., max_length=100)

    class Config:
        from_attributes = True
