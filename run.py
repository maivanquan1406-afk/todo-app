#!/usr/bin/env python
"""
Application runner for production deployment
Supports both gunicorn and uvicorn with auto PORT detection
"""
import os
import sys
import subprocess

def main():
    # Get PORT from environment, default to 8000
    port = os.getenv("PORT", "8000")
    
    # Validate port is a number
    try:
        port_int = int(port)
    except ValueError:
        print(f"Error: PORT '{port}' is not a valid port number")
        sys.exit(1)
    
    # Get number of workers (default 4, but can be reduced for small instances)
    workers = int(os.getenv("GUNICORN_WORKERS", "4"))
    
    # Build gunicorn command
    cmd = [
        "gunicorn",
        "--workers", str(workers),
        "--worker-class", "sync",
        "--bind", f"0.0.0.0:{port}",
        "--timeout", "120",
        "--access-logfile", "-",
        "--error-logfile", "-",
        "app.main:app"
    ]
    
    print(f"Starting application on port {port} with {workers} workers...")
    
    # Execute gunicorn
    os.execvp("gunicorn", cmd)

if __name__ == "__main__":
    main()
