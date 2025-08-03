#!/bin/bash
set -e

echo "Starting Prombank MCP deployment..."

# Wait for database to be ready
echo "Waiting for database connection..."
python -c "
import time
import sys
from sqlalchemy import create_engine
from src.prombank.config import settings

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        engine = create_engine(settings.database_url)
        connection = engine.connect()
        connection.close()
        print('Database connection successful!')
        break
    except Exception as e:
        retry_count += 1
        print(f'Database connection attempt {retry_count}/{max_retries} failed: {e}')
        if retry_count >= max_retries:
            print('Failed to connect to database after maximum retries')
            sys.exit(1)
        time.sleep(2)
"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Initialize default data if needed
echo "Initializing default data..."
python -c "
from src.prombank.database import init_db
init_db()
print('Database initialization complete!')
"

# Create necessary directories
mkdir -p /app/data /app/backups

echo "Starting application..."
exec "$@"