#!/bin/sh
set -e

echo "Waiting for MySQL..."
while ! python -c "import pymysql; pymysql.connect(host='mysql', user='campus_user', password='campus123', database='campus_monitor')" 2>/dev/null; do
    sleep 1
done
echo "MySQL is ready."

echo "Running database migrations..."
alembic upgrade head

echo "Seeding admin user..."
python scripts/seed.py

echo "Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
