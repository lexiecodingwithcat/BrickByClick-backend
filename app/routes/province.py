from fastapi import HTTPException, APIRouter, Depends
from typing import Annotated, List
from app.database import get_db
from sqlalchemy.orm import Session
from app.schemas.province import ProvinceBase
from app.schemas.city import CityBase
from app.models.province import Province
from app.models.city import City
from starlette import status


router = APIRouter(tags=["provinces"], prefix="/provinces")
db_dependence = Annotated[Session, Depends(get_db)]


@router.post("/", response_model=List[ProvinceBase])
async def get_all_provinces(db: db_dependence):
    db_provinces = db.query(Province).all()
    return [ProvinceBase.model_validate(province) for province in db_provinces]


@router.post("/{province_id}/cities", response_model=List[CityBase])
async def get_cities_by_province(db: db_dependence, province_id: int):
    db_cities = db.query(City).filter(City.province_id == province_id).all()
    if not db_cities:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No cities found for this province.",
        )
    return [CityBase.model_validate(city) for city in db_cities]
