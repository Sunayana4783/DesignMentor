#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding curriculum..."
python -m app.curriculum.seeder

echo "Starting server..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
