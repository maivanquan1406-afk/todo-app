#!/usr/bin/env python
"""
Application runner for production deployment
Supports both gunicorn and uvicorn with auto PORT detection
"""
import os
import sys

from app.core.config import logger

def main():
    # Get PORT from Railway environment, default to 8000
    port = os.getenv("PORT", "8000")
    
    # Validate port is a number
    try:
        port_int = int(port)
    except ValueError:
        logger.error("PORT '%s' is not a valid port number", port)
        sys.exit(1)
    
    # Get number of workers (default 1 for Railway free tier to save RAM)
    workers = int(os.getenv("GUNICORN_WORKERS", "1"))
    
    # Build gunicorn command
    cmd = [
        "gunicorn",
        "--workers", str(workers),
        "--worker-class", "uvicorn.workers.UvicornWorker",
        "--bind", f"0.0.0.0:{port_int}",
        "--timeout", "120",
        "--max-requests", "1000",
        "--max-requests-jitter", "100",
        "--access-logfile", "-",
        "--error-logfile", "-",
        "app.main:app"
    ]
    
    env_name = os.getenv('ENVIRONMENT', 'development')
    db_url = os.getenv('DATABASE_URL', 'sqlite')
    logger.info("Starting application on 0.0.0.0:%s with %s workers", port_int, workers)
    logger.info("Environment: %s", env_name)
    logger.info("Database: %s...", db_url[:30])
    
    # Execute gunicorn
    os.execvp("gunicorn", cmd)

if __name__ == "__main__":
    main()
