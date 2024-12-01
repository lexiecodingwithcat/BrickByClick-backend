from fastapi import FastAPI, HTTPException, Depnds
from pydantic import BaseModel
from typing import List, Annotated
# import database tables
import models
from database import SessionLocal, engine
from sqlalchemy.orm import Session
# import schema
from schemas import userBase

app = FastAPI()
# create tables in database
models.Base.metadata.create_all(bind=engine)


# connect to database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()








