from pydantic_settings import BaseSettings
# BaseSettings is a class that allows us to define the settings for our application
# load the environment variables from the .env file in a safe way automatically


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int


class Config:
    env_file = ".env"


settings = Settings()
