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
from passlib.context import CryptContext
import os



app = FastAPI()

# create tables in database
Base.metadata.create_all(bind=engine)
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[UserModel, Depends(get_current_user)]
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def initial_admin(db: Session):
    db_user = db.query(UserModel).filter(UserModel.email == "test@example.com").first()
    if db_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Email already registered")

    # Encrypt the password
    hashed_password = pwd_context.hash(os.getenv("ADMIN_PASSWORD"))
    db_user = UserModel(first_name="test", last_name="demo",
                   email="test@example.com", password=hashed_password, is_admin=True)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

@app.on_event("startup")
async def startup_event():
    # Get a database session
    db: Session = next(get_db())
    initial_admin(db)


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
