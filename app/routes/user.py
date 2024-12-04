from fastapi import APIRouter, HTTPException, Depends
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing import Annotated, List
from app.models.user import User
from app.schemas.user import UserBase, UserCreate, UserUpdate
from app.database import get_db
from app.routes.auth import get_current_user
from starlette import status


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user


@router.post("/", response_model=UserBase)
async def create_user(user: UserCreate, db: db_dependency, current_user: User = Depends(get_current_user)):
    # check if the current user is an admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not enough permissions")
    # check if the user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Email already registered")
    # encrypt the password
    hashed_password = pwd_context.hash(user.password)
    db_users = User(first_name=user.first_name, last_name=user.last_name,
                    email=user.email, password=hashed_password, is_admin=user.is_admin)

    db.add(db_users)
    db.commit()
    db.refresh(db_users)
    return db_users


@router.put("/{id}", response_model=UserBase)
async def update_user(id: int, user: UserUpdate, db: db_dependency, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not enough permissions")
    db_user = db.query(User).filter(User.id == id).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.first_name is not None:
        db_user.first_name = user.first_name
    if user.last_name is not None:
        db_user.last_name = user.last_name
    if user.email is not None:
        db_user.email = user.email
    if user.password is not None:
        db_user.password = pwd_context.hash(user.password)
    if user.is_admin is not None:
        db_user.is_admin = user.is_admin
    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{id}", status_code=204)
def delete_user(id: int, db: db_dependency, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not enough permissions")
    db_user = db.query(User).filter(User.id == id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return db_user
