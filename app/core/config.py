from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "ToDo App"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./todo.db"

    class Config:
        env_file = ".env"

settings = Settings()
