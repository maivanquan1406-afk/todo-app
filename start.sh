#!/bin/bash
set -euo pipefail

PORT=${PORT:-8000}
DATA_DIR=${PERSIST_DIR:-/data}

# When DATABASE_URL is not provided we fall back to a persistent sqlite file.
if [[ -z "${DATABASE_URL:-}" ]]; then
	if [[ -n "$DATA_DIR" ]]; then
		mkdir -p "$DATA_DIR"
		DEFAULT_DB_PATH="${DATA_DIR%/}/todo.db"
		if [[ "$DEFAULT_DB_PATH" = /* ]]; then
			export DATABASE_URL="sqlite:////${DEFAULT_DB_PATH#/}"
		else
			export DATABASE_URL="sqlite:///${DEFAULT_DB_PATH}"
		fi
		touch "$DEFAULT_DB_PATH"
		echo "DATABASE_URL not provided. Using SQLite at $DEFAULT_DB_PATH"
	else
		export DATABASE_URL="sqlite:///./todo.db"
		echo "DATABASE_URL not provided. Using default ./todo.db"
	fi
fi

# Ensure the directory for sqlite URLs exists so data is not lost between restarts.
if [[ "$DATABASE_URL" == sqlite:////* ]]; then
	SQLITE_PATH="/${DATABASE_URL#sqlite:////}"
	SQLITE_DIR="$(dirname "$SQLITE_PATH")"
	mkdir -p "$SQLITE_DIR"
	touch "$SQLITE_PATH"
fi

exec gunicorn --workers 4 --bind 0.0.0.0:"$PORT" app.main:app
