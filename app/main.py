from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated
# import database tables
# import app.models as models
from app.database import SessionLocal, engine, get_db, Base
from sqlalchemy.orm import Session
# from app.models.user import User
import app.routes.user as User

# import schema
# from  import UserBase


app = FastAPI()
# create tables in database
Base.metadata.create_all(bind=engine)
db_dependency = Annotated[Session, Depends(get_db)]

# user router
app.include_router(User.router)
