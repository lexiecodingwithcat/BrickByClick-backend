from fastapi import HTTPException, APIRouter, Depends
from typing import Annotated, List
from app.database import get_db
from sqlalchemy.orm import Session
from app.schemas.province import ProvinceBase
from app.models.province import Province


router = APIRouter(tags=['provinces'], prefix="/provinces")
db_dependence = Annotated[Session, Depends(get_db)]

@router.get("/", response_model = List[ProvinceBase])
async def get_provinces(db:db_dependence):
    db_provinces = db.query(Province).all()
    return [ProvinceBase.from_orm(province) for province in db_provinces]