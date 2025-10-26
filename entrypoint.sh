#!/bin/bash
set -e

echo "🚀 Starting Railway Django deployment..."

# Debug: Show all environment variables
echo "🔍 Environment variables:"
echo "  - PORT: ${PORT:-NOT_SET}"
echo "  - DATABASE_URL: ${DATABASE_URL:+SET}"
echo "  - DJANGO_DEBUG: ${DJANGO_DEBUG:-NOT_SET}"
echo "  - RAILWAY_PUBLIC_DOMAIN: ${RAILWAY_PUBLIC_DOMAIN:-NOT_SET}"

# Set default port if not provided
PORT=${PORT:-8000}
echo "📡 Using port: $PORT"

# Apply database migrations
echo "📁 Applying database migrations..."
cd /app/backend
python manage.py migrate --noinput

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

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