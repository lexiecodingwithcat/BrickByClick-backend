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
from app.models.user import User, Role
from app.models.company import Company
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from app.schemas.user import UserBase
from app.schemas.auth import (
    ActivateEmailResponse,
    ResetPasswordResponse,
    SignUpRequest,
    ForgetPasswordRequest,
    Token,
    SignUpResponse,
    ForgetPasswordResponse,
    VerifyCodeResponse,
)
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

db_dependency = Annotated[Session, Depends(get_db)]


# new user register
@router.post("/signup", response_model=SignUpResponse)
async def register(
    user: SignUpRequest, background_tasks: BackgroundTasks, db: db_dependency
):
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
        email=user.email,
        password=hashed_password,
        company_id=new_company.id,
        is_admin=True,
        role=Role.ADMIN,
        is_active=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {"sub": user.email, "exp": expire}
    activation_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    # activation link
    activation_link = (
        f"{settings.FRONTEND_URL}/activate-account?token={activation_token}"
    )

    # send email with activation link to the user
    background_tasks.add_task(
        send_email,
        email_to=user.email,
        subject="Activate your account",
        template_name="activate_account",
        data={"activation_link": activation_link},
    )
    # print(f"sender email: {settings.MAIL_FROM}")
    # print(f"sender email: {settings.MAIL_USERNAME}")
    # print(f"sender email: {settings.MAIL_PORT}")
    # print(f"sender email: {settings.MAIL_SERVER}")
    # print(f"sender email: {settings.MAIL_FROM_NAME}")
    # print(f"sender email: {settings.MAIL_PASSWORD}")
    # print(f"activation_link: {activation_link}")

    return SignUpResponse(
        email=user.email, company=user.company, created_at=new_user.created_at
    )


# forget password
@router.post("/forget-password", response_model=ForgetPasswordResponse)
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
        template_name="verification_code",
        data={"verification_code": verification_code},
    )
    return ForgetPasswordResponse(email=db_user.email, expires_at=db_user.expires_at)


# verification code
@router.post("/verify-code", response_model=VerifyCodeResponse)
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

    return VerifyCodeResponse(
        email=db_user.email,
        verification_status="successful",
        expires_at=db_user.expires_at,
    )


# reset password
@router.post("/reset-password", response_model=ResetPasswordResponse)
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
    return ResetPasswordResponse(
        email=db_user.email, password_reset_status="successful"
    )


# send activate email
@router.post("/send-activate-email", response_model=ActivateEmailResponse)
async def send_activate_email(
    email: str, background_tasks: BackgroundTasks, db: db_dependency
):
    db_user = db.query(User).filter(User.email == email).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email not found"
        )
    if db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already activated"
        )

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {"sub": email, "exp": expire}
    activation_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    # activation link
    activation_link = (
        f"{settings.FRONTEND_URL}/activate-account?token={activation_token}"
    )

    # send email with activation link to the user
    background_tasks.add_task(
        send_email,
        email_to=email,
        subject="Activate your account",
        template_name="activate_account",
        data={"activation_link": activation_link},
    )

    return ActivateEmailResponse(
        email=email, status="success", message="Activation email sent successfully"
    )


# activate user account
@router.post("/activate-account")
async def activate_account(token: str, db: Session = Depends(db_dependency)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )

    db_user = db.query(User).filter(User.email == email).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if db_user.is_active:
        return {"message": "Account is already activated"}

    # activate the account
    db_user.is_active = True
    db.commit()
    return {"message": "Account activated successfully"}


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

    # check if the user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not active"
        )

    # if there is a valid user, create a token
    token = create_access_token(
        form_data.username, timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "type": "admin" if user.is_admin else "contractor",
    }


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


# create a JWT token
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
