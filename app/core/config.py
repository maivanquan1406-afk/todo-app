from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from pathlib import Path
import os

import logging
from dotenv import load_dotenv


def _env_bool(key: str, default: bool) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

# Logging config
LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(module)s] %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("todoapp")

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env", override=False)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    APP_NAME: str = "ToDo App"
    APP_DOMAIN: str = os.getenv("APP_DOMAIN", "http://localhost:8000")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    APP_TIMEZONE: str = os.getenv("APP_TIMEZONE", "Asia/Ho_Chi_Minh")
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
    SMTP_USERNAME: str | None = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER")
    SMTP_PASSWORD: str | None = os.getenv("SMTP_PASSWORD")
    SMTP_FROM: str | None = os.getenv("SMTP_FROM")
    SMTP_USE_TLS: bool = _env_bool("SMTP_USE_TLS", True)
    SMTP_USE_SSL: bool = _env_bool("SMTP_USE_SSL", False)
    
    # CORS & Hosts
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]
    
    # Cookie settings
    COOKIE_SECURE: bool = ENVIRONMENT == "production"
    COOKIE_HTTPONLY: bool = True
    COOKIE_SAMESITE: str = "lax"

    # Default admin seeding
    DEFAULT_ADMIN_EMAIL: str | None = os.getenv("DEFAULT_ADMIN_EMAIL")
    DEFAULT_ADMIN_PASSWORD: str | None = os.getenv("DEFAULT_ADMIN_PASSWORD")

    # Reminder scheduler
    REMINDER_ENABLED: bool = _env_bool("REMINDER_ENABLED", True)
    REMINDER_LEAD_MINUTES: int = int(os.getenv("REMINDER_LEAD_MINUTES", "30"))
    REMINDER_CHECK_INTERVAL_SECONDS: int = int(os.getenv("REMINDER_CHECK_INTERVAL_SECONDS", "60"))
    REMINDER_GRACE_PERIOD_MINUTES: int = int(os.getenv("REMINDER_GRACE_PERIOD_MINUTES", "5"))
    REMINDER_MAX_LEAD_MINUTES: int = int(os.getenv("REMINDER_MAX_LEAD_MINUTES", "240"))

    @field_validator("ALLOWED_HOSTS", mode="before")
    def _split_hosts(cls, value):
        if isinstance(value, str):
            return [host.strip() for host in value.split(",") if host.strip()]
        return value

settings = Settings()

# Ready for structured logging in the future
# Example: use structlog or loguru, just replace logger above

