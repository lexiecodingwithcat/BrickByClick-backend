from fastapi import APIRouter, HTTPException, Depends
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing import Annotated, List
from app.models.user import User
from app.schemas.user import UserBase, UserCreate, UserUpdate
from app.database import get_db


# the function of annotated:
# Specify the type: Informs FastAPI and type-checking tools that the type of db_dependency is Session.
# Bind the dependency: Uses Depends(get_db) to tell FastAPI that the Session instance is provided by get_db.
router = APIRouter(tags=["users"], prefix="/users")
db_dependency = Annotated[Session, Depends(get_db)]
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/", response_model=List[UserBase])
async def get_users(db: db_dependency):
    db_users = db.query(User).all()
    return db_users


@router.get("/{id}", response_model=UserBase)
async def get_user(id: int, db: db_dependency):
    db_user = db.query(User).filter(User.id == id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.post("/", response_model=UserBase)
async def create_user(user: UserCreate, db: db_dependency):
    # encrypt the password
    hashed_password = pwd_context.hash(user.password)
    db_users = User(first_name=user.first_name, last_name=user.last_name,
                    email=user.email, password=hashed_password)

    db.add(db_users)
    db.commit()
    db.refresh(db_users)
    return db_users


@router.put("/{id}", response_model=UserBase)
async def update_user(id: int, user: UserUpdate, db: db_dependency):
    db_user = db.query(User).filter(User.id == id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.first_name is not None:
        db_user.first_name = user.first_name
    if user.last_name is not None:
        db_user.last_name = user.last_name
    if user.email is not None:
        db_user.email = user.email
    if user.password is not None:
        db_user.password = pwd_context.hash(user.password)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{id}", status_code=204)
def delete_user(id: int, db: db_dependency):
    db_user = db.query(User).filter(User.id == id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return db_user
