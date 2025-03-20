from pydantic import BaseModel

class ProvinceBase(BaseModel):
    id:int
    name:str
    code:str
  

    class Config:
        from_attributes = True