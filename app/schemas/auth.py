from pydantic import BaseModel
from datetime import datetime


class SignUpRequest(BaseModel):
    email: str
    password: str
    company: str


class SignUpResponse(BaseModel):
    email: str
    company: str
    created_at: datetime

    class Config:
        from_attributes = True


class ForgetPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    email: str
    password: str


class ActivateRequest(BaseModel):
    token: str


class ForgetPasswordResponse(BaseModel):
    email: str
    expires_at: datetime

    class Config:
        from_attributes = True


class VerifyCodeResponse(BaseModel):
    email: str
    verification_status: str
    expires_at: datetime

    class Config:
        from_attributes = True


class ResetPasswordResponse(BaseModel):
    email: str
    password_reset_status: str

    class Config:
        from_attributes = True


class ActivateEmailResponse(BaseModel):
    email: str
    status: str
    message: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    type: str
