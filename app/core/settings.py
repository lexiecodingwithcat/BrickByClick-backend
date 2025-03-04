from pydantic_settings import BaseSettings


# Settings
class Settings(BaseSettings):
    # Secret key settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    # Access token settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ADMIN_PASSWORD
    ADMIN_PASSWORD: str

    # Database settings
    DATABASE_URL: str

    # Email settings
    # SERVER_EMAIL: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    FRONTEND_URL: str = "http://localhost:3000"

    # API URL
    API_URL: str

    class Config:
        env_file = ".env"


settings = Settings()
