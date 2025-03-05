from datetime import datetime, timedelta
from typing import Annotated
from fastapi import Depends, HTTPException, APIRouter, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.email import send_email

# includes common used http status code, make it easier to read
from starlette import status
from app.database import SessionLocal
from app.models.user import User
from app.models.company import Company
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from app.schemas.user import UserBase
from app.schemas.company import CompanyCreate
import random
from app.core.settings import settings

router = APIRouter(tags=["auth"], prefix="/auth")

# used to identify and decode JWT
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
# password hashing and unhashing
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# auth is this file while token is the endpoint of API
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

# we use this request to validate before submitting it to DB as a new user


class CreateUserRequest(BaseModel):
    email: str
    password: str
    company: str


class ForgetPasswordRequest(BaseModel):
    email: str


class Token(BaseModel):
    access_token: str
    token_type: str


db_dependency = Annotated[Session, Depends(get_db)]


# new user register
@router.post("/signup", response_model=UserBase)
async def register(user: CreateUserRequest, db: db_dependency):
    # check if the user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    db_company = db.query(Company).filter(Company.name == user.company).first()
    if db_company is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Company already exists"
        )
    new_company = Company(name=user.company)
    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    # encrypt the password
    hashed_password = bcrypt_context.hash(user.password)
    new_user = User(
        email=user.email, password=hashed_password, company_id=new_company.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# forget password
@router.post("/forget-password", response_model=UserBase)
async def forget_password(
    user: ForgetPasswordRequest, background_tasks: BackgroundTasks, db: db_dependency
):
    # check if the user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email not found"
        )
    verification_code = str(random.randint(10000, 99999))
    db_user.verification_code = verification_code
    db_user.expires_at = datetime.utcnow() + timedelta(minutes=5)  # 5 minutes to verify
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # send email with verification code to the user
    background_tasks.add_task(
        send_email,
        email_to=user.email,
        subject="Verify your email",
        template_name="verification_code.html",
        data={"verification_code": verification_code},
    )
    return db_user


# verification code
@router.post("/verify-code", response_model=UserBase)
async def verify_code(code: str, db: db_dependency):
    db_user = db.query(User).filter(User.verification_code == code).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Invalid verification code"
        )
    if db_user.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Verification code expired"
        )
    return db_user


# reset password
@router.post("/reset-password", response_model=UserBase)
async def reset_password(email: str, password: str, db: db_dependency):
    db_user = db.query(User).filter(User.email == email).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email not found"
        )
    db_user.password = bcrypt_context.hash(password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# if the user is authenticated, return the token
# OAuth2PasswordRequestForm is a class that FastAPI provides to extract the email and password from the request
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user"
        )
    # if there is a valid user, create a token
    token = create_access_token(
        form_data.username, timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    )
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
    expire = datetime.utcnow() + expires_delta
    encode = {"sub": email, "exp": expire}
    # print(f"Token will expire at: {expire}")
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


# decode JWT to get the current user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_bearer)], db: db_dependency
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(payload)
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user-email",
            )
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        return user
    except JWTError:
        # print(f"JWT error{e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user-payload",
        )


# get the current user and check if the user is an admin
async def get_current_admin(
    token: Annotated[str, Depends(oauth2_bearer)], db: db_dependency
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(payload)
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user-email",
            )
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        if not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is not an administrator",
            )
        return user
    except JWTError:
        # print(f"JWT error{e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user-payload",
        )
