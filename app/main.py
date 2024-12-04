from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated
from app.database import SessionLocal, engine, get_db, Base
from sqlalchemy.orm import Session
from app.models.user import User as UserModel
import app.routes.user as User
import app.routes.auth as Auth
import starlette.status as status
from app.routes.auth import get_current_user
from app.init import initial_admin

app = FastAPI()

# create tables in database
Base.metadata.create_all(bind=engine)
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[UserModel, Depends(get_current_user)]

@app.on_event("startup")
async def startup_event():
    initial_admin(db_dependency)


@app.get("/", status_code=status.HTTP_200_OK)
async def read_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return {"User": user}

# user router
app.include_router(User.router)
# auth router
app.include_router(Auth.router)
