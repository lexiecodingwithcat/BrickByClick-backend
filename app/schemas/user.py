# define request body and response body
from pydantic import BaseModel

# schema for outputting user data
class UserBase(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    
  

