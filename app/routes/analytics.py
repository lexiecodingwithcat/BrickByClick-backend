from fastapi import HTTPException, APIRouter, Depends
from typing import Annotated, List, Optional
from sqlalchemy.orm import Session
from app.database import get_db


router = APIRouter(tags=["analytics"], prefix="/analytics")
db_dependence = Annotated[Session, Depends(get_db)]


@router.post("/budget")
async def get_budget(
    db: db_dependence, start_date: Optional[str] = None, end_date: Optional[str] = None
):
    pass
