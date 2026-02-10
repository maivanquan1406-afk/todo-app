#!/bin/bash
set -e

# Get PORT from environment, default to 8000
PORT=${PORT:-8000}

# Start gunicorn with dynamic port binding
exec gunicorn --workers 4 --bind 0.0.0.0:$PORT app.main:app
