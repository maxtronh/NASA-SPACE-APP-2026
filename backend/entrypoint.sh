#!/bin/sh
set -e

echo "=== Flame in Freefall Backend Initialization ==="
echo "Executing database migrations (alembic upgrade head)..."
alembic upgrade head || {
    echo "Warning: Alembic migration encountered an error; proceeding with startup..."
}

echo "Starting Uvicorn server..."
exec "$@"
