# define request body and response body
from pydantic import BaseModel
from typing import Optional
# schema for outputting user data


class UserBase(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str

    class Config:
        from_attributes = True

# create a new user


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str

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
