#!/bin/bash
set -e

# Render provides DATABASE_URL as postgresql:// but we need postgresql+asyncpg://
# Convert it for SQLAlchemy async
if [ -n "$DATABASE_URL" ]; then
    export DATABASE_URL=$(echo $DATABASE_URL | sed 's|postgres://|postgresql+asyncpg://|g' | sed 's|postgresql://|postgresql+asyncpg://|g')
fi

echo "DATABASE_URL scheme fixed"

echo "Running database migrations..."
# Use sync URL for alembic
SYNC_URL=$(echo $DATABASE_URL | sed 's|postgresql+asyncpg://|postgresql+psycopg2://|g')
DATABASE_URL=$SYNC_URL alembic upgrade head

echo "Seeding curriculum..."
python -m app.curriculum.seeder

echo "Starting server..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
