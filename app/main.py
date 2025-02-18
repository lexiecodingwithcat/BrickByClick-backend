from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated
from app.database import SessionLocal, engine, get_db, Base
from sqlalchemy.orm import Session
from app.models.user import User as UserModel
import app.routes.user as User
import app.routes.auth as Auth
import app.routes.project as Project
import starlette.status as status
from app.routes.auth import get_current_user
from fastapi.middleware.cors import CORSMiddleware
from app.init.init_db import (
    initial_company,
    initial_admin,
    initialize_default_countries,
    initialize_canadian_province,
    initialize_canadian_cities,
)
import app.models


# Create a FastAPI instance
app = FastAPI()

Base.metadata.create_all(bind=engine)  # create all tables in database

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[UserModel, Depends(get_current_user)]



@app.on_event("startup")
async def startup_event():
    initialize_default_countries()
    # initialize Canadian provinces
    initialize_canadian_province()
    # initialize Canadian cities
    initialize_canadian_cities()
    # initialize Raynow as first company
    initial_company()
    # initialize admin user
    initial_admin()
    # initialize default countries
                                                                                                                                                                                                                                                                                                                                               

@app.get("/", status_code=status.HTTP_200_OK)
async def read_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )
    return {"User": user}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# user router
app.include_router(User.router)
# auth router
app.include_router(Auth.router)
# project router
app.include_router(Project.router)
