from datetime import datetime, timedelta
from typing import Annotated
from fastapi import Depends, HTTPException, APIRouter
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
# includes common used http status code, make it easier to read
from starlette import status
from app.database import SessionLocal
from app.models.user import User
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import os

router = APIRouter(tags=["auth"], prefix="/auth")

# used to identify and decode JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
# password hashing and unhashing
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# auth is this file while token is the endpoint of API
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

# we use this request to validate before submitting it to DB as a new user


class CreateUserRequest(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def register_user(user: CreateUserRequest, db: db_dependency):

    # check if email is in the database
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Email already registered")

    user = User(email=user.email, password=bcrypt_context.hash(user.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created successfully"}


# if the user is authenticated, return the token
# OAuth2PasswordRequestForm is a class that FastAPI provides to extract the email and password from the request
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate user"
                            )
    # if there is a valid user, create a token
    token = create_access_token(form_data.username, timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": token, "token_type": "bearer"}


# check whether the user is authenticated
def authenticate_user(email: str, password: str, db):
    #  check if the user exists
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    # check if the password matches the hashed password in the database
    if not bcrypt_context.verify(password, user.password):
        return False
    return user

# create a JWT


def create_access_token(email: str, expires_delta: timedelta):
    encode = {"sub": email, "exp": datetime.now() + expires_delta}
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

# decode JWT to get the current user


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)], db: db_dependency):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate user")
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate user")
