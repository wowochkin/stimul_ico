#!/bin/bash
set -e

echo "🚀 Starting Railway Django deployment..."

# Set default port if not provided
PORT=${PORT:-8000}
echo "📡 Using port: $PORT"

# Apply database migrations
echo "📁 Applying database migrations..."
python backend/manage.py migrate --noinput

# Collect static files
echo "📦 Collecting static files..."
python backend/manage.py collectstatic --noinput

# Change to backend directory
cd /app/backend

# Start Gunicorn server
echo "🚀 Starting Gunicorn server on port $PORT..."
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    stimul_ico.wsgi:application