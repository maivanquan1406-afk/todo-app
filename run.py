#!/usr/bin/env python
"""
Application runner for production deployment
Supports both gunicorn and uvicorn with auto PORT detection
"""
import os
import sys
import subprocess

def main():
    # Get PORT from environment, default to 8000 for Railway
    port = os.getenv("PORT", "8000")
    
    # Validate port is a number
    try:
        port_int = int(port)
    except ValueError:
        print(f"Error: PORT '{port}' is not a valid port number")
        sys.exit(1)
    
    # Get number of workers (default 1 for Railway free tier to save RAM)
    workers = int(os.getenv("GUNICORN_WORKERS", "1"))
    
    # Build gunicorn command
    cmd = [
        "gunicorn",
        "--workers", str(workers),
        "--worker-class", "sync",
        "--bind", f"0.0.0.0:{port_int}",
        "--timeout", "120",
        "--max-requests", "1000",
        "--max-requests-jitter", "100",
        "--access-logfile", "-",
        "--error-logfile", "-",
        "app.main:app"
    ]
    
    print(f"✅ Starting application on 0.0.0.0:{port_int} with {workers} workers...")
    print(f"📦 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🗄️  Database: {os.getenv('DATABASE_URL', 'sqlite')[:30]}...")
    
    # Execute gunicorn
    os.execvp("gunicorn", cmd)

if __name__ == "__main__":
    main()
