# define request body and response body
from pydantic import BaseModel
from typing import Optional

# schema for outputting user data


class UserBase(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    is_active: bool
    company_id: int

    class Config:
        from_attributes = True


# create a new user


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    is_admin: Optional[bool] = False
    company_id: Optional[int] = 1
    is_active: Optional[bool] = True

    class Config:
        from_attributes = True


# schema for updating user data


class UserUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    password: Optional[str]

    class Config:
        from_attributes = True


#   schema for deleting user data


class UserDelete(BaseModel):
    id: int

    class Config:
        from_attributes = True
