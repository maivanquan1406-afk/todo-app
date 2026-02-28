from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os

import logging

# Logging config
LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(module)s] %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("todoapp")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    APP_NAME: str = "ToDo App"
    APP_DOMAIN: str = os.getenv("APP_DOMAIN", "http://localhost:8000")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # Database - Railway provides DATABASE_URL with PostgreSQL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./todo.db"  # Default to SQLite for local dev
    )
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # SMTP / Email
    SMTP_HOST: str | None = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str | None = os.getenv("SMTP_USER")
    SMTP_PASSWORD: str | None = os.getenv("SMTP_PASSWORD")
    
    # CORS & Hosts
    ALLOWED_HOSTS: list = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    
    # Cookie settings
    COOKIE_SECURE: bool = ENVIRONMENT == "production"
    COOKIE_HTTPONLY: bool = True
    COOKIE_SAMESITE: str = "lax"

settings = Settings()

# Ready for structured logging in the future
# Example: use structlog or loguru, just replace logger above

