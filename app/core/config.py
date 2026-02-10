from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    APP_NAME: str = "ToDo App"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # Database - Railway provides DATABASE_URL with PostgreSQL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./todo.db"  # Default to SQLite for local dev
    )
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # CORS & Hosts
    ALLOWED_HOSTS: list = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    
    # Cookie settings
    COOKIE_SECURE: bool = ENVIRONMENT == "production"
    COOKIE_HTTPONLY: bool = True
    COOKIE_SAMESITE: str = "lax"

    class Config:
        env_file = ".env"

settings = Settings()

