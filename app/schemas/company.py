from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CompanyBase(BaseModel):
    name = str
    address = Optional[str] = None
    postal_code = Optional[str] = None
    phone_number = Optional[str] = None
    city_id = Optional[int] = 0
    province_id = Optional[int] = 0
    phone_number = Optional[str] = None
    created_at = datetime
    updated_at = datetime


class CompanyCreate(BaseModel):
    name = str

    class Config:
        from_attributes = True
